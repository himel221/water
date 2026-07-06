// ===== Admin Orders JavaScript =====

let currentOrders = [];
let filteredOrders = [];
let currentPage = 1;
const itemsPerPage = 10;

// ===== Initialize =====
function initializeOrders(orders) {
    console.log('📊 Orders Data:', orders);
    console.log('📊 Total Orders:', orders.length);
    
    if (!orders || orders.length === 0) {
        console.log('⚠️ No orders found!');
        const tbody = document.getElementById('ordersTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="13" class="no-orders">
                        <i class="fas fa-shopping-bag"></i>
                        <h3>No Orders Found</h3>
                        <p>Start making sales and watch your orders grow!</p>
                    </td>
                </tr>
            `;
        }
        return;
    }
    
    currentOrders = orders;
    filteredOrders = orders;
    updateStats();
    setupEventListeners();
    renderTable();
}

// ===== Update Stats =====
function updateStats() {
    const total = currentOrders.length;
    const pending = currentOrders.filter(o => o.status === 'pending').length;
    const shipped = currentOrders.filter(o => o.status === 'shipped').length;
    const delivered = currentOrders.filter(o => o.status === 'delivered').length;
    const cancelled = currentOrders.filter(o => o.status === 'cancelled').length;
    
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 5) {
        statNumbers[0].textContent = total;
        statNumbers[1].textContent = pending;
        statNumbers[2].textContent = shipped;
        statNumbers[3].textContent = delivered;
        statNumbers[4].textContent = cancelled;
    }
}

// ===== Setup Event Listeners =====
function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', filterOrders);
    }
    
    // Status Filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterOrders);
    }
    
    // Date Filter
    const dateFilter = document.getElementById('dateFilter');
    if (dateFilter) {
        dateFilter.addEventListener('change', filterOrders);
    }
    
    // Select All
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            document.querySelectorAll('.order-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }
    
    // View Order - Event Delegation
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view');
        if (viewBtn) {
            const orderId = viewBtn.dataset.orderId;
            viewOrder(orderId);
        }
    });
    
    // Edit Order
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit');
        if (editBtn) {
            const orderId = editBtn.dataset.orderId;
            window.location.href = `/admin/water_app/order/${orderId}/change/`;
        }
    });
    
    // Delete Order
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete');
        if (deleteBtn) {
            const orderId = deleteBtn.dataset.orderId;
            if (confirm(`Are you sure you want to delete order ${orderId}?`)) {
                deleteOrder(orderId);
            }
        }
    });
    
    // Modal Close
    const closeModalBtn = document.getElementById('closeModal');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }
    
    const orderModal = document.getElementById('orderModal');
    if (orderModal) {
        orderModal.addEventListener('click', function(e) {
            if (e.target === this) closeModal();
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
    
    // Export
    const exportBtn = document.getElementById('exportOrders');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportOrders();
        });
    }
}

// ===== Filter Orders =====
function filterOrders() {
    const search = document.getElementById('searchInput').value.toLowerCase();
    const status = document.getElementById('statusFilter').value;
    const date = document.getElementById('dateFilter').value;
    
    filteredOrders = currentOrders.filter(order => {
        const matchSearch = !search || 
            order.order_id.toLowerCase().includes(search) ||
            order.customer_name.toLowerCase().includes(search) ||
            order.customer_email.toLowerCase().includes(search);
        
        const matchStatus = status === 'all' || order.status === status;
        
        let matchDate = true;
        if (date !== 'all') {
            const now = new Date();
            const orderDate = new Date(order.created_at);
            if (date === 'today') {
                matchDate = orderDate.toDateString() === now.toDateString();
            } else if (date === 'week') {
                const weekAgo = new Date(now);
                weekAgo.setDate(now.getDate() - 7);
                matchDate = orderDate >= weekAgo;
            } else if (date === 'month') {
                matchDate = orderDate.getMonth() === now.getMonth() &&
                            orderDate.getFullYear() === now.getFullYear();
            }
        }
        
        return matchSearch && matchStatus && matchDate;
    });
    
    currentPage = 1;
    renderTable();
}

// ===== Render Table =====
function renderTable() {
    const tbody = document.getElementById('ordersTableBody');
    const totalCount = document.getElementById('totalCount');
    
    if (!tbody) return;
    
    if (filteredOrders.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="13" class="no-orders">
                    <i class="fas fa-shopping-bag"></i>
                    <h3>No Orders Found</h3>
                    <p>Try adjusting your filters.</p>
                </td>
            </tr>
        `;
        if (totalCount) totalCount.textContent = '0';
        updatePagination();
        return;
    }
    
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, filteredOrders.length);
    const pageOrders = filteredOrders.slice(start, end);
    
    let html = '';
    pageOrders.forEach(order => {
        const totalDiscount = order.total_discount > 0 ? 
            `<span class="total-discount">-৳${order.total_discount.toFixed(2)}</span>` : 
            `<span class="no-discount">-</span>`;
        
        const statusClass = order.status;
        const statusLabel = order.status.charAt(0).toUpperCase() + order.status.slice(1);
        
        let productsHtml = '';
        if (order.items && order.items.length > 0) {
            order.items.slice(0, 3).forEach(item => {
                const discountText = item.discount_percentage > 0 ? `(${item.discount_percentage}% OFF)` : '';
                productsHtml += `
                    <div class="product-item-small">
                        <span class="product-name-small">${item.product_name}</span>
                        <span class="product-qty">x${item.quantity}</span>
                        ${discountText ? `<span class="product-discount-small">${discountText}</span>` : ''}
                    </div>
                `;
            });
            if (order.items.length > 3) {
                productsHtml += `<div style="font-size: 12px; color: #999;">+${order.items.length - 3} more</div>`;
            }
        }
        
        let offerHtml = '';
        if (order.special_offers_list && order.special_offers_list.length > 0) {
            offerHtml = `<div>`;
            order.special_offers_list.slice(0, 2).forEach(offer => {
                offerHtml += `<span class="offer-tag">🎉 ${offer}</span>`;
            });
            if (order.special_offers_list.length > 2) {
                offerHtml += `<span class="offer-tag">+${order.special_offers_list.length - 2} more</span>`;
            }
            offerHtml += `</div>`;
        } else {
            offerHtml = `<span style="color: #b2bec3;">-</span>`;
        }
        
        const eligibilityHtml = order.is_eligible_for_offer ?
            `<span class="offer-badge eligible"><i class="fas fa-check-circle"></i> Eligible</span>` :
            `<span class="offer-badge non-eligible"><i class="fas fa-times-circle"></i> Not Eligible</span>`;
        
        html += `
            <tr>
                <td><input type="checkbox" class="order-checkbox" /></td>
                <td><span class="order-id">${order.order_id}</span></td>
                <td>
                    <span class="customer-name">${order.customer_name}</span>
                    <span class="customer-email">${order.customer_email}</span>
                </td>
                <td>${order.customer_district || '-'}</td>
                <td>${order.get_total_items}</td>
                <td><div class="products-info">${productsHtml}</div></td>
                <td><span class="amount">৳${order.total_amount.toFixed(2)}</span></td>
                <td>${totalDiscount}</td>
                <td><span class="status-badge ${statusClass}"><i class="fas fa-circle"></i> ${statusLabel}</span></td>
                <td>${offerHtml}</td>
                <td>${eligibilityHtml}</td>
                <td>
                    <span style="display: block; font-weight: 500; font-size: 13px;">${formatDate(order.created_at)}</span>
                    <span style="display: block; font-size: 11px; color: #b2bec3;">${formatTime(order.created_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-view" data-order-id="${order.order_id}"><i class="fas fa-eye"></i></button>
                        <button class="btn-edit" data-order-id="${order.order_id}"><i class="fas fa-edit"></i></button>
                        <button class="btn-delete" data-order-id="${order.order_id}"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    if (totalCount) totalCount.textContent = filteredOrders.length;
    updatePagination();
}

// ===== View Order =====
function viewOrder(orderId) {
    const order = currentOrders.find(o => o.order_id === orderId);
    if (!order) return;
    
    const modal = document.getElementById('orderModal');
    const body = document.getElementById('orderDetailBody');
    if (!modal || !body) return;
    
    let itemsHtml = '';
    if (order.items) {
        order.items.forEach(item => {
            itemsHtml += `
                <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #f0f0f0;">
                    <span>${item.product_name} x ${item.quantity}</span>
                    <span>৳${item.product_price.toFixed(2)}</span>
                </div>
            `;
        });
    }
    
    body.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div><strong>Order ID</strong><br>${order.order_id}</div>
            <div><strong>Customer</strong><br>${order.customer_name}</div>
            <div><strong>Email</strong><br>${order.customer_email}</div>
            <div><strong>Total</strong><br>৳${order.total_amount.toFixed(2)}</div>
            <div><strong>Discount</strong><br>${order.total_discount > 0 ? '৳' + order.total_discount.toFixed(2) : 'N/A'}</div>
            <div><strong>Status</strong><br>${order.status}</div>
        </div>
        <div style="margin-top: 16px;">
            <strong>Products:</strong>
            <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 6px;">
                ${itemsHtml}
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// ===== Close Modal =====
function closeModal() {
    const modal = document.getElementById('orderModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ===== Delete Order =====
function deleteOrder(orderId) {
    fetch(`/api/orders/${orderId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Failed to delete order');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting order');
    });
}

