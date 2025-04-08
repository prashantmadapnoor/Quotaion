// script.js

let itemCount = 0;
let items = [];

function addItem() {
    itemCount++;

    const tableBody = document.querySelector("#items-table tbody");

    const row = document.createElement("tr");

    row.innerHTML = `
        <td><input type="text" class="serial-number" value="${itemCount}" disabled></td>
        <td><input type="text" class="description" placeholder="Description"></td>
        <td><input type="number" class="quantity" placeholder="Quantity" value="1" onchange="calculateTotal()"></td>
        <td><input type="text" class="units" placeholder="Units"></td>
        <td><input type="number" class="price" placeholder="Price" value="0" onchange="calculateTotal()"></td>
        <td><input type="number" class="gst" placeholder="GST (%)" value="10" onchange="calculateTotal()"></td>
        <td><input type="text" class="gst-amount" disabled></td>
        <td><input type="text" class="total" disabled></td>
        <td><button onclick="removeItem(this)">Remove</button></td>
    `;

    tableBody.appendChild(row);
    items.push(row);
    calculateTotal();
}

function removeItem(button) {
    const row = button.closest("tr");
    row.remove();
    items = items.filter(item => item !== row);
    calculateTotal();
}

function calculateTotal() {
    let grandTotal = 0;

    items.forEach(item => {
        const quantity = parseFloat(item.querySelector(".quantity").value);
        const price = parseFloat(item.querySelector(".price").value);
        const gst = parseFloat(item.querySelector(".gst").value);
        
        const gstAmount = (price * quantity * gst) / 100;
        const total = (price * quantity) + gstAmount;

        item.querySelector(".gst-amount").value = gstAmount.toFixed(2);
        item.querySelector(".total").value = total.toFixed(2);

        grandTotal += total;
    });

    const discount = parseFloat(document.getElementById("discount").value) || 0;
    const tax = parseFloat(document.getElementById("tax").value) || 10;

    const discountAmount = (grandTotal * discount) / 100;
    const taxAmount = (grandTotal * tax) / 100;

    grandTotal -= discountAmount;
    grandTotal += taxAmount;

    document.getElementById("grand-total").innerText = grandTotal.toFixed(2);
}

function generatePDF() {
    const doc = new jsPDF();

    doc.text("Quotation", 20, 20);
    doc.text(`Customer Name: ${document.getElementById("customer-name").value}`, 20, 30);
    doc.text(`Customer Email: ${document.getElementById("customer-email").value}`, 20, 40);
    doc.text(`Customer Phone: ${document.getElementById("customer-phone").value}`, 20, 50);

    let yOffset = 60;

    items.forEach(item => {
        const description = item.querySelector(".description").value;
        const quantity = item.querySelector(".quantity").value;
        const price = item.querySelector(".price").value;
        const gstAmount = item.querySelector(".gst-amount").value;
        const total = item.querySelector(".total").value;

        doc.text(`Description: ${description}, Qty: ${quantity}, Price: ${price}, GST: ${gstAmount}, Total: ${total}`, 20, yOffset);
        yOffset += 10;
    });

    doc.text(`Grand Total: ${document.getElementById("grand-total").innerText}`, 20, yOffset + 10);
    doc.save("quotation.pdf");
}
