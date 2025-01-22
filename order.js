$(document).ready(function () {
  let cart = {};

  // Load cart from localStorage
  if (localStorage.getItem("cart") == null) {
    cart = {};
  } else {
    cart = JSON.parse(localStorage.getItem("cart"));
  }
  listcart(cart);
  console.log(cart);
  // Auto-fill Name and Email using token
  const token = localStorage.getItem("token");

  // Submit Order
  $(".submit button").click(function (e) {
    e.preventDefault(); // Prevent form submission reload

    // Validate form
    const name = $("#inputEmail4").val();
    const phone = $("#inputPassword4").val();
    const email = $("#inputAddress").val();
    const address = $("#inputAddress2").val();
    const city = $("#inputCity").val();
    const state = $("#inputState").val();

    if (!name || !phone || !email || !address || !city || !state) {
      alert("Please fill all fields to submit your order.");
      return;
    }

    // Prepare the order data
    const orderData = {
      name: name,
      phone_number: phone, // Using phone_number as per FastAPI model
      email: email,
      address: address,
      city: city,
      state: state,
      items: [], // Will populate with cart items
    };

    // Populate order items from cart
    for (let item in cart) {
      orderData.items.push({
        menu_id: item,
        quantity: cart[item].quantity,
      });
    }

    // API call to submit the order
    console.log(orderData);
    fetch("http://localhost:8000/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`, // Add token for authentication
      },
      body: JSON.stringify(orderData),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to submit order. Please try again.");
        }
        return response.json();
      })
      .then((data) => {
        alert(
          "Order submitted successfully! Your order ID is " + data.order_id
        );
        localStorage.setItem("order_id", data.order_id);
        localStorage.removeItem("cart"); // Clear cart after submission
        window.location.href = "trackorder.html"; // Redirect to tracking page
      })
      .catch((err) => {
        console.error(err);
        alert(
          "An error occurred while submitting your order. Please try again."
        );
      });
  });
});

// Function to list cart items in the order summary
function listcart(cart) {
  let str_order = ``;
  for (let item in cart) {
    str_order += `<div class="row">
          <div class="col">
            ${cart[item].name}
          </div>
          <div class="col">
            x${cart[item].quantity}
          </div>
          <div class="col">
            = Rs.${cart[item].price * cart[item].quantity}
          </div>
        </div>`;
  }

  if (str_order == ``)
    str_order = `<h5 class='default'> Your Cart is Empty. Click here to Go to Menu </h5>`;
  document.getElementById("items").innerHTML = str_order;
}