// ===== Format Date =====
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        day: '2-digit', 
        month: 'short', 
        year: 'numeric' 
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
}

// ===== Pagination =====
function changePage(direction) {
    const totalPages = Math.ceil(filteredOrders.length / itemsPerPage);
    const newPage = currentPage + direction;
    if (newPage < 1 || newPage > totalPages) return;
    currentPage = newPage;
    renderTable();
}

function goToPage(page) {
    const totalPages = Math.ceil(filteredOrders.length / itemsPerPage);
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
}

function updatePagination() {
    const totalPages = Math.ceil(filteredOrders.length / itemsPerPage);
    const start = (currentPage - 1) * itemsPerPage + 1;
    const end = Math.min(currentPage * itemsPerPage, filteredOrders.length);
    
    document.getElementById('startCount').textContent = filteredOrders.length > 0 ? start : 0;
    document.getElementById('endCount').textContent = end;
    document.getElementById('totalCount').textContent = filteredOrders.length;
}

// ===== Export Orders =====
function exportOrders() {
    alert('Export functionality coming soon!');
}

// ===== Get CSRF Token =====
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
    
    // Update Date
    function updateDate() {
        const now = new Date();
        const options = { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
        };
        const dateEl = document.getElementById('currentDate');
        if (dateEl) {
            dateEl.textContent = now.toLocaleDateString('en-US', options);
        }
    }
    updateDate();
});

// Make functions global
window.initializeOrders = initializeOrders;
window.renderTable = renderTable;
window.filterOrders = filterOrders;
window.viewOrder = viewOrder;
window.closeModal = closeModal;
window.exportOrders = exportOrders;