'use strict';

const productsElement = document.querySelector('#products');
const statusElement = document.querySelector('#status');

fetch('/api/products')
  .then((response) => {
    if (!response.ok) throw new Error('Inventory service unavailable');
    return response.json();
  })
  .then(({ products }) => {
    statusElement.textContent = `${products.length} products available`;
    productsElement.innerHTML = products.map((product) => `
      <article class="card">
        <span class="number">PRODUCT ${String(product.id).padStart(2, '0')}</span>
        <h3>${escapeHtml(product.name)}</h3>
        <p>${escapeHtml(product.description)}</p>
        <span class="price">₹${Number(product.price).toLocaleString('en-IN')}</span>
      </article>`).join('');
  })
  .catch((error) => {
    statusElement.textContent = error.message;
  });

function escapeHtml(value) {
  const element = document.createElement('div');
  element.textContent = value;
  return element.innerHTML;
}
