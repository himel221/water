// ===== Admin Inventory JavaScript - Complete =====

let currentProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 10;

/**
 * Initialize inventory management
 */
function initializeInventory(products) {
    console.log('📦 Inventory Data:', products);
    console.log('📦 Total Products:', products ? products.length : 0);
    
    currentProducts = products || [];
    filteredProducts = [...currentProducts];
    
    updateStats();
    setupEventListeners();
    renderTable();
}

// ===== Update Stats =====
function updateStats() {
    const total = currentProducts.length;
    const inStock = currentProducts.filter(p => (p.inventory_total || 0) > 20).length;
    const lowStock = currentProducts.filter(p => (p.inventory_total || 0) > 0 && (p.inventory_total || 0) <= 20).length;
    const outOfStock = currentProducts.filter(p => (p.inventory_total || 0) === 0).length;
    
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 4) {
        statNumbers[0].textContent = total;
        statNumbers[1].textContent = inStock;
        statNumbers[2].textContent = lowStock;
        statNumbers[3].textContent = outOfStock;
    }
}

// ===== Setup Event Listeners =====
function setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterProducts, 300));
    }
    
    const stockFilter = document.getElementById('stockFilter');
    if (stockFilter) {
        stockFilter.addEventListener('change', filterProducts);
    }
    
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            document.querySelectorAll('.product-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }
    
    document.getElementById('exportExcel')?.addEventListener('click', function() {
        exportInventory('excel');
    });
    document.getElementById('exportPdf')?.addEventListener('click', function() {
        exportInventory('pdf');
    });
    document.getElementById('refreshBtn')?.addEventListener('click', function() {
        location.reload();
    });
    
    // View Product
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view');
        if (viewBtn) {
            const productId = viewBtn.dataset.productId;
            if (productId) viewProduct(productId);
        }
    });
    
    // Add Stock
    document.addEventListener('click', function(e) {
        const addStockBtn = e.target.closest('.btn-add-stock');
        if (addStockBtn) {
            const productId = addStockBtn.dataset.productId;
            if (productId) openAddStockModal(productId);
        }
    });
    
    // 🔥 Edit Inventory Product
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit-inventory');
        if (editBtn) {
            e.preventDefault();
            const productId = editBtn.dataset.productId;
            if (productId) {
                editInventoryProduct(productId);
            }
        }
    });
    
    // 🔥 Delete Inventory Product
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete-inventory');
        if (deleteBtn) {
            e.preventDefault();
            const productId = deleteBtn.dataset.productId;
            if (productId) {
                deleteInventoryProduct(productId);
            }
        }
    });
    
    // Modal Close
    document.getElementById('closeViewModal')?.addEventListener('click', function() {
        document.getElementById('viewProductModal').style.display = 'none';
    });
    document.getElementById('closeStockModal')?.addEventListener('click', function() {
        document.getElementById('addStockModal').style.display = 'none';
    });
    document.getElementById('cancelStockBtn')?.addEventListener('click', function() {
        document.getElementById('addStockModal').style.display = 'none';
    });
    
    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
            }
        });
    });
    
    // Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
        }
    });
    
    // Add Stock Form Submit
    document.getElementById('addStockForm')?.addEventListener('submit', function(e) {
        e.preventDefault();
        saveAddStock();
    });
    
    document.getElementById('addStockQuantity')?.addEventListener('input', function() {
        updateStockPreview();
    });
    
    // Pagination
    document.querySelectorAll('.page-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (this.id === 'prevPage') {
                changePage(-1);
            } else if (this.id === 'nextPage') {
                changePage(1);
            } else {
                const page = parseInt(this.textContent);
                if (!isNaN(page)) {
                    goToPage(page);
                }
            }
        });
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ===== Filter Products =====
function filterProducts() {
    const searchInput = document.getElementById('searchInput');
    const stockFilter = document.getElementById('stockFilter');
    
    const search = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const stock = stockFilter ? stockFilter.value : 'all';
    
    filteredProducts = currentProducts.filter(product => {
        const matchSearch = !search || 
            (product.name || '').toLowerCase().includes(search);
        
        const stockQty = product.inventory_total || 0;
        let matchStock = true;
        if (stock === 'in-stock') matchStock = stockQty > 20;
        else if (stock === 'low-stock') matchStock = stockQty > 0 && stockQty <= 20;
        else if (stock === 'critical') matchStock = stockQty > 0 && stockQty <= 5;
        else if (stock === 'out-of-stock') matchStock = stockQty === 0;
        
        return matchSearch && matchStock;
    });
    
    currentPage = 1;
    renderTable();
}

