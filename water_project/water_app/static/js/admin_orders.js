// ===== Admin Orders JavaScript - Complete with Full Report Fields =====

let currentOrders = [];
let filteredOrders = [];
let currentPage = 1;
const itemsPerPage = 10;

/**
 * Initialize orders and render table
 */
function initializeOrders(orders) {
    console.log('📊 Orders Data:', orders);
    console.log('📊 Total Orders:', orders ? orders.length : 0);
    
    if (!orders || orders.length === 0) {
        console.log('⚠️ No orders found!');
        const tbody = document.getElementById('ordersTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="14" class="no-orders">
                        <i class="fas fa-shopping-bag"></i>
                        <h3>No Orders Found</h3>
                        <p>Start making sales and watch your orders grow!</p>
                    </td>
                </tr>
            `;
        }
        // Update empty stats
        const statNumbers = document.querySelectorAll('.stat-number');
        if (statNumbers.length >= 5) {
            statNumbers[0].textContent = '0';
            statNumbers[1].textContent = '0';
            statNumbers[2].textContent = '0';
            statNumbers[3].textContent = '0';
            statNumbers[4].textContent = '0';
        }
        return;
    }
    
    currentOrders = orders;
    filteredOrders = [...orders];
    updateStats();
    setupEventListeners();
    renderTable();
}

// ===== Update Stats =====
function updateStats() {
    const total = currentOrders.length;
    const pending = currentOrders.filter(o => o.status === 'pending').length;
    const processing = currentOrders.filter(o => o.status === 'processing').length;
    const shipped = currentOrders.filter(o => o.status === 'shipped').length;
    const delivered = currentOrders.filter(o => o.status === 'delivered').length;
    const cancelled = currentOrders.filter(o => o.status === 'cancelled').length;
    
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 5) {
        statNumbers[0].textContent = total;
        statNumbers[1].textContent = pending + processing;
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
        searchInput.addEventListener('input', debounce(filterOrders, 300));
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
    
    // ===== Export All Excel =====
    const exportExcelAll = document.getElementById('exportExcelAll');
    if (exportExcelAll) {
        exportExcelAll.addEventListener('click', function() {
            exportOrders('excel', 'all');
        });
    }
    
    // ===== Export All PDF =====
    const exportPdfAll = document.getElementById('exportPdfAll');
    if (exportPdfAll) {
        exportPdfAll.addEventListener('click', function() {
            exportOrders('pdf', 'all');
        });
    }
    
    // ===== Export Selected Excel =====
    const exportExcelSelected = document.getElementById('exportExcelSelected');
    if (exportExcelSelected) {
        exportExcelSelected.addEventListener('click', function() {
            exportOrders('excel', 'selected');
        });
    }
    
    // ===== Export Selected PDF =====
    const exportPdfSelected = document.getElementById('exportPdfSelected');
    if (exportPdfSelected) {
        exportPdfSelected.addEventListener('click', function() {
            exportOrders('pdf', 'selected');
        });
    }
    
    // ===== Refresh =====
    const exportRefresh = document.getElementById('exportRefresh');
    if (exportRefresh) {
        exportRefresh.addEventListener('click', function() {
            location.reload();
        });
    }
    
    // View Order - Event Delegation
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view');
        if (viewBtn) {
            const orderId = viewBtn.dataset.orderId;
            if (orderId) viewOrder(orderId);
        }
    });
    
    // Edit Order
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit');
        if (editBtn) {
            const orderId = editBtn.dataset.orderId;
            if (orderId) {
                window.location.href = `/admin/water_app/order/${orderId}/change/`;
            }
        }
    });
    
    // Delete Order
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete');
        if (deleteBtn) {
            const orderId = deleteBtn.dataset.orderId;
            if (orderId && confirm(`Are you sure you want to delete order ${orderId}?`)) {
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
    
    // Keyboard shortcut: Escape to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeModal();
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

// ===== Filter Orders =====
function filterOrders() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const dateFilter = document.getElementById('dateFilter');
    
    const search = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const status = statusFilter ? statusFilter.value : 'all';
    const date = dateFilter ? dateFilter.value : 'all';
    
    filteredOrders = currentOrders.filter(order => {
        // Search filter
        const matchSearch = !search || 
            order.order_id.toLowerCase().includes(search) ||
            order.customer_name.toLowerCase().includes(search) ||
            order.customer_email.toLowerCase().includes(search) ||
            (order.customer_phone && order.customer_phone.toLowerCase().includes(search)) ||
            (order.customer_address && order.customer_address.toLowerCase().includes(search)) ||
            (order.customer_district && order.customer_district.toLowerCase().includes(search));
        
        // Status filter
        const matchStatus = status === 'all' || order.status === status;
        
        // Date filter
        let matchDate = true;
        if (date !== 'all' && order.created_at) {
            const now = new Date();
            const orderDate = new Date(order.created_at);
            
            // Reset time for date comparison
            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const orderDay = new Date(orderDate.getFullYear(), orderDate.getMonth(), orderDate.getDate());
            
            if (date === 'today') {
                matchDate = orderDay.getTime() === today.getTime();
            } else if (date === 'week') {
                const weekAgo = new Date(today);
                weekAgo.setDate(today.getDate() - 7);
                matchDate = orderDay >= weekAgo;
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
                <td colspan="14" class="no-orders">
                    <i class="fas fa-shopping-bag"></i>
                    <h3>No Orders Found</h3>
                    <p>Try adjusting your filters or search terms.</p>
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
        
        const statusClass = order.status || 'pending';
        const statusLabel = order.status ? order.status.charAt(0).toUpperCase() + order.status.slice(1) : 'Pending';
        
        // Offer HTML
        let offerHtml = '';
        if (order.special_offers_list && order.special_offers_list.length > 0) {
            offerHtml = `<div>`;
            order.special_offers_list.slice(0, 2).forEach(offer => {
                offerHtml += `<span class="offer-tag">🎉 ${escapeHtml(offer)}</span>`;
            });
            if (order.special_offers_list.length > 2) {
                offerHtml += `<span class="offer-tag">+${order.special_offers_list.length - 2} more</span>`;
            }
            offerHtml += `</div>`;
        } else {
            offerHtml = `<span style="color: #b2bec3;">-</span>`;
        }
        
        // Eligibility HTML
        const eligibilityHtml = order.is_eligible_for_offer ?
            `<span class="offer-eligibility-badge eligible"><i class="fas fa-check-circle"></i> Eligible</span>` :
            `<span class="offer-eligibility-badge not-eligible"><i class="fas fa-times-circle"></i> Not Eligible</span>`;
        
        html += `
            <tr>
                <td><input type="checkbox" class="order-checkbox" data-order-id="${escapeHtml(order.order_id)}" /></td>
                <td><span class="order-id">${escapeHtml(order.order_id)}</span></td>
                <td>
                    <span class="customer-name">${escapeHtml(order.customer_name)}</span>
                    <span class="customer-email">${escapeHtml(order.customer_email)}</span>
                </td>
                <td>
                    <span class="customer-phone"><i class="fas fa-phone"></i> ${escapeHtml(order.customer_phone || '-')}</span>
                </td>
                <td>
                    <span class="customer-address"><i class="fas fa-map-marker-alt"></i> ${escapeHtml(order.customer_address ? truncateText(order.customer_address, 40) : '-')}</span>
                </td>
                <td>${escapeHtml(order.customer_district || '-')}</td>
                <td>${order.get_total_items || 0}</td>
                <td><span class="amount">৳${(order.total_amount || 0).toFixed(2)}</span></td>
                <td>${totalDiscount}</td>
                <td><span class="status-badge ${statusClass}"><i class="fas fa-circle"></i> ${statusLabel}</span></td>
                <td>${offerHtml}</td>
                <td>${eligibilityHtml}</td>
                <td>
                    <span style="display: block; font-weight: 500; font-size: 12px;">${formatDate(order.created_at)}</span>
                    <span style="display: block; font-size: 10px; color: #b2bec3;">${formatTime(order.created_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-view" data-order-id="${escapeHtml(order.order_id)}" title="View Details"><i class="fas fa-eye"></i></button>
                        <button class="btn-edit" data-order-id="${escapeHtml(order.order_id)}" title="Edit"><i class="fas fa-edit"></i></button>
                        <button class="btn-delete" data-order-id="${escapeHtml(order.order_id)}" title="Delete"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    if (totalCount) totalCount.textContent = filteredOrders.length;
    updatePagination();
    
    // Re-bind select all state
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        const checkboxes = document.querySelectorAll('.order-checkbox');
        const checked = document.querySelectorAll('.order-checkbox:checked');
        selectAll.checked = checkboxes.length > 0 && checkboxes.length === checked.length;
    }
}

// ===== Export Orders with Complete Fields =====
function exportOrders(format, type) {
    let orderIds = [];
    let ordersToExport = [];
    
    if (type === 'selected') {
        document.querySelectorAll('.order-checkbox:checked').forEach(cb => {
            const orderId = cb.dataset.orderId;
            if (orderId) orderIds.push(orderId);
        });
        
        if (orderIds.length === 0) {
            alert('Please select at least one order to export!');
            return;
        }
        
        ordersToExport = currentOrders.filter(o => orderIds.includes(o.order_id));
    } else {
        // All orders with current filters
        ordersToExport = filteredOrders;
    }
    
    if (ordersToExport.length === 0) {
        alert('No orders to export!');
        return;
    }
    
    // Build URL with complete data
    let url = `/api/orders/export/${format}/`;
    const params = new URLSearchParams();
    
    // Add all order IDs for selected export
    if (type === 'selected') {
        params.append('ids', orderIds.join(','));
    } else {
        const status = document.getElementById('statusFilter')?.value || 'all';
        const date = document.getElementById('dateFilter')?.value || 'all';
        if (status !== 'all') params.append('status', status);
        if (date !== 'all') params.append('date', date);
    }
    
    // Add full fields flag to include all columns
    params.append('full_fields', 'true');
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    // Get the button
    let btn = null;
    if (format === 'excel' && type === 'all') btn = document.getElementById('exportExcelAll');
    else if (format === 'pdf' && type === 'all') btn = document.getElementById('exportPdfAll');
    else if (format === 'excel' && type === 'selected') btn = document.getElementById('exportExcelSelected');
    else if (format === 'pdf' && type === 'selected') btn = document.getElementById('exportPdfSelected');
    
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;
        
        // Fetch and download
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status}`);
            }
            return response.blob();
        })
        .then(blob => {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            const extension = format === 'excel' ? 'xlsx' : 'pdf';
            const dateStr = new Date().toISOString().slice(0,10);
            const count = ordersToExport.length;
            link.download = `orders_${type}_${count}_${dateStr}.${extension}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
            showToast(`${count} orders exported successfully as ${format.toUpperCase()}!`, 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showToast('Failed to export orders. Please try again.', 'error');
        })
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
    }
}

