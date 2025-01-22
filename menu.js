$(document).ready(function () {
  // Flag to prevent multiple API calls
  let isMenuLoaded = false;

  // Fetch and display menu items
  async function fetchMenu() {
    const menuTableBody = document.getElementById("menu");
    const errorContainer = document.getElementById("error");

    try {
      if (isMenuLoaded) return; // Prevent multiple calls
      isMenuLoaded = true;

      // Clear the table body to prevent duplicates
      menuTableBody.innerHTML = "";

      const response = await fetch("http://localhost:8000/menu");
      if (!response.ok) {
        throw new Error("Failed to fetch menu items");
      }

      const menuItems = await response.json();
      errorContainer.textContent = "";

      if (menuItems.length === 0) {
        const noItemsRow = document.createElement("tr");
        noItemsRow.innerHTML = `
                <td colspan="4" style="text-align: center;">No items available in the menu.</td>
            `;
        menuTableBody.appendChild(noItemsRow);
        return;
      }

      menuItems.forEach((item) => {
        const row = document.createElement("tr");

        // Check if the item is already in the cart
        if (cart[item.id]) {
          // Item is in the cart, display the quantity controls
          row.innerHTML = `
                    <td id="item${item.id}">${item.name}</td>
                    <td id="price${item.id}">Rs.${item.price}</td>
                    <td id="r${item.id}">
                        <button id="minus${
                          item.id
                        }" class="btn minus">-</button>
                        <span>${cart[item.id].quantity}</span>
                        <button id="plus${item.id}" class="btn plus">+</button>
                    </td>
                `;
        } else {
          // Item is not in the cart, display the "Add" button
          row.innerHTML = `
                    <td id="item${item.id}">${item.name}</td>
                    <td id="price${item.id}">Rs.${item.price}</td>
                    <td id="r${item.id}">
                        <button id="${item.id}" class="btn cart" type="button">Add</button>
                    </td>
                `;
        }

        menuTableBody.appendChild(row);
      });
    } catch (error) {
      errorContainer.textContent = `Error: ${error.message}`;
    }
  }

  // Initialize or load cart
  let cart = localStorage.getItem("cart")
    ? JSON.parse(localStorage.getItem("cart"))
    : {};

  updatecart(cart);
  $(".sidebar").hide();

  // Add item to cart
  $(document).on("click", ".cart", function () {
    const ids = $(this).attr("id");
    if (cart[ids]) {
      cart[ids].quantity += 1;
    } else {
      const itemname = $(`#item${ids}`).text();
      const itemprice = parseInt($(`#price${ids}`).text().slice(3));
      cart[ids] = { name: itemname, price: itemprice, quantity: 1 };
    }
    updatecart(cart);
  });

  // Show and hide cart
  $(".cartsidebar").click(function () {
    checkcart(cart);
    $(".sidebar").show(500);
    $(this).hide();
  });

  $(".close").click(function () {
    $(".sidebar").hide(500);
    $(".cartsidebar").show();
  });

  // Adjust item quantity
  $(document).on("click", ".minus", function () {
    const id = this.id.slice(5);
    cart[id].quantity = Math.max(0, cart[id].quantity - 1);
    updatecart(cart);
  });

  $(document).on("click", ".plus", function () {
    const id = this.id.slice(4);
    cart[id].quantity += 1;
    updatecart(cart);
  });

  // Clear cart
  $("#clear").click(function () {
    clearcart(cart);
  });

  // Remove item from cart
  $(document).on("click", ".remove", function () {
    const id = this.id.slice(6);
    cart[id].quantity = 0;
    updatecart(cart);
  });

  // Update cart UI
  function updatecart(cart) {
    for (const item in cart) {
      if (cart[item].quantity === 0) {
        delete cart[item];
        $(`#r${item}`).html(
          `<button id="${item}" class="btn cart" type="button">Add</button>`
        );
      } else {
        $(`#r${item}`).html(` 
          <button id="minus${item}" class="btn minus">-</button>
          <span>${cart[item].quantity}</span>
          <button id="plus${item}" class="btn plus">+</button>
        `);
      }
    }
    localStorage.setItem("cart", JSON.stringify(cart));
    addtocart(cart);
  }

  // Populate cart sidebar
  function addtocart(cart) {
    let str = ``;
    for (const item in cart) {
      str += `
        <div class="row item-card">
          <div class="col">
            <h3>${cart[item].name}</h3>
            <p>Price: Rs.${cart[item].price}</p>
            <p>Quantity: ${cart[item].quantity}</p>
            <button id="remove${item}" class="remove">Remove</button>
          </div>
        </div>
      `;
    }
    $("#cartcontainer").html(str);
    totprice(cart);
  }

  // Calculate total price
  function totprice(cart) {
    let total = 0;
    for (const item in cart) {
      total += cart[item].price * cart[item].quantity;
    }
    $("#lbltotal").text(total);
  }

  // Check if cart is empty
  function checkcart(cart) {
    if (Object.keys(cart).length === 0) {
      $("#divempty").show();
      $("#divcart").hide();
    } else {
      $("#divempty").hide();
      $("#divcart").show();
    }
  }

  // Clear cart
  function clearcart(cart) {
    for (const item in cart) {
      $(`#r${item}`).html(
        `<button id="${item}" class="btn cart" type="button">Add</button>`
      );
    }
    localStorage.clear();
    cart = {};
    updatecart(cart);
  }

  // Fetch menu on page load
  fetchMenu();
});
