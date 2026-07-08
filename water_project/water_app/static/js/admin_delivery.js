// ===== Admin Delivery JavaScript - Complete =====

let currentDistricts = [];
let filteredDistricts = [];
let currentPage = 1;
const itemsPerPage = 10;

/**
 * Initialize delivery management
 */
function initializeDelivery(districts) {
    console.log('📦 Districts Data:', districts);
    console.log('📦 Total Districts:', districts ? districts.length : 0);
    
    currentDistricts = districts || [];
    filteredDistricts = [...currentDistricts];
    
    updateStats();
    setupEventListeners();
    renderTable();
}

// ===== Update Stats =====
function updateStats() {
    const total = currentDistricts.length;
    const active = currentDistricts.filter(d => d.is_active).length;
    const inactive = currentDistricts.filter(d => !d.is_active).length;
    const avgCharge = currentDistricts.length > 0 ? 
        (currentDistricts.reduce((sum, d) => sum + d.charge, 0) / currentDistricts.length) : 0;
    
    const statNumbers = document.querySelectorAll('.stat-number');
    if (statNumbers.length >= 4) {
        statNumbers[0].textContent = total;
        statNumbers[1].textContent = active;
        statNumbers[2].textContent = inactive;
        statNumbers[3].textContent = Math.round(avgCharge);
    }
}

// ===== Setup Event Listeners =====
function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterDistricts, 300));
    }
    
    // Status Filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', filterDistricts);
    }
    
    // Select All
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            document.querySelectorAll('.district-checkbox').forEach(cb => {
                cb.checked = this.checked;
            });
        });
    }
    
    // Export Excel
    const exportExcel = document.getElementById('exportExcel');
    if (exportExcel) {
        exportExcel.addEventListener('click', function() {
            exportDistricts('excel');
        });
    }
    
    // Export PDF
    const exportPdf = document.getElementById('exportPdf');
    if (exportPdf) {
        exportPdf.addEventListener('click', function() {
            exportDistricts('pdf');
        });
    }
    
    // Refresh
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            location.reload();
        });
    }
    
    // Add District
    const addDistrictBtn = document.getElementById('addDistrictBtn');
    if (addDistrictBtn) {
        addDistrictBtn.addEventListener('click', function() {
            openDistrictForm();
        });
    }
    
    const emptyAddBtn = document.getElementById('emptyAddBtn');
    if (emptyAddBtn) {
        emptyAddBtn.addEventListener('click', function() {
            openDistrictForm();
        });
    }
    
    // Edit District
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.btn-edit');
        if (editBtn) {
            const districtId = editBtn.dataset.districtId;
            if (districtId) openDistrictForm(districtId);
        }
    });
    
    // Toggle Status
    document.addEventListener('click', function(e) {
        const toggleBtn = e.target.closest('.btn-toggle');
        if (toggleBtn) {
            const districtId = toggleBtn.dataset.districtId;
            if (districtId) toggleDistrictStatus(districtId);
        }
    });
    
    // Delete District
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.btn-delete');
        if (deleteBtn) {
            const districtId = deleteBtn.dataset.districtId;
            if (districtId && confirm('Are you sure you want to delete this district?')) {
                deleteDistrict(districtId);
            }
        }
    });
    
    // Modal Close
    const closeFormModal = document.getElementById('closeFormModal');
    if (closeFormModal) {
        closeFormModal.addEventListener('click', function() {
            document.getElementById('districtFormModal').style.display = 'none';
        });
    }
    
    const cancelFormBtn = document.getElementById('cancelFormBtn');
    if (cancelFormBtn) {
        cancelFormBtn.addEventListener('click', function() {
            document.getElementById('districtFormModal').style.display = 'none';
        });
    }
    
    // Close modal on overlay click
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
    
    // Form Submit
    const districtForm = document.getElementById('districtForm');
    if (districtForm) {
        districtForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveDistrict();
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

// ===== Filter Districts =====
function filterDistricts() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    
    const search = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const status = statusFilter ? statusFilter.value : 'all';
    
    filteredDistricts = currentDistricts.filter(district => {
        const matchSearch = !search || 
            district.district_name.toLowerCase().includes(search) ||
            district.district.toLowerCase().includes(search);
        
        const matchStatus = status === 'all' || 
            (status === 'active' && district.is_active) ||
            (status === 'inactive' && !district.is_active);
        
        return matchSearch && matchStatus;
    });
    
    currentPage = 1;
    renderTable();
}