// ===== View Order Details =====
function viewOrder(orderId) {
    const order = currentOrders.find(o => o.order_id === orderId);
    if (!order) {
        showToast('Order not found!', 'error');
        return;
    }
    
    const modal = document.getElementById('orderModal');
    const body = document.getElementById('orderDetailBody');
    if (!modal || !body) return;
    
    // Calculate totals
    let subtotal = 0;
    let totalDiscount = 0;
    let totalSavings = 0;
    let itemsHtml = '';
    
    if (order.items && order.items.length > 0) {
        order.items.forEach(item => {
            const originalPrice = item.original_price || item.product_price || 0;
            const price = item.product_price || 0;
            const quantity = item.quantity || 0;
            const discount = originalPrice - price;
            subtotal += originalPrice * quantity;
            totalDiscount += discount * quantity;
            totalSavings += discount * quantity;
            
            const discountText = item.discount_percentage > 0 ? `${item.discount_percentage}%` : '-';
            const specialOffer = item.special_offer || '-';
            
            itemsHtml += `
                <tr>
                    <td>${escapeHtml(item.product_name || 'Unknown Product')}</td>
                    <td style="text-align: center;">${quantity}</td>
                    <td style="text-align: right;">৳${price.toFixed(2)}</td>
                    <td style="text-align: right; text-decoration: line-through; color: #999;">${originalPrice > price ? '৳' + originalPrice.toFixed(2) : '-'}</td>
                    <td style="text-align: center;">${escapeHtml(discountText)}</td>
                    <td style="text-align: center; color: #856404; font-size: 12px;">${escapeHtml(specialOffer)}</td>
                    <td style="text-align: right; font-weight: 700; color: #007bff;">৳${(price * quantity).toFixed(2)}</td>
                </tr>
            `;
        });
    } else {
        itemsHtml = `
            <tr>
                <td colspan="7" style="text-align: center; color: #999; padding: 20px;">
                    <i class="fas fa-box-open"></i> No items found for this order
                </td>
            </tr>
        `;
    }
    
    const totalAmount = order.total_amount || (subtotal - totalSavings);
    const deliveryCharge = order.delivery_charge || 0;
    
    body.innerHTML = `
        <div class="detail-section">
            <h5><i class="fas fa-info-circle"></i> Order Information</h5>
            <div class="detail-row">
                <span class="label">Order ID</span>
                <span class="value">${escapeHtml(order.order_id)}</span>
            </div>
            <div class="detail-row">
                <span class="label">Status</span>
                <span class="value"><span class="status-badge ${order.status || 'pending'}">${order.status ? order.status.charAt(0).toUpperCase() + order.status.slice(1) : 'Pending'}</span></span>
            </div>
            <div class="detail-row">
                <span class="label">Date & Time</span>
                <span class="value">${order.created_at ? new Date(order.created_at).toLocaleString() : 'N/A'}</span>
            </div>
            <div class="detail-row">
                <span class="label">Payment Method</span>
                <span class="value">${escapeHtml(order.payment_method || 'Cash on Delivery')}</span>
            </div>
            ${order.payment_status ? `
            <div class="detail-row">
                <span class="label">Payment Status</span>
                <span class="value">${escapeHtml(order.payment_status)}</span>
            </div>
            ` : ''}
        </div>
        
        <div class="detail-section">
            <h5><i class="fas fa-user"></i> Customer Details</h5>
            <div class="detail-row">
                <span class="label">Name</span>
                <span class="value">${escapeHtml(order.customer_name)}</span>
            </div>
            <div class="detail-row">
                <span class="label">Email</span>
                <span class="value">${escapeHtml(order.customer_email)}</span>
            </div>
            <div class="detail-row">
                <span class="label">Phone</span>
                <span class="value">${escapeHtml(order.customer_phone || 'N/A')}</span>
            </div>
            <div class="detail-row">
                <span class="label">Address</span>
                <span class="value" style="white-space: normal;">${escapeHtml(order.customer_address || 'N/A')}</span>
            </div>
            <div class="detail-row">
                <span class="label">District</span>
                <span class="value">${escapeHtml(order.customer_district || 'N/A')}</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h5><i class="fas fa-box"></i> Products</h5>
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th style="text-align: center;">Qty</th>
                        <th style="text-align: right;">Price</th>
                        <th style="text-align: right;">Original</th>
                        <th style="text-align: center;">Discount</th>
                        <th style="text-align: center;">Special Offer</th>
                        <th style="text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${itemsHtml}
                </tbody>
            </table>
        </div>
        
        <div class="detail-section">
            <h5><i class="fas fa-receipt"></i> Order Summary</h5>
            <div class="detail-row">
                <span class="label">Subtotal</span>
                <span class="value amount">৳${subtotal.toFixed(2)}</span>
            </div>
            ${totalDiscount > 0 ? `
            <div class="detail-row">
                <span class="label">Total Discount</span>
                <span class="value discount">-৳${totalDiscount.toFixed(2)}</span>
            </div>
            ` : ''}
            ${deliveryCharge > 0 ? `
            <div class="detail-row">
                <span class="label">Delivery Charge</span>
                <span class="value">৳${deliveryCharge.toFixed(2)}</span>
            </div>
            ` : ''}
            <div class="detail-row" style="border-top: 2px solid #dee2e6; padding-top: 10px; margin-top: 4px;">
                <span class="label" style="font-weight: 700; font-size: 16px;">Total Amount</span>
                <span class="value amount" style="font-size: 20px; color: #007bff;">৳${totalAmount.toFixed(2)}</span>
            </div>
            ${order.is_eligible_for_offer ? `
            <div class="detail-row" style="background: #d4edda; border-radius: 6px; padding: 8px 12px; margin-top: 6px;">
                <span class="label" style="color: #155724;">
                    <i class="fas fa-check-circle" style="color: #28a745;"></i> Special Offer Eligible
                </span>
                <span class="value eligible" style="color: #28a745;">
                    <i class="fas fa-gift"></i> ${order.special_offers_list && order.special_offers_list.length > 0 ? order.special_offers_list.join(', ') : 'Yes'}
                </span>
            </div>
            ` : `
            <div class="detail-row" style="background: #f8d7da; border-radius: 6px; padding: 8px 12px; margin-top: 6px;">
                <span class="label" style="color: #721c24;">
                    <i class="fas fa-times-circle" style="color: #dc3545;"></i> Not Eligible for Special Offer
                </span>
                <span class="value not-eligible" style="color: #dc3545;">Minimum order amount required</span>
            </div>
            `}
        </div>
        
        ${order.special_offers_list && order.special_offers_list.length > 0 ? `
        <div class="detail-section">
            <h5><i class="fas fa-gift"></i> Special Offers Applied</h5>
            ${order.special_offers_list.map(offer => `
                <div style="background: #fff3cd; color: #856404; padding: 6px 12px; border-radius: 6px; margin: 4px 0; border-left: 3px solid #f39c12;">
                    🎉 ${escapeHtml(offer)}
                </div>
            `).join('')}
        </div>
        ` : ''}
        
        <div class="detail-section" style="margin-bottom: 0;">
            <div style="display: flex; gap: 10px; justify-content: flex-end; padding-top: 12px; border-top: 1px solid #e8ecf1; flex-wrap: wrap;">
                <button onclick="window.location.href='/admin/water_app/order/${order.order_id}/change/'" 
                        style="padding: 8px 20px; background: #f39c12; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-edit"></i> Edit Order
                </button>
                <button onclick="downloadInvoice('${order.order_id}')" 
                        style="padding: 8px 20px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-file-pdf"></i> Download Invoice
                </button>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

// ===== Download Invoice =====
function downloadInvoice(orderId) {
    const url = `/api/invoice/${orderId}/`;
    
    const btn = document.querySelector(`button[onclick*="downloadInvoice('${orderId}')"]`);
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        btn.disabled = true;
        
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.blob();
            })
            .then(blob => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `invoice_${orderId}.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(link.href);
                showToast('Invoice downloaded successfully!', 'success');
            })
            .catch(error => {
                console.error('Download error:', error);
                showToast('Failed to download invoice. Please try again.', 'error');
            })
            .finally(() => {
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
    } else {
        window.location.href = url;
    }
}