// ===== Render Table =====
function renderTable() {
    const tbody = document.getElementById('inventoryTableBody');
    const totalCount = document.getElementById('totalCount');
    
    if (!tbody) return;
    
    if (filteredProducts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="no-data">
                    <i class="fas fa-box-open"></i>
                    <h3>No Products Found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </td>
            </tr>
        `;
        if (totalCount) totalCount.textContent = '0';
        updatePagination();
        return;
    }
    
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, filteredProducts.length);
    const pageProducts = filteredProducts.slice(start, end);
    
    let html = '';
    pageProducts.forEach(product => {
        const stockQty = product.inventory_total || 0;
        
        let stockHtml;
        if (stockQty > 20) {
            stockHtml = `<span class="stock-badge in-stock"><i class="fas fa-check-circle"></i> ${stockQty}</span>`;
        } else if (stockQty > 5) {
            stockHtml = `<span class="stock-badge low-stock"><i class="fas fa-exclamation-circle"></i> ${stockQty}</span>`;
        } else if (stockQty > 0) {
            stockHtml = `<span class="stock-badge critical-stock"><i class="fas fa-exclamation-triangle"></i> ${stockQty}</span>`;
        } else {
            stockHtml = `<span class="stock-badge out-of-stock"><i class="fas fa-times-circle"></i> ${stockQty}</span>`;
        }
        
        let statusHtml;
        if (stockQty > 20) {
            statusHtml = `<span class="status-badge active"><i class="fas fa-circle"></i> In Stock</span>`;
        } else if (stockQty > 0) {
            statusHtml = `<span class="status-badge low-stock"><i class="fas fa-circle"></i> Low Stock</span>`;
        } else {
            statusHtml = `<span class="status-badge out-of-stock"><i class="fas fa-circle"></i> Out of Stock</span>`;
        }
        
        const imageHtml = product.image_url ? 
            `<img src="${product.image_url}" alt="${escapeHtml(product.name)}" class="product-image-thumb" />` :
            `<div class="product-image-thumb" style="background: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #ccc;">
                <i class="fas fa-image fa-2x"></i>
            </div>`;
        
        let priceHtml = `<span class="price-current">৳${(product.price || 0).toFixed(2)}</span>`;
        if (product.is_on_sale && product.discount_price) {
            priceHtml += `<span style="display:block; font-size:10px; color:#dc3545;">Sale: ৳${product.discount_price.toFixed(2)}</span>`;
        }
        
        html += `
            <tr>
                <td><input type="checkbox" class="product-checkbox" data-product-id="${product.id}" /></td>
                <td>${imageHtml}</td>
                <td>
                    <span class="product-name-cell">${escapeHtml(product.name)}</span>
                </td>
                <td>${priceHtml}</td>
                <td>${stockHtml}</td>
                <td>
                    <span class="inventory-badge">
                        <i class="fas fa-warehouse"></i> ${product.stock_quantity || 0}
                    </span>
                </td>
                <td>${statusHtml}</td>
                <td>
                    <span style="display: block; font-weight: 500; font-size: 13px;">${formatDate(product.created_at)}</span>
                    <span style="display: block; font-size: 11px; color: #b2bec3;">${formatTime(product.created_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-view" data-product-id="${product.id}" title="View Details"><i class="fas fa-eye"></i></button>
                        <button class="btn-add-stock" data-product-id="${product.id}" title="Add Stock"><i class="fas fa-plus-circle"></i></button>
                        <button class="btn-edit-inventory" data-product-id="${product.id}" title="Edit Inventory"><i class="fas fa-edit"></i></button>
                        <button class="btn-delete-inventory" data-product-id="${product.id}" title="Delete Inventory"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    if (totalCount) totalCount.textContent = filteredProducts.length;
    updatePagination();
    
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        const checkboxes = document.querySelectorAll('.product-checkbox');
        const checked = document.querySelectorAll('.product-checkbox:checked');
        selectAll.checked = checkboxes.length > 0 && checkboxes.length === checked.length;
    }
}

// ===== View Product =====
function viewProduct(productId) {
    const product = currentProducts.find(p => p.id == productId);
    if (!product) {
        showToast('Product not found!', 'error');
        return;
    }
    
    const modal = document.getElementById('viewProductModal');
    const body = document.getElementById('productDetailBody');
    if (!modal || !body) return;
    
    const stockQty = product.inventory_total || 0;
    const stockQuantity = product.stock_quantity || 0;
    const totalAvailable = stockQty + stockQuantity;
    
    body.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            ${product.image_url ? 
                `<img src="${product.image_url}" alt="${escapeHtml(product.name)}" class="modal-product-image" />` :
                `<div style="width: 100%; height: 200px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: #ccc;">
                    <i class="fas fa-image fa-4x"></i>
                </div>`
            }
        </div>
        
        <h4 style="color: #1a2332; margin-bottom: 4px;">${escapeHtml(product.name)}</h4>
        
        <div class="modal-detail-grid">
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-tag"></i> Price</span>
                <span class="value price">৳${(product.price || 0).toFixed(2)}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-boxes"></i> Inventory Stock</span>
                <span class="value stock-value">${stockQty}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-warehouse"></i> Stock Quantity</span>
                <span class="value stock-value">${stockQuantity}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-cubes"></i> Total Available</span>
                <span class="value inventory-value">${totalAvailable}</span>
            </div>
            ${product.is_on_sale && product.discount_price ? `
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-gift"></i> Sale Price</span>
                <span class="value price">৳${product.discount_price.toFixed(2)}</span>
            </div>
            ` : ''}
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-power-off"></i> Status</span>
                <span class="value">
                    ${stockQty > 20 ? '<span class="status-badge active">In Stock</span>' : 
                      stockQty > 0 ? '<span class="status-badge low-stock">Low Stock</span>' : 
                      '<span class="status-badge out-of-stock">Out of Stock</span>'}
                </span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-calendar"></i> Created</span>
                <span class="value">${formatDate(product.created_at)} ${formatTime(product.created_at)}</span>
            </div>
        </div>
        
        ${product.description ? `
        <div style="margin-top: 16px; padding: 12px 16px; background: #f8f9fa; border-radius: 10px;">
            <strong style="color: #2c3e50;">Description:</strong>
            <p style="color: #6c757d; margin-top: 4px; font-size: 14px; line-height: 1.6;">${escapeHtml(product.description)}</p>
        </div>
        ` : ''}
        
        <div style="display: flex; gap: 10px; justify-content: flex-end; padding-top: 16px; border-top: 2px solid #e8ecf1; margin-top: 16px;">
            <button onclick="closeModal('viewProductModal')" class="btn-cancel" style="padding: 8px 20px;">Close</button>
            <button onclick="openAddStockModal(${product.id})" style="padding: 8px 20px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                <i class="fas fa-plus-circle"></i> Add Stock
            </button>
            <button onclick="editInventoryProduct(${product.id})" style="padding: 8px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                <i class="fas fa-edit"></i> Edit Inventory
            </button>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// ===== Open Add Stock Modal =====
function openAddStockModal(productId) {
    const product = currentProducts.find(p => p.id == productId);
    if (!product) {
        showToast('Product not found!', 'error');
        return;
    }
    
    const modal = document.getElementById('addStockModal');
    if (!modal) return;
    
    document.getElementById('stockProductId').value = product.id;
    document.getElementById('stockProductName').textContent = product.name;
    document.getElementById('currentStock').textContent = product.inventory_total || 0;
    document.getElementById('addStockQuantity').value = '';
    document.getElementById('newStockAfterAdd').textContent = product.inventory_total || 0;
    
    modal.style.display = 'flex';
}

// ===== Update Stock Preview =====
function updateStockPreview() {
    const currentStock = parseInt(document.getElementById('currentStock').textContent) || 0;
    const addQuantity = parseInt(document.getElementById('addStockQuantity').value) || 0;
    const newStock = currentStock + addQuantity;
    document.getElementById('newStockAfterAdd').textContent = newStock;
}

// ============================================================
// 🔥 SAVE ADD STOCK - আপডেটেড (product_id সহ URL)
// ============================================================

function saveAddStock() {
    const productId = document.getElementById('stockProductId').value;
    const addQuantity = document.getElementById('addStockQuantity').value;
    
    if (!addQuantity || parseInt(addQuantity) < 1) {
        showToast('Please enter a valid quantity!', 'error');
        return;
    }
    
    const csrfToken = getCookie('csrftoken');
    
    const btn = document.querySelector('#addStockForm .btn-save');
    const originalText = btn ? btn.innerHTML : 'Save';
    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        btn.disabled = true;
    }
    
    // 🔥 product_id সহ URL ব্যবহার করুন
    const url = `/api/inventory/${productId}/add-stock/`;
    console.log('📤 Sending request to:', url);
    console.log('📤 Data:', { quantity: parseInt(addQuantity) });
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({ 
            quantity: parseInt(addQuantity) 
        })
    })
    .then(response => {
        console.log('📥 Response status:', response.status);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || `HTTP ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('📦 Response data:', data);
        if (data.status === 'success') {
            showToast('✅ Stock added successfully!', 'success');
            document.getElementById('addStockModal').style.display = 'none';
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Failed to add stock', 'error');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('❌ Error:', error);
        showToast('❌ Error adding stock: ' + (error.message || 'Please try again.'), 'error');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// ============================================================
// 🔥 DELETE INVENTORY PRODUCT (শুধু ইনভেন্টরি থেকে ডিলিট)
// ============================================================

function deleteInventoryProduct(productId) {
    if (!confirm('⚠️ Are you sure you want to delete this inventory record?\n\nThe product will remain in admin_products.')) {
        return;
    }
    
    const csrfToken = getCookie('csrftoken');
    
    showToast('🔄 Deleting inventory record...', 'info');
    
    fetch(`/api/inventory/${productId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('✅ Inventory record deleted successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('❌ Error deleting inventory record', 'error');
    });
}

// ============================================================
// 🔥 EDIT INVENTORY PRODUCT (শুধু ইনভেন্টরি এডিট)
// ============================================================

function editInventoryProduct(productId) {
    const product = currentProducts.find(p => p.id == productId);
    if (!product) {
        showToast('Product not found!', 'error');
        return;
    }
    
    const currentInventory = product.inventory_total || 0;
    const stockQuantity = product.stock_quantity || 0;
    
    // Prompt with current value
    const newQuantity = prompt(
        `Edit Inventory for: ${product.name}\n\n` +
        `Current Inventory Stock: ${currentInventory}\n` +
        `Stock Quantity (admin_products): ${stockQuantity}\n\n` +
        `Enter new inventory quantity:`,
        currentInventory
    );
    
    if (newQuantity === null) return; // Cancel
    
    const quantity = parseInt(newQuantity);
    if (isNaN(quantity) || quantity < 0) {
        showToast('❌ Please enter a valid quantity (0 or more)', 'error');
        return;
    }
    
    const csrfToken = getCookie('csrftoken');
    
    showToast('🔄 Updating inventory...', 'info');
    
    fetch(`/api/inventory/${productId}/edit/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            inventory_quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('✅ Inventory updated successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('❌ Error updating inventory', 'error');
    });
}

// ============================================================
// 🔥 SETUP ADD INVENTORY MODAL
// ============================================================

function setupAddInventoryModal() {
    const modal = document.getElementById('addInventoryModal');
    const openBtn = document.getElementById('openAddInventoryBtn');
    const closeBtn = document.getElementById('closeInventoryModal');
    const cancelBtn = document.getElementById('cancelInventoryBtn');
    const form = document.getElementById('addInventoryForm');
    const productNameInput = document.getElementById('productNameInput');
    const quantityInput = document.getElementById('inventoryQuantity');
    const notesInput = document.getElementById('inventoryNotes');
    
    // Check if elements exist
    if (!modal || !openBtn || !form) {
        console.warn('⚠️ Required elements not found for add inventory modal');
        return;
    }
    
    // Open Modal
    openBtn.addEventListener('click', function() {
        modal.classList.add('show');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        if (form) form.reset();
        if (productNameInput) productNameInput.focus();
    });
    
    // Close Modal functions
    function closeModalFunc() {
        modal.classList.remove('show');
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
    
    if (closeBtn) closeBtn.addEventListener('click', closeModalFunc);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModalFunc);
    
    // Close on overlay click
    modal.addEventListener('click', function(e) {
        if (e.target === this) closeModalFunc();
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('show')) closeModalFunc();
    });
    
    // Enter key to submit
    if (productNameInput) {
        productNameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (quantityInput) quantityInput.focus();
            }
        });
    }
    
    if (quantityInput) {
        quantityInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                form.dispatchEvent(new Event('submit'));
            }
        });
    }
    
    // Form Submit
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!productNameInput || !quantityInput) {
            showToast('Form elements not found!', 'error');
            return;
        }
        
        const productName = productNameInput.value.trim();
        const quantity = parseInt(quantityInput.value);
        const notes = notesInput ? notesInput.value.trim() : '';
        
        // Validation
        if (!productName) {
            showToast('Please enter product name!', 'error');
            productNameInput.focus();
            productNameInput.style.borderColor = '#dc3545';
            setTimeout(() => {
                productNameInput.style.borderColor = '';
            }, 3000);
            return;
        }
        
        if (!quantity || quantity < 1) {
            showToast('Please enter a valid quantity!', 'error');
            quantityInput.focus();
            quantityInput.style.borderColor = '#dc3545';
            setTimeout(() => {
                quantityInput.style.borderColor = '';
            }, 3000);
            return;
        }
        
        // Check if product already exists
        const existingProduct = currentProducts.find(p => 
            p.name.toLowerCase() === productName.toLowerCase()
        );
        
        if (existingProduct) {
            // Product exists, add stock to existing product
            if (confirm(`Product "${productName}" already exists with ${existingProduct.inventory_total || 0} units.\nDo you want to add ${quantity} more?`)) {
                addStockToExistingProduct(existingProduct.id, productName, quantity, notes);
            }
            return;
        }
        
        // Product doesn't exist - Create using new API
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
        const submitBtn = form.querySelector('.btn-submit-modal');
        const originalText = submitBtn ? submitBtn.innerHTML : 'Create';
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
            submitBtn.disabled = true;
        }
        
        const productData = {
            name: productName,
            quantity: quantity,
            price: 0,
            description: notes || ''
        };
        
        console.log('📤 Creating product via API:', productData);
        
        fetch('/api/inventory/add-product-by-name/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            body: JSON.stringify(productData)
        })
        .then(response => {
            console.log('📥 Response status:', response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || data.error || `HTTP ${response.status}`);
                }).catch(() => {
                    throw new Error(`HTTP ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('✅ Response data:', data);
            if (data.status === 'success') {
                showToast('✅ ' + data.message, 'success');
                closeModalFunc();
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast('❌ Failed: ' + (data.message || 'Unknown error'), 'error');
                if (submitBtn) {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            showToast('❌ Error: ' + (error.message || 'Please try again.'), 'error');
            if (submitBtn) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    });
}

// ============================================================
// 🔥 ADD STOCK TO EXISTING PRODUCT
// ============================================================

function addStockToExistingProduct(productId, productName, quantity, notes) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    
    showToast('➕ Adding stock to existing product...', 'info');
    
    // 🔥 product_id সহ URL ব্যবহার করুন
    const url = `/api/inventory/${productId}/add-stock/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            quantity: parseInt(quantity)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast('✅ Added ' + quantity + ' units to "' + productName + '"!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast('❌ Failed to add stock: ' + (data.message || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Add stock error:', error);
        showToast('❌ Error adding stock. Please try again.', 'error');
    });
}

// ============================================================
// 🔥 EXPORT INVENTORY
// ============================================================

function exportInventory(format) {
    const url = `/api/inventory/export/${format}/`;
    
    const btn = document.getElementById(format === 'excel' ? 'exportExcel' : 'exportPdf');
    const originalText = btn ? btn.innerHTML : 'Export';
    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;
    }
    
    fetch(url)
        .then(function(response) {
            if (!response.ok) throw new Error('Export failed');
            return response.blob();
        })
        .then(function(blob) {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            const extension = format === 'excel' ? 'xlsx' : 'pdf';
            link.download = 'inventory_' + new Date().toISOString().slice(0,10) + '.' + extension;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
            showToast('✅ Inventory exported successfully as ' + format.toUpperCase() + '!', 'success');
        })
        .catch(function(error) {
            console.error('Export error:', error);
            showToast('❌ Failed to export inventory. Please try again.', 'error');
        })
        .finally(function() {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
}

// ============================================================
// 🔥 HELPER FUNCTIONS
// ============================================================

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            day: '2-digit', 
            month: 'short', 
            year: 'numeric' 
        });
    } catch {
        return 'N/A';
    }
}

function formatTime(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });
    } catch {
        return 'N/A';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
}

// ============================================================
// 🔥 TOAST NOTIFICATION
// ============================================================

function showToast(message, type) {
    type = type || 'info';
    
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = 'toast-notification ' + type;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    document.body.appendChild(toast);
    
    setTimeout(function() {
        if (toast.parentElement) toast.remove();
    }, 5000);
}

// ============================================================
// 🔥 PAGINATION
// ============================================================

function changePage(direction) {
    const totalPages = Math.max(1, Math.ceil(filteredProducts.length / itemsPerPage));
    const newPage = currentPage + direction;
    if (newPage < 1 || newPage > totalPages) return;
    currentPage = newPage;
    renderTable();
    updatePaginationButtons();
}

function goToPage(page) {
    const totalPages = Math.max(1, Math.ceil(filteredProducts.length / itemsPerPage));
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    updatePaginationButtons();
}

function updatePagination() {
    const totalPages = Math.max(1, Math.ceil(filteredProducts.length / itemsPerPage));
    const start = filteredProducts.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, filteredProducts.length);
    
    const startCount = document.getElementById('startCount');
    const endCount = document.getElementById('endCount');
    const totalCount = document.getElementById('totalCount');
    
    if (startCount) startCount.textContent = start;
    if (endCount) endCount.textContent = end;
    if (totalCount) totalCount.textContent = filteredProducts.length;
    
    updatePaginationButtons();
}

function updatePaginationButtons() {
    const totalPages = Math.max(1, Math.ceil(filteredProducts.length / itemsPerPage));
    const paginationContainer = document.querySelector('.pagination-buttons');
    if (!paginationContainer) return;
    
    const pageBtns = paginationContainer.querySelectorAll('.page-btn:not(#prevPage):not(#nextPage)');
    pageBtns.forEach(btn => btn.remove());
    
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        const firstBtn = createPageButton(1);
        paginationContainer.insertBefore(firstBtn, document.getElementById('nextPage'));
        if (startPage > 2) {
            const dots = createDotsButton();
            paginationContainer.insertBefore(dots, document.getElementById('nextPage'));
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const btn = createPageButton(i);
        if (i === currentPage) btn.classList.add('active');
        paginationContainer.insertBefore(btn, document.getElementById('nextPage'));
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const dots = createDotsButton();
            paginationContainer.insertBefore(dots, document.getElementById('nextPage'));
        }
        const lastBtn = createPageButton(totalPages);
        paginationContainer.insertBefore(lastBtn, document.getElementById('nextPage'));
    }
    
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = currentPage === totalPages;
}

function createPageButton(page) {
    const btn = document.createElement('button');
    btn.className = 'page-btn';
    btn.textContent = page;
    btn.addEventListener('click', function() {
        goToPage(page);
    });
    return btn;
}

function createDotsButton() {
    const btn = document.createElement('button');
    btn.className = 'page-btn';
    btn.textContent = '...';
    btn.disabled = true;
    btn.style.cursor = 'default';
    btn.style.opacity = '0.6';
    return btn;
}

// ============================================================
// 🔥 SIDEBAR TOGGLE
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('adminSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const mainContent = document.getElementById('mainContent');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            if (overlay) overlay.classList.toggle('active');
            if (mainContent) mainContent.classList.toggle('sidebar-open');
        });
    }
    
    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
            if (mainContent) mainContent.classList.remove('sidebar-open');
        });
    }
    
    window.addEventListener('resize', function() {
        if (window.innerWidth > 992) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
            if (mainContent) mainContent.classList.remove('sidebar-open');
        }
    });
});

// ============================================================
// 🔥 MAKE FUNCTIONS GLOBAL
// ============================================================

window.initializeInventory = initializeInventory;
window.renderTable = renderTable;
window.filterProducts = filterProducts;
window.viewProduct = viewProduct;
window.openAddStockModal = openAddStockModal;
window.saveAddStock = saveAddStock;
window.exportInventory = exportInventory;
window.showToast = showToast;
window.closeModal = closeModal;
window.goToPage = goToPage;
window.changePage = changePage;
window.setupAddInventoryModal = setupAddInventoryModal;
window.addStockToExistingProduct = addStockToExistingProduct;
window.deleteInventoryProduct = deleteInventoryProduct;
window.editInventoryProduct = editInventoryProduct;

console.log('✅ Admin Inventory JavaScript loaded successfully!');
console.log('🔧 Edit & Delete inventory features enabled');