// ===== Render Table =====
function renderTable() {
    const tbody = document.getElementById('deliveryTableBody');
    const totalCount = document.getElementById('totalCount');
    
    if (!tbody) return;
    
    if (filteredDistricts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="no-data">
                    <i class="fas fa-truck"></i>
                    <h3>No Districts Found</h3>
                    <p>Try adjusting your filters or search terms.</p>
                </td>
            </tr>
        `;
        if (totalCount) totalCount.textContent = '0';
        updatePagination();
        return;
    }
    
    const start = (currentPage - 1) * itemsPerPage;
    const end = Math.min(start + itemsPerPage, filteredDistricts.length);
    const pageDistricts = filteredDistricts.slice(start, end);
    
    let html = '';
    let counter = start + 1;
    pageDistricts.forEach(district => {
        const statusClass = district.is_active ? 'active' : 'inactive';
        const statusText = district.is_active ? 'Active' : 'Inactive';
        
        html += `
            <tr>
                <td><input type="checkbox" class="district-checkbox" data-district-id="${district.id}" /></td>
                <td>${counter}</td>
                <td>
                    <span class="district-name">${escapeHtml(district.district_name)}</span>
                    <span class="district-code">${escapeHtml(district.district)}</span>
                </td>
                <td><span class="charge-amount">৳${(district.charge || 0).toFixed(2)}</span></td>
                <td><span class="delivery-time">${escapeHtml(district.delivery_time || '2-3 days')}</span></td>
                <td><span class="status-badge ${statusClass}"><i class="fas fa-circle"></i> ${statusText}</span></td>
                <td>
                    <span style="display: block; font-weight: 500; font-size: 12px;">${formatDate(district.created_at)}</span>
                    <span style="display: block; font-size: 10px; color: #b2bec3;">${formatTime(district.created_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-edit" data-district-id="${district.id}" title="Edit"><i class="fas fa-edit"></i></button>
                        <button class="btn-toggle" data-district-id="${district.id}" title="Toggle Status">
                            <i class="fas ${district.is_active ? 'fa-eye-slash' : 'fa-eye'}"></i>
                        </button>
                        <button class="btn-delete" data-district-id="${district.id}" title="Delete"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `;
        counter++;
    });
    
    tbody.innerHTML = html;
    if (totalCount) totalCount.textContent = filteredDistricts.length;
    updatePagination();
}

// ===== Open District Form =====
function openDistrictForm(districtId = null) {
    const modal = document.getElementById('districtFormModal');
    const title = document.getElementById('formModalTitle');
    const editId = document.getElementById('editDistrictId');
    
    if (!modal) return;
    
    if (districtId) {
        // Edit mode
        const district = currentDistricts.find(d => d.id == districtId);
        if (!district) {
            showToast('District not found!', 'error');
            return;
        }
        
        title.innerHTML = `<i class="fas fa-edit"></i> Edit District: ${escapeHtml(district.district_name)}`;
        editId.value = district.id;
        
        document.getElementById('districtName').value = district.district_name || '';
        document.getElementById('districtCode').value = district.district || '';
        document.getElementById('districtCharge').value = district.charge || '';
        document.getElementById('deliveryTime').value = district.delivery_time || '2-3 days';
        document.getElementById('districtStatus').value = district.is_active ? 'true' : 'false';
    } else {
        // Add mode
        title.innerHTML = `<i class="fas fa-plus"></i> Add New District`;
        editId.value = '';
        document.getElementById('districtForm').reset();
        document.getElementById('deliveryTime').value = '2-3 days';
        document.getElementById('districtStatus').value = 'true';
    }
    
    modal.style.display = 'flex';
}

// ===== Save District =====
function saveDistrict() {
    const editId = document.getElementById('editDistrictId');
    const districtName = document.getElementById('districtName');
    const districtCode = document.getElementById('districtCode');
    const districtCharge = document.getElementById('districtCharge');
    const deliveryTime = document.getElementById('deliveryTime');
    const districtStatus = document.getElementById('districtStatus');
    
    // Validate
    if (!districtName || !districtName.value.trim()) {
        showToast('District name is required!', 'error');
        return;
    }
    if (!districtCharge || !districtCharge.value) {
        showToast('Delivery charge is required!', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('district_name', districtName.value.trim());
    formData.append('district', districtCode ? districtCode.value.trim().toLowerCase() : '');
    formData.append('charge', districtCharge.value);
    formData.append('delivery_time', deliveryTime ? deliveryTime.value.trim() : '2-3 days');
    formData.append('is_active', districtStatus ? districtStatus.value === 'true' : true);
    
    const csrfToken = getCookie('csrftoken');
    const isEdit = editId && editId.value;
    const url = isEdit ? `/api/delivery/${editId.value}/update/` : '/api/delivery/create/';
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
            showToast(isEdit ? 'District updated successfully!' : 'District added successfully!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Failed to save district', 'error');
            if (btn) {
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error saving district. Please try again.', 'error');
        if (btn) {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// ===== Toggle District Status =====
function toggleDistrictStatus(districtId) {
    const district = currentDistricts.find(d => d.id == districtId);
    if (!district) return;
    
    const newStatus = !district.is_active;
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/delivery/${districtId}/toggle/`, {
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
            district.is_active = newStatus;
            renderTable();
            updateStats();
            showToast(`District ${newStatus ? 'activated' : 'deactivated'} successfully!`, 'success');
        } else {
            showToast(data.message || 'Failed to toggle status', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error toggling district status', 'error');
    });
}

// ===== Delete District =====
function deleteDistrict(districtId) {
    const csrfToken = getCookie('csrftoken');
    
    fetch(`/api/delivery/${districtId}/delete/`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            currentDistricts = currentDistricts.filter(d => d.id != districtId);
            filteredDistricts = filteredDistricts.filter(d => d.id != districtId);
            renderTable();
            updateStats();
            showToast('District deleted successfully!', 'success');
        } else {
            showToast(data.message || 'Failed to delete district', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error deleting district. Please try again.', 'error');
    });
}

// ===== Export Districts =====
function exportDistricts(format) {
    const url = `/api/delivery/export/${format}/`;
    
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
            link.download = `districts_${new Date().toISOString().slice(0,10)}.${extension}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
            showToast(`Districts exported successfully as ${format.toUpperCase()}!`, 'success');
        })
        .catch(error => {
            console.error('Export error:', error);
            showToast('Failed to export districts. Please try again.', 'error');
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

// ===== Pagination =====
function changePage(direction) {
    const totalPages = Math.max(1, Math.ceil(filteredDistricts.length / itemsPerPage));
    const newPage = currentPage + direction;
    if (newPage < 1 || newPage > totalPages) return;
    currentPage = newPage;
    renderTable();
    updatePaginationButtons();
}

function goToPage(page) {
    const totalPages = Math.max(1, Math.ceil(filteredDistricts.length / itemsPerPage));
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    renderTable();
    updatePaginationButtons();
}

function updatePagination() {
    const totalPages = Math.max(1, Math.ceil(filteredDistricts.length / itemsPerPage));
    const start = filteredDistricts.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const end = Math.min(currentPage * itemsPerPage, filteredDistricts.length);
    
    const startCount = document.getElementById('startCount');
    const endCount = document.getElementById('endCount');
    const totalCount = document.getElementById('totalCount');
    
    if (startCount) startCount.textContent = start;
    if (endCount) endCount.textContent = end;
    if (totalCount) totalCount.textContent = filteredDistricts.length;
    
    updatePaginationButtons();
}

function updatePaginationButtons() {
    const totalPages = Math.max(1, Math.ceil(filteredDistricts.length / itemsPerPage));
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
window.initializeDelivery = initializeDelivery;
window.renderTable = renderTable;
window.filterDistricts = filterDistricts;
window.openDistrictForm = openDistrictForm;
window.saveDistrict = saveDistrict;
window.toggleDistrictStatus = toggleDistrictStatus;
window.deleteDistrict = deleteDistrict;
window.exportDistricts = exportDistricts;
window.showToast = showToast;
window.goToPage = goToPage;
window.changePage = changePage;

console.log('✅ Admin Delivery JavaScript loaded successfully!');