// ===== Close Modal =====
function closeModal() {
    const modal = document.getElementById('orderModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
}

// ===== Delete Order =====
function deleteOrder(orderId) {
    if (!confirm(`Are you sure you want to delete order ${orderId}? This action cannot be undone.`)) return;
    
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/orders/${orderId}/delete/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success' || data.success) {
            currentOrders = currentOrders.filter(o => o.order_id !== orderId);
            filteredOrders = filteredOrders.filter(o => o.order_id !== orderId);
            updateStats();
            renderTable();
            showToast('Order deleted successfully!', 'success');
        } else {
            showToast(data.message || 'Failed to delete order', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error deleting order. Please try again.', 'error');
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

function truncateText(text, maxLength = 35) {
    if (!text) return '-';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
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

// ===== Pagination =====
function changePage(direction) {
    const totalPages = Math.max(1, Math.ceil(filteredOrders.length / itemsPerPage));
    const newPage = currentPage + direction;
    if (newPage < 1 || newPage > totalPages) return;
    currentPage = newPage;
    renderTable();
    updatePaginationButtons();
}

function goToPage(page) {
    const totalPages = Math.max(1, Math.ceil(filteredOrders.length / itemsPerPage));
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    updatePaginationButtons();
}

function updatePagination() {
    const totalPages = Math.max(1, Math.ceil(filteredOrders.length / itemsPerPage));
    const start = filteredOrders.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, filteredOrders.length);
    
    const startCount = document.getElementById('startCount');
    const endCount = document.getElementById('endCount');
    const totalCount = document.getElementById('totalCount');
    
    if (startCount) startCount.textContent = start;
    if (endCount) endCount.textContent = end;
    if (totalCount) totalCount.textContent = filteredOrders.length;
    
    updatePaginationButtons();
}

function updatePaginationButtons() {
    const totalPages = Math.max(1, Math.ceil(filteredOrders.length / itemsPerPage));
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
window.initializeOrders = initializeOrders;
window.renderTable = renderTable;
window.filterOrders = filterOrders;
window.viewOrder = viewOrder;
window.closeModal = closeModal;
window.exportOrders = exportOrders;
window.deleteOrder = deleteOrder;
window.showToast = showToast;
window.goToPage = goToPage;
window.changePage = changePage;
window.downloadInvoice = downloadInvoice;

// Add toast animation styles
(function addToastStyles() {
    if (document.getElementById('toast-styles')) return;
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .toast-notification {
            animation: slideUp 0.3s ease;
        }
    `;
    document.head.appendChild(style);
})();

console.log('✅ Admin Orders JavaScript loaded successfully!');
console.log('📋 All fields included in export: Order ID, Customer, Phone, Address, District, Items, Total, Discount, Status, Special Offer, Eligibility, Date');