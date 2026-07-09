// ===== Admin Customer JavaScript - Complete =====

let currentCustomers = [];
let filteredCustomers = [];
let currentPage = 1;
const itemsPerPage = 10;

/**
 * Initialize customer management
 */
function initializeCustomers(customers) {
    console.log('👥 Customer Data:', customers);
    console.log('👥 Total Customers:', customers ? customers.length : 0);
    
    currentCustomers = customers || [];
    filteredCustomers = [...currentCustomers];
    
    updateStats();
    setupEventListeners();
    renderTable();
}

// ===== Update Stats =====
function updateStats() {
    const total = currentCustomers.length;
    const active = currentCustomers.filter(c => c.is_active).length;
    const inactive = currentCustomers.filter(c => !c.is_active).length;
    const totalRevenue = currentCustomers.reduce((sum, c) => sum + (c.total_spent || 0), 0);
    const totalOrders = currentCustomers.reduce((sum, c) => sum + (c.order_count || 0), 0);
    
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 5) {
        statNumbers[0].textContent = total;
        statNumbers[1].textContent = active;
        statNumbers[2].textContent = inactive;
        statNumbers[3].textContent = totalRevenue.toFixed(0);
        statNumbers[4].textContent = totalOrders;
    }
}

// ===== Setup Event Listeners =====
function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterCustomers, 300));
    }
    
    // Status Filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterCustomers);
    }
    
    // Order Filter
    const orderFilter = document.getElementById('orderFilter');
    if (orderFilter) {
        orderFilter.addEventListener('change', filterCustomers);
    }
    
    // Select All
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            document.querySelectorAll('.customer-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }
    
    // Export Excel
    const exportExcel = document.getElementById('exportExcel');
    if (exportExcel) {
        exportExcel.addEventListener('click', function() {
            exportCustomers('excel');
        });
    }
    
    // Export PDF
    const exportPdf = document.getElementById('exportPdf');
    if (exportPdf) {
        exportPdf.addEventListener('click', function() {
            exportCustomers('pdf');
        });
    }
    
    // Refresh
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            location.reload();
        });
    }
    
    // Add Customer
    const addCustomerBtn = document.getElementById('addCustomerBtn');
    if (addCustomerBtn) {
        addCustomerBtn.addEventListener('click', function() {
            openCustomerForm();
        });
    }
    
    const emptyAddBtn = document.getElementById('emptyAddBtn');
    if (emptyAddBtn) {
        emptyAddBtn.addEventListener('click', function() {
            openCustomerForm();
        });
    }
    
    // View Customer
    document.addEventListener('click', function(e) {
        const viewBtn = e.target.closest('.btn-view');
        if (viewBtn) {
            const customerId = viewBtn.dataset.customerId;
            if (customerId) viewCustomer(customerId);
        }
    });
    
    // Edit Customer
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit');
        if (editBtn) {
            const customerId = editBtn.dataset.customerId;
            if (customerId) openCustomerForm(customerId);
        }
    });
    
    // View Orders
    document.addEventListener('click', function(e) {
        const ordersBtn = e.target.closest('.btn-orders');
        if (ordersBtn) {
            const customerId = ordersBtn.dataset.customerId;
            if (customerId) viewCustomerOrders(customerId);
        }
    });
    
    // Delete Customer
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete');
        if (deleteBtn) {
            const customerId = deleteBtn.dataset.customerId;
            if (customerId && confirm('Are you sure you want to delete this customer?')) {
                deleteCustomer(customerId);
            }
        }
    });
    
    // Modal Close
    const closeViewModal = document.getElementById('closeViewModal');
    if (closeViewModal) {
        closeViewModal.addEventListener('click', function() {
            document.getElementById('viewCustomerModal').style.display = 'none';
        });
    }
    
    const closeFormModal = document.getElementById('closeFormModal');
    if (closeFormModal) {
        closeFormModal.addEventListener('click', function() {
            document.getElementById('customerFormModal').style.display = 'none';
        });
    }
    
    const cancelFormBtn = document.getElementById('cancelFormBtn');
    if (cancelFormBtn) {
        cancelFormBtn.addEventListener('click', function() {
            document.getElementById('customerFormModal').style.display = 'none';
        });
    }
    
    const closeOrdersModal = document.getElementById('closeOrdersModal');
    if (closeOrdersModal) {
        closeOrdersModal.addEventListener('click', function() {
            document.getElementById('customerOrdersModal').style.display = 'none';
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
    
    // Customer Form Submit
    const customerForm = document.getElementById('customerForm');
    if (customerForm) {
        customerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveCustomer();
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

// ===== Filter Customers =====
function filterCustomers() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const orderFilter = document.getElementById('orderFilter');
    
    const search = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const status = statusFilter ? statusFilter.value : 'all';
    const order = orderFilter ? orderFilter.value : 'all';
    
    filteredCustomers = currentCustomers.filter(customer => {
        const matchSearch = !search || 
            customer.name.toLowerCase().includes(search) ||
            customer.email.toLowerCase().includes(search) ||
            (customer.phone && customer.phone.toLowerCase().includes(search));
        
        const matchStatus = status === 'all' || 
            (status === 'active' && customer.is_active) ||
            (status === 'inactive' && !customer.is_active);
        
        const matchOrder = order === 'all' || 
            (order === 'has-orders' && customer.order_count > 0) ||
            (order === 'no-orders' && customer.order_count === 0);
        
        return matchSearch && matchStatus && matchOrder;
    });
    
    currentPage = 1;
    renderTable();
}

// ===== Render Table =====
function renderTable() {
    const tbody = document.getElementById('customersTableBody');
    const totalCount = document.getElementById('totalCount');
    
    if (!tbody) return;
    
    if (filteredCustomers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="no-data">
                    <i class="fas fa-users"></i>
                    <h3>No Customers Found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </td>
            </tr>
        `;
        if (totalCount) totalCount.textContent = '0';
        updatePagination();
        return;
    }
    
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, filteredCustomers.length);
    const pageCustomers = filteredCustomers.slice(start, end);
    
    let html = '';
    let counter = start + 1;
    const avatarColors = ['blue', 'green', 'orange', 'purple', 'red', 'pink', 'teal'];
    
    pageCustomers.forEach(customer => {
        const colorIndex = (customer.id || counter) % avatarColors.length;
        const avatarColor = avatarColors[colorIndex];
        const initial = (customer.name || 'U').charAt(0).toUpperCase();
        
        let healthHtml = '';
        if (customer.is_diabetic || customer.has_high_blood_pressure) {
            if (customer.is_diabetic) {
                healthHtml += `<span class="health-badge diabetic">🩸 Diabetic</span>`;
            }
            if (customer.has_high_blood_pressure) {
                healthHtml += `<span class="health-badge high-bp">❤️ High BP</span>`;
            }
        } else {
            healthHtml = `<span class="health-badge normal">✅ Healthy</span>`;
        }
        
        const statusClass = customer.is_active ? 'active' : 'inactive';
        const statusText = customer.is_active ? 'Active' : 'Inactive';
        
        html += `
            <tr>
                <td><input type="checkbox" class="customer-checkbox" data-customer-id="${customer.id}" /></td>
                <td>
                    <div class="customer-avatar ${avatarColor}">
                        ${initial}
                    </div>
                </td>
                <td>
                    <span class="customer-name-cell">${escapeHtml(customer.name)}</span>
                    <span class="customer-email">${escapeHtml(customer.email)}</span>
                </td>
                <td>
                    <span class="customer-phone"><i class="fas fa-phone"></i> ${escapeHtml(customer.phone || '-')}</span>
                </td>
                <td>
                    <span class="order-count">${customer.order_count || 0}</span>
                </td>
                <td>
                    <span class="total-spent">৳${(customer.total_spent || 0).toFixed(2)}</span>
                </td>
                <td>${healthHtml}</td>
                <td>
                    <span class="customer-status ${statusClass}">
                        <i class="fas fa-circle"></i>
                        ${statusText}
                    </span>
                </td>
                <td>
                    <span style="display: block; font-weight: 500; font-size: 13px;">${formatDate(customer.created_at)}</span>
                    <span style="display: block; font-size: 11px; color: #b2bec3;">${formatTime(customer.created_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-view" data-customer-id="${customer.id}" title="View Details"><i class="fas fa-eye"></i></button>
                        <button class="btn-edit" data-customer-id="${customer.id}" title="Edit Customer"><i class="fas fa-edit"></i></button>
                        <button class="btn-orders" data-customer-id="${customer.id}" title="View Orders"><i class="fas fa-shopping-bag"></i></button>
                        <button class="btn-delete" data-customer-id="${customer.id}" title="Delete Customer"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
        counter++;
    });
    
    tbody.innerHTML = html;
    if (totalCount) totalCount.textContent = filteredCustomers.length;
    updatePagination();
}

// ===== View Customer =====
function viewCustomer(customerId) {
    const customer = currentCustomers.find(c => c.id == customerId);
    if (!customer) {
        showToast('Customer not found!', 'error');
        return;
    }
    
    const modal = document.getElementById('viewCustomerModal');
    const body = document.getElementById('customerDetailBody');
    if (!modal || !body) return;
    
    const ordersHtml = customer.order_count > 0 ? `
        <div style="margin-top: 16px;">
            <h5 style="color: #2c3e50; font-weight: 700; font-size: 14px; border-bottom: 2px solid #e8ecf1; padding-bottom: 8px; margin-bottom: 12px;">
                <i class="fas fa-shopping-bag"></i> Recent Orders
            </h5>
            <table class="customer-orders-table">
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Total</th>
                        <th>Status</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${customer.orders && customer.orders.length > 0 ? 
                        customer.orders.slice(0, 5).map(order => `
                            <tr>
                                <td><strong>${escapeHtml(order.order_id)}</strong></td>
                                <td>৳${(order.total_amount || 0).toFixed(2)}</td>
                                <td><span class="status-badge ${order.status || 'pending'}">${order.status_display || order.status || 'Pending'}</span></td>
                                <td style="font-size: 12px; color: #7f8c8d;">${formatDate(order.created_at)}</td>
                            </tr>
                        `).join('') :
                        '<tr><td colspan="4" style="text-align: center; color: #999; padding: 10px;">No orders found</td></tr>'
                    }
                </tbody>
            </table>
        </div>
    ` : '';
    
    body.innerHTML = `
        <div class="modal-detail-grid">
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-user"></i> Name</span>
                <span class="value">${escapeHtml(customer.name)}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-envelope"></i> Email</span>
                <span class="value">${escapeHtml(customer.email)}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-phone"></i> Phone</span>
                <span class="value">${escapeHtml(customer.phone || 'N/A')}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-map-marker-alt"></i> District</span>
                <span class="value">${escapeHtml(customer.district || 'N/A')}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-shopping-cart"></i> Total Orders</span>
                <span class="value orders">${customer.order_count || 0}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-money-bill"></i> Total Spent</span>
                <span class="value spent">৳${(customer.total_spent || 0).toFixed(2)}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-heartbeat"></i> Diabetes</span>
                <span class="value">${customer.is_diabetic ? '🩸 ' + (customer.diabetes_type || 'Yes') : 'No'}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-heart"></i> Blood Pressure</span>
                <span class="value">${customer.has_high_blood_pressure ? '❤️ High' : 'Normal'}</span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-power-off"></i> Status</span>
                <span class="value"><span class="customer-status ${customer.is_active ? 'active' : 'inactive'}">${customer.is_active ? 'Active' : 'Inactive'}</span></span>
            </div>
            <div class="modal-detail-item">
                <span class="label"><i class="fas fa-calendar"></i> Joined</span>
                <span class="value">${formatDate(customer.created_at)} ${formatTime(customer.created_at)}</span>
            </div>
        </div>
        
        ${customer.address ? `
        <div style="margin-top: 12px; padding: 12px 16px; background: #f8f9fa; border-radius: 10px;">
            <strong style="color: #2c3e50;">Address:</strong>
            <p style="color: #6c757d; margin-top: 4px; font-size: 14px;">${escapeHtml(customer.address)}</p>
        </div>
        ` : ''}
        
        ${ordersHtml}
        
        <div style="display: flex; gap: 10px; justify-content: flex-end; padding-top: 16px; border-top: 2px solid #e8ecf1; margin-top: 16px;">
            <button onclick="closeModal('viewCustomerModal')" class="btn-cancel" style="padding: 8px 20px;">Close</button>
            <button onclick="openCustomerForm(${customer.id})" style="padding: 8px 20px; background: #f39c12; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                <i class="fas fa-edit"></i> Edit
            </button>
        </div>
    `;
    
    modal.style.display = 'flex';
}

// ===== Open Customer Form =====
function openCustomerForm(customerId = null) {
    const modal = document.getElementById('customerFormModal');
    const title = document.getElementById('formModalTitle');
    const editId = document.getElementById('editCustomerId');
    
    if (!modal) return;
    
    if (customerId) {
        const customer = currentCustomers.find(c => c.id == customerId);
        if (!customer) {
            showToast('Customer not found!', 'error');
            return;
        }
        
        title.innerHTML = `<i class="fas fa-edit"></i> Edit Customer: ${escapeHtml(customer.name)}`;
        editId.value = customer.id;
        
        document.getElementById('customerName').value = customer.name || '';
        document.getElementById('customerEmail').value = customer.email || '';
        document.getElementById('customerPhone').value = customer.phone || '';
        document.getElementById('customerAddress').value = customer.address || '';
        document.getElementById('customerDistrict').value = customer.district || '';
        document.getElementById('customerStatus').value = customer.is_active ? 'true' : 'false';
        document.getElementById('customerDiabetes').value = customer.diabetes_type || 'none';
        document.getElementById('customerBloodPressure').value = customer.blood_pressure_status || 'normal';
    } else {
        title.innerHTML = `<i class="fas fa-user-plus"></i> Add New Customer`;
        editId.value = '';
        document.getElementById('customerForm').reset();
        document.getElementById('customerStatus').value = 'true';
        document.getElementById('customerDiabetes').value = 'none';
        document.getElementById('customerBloodPressure').value = 'normal';
    }
    
    modal.style.display = 'flex';
}

// ===== Save Customer =====
function saveCustomer() {
    const editId = document.getElementById('editCustomerId');
    const customerName = document.getElementById('customerName');
    const customerEmail = document.getElementById('customerEmail');
    const customerPhone = document.getElementById('customerPhone');
    const customerAddress = document.getElementById('customerAddress');
    const customerDistrict = document.getElementById('customerDistrict');
    const customerStatus = document.getElementById('customerStatus');
    const customerDiabetes = document.getElementById('customerDiabetes');
    const customerBloodPressure = document.getElementById('customerBloodPressure');
    
    if (!customerName || !customerName.value.trim()) {
        showToast('Customer name is required!', 'error');
        return;
    }
    if (!customerEmail || !customerEmail.value.trim()) {
        showToast('Customer email is required!', 'error');
        return;
    }
    
    const data = {
        name: customerName.value.trim(),
        email: customerEmail.value.trim(),
        phone: customerPhone ? customerPhone.value.trim() : '',
        address: customerAddress ? customerAddress.value.trim() : '',
        district: customerDistrict ? customerDistrict.value.trim() : '',
        is_active: customerStatus ? customerStatus.value === 'true' : true,
        is_diabetic: customerDiabetes ? customerDiabetes.value !== 'none' : false,
        diabetes_type: customerDiabetes ? customerDiabetes.value : 'none',
        has_high_blood_pressure: customerBloodPressure ? customerBloodPressure.value === 'high' : false,
        blood_pressure_status: customerBloodPressure ? customerBloodPressure.value : 'normal',
    };
    
    const csrfToken = getCookie('csrftoken');
    const isEdit = editId && editId.value;
    const url = isEdit ? `/api/customers/${editId.value}/update/` : '/api/customers/create/';
    
    const btn = document.querySelector('.btn-save');
    const originalText = btn ? btn.innerHTML : 'Save';
    if (btn) {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        btn.disabled = true;
    }
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(responseData => {
        if (responseData.status === 'success') {
            showToast(isEdit ? 'Customer updated successfully!' : 'Customer added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(responseData.message || 'Failed to save customer', 'error');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error saving customer. Please try again.', 'error');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// ===== View Customer Orders =====
function viewCustomerOrders(customerId) {
    const customer = currentCustomers.find(c => c.id == customerId);
    if (!customer) {
        showToast('Customer not found!', 'error');
        return;
    }
    
    const modal = document.getElementById('customerOrdersModal');
    const body = document.getElementById('customerOrdersBody');
    if (!modal || !body) return;
    
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/customers/${customerId}/orders/`, {
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const orders = data.orders || [];
            const totalOrders = data.total_orders || 0;
            const totalSpent = data.total_spent || 0;
            
            let ordersHtml = '';
            if (orders.length === 0) {
                ordersHtml = `
                    <div style="text-align: center; padding: 40px 0; color: #999;">
                        <i class="fas fa-shopping-bag" style="font-size: 48px; display: block; margin-bottom: 16px;"></i>
                        <p>No orders found for this customer.</p>
                    </div>
                `;
            } else {
                ordersHtml = `
                    <div style="margin-bottom: 16px; display: flex; gap: 20px; flex-wrap: wrap;">
                        <div style="background: #f8f9fa; padding: 10px 20px; border-radius: 8px;">
                            <span style="color: #7f8c8d;">Total Orders:</span>
                            <span style="font-weight: 700; color: #3498db; font-size: 18px; margin-left: 8px;">${totalOrders}</span>
                        </div>
                        <div style="background: #f8f9fa; padding: 10px 20px; border-radius: 8px;">
                            <span style="color: #7f8c8d;">Total Spent:</span>
                            <span style="font-weight: 700; color: #28a745; font-size: 18px; margin-left: 8px;">৳${totalSpent.toFixed(2)}</span>
                        </div>
                    </div>
                    <table class="customer-orders-table">
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>Items</th>
                                <th>Total</th>
                                <th>Status</th>
                                <th>Payment</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${orders.map(order => `
                                <tr>
                                    <td><strong>${escapeHtml(order.order_id)}</strong></td>
                                    <td>${order.items_count || 0}</td>
                                    <td>৳${(order.total_amount || 0).toFixed(2)}</td>
                                    <td><span class="status-badge ${order.status || 'pending'}">${order.status_display || order.status || 'Pending'}</span></td>
                                    <td><span class="payment-badge ${order.payment_status || 'pending'}">${order.payment_status || 'Pending'}</span></td>
                                    <td style="font-size: 12px; color: #7f8c8d;">${formatDate(order.created_at)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            
            body.innerHTML = `
                <div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 2px solid #e8ecf1;">
                    <h4 style="color: #2c3e50;">${escapeHtml(data.customer_name)}</h4>
                    <p style="color: #7f8c8d; font-size: 13px;">All orders placed by this customer</p>
                </div>
                ${ordersHtml}
                <div style="display: flex; gap: 10px; justify-content: flex-end; padding-top: 16px; border-top: 2px solid #e8ecf1; margin-top: 16px;">
                    <button onclick="closeModal('customerOrdersModal')" class="btn-cancel" style="padding: 8px 20px;">Close</button>
                </div>
            `;
            
            modal.style.display = 'flex';
        } else {
            showToast(data.message || 'Failed to load orders', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error loading orders. Please try again.', 'error');
    });
}

// ===== Delete Customer =====
function deleteCustomer(customerId) {
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/customers/${customerId}/delete/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            currentCustomers = currentCustomers.filter(c => c.id != customerId);
            filteredCustomers = filteredCustomers.filter(c => c.id != customerId);
            renderTable();
            updateStats();
            showToast('Customer deleted successfully!', 'success');
        } else {
            showToast(data.message || 'Failed to delete customer', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error deleting customer. Please try again.', 'error');
    });
}

// ===== Export Customers =====
function exportCustomers(format) {
    const url = `/api/customers/export/${format}/`;
    
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
            link.download = `customers_${new Date().toISOString().slice(0,10)}.${extension}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
            showToast(`Customers exported successfully as ${format.toUpperCase()}!`, 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showToast('Failed to export customers. Please try again.', 'error');
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
    const totalPages = Math.max(1, Math.ceil(filteredCustomers.length / itemsPerPage));
    const newPage = currentPage + direction;
    if (newPage < 1 || newPage > totalPages) return;
    currentPage = newPage;
    renderTable();
    updatePaginationButtons();
}

function goToPage(page) {
    const totalPages = Math.max(1, Math.ceil(filteredCustomers.length / itemsPerPage));
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    updatePaginationButtons();
}

function updatePagination() {
    const totalPages = Math.max(1, Math.ceil(filteredCustomers.length / itemsPerPage));
    const start = filteredCustomers.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, filteredCustomers.length);
    
    const startCount = document.getElementById('startCount');
    const endCount = document.getElementById('endCount');
    const totalCount = document.getElementById('totalCount');
    
    if (startCount) startCount.textContent = start;
    if (endCount) endCount.textContent = end;
    if (totalCount) totalCount.textContent = filteredCustomers.length;
    
    updatePaginationButtons();
}

function updatePaginationButtons() {
    const totalPages = Math.max(1, Math.ceil(filteredCustomers.length / itemsPerPage));
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
window.initializeCustomers = initializeCustomers;
window.renderTable = renderTable;
window.filterCustomers = filterCustomers;
window.viewCustomer = viewCustomer;
window.openCustomerForm = openCustomerForm;
window.saveCustomer = saveCustomer;
window.viewCustomerOrders = viewCustomerOrders;
window.deleteCustomer = deleteCustomer;
window.exportCustomers = exportCustomers;
window.showToast = showToast;
window.closeModal = closeModal;
window.goToPage = goToPage;
window.changePage = changePage;

console.log('✅ Admin Customer JavaScript loaded successfully!');