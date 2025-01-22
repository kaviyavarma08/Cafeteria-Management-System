from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from passlib.context import CryptContext
import asyncpg
import jwt
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins like ["http://localhost:5500"]
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all HTTP headers
)

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'cafe',
    'user': 'postgres',
    'password': 'root'
}
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.on_event("startup")
async def startup():
    app.state.db = await asyncpg.create_pool(**DB_CONFIG)


@app.on_event("shutdown")
async def shutdown():
    await app.state.db.close()


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


class TokenData(BaseModel):
    username: str


class MenuItem(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    menu_id: int
    quantity: int


class Order(BaseModel):
    name: str
    phone_number: str
    email: str
    address: str
    city: str
    state: str
    items: List[OrderItem]

    class Config:
        from_attributes = True


def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    """Generate a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/signup")
async def signup(data: SignupRequest):
    hashed_password = pwd_context.hash(data.password)
    async with app.state.db.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO users (username, email, password) VALUES ($1, $2, $3)",
                data.username, data.email, hashed_password
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User created successfully!"}


@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    async with app.state.db.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", form_data.username)
        if user and pwd_context.verify(form_data.password, user["password"]):
            token = create_access_token(data={"sub": form_data.username})
            return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username or password")


@app.get("/menu", response_model=List[MenuItem])
async def get_menu():
    async with app.state.db.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, price FROM menu")
        return [dict(row) for row in rows]


@app.post("/orders")
async def create_order(order_request: Order, token: str = Depends(oauth2_scheme)):
    print(order_request.dict())
    try:
        # Decode token to get the user's identity
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        async with app.state.db.acquire() as conn:
            # Fetch user ID
            user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            user_id = user["id"]

            # Calculate total price and validate menu items
            total_price = 0
            for item in order_request.items:
                menu_item = await conn.fetchrow("SELECT price FROM menu WHERE id = $1", item.menu_id)
                if not menu_item:
                    raise HTTPException(status_code=404, detail=f"Menu item {item.menu_id} not found")
                total_price += menu_item["price"] * item.quantity

            # Insert into orders table
            order_id = await conn.fetchval(
                "INSERT INTO orders (user_id, total_price, name, phone_number, email, address, state, city) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id",
                user_id, total_price, order_request.name, order_request.phone_number, order_request.email,
                order_request.address, order_request.state, order_request.city
            )

            # Insert each item into order_items table
            for item in order_request.items:
                menu_item = await conn.fetchrow("SELECT price FROM menu WHERE id = $1", item.menu_id)
                await conn.execute(
                    "INSERT INTO order_items (order_id, menu_id, quantity, price_per_item) VALUES ($1, $2, $3, $4)",
                    order_id, item.menu_id, item.quantity, menu_item["price"]
                )

        return {"message": "Order created successfully!", "order_id": order_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/orders")
async def get_orders(token: str = Depends(oauth2_scheme)):
    """Retrieve all orders for the authenticated user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        async with app.state.db.acquire() as conn:
            # Fetch user ID
            user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user_id = user["id"]
            # Fetch all orders for the user
            orders = await conn.fetch(
                "SELECT * FROM orders WHERE user_id = $1",
                user_id
            )
            # Convert result rows to a list of dictionaries
            result =  [dict(order) for order in orders]
            return result
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/orders/{order_id}")
async def get_order_details(order_id: int, token: str = Depends(oauth2_scheme)):
    """Retrieve details of a specific order."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")

        async with app.state.db.acquire() as conn:
            # Fetch order details including customer information
            order = await conn.fetchrow(
                """
                SELECT o.id, o.name, o.phone_number, o.email, o.address, o.state, o.city, o.order_date, o.status, o.total_price
                FROM orders o
                WHERE o.id = $1
                """,
                order_id
            )
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            # Fetch order items including menu item details
            items = await conn.fetch(
                """
                SELECT oi.quantity, oi.price_per_item, m.name AS menu_item_name, m.price AS menu_item_price
                FROM order_items oi
                JOIN menu m ON oi.menu_id = m.id
                WHERE oi.order_id = $1
                """,
                order_id
            )

            # Combine order and items
            order_data = dict(order)
            order_data["items"] = [
                {"name": item["menu_item_name"], "quantity": item["quantity"], "price_per_item": item["price_per_item"], "total_item_price": item["quantity"] * item["price_per_item"]}
                for item in items
            ]

            return order_data

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

