
CREATE TABLE users
(
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    username character varying(50) COLLATE pg_catalog."default" NOT NULL,
    email character varying(100) COLLATE pg_catalog."default" NOT NULL,
    password text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_username_key UNIQUE (username)
)
-- Create the Menu table
CREATE TABLE menu (
    id SERIAL PRIMARY KEY, -- Unique ID for each menu item
    name VARCHAR(255) NOT NULL, -- Name of the menu item
    price NUMERIC(10, 2) NOT NULL -- Price of the menu item
);

-- Insert sample data into the Menu table
INSERT INTO menu (name, price)
VALUES 
    ('Hot Coffee', 80.00),
    ('Black Coffee', 80.00),
    ('Hazelnut Cold Coffee', 125.00),
    ('Chocolate Cold Coffee', 125.00),
    ('Caramel Cold Coffee', 125.00),
    ('Classic Cold Coffee', 100.00),
    ('Iced Americano', 160.00),
    ('Maggie', 30.00);

-- Create the Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY, -- Unique ID for each order
    user_id INT NOT NULL, -- Foreign key referencing the user who placed the order
    total_price NUMERIC(10, 2) NOT NULL, -- Total price for the entire order
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Order timestamp
    name VARCHAR(255) NOT NULL, -- Customer's name
    phone_number VARCHAR(15) NOT NULL, -- Customer's phone number
    email VARCHAR(255) NOT NULL, -- Customer's email address
    address VARCHAR(255) NOT NULL, -- Customer's address
    state VARCHAR(100) NOT NULL, -- State where the customer is located
    city VARCHAR(100) NOT NULL, -- City where the customer is located
    FOREIGN KEY (user_id) REFERENCES users (id) -- Link to the Users table
);



CREATE TABLE order_items (
    id SERIAL PRIMARY KEY, -- Unique ID for each order item
    order_id INT NOT NULL, -- Foreign key referencing the order
    menu_id INT NOT NULL, -- Foreign key referencing the menu item
    quantity INT NOT NULL CHECK (quantity > 0), -- Quantity of the item ordered
    price_per_item NUMERIC(10, 2) NOT NULL, -- Price of a single item at the time of ordering
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE, -- Link to Orders table
    FOREIGN KEY (menu_id) REFERENCES menu (id) -- Link to Menu table
);