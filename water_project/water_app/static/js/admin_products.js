// ===== Admin Products JavaScript - Complete =====

let currentProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 10;

/**
 * Initialize products and render table
 */
function initializeProducts(products) {
    console.log('📦 Products Data:', products);
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
    const active = currentProducts.filter(p => p.is_active).length;
    const inactive = currentProducts.filter(p => !p.is_active).length;
    const lowStock = currentProducts.filter(p => p.stock > 0 && p.stock <= 10).length;
    
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 4) {
        statNumbers[0].textContent = total;
        statNumbers[1].textContent = active;
        statNumbers[2].textContent = inactive;
        statNumbers[3].textContent = lowStock;
    }
}

// ===== Setup Event Listeners =====
function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterProducts, 300));
    }
    
    // Status Filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterProducts);
    }
    
    // Stock Filter
    const stockFilter = document.getElementById('stockFilter');
    if (stockFilter) {
        stockFilter.addEventListener('change', filterProducts);
    }
    
    // Select All
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            document.querySelectorAll('.product-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }
    
    // Export Excel
    const exportExcel = document.getElementById('exportExcel');
    if (exportExcel) {
        exportExcel.addEventListener('click', function() {
            exportProducts('excel');
        });
    }
    
    // Export PDF
    const exportPdf = document.getElementById('exportPdf');
    if (exportPdf) {
        exportPdf.addEventListener('click', function() {
            exportProducts('pdf');
        });
    }
    
    // Refresh
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            location.reload();
        });
    }
    
    // Add Product
    const addProductBtn = document.getElementById('addProductBtn');
    if (addProductBtn) {
        addProductBtn.addEventListener('click', function() {
            openProductForm();
        });
    }
    
    const emptyAddBtn = document.getElementById('emptyAddBtn');
    if (emptyAddBtn) {
        emptyAddBtn.addEventListener('click', function() {
            openProductForm();
        });
    }
    
    // View Product - Event Delegation
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view');
        if (viewBtn) {
            const productId = viewBtn.dataset.productId;
            if (productId) viewProduct(productId);
        }
    });
    
    // Edit Product
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit');
        if (editBtn) {
            const productId = editBtn.dataset.productId;
            if (productId) openProductForm(productId);
        }
    });
    
    // Toggle Status
    document.addEventListener('click', function(e) {
        const toggleBtn = e.target.closest('.btn-toggle');
        if (toggleBtn) {
            const productId = toggleBtn.dataset.productId;
            if (productId) toggleProductStatus(productId);
        }
    });
    
    // Delete Product
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete');
        if (deleteBtn) {
            const productId = deleteBtn.dataset.productId;
            if (productId && confirm('Are you sure you want to delete this product?')) {
                deleteProduct(productId);
            }
        }
    });
    
    // Modal Close
    const closeViewModal = document.getElementById('closeViewModal');
    if (closeViewModal) {
        closeViewModal.addEventListener('click', function() {
            document.getElementById('viewProductModal').style.display = 'none';
        });
    }
    
    const closeFormModal = document.getElementById('closeFormModal');
    if (closeFormModal) {
        closeFormModal.addEventListener('click', function() {
            document.getElementById('productFormModal').style.display = 'none';
        });
    }
    
    const cancelFormBtn = document.getElementById('cancelFormBtn');
    if (cancelFormBtn) {
        cancelFormBtn.addEventListener('click', function() {
            document.getElementById('productFormModal').style.display = 'none';
        });
    }
    
    // Close modals on overlay click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.style.display = 'none';
            }
        });
    });
    
    // Keyboard shortcut: Escape to close modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
        }
    });
    
    // Product Form Submit
    const productForm = document.getElementById('productForm');
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveProduct();
        });
    }
    
    // Image Preview
    const productImage = document.getElementById('productImage');
    if (productImage) {
        productImage.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const preview = document.getElementById('imagePreview');
                    if (preview) {
                        const img = preview.querySelector('img');
                        if (img) {
                            img.src = event.target.result;
                        }
                        preview.style.display = 'block';
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
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

// ===== Debounce Function =====
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
    const statusFilter = document.getElementById('statusFilter');
    const stockFilter = document.getElementById('stockFilter');
    
    const search = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const status = statusFilter ? statusFilter.value : 'all';
    const stock = stockFilter ? stockFilter.value : 'all';
    
    filteredProducts = currentProducts.filter(product => {
        // Search filter
        const matchSearch = !search || 
            product.name.toLowerCase().includes(search) ||
            (product.sku && product.sku.toLowerCase().includes(search)) ||
            (product.description && product.description.toLowerCase().includes(search));
        
        // Status filter
        const matchStatus = status === 'all' || 
            (status === 'active' && product.is_active) ||
            (status === 'inactive' && !product.is_active);
        
        // Stock filter
        let matchStock = true;
        if (stock === 'in-stock') matchStock = product.stock > 20;
        else if (stock === 'low-stock') matchStock = product.stock > 0 && product.stock <= 20;
        else if (stock === 'out-of-stock') matchStock = product.stock === 0;
        
        return matchSearch && matchStatus && matchStock;
    });
    
    currentPage = 1;
    renderTable();
}

// ===== Render Table =====
function renderTable() {
    const tbody = document.getElementById('productsTableBody');
    const totalCount = document.getElementById('totalCount');
    
    if (!tbody) return;
    
    if (filteredProducts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="no-products">
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
        let priceHtml = `
            <span class="price-current">৳${(product.price || 0).toFixed(2)}</span>
        `;
        if (product.compare_price && product.compare_price > product.price) {
            const savings = ((product.compare_price - product.price) / product.compare_price * 100).toFixed(0);
            priceHtml += `
                <span class="price-original">৳${product.compare_price.toFixed(2)}</span>
                <span class="price-savings">Save ${savings}%</span>
            `;
        }
        
        let stockHtml;
        if (product.stock > 20) {
            stockHtml = `<span class="stock-badge in-stock"><i class="fas fa-check-circle"></i> ${product.stock} in stock</span>`;
        } else if (product.stock > 0) {
            stockHtml = `<span class="stock-badge low-stock"><i class="fas fa-exclamation-circle"></i> ${product.stock} left</span>`;
        } else {
            stockHtml = `<span class="stock-badge out-of-stock"><i class="fas fa-times-circle"></i> Out of stock</span>`;
        }
        
        let offerHtml;
        if (product.has_active_offer) {
            offerHtml = `<span class="offer-tag active"><i class="fas fa-gift"></i> ${product.active_offer || 'Active Offer'}</span>`;
        } else {
            offerHtml = `<span class="offer-tag" style="background: #f0f0f0; color: #999;">No offer</span>`;
        }
        
        const statusClass = product.is_active ? 'active' : 'inactive';
        const statusText = product.is_active ? 'Active' : 'Inactive';
        
        const imageHtml = product.image_url ? 
            `<img src="${product.image_url}" alt="${escapeHtml(product.name)}" class="product-image-thumb" />` :
            `<div class="product-image-thumb" style="background: #f0f0f0; display: flex; align-items: center; justify-content: center; color: #ccc;">
                <i class="fas fa-image fa-2x"></i>
            </div>`;
        
        html += `
            <tr>
                <td><input type="checkbox" class="product-checkbox" data-product-id="${product.id}" /></td>
                <td>${imageHtml}</td>
                <td>
                    <span class="product-name-cell">${escapeHtml(product.name)}</span>
                    <span class="product-sku">SKU: ${escapeHtml(product.sku || 'N/A')}</span>
                </td>
                <td>${priceHtml}</td>
                <td>${stockHtml}</td>
                <td>${offerHtml}</td>
                <td><span class="status-badge ${statusClass}"><i class="fas fa-circle"></i> ${statusText}</span></td>
                <td>
                    <span style="display: block; font-weight: 500; font-size: 12px;">${formatDate(product.created_at)}</span>
                    <span style="display: block; font-size: 10px; color: #b2bec3;">${formatTime(product.created_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-view" data-product-id="${product.id}" title="View Details"><i class="fas fa-eye"></i></button>
                        <button class="btn-edit" data-product-id="${product.id}" title="Edit Product"><i class="fas fa-edit"></i></button>
                        <button class="btn-toggle" data-product-id="${product.id}" title="Toggle Status">
                            <i class="fas ${product.is_active ? 'fa-eye-slash' : 'fa-eye'}"></i>
                        </button>
                        <button class="btn-delete" data-product-id="${product.id}" title="Delete Product"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    if (totalCount) totalCount.textContent = filteredProducts.length;
    updatePagination();
    
    // Re-bind select all state
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
        <p style="color: #7f8c8d; font-size: 13px; margin-bottom: 16px;">SKU: ${escapeHtml(product.sku || 'N/A')}</p>
        
        <div class="modal-detail-grid">
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-tag"></i> Price</span>
                <span class="value price">৳${(product.price || 0).toFixed(2)}</span>
            </div>
            ${product.compare_price && product.compare_price > product.price ? `
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-tags"></i> Compare Price</span>
                <span class="value" style="text-decoration: line-through; color: #dc3545;">৳${product.compare_price.toFixed(2)}</span>
            </div>
            ` : ''}
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-boxes"></i> Stock</span>
                <span class="value">${product.stock || 0}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-gift"></i> Offer</span>
                <span class="value">${product.has_active_offer ? escapeHtml(product.active_offer || 'Active') : 'No offer'}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-power-off"></i> Status</span>
                <span class="value"><span class="status-badge ${product.is_active ? 'active' : 'inactive'}">${product.is_active ? 'Active' : 'Inactive'}</span></span>
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
            <button onclick="openProductForm(${product.id})" style="padding: 8px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                <i class="fas fa-edit"></i> Edit
            </button>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// ===== Open Product Form =====
function openProductForm(productId = null) {
    const modal = document.getElementById('productFormModal');
    const title = document.getElementById('formModalTitle');
    const editId = document.getElementById('editProductId');
    
    if (!modal) return;
    
    if (productId) {
        // Edit mode
        const product = currentProducts.find(p => p.id == productId);
        if (!product) {
            showToast('Product not found!', 'error');
            return;
        }
        
        title.innerHTML = `<i class="fas fa-edit"></i> Edit Product: ${escapeHtml(product.name)}`;
        editId.value = product.id;
        
        document.getElementById('productName').value = product.name || '';
        document.getElementById('productSku').value = product.sku || '';
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productPrice').value = product.price || '';
        document.getElementById('productComparePrice').value = product.compare_price || '';
        document.getElementById('productStock').value = product.stock || 0;
        document.getElementById('productStatus').value = product.is_active ? 'true' : 'false';
        document.getElementById('productOffer').value = product.active_offer || '';
        
        // Show image preview if exists
        const preview = document.getElementById('imagePreview');
        if (product.image_url) {
            const img = preview.querySelector('img');
            img.src = product.image_url;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    } else {
        // Add mode
        title.innerHTML = `<i class="fas fa-plus"></i> Add New Product`;
        editId.value = '';
        document.getElementById('productForm').reset();
        document.getElementById('imagePreview').style.display = 'none';
        document.getElementById('productStatus').value = 'true';
    }
    
    modal.style.display = 'flex';
}

// ===== Save Product =====
function saveProduct() {
    const editId = document.getElementById('editProductId');
    const productName = document.getElementById('productName');
    const productSku = document.getElementById('productSku');
    const productDescription = document.getElementById('productDescription');
    const productPrice = document.getElementById('productPrice');
    const productComparePrice = document.getElementById('productComparePrice');
    const productStock = document.getElementById('productStock');
    const productStatus = document.getElementById('productStatus');
    const productOffer = document.getElementById('productOffer');
    const productImage = document.getElementById('productImage');
    
    // Check if all required elements exist
    if (!productName || !productPrice || !productStock) {
        showToast('Form elements not found!', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('name', productName.value.trim());
    formData.append('sku', productSku ? productSku.value.trim() : '');
    formData.append('description', productDescription ? productDescription.value.trim() : '');
    formData.append('price', productPrice.value);
    formData.append('compare_price', productComparePrice ? productComparePrice.value || '' : '');
    formData.append('stock', productStock.value);
    formData.append('is_active', productStatus ? productStatus.value === 'true' : true);
    formData.append('active_offer', productOffer ? productOffer.value.trim() : '');
    
    if (productImage && productImage.files[0]) {
        formData.append('image', productImage.files[0]);
    }
    
    const csrfToken = getCookie('csrftoken');
    const isEdit = editId && editId.value;
    const url = isEdit ? `/api/products/${editId.value}/update/` : '/api/products/create/';
    const method = isEdit ? 'POST' : 'POST';
    
    const btn = document.querySelector('.btn-save');
    const originalText = btn ? btn.innerHTML : 'Save';
    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        btn.disabled = true;
    }
    
    fetch(url, {
        method: method,
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(isEdit ? 'Product updated successfully!' : 'Product added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Failed to save product', 'error');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error saving product. Please try again.', 'error');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// ===== Toggle Product Status =====
function toggleProductStatus(productId) {
    const product = currentProducts.find(p => p.id == productId);
    if (!product) return;
    
    const newStatus = !product.is_active;
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/products/${productId}/toggle/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ is_active: newStatus })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            product.is_active = newStatus;
            renderTable();
            updateStats();
            showToast(`Product ${newStatus ? 'activated' : 'deactivated'} successfully!`, 'success');
        } else {
            showToast(data.message || 'Failed to toggle status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error toggling product status', 'error');
    });
}

// ===== Delete Product =====
function deleteProduct(productId) {
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/products/${productId}/delete/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            currentProducts = currentProducts.filter(p => p.id != productId);
            filteredProducts = filteredProducts.filter(p => p.id != productId);
            renderTable();
            updateStats();
            showToast('Product deleted successfully!', 'success');
        } else {
            showToast(data.message || 'Failed to delete product', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error deleting product. Please try again.', 'error');
    });
}

// ===== Export Products =====
function exportProducts(format) {
    const url = `/api/products/export/${format}/`;
    
    const btn = document.getElementById(format === 'excel' ? 'exportExcel' : 'exportPdf');
    const originalText = btn ? btn.innerHTML : 'Export';
    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;
    }
    
    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Export failed');
            return response.blob();
        })
        .then(blob => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            const extension = format === 'excel' ? 'xlsx' : 'pdf';
            link.download = `products_${new Date().toISOString().slice(0,10)}.${extension}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
            showToast(`Products exported successfully as ${format.toUpperCase()}!`, 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showToast('Failed to export products. Please try again.', 'error');
        })
        .finally(() => {
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
}

// ===== Toast Notification =====
function showToast(message, type = 'info') {
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) existingToast.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        z-index: 10000;
        min-width: 280px;
        max-width: 450px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: slideUp 0.3s ease;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
        font-family: system-ui, -apple-system, sans-serif;
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 5000);
}

// ===== Helper Functions =====
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

// ===== Pagination =====
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

// ===== Sidebar Toggle =====
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

// ===== Make functions global =====
window.initializeProducts = initializeProducts;
window.renderTable = renderTable;
window.filterProducts = filterProducts;
window.viewProduct = viewProduct;
window.openProductForm = openProductForm;
window.saveProduct = saveProduct;
window.toggleProductStatus = toggleProductStatus;
window.deleteProduct = deleteProduct;
window.exportProducts = exportProducts;
window.showToast = showToast;
window.closeModal = closeModal;
window.goToPage = goToPage;
window.changePage = changePage;

console.log('✅ Admin Products JavaScript loaded successfully!');