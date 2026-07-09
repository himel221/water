// ============================================
// ADMIN DASHBOARD JAVASCRIPT (COMPLETE)
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    'use strict';

    // ============================================
    // DOM ELEMENTS
    // ============================================
    const sidebar = document.getElementById('adminSidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarClose = document.getElementById('sidebarClose');
    const mainContent = document.getElementById('mainContent');
    const notificationIcon = document.querySelector('.notification-icon');
    const adminProfile = document.querySelector('.admin-profile');
    const currentDateTime = document.getElementById('currentDateTime');

    // ============================================
    // DEBUG - CHECK ELEMENTS
    // ============================================
    console.log('🔍 Sidebar element:', sidebar);
    console.log('🔍 Toggle button:', sidebarToggle);
    console.log('🔍 Overlay:', sidebarOverlay);
    console.log('🔍 Close button:', sidebarClose);
    console.log('🔍 Main content:', mainContent);

    // ============================================
    // SIDEBAR FUNCTIONALITY
    // ============================================
    
    // Initialize sidebar state
    function initSidebar() {
        if (!sidebar) return;
        
        if (window.innerWidth <= 768) {
            sidebar.classList.add('mobile');
            sidebar.classList.remove('collapsed');
            if (mainContent) {
                mainContent.classList.remove('expanded');
            }
        } else {
            sidebar.classList.remove('mobile');
            // Restore collapsed state from localStorage
            const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
                if (mainContent) {
                    mainContent.classList.add('expanded');
                }
            } else {
                sidebar.classList.remove('collapsed');
                if (mainContent) {
                    mainContent.classList.remove('expanded');
                }
            }
        }
    }

    // Toggle sidebar
    function toggleSidebar(e) {
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        if (!sidebar) {
            console.error('❌ Sidebar not found!');
            return;
        }
        
        if (window.innerWidth <= 768) {
            // Mobile: Toggle open/close
            sidebar.classList.toggle('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
            document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
            console.log('📱 Sidebar toggled:', sidebar.classList.contains('open') ? 'OPEN' : 'CLOSED');
        } else {
            // Desktop: Toggle collapsed/expanded
            sidebar.classList.toggle('collapsed');
            if (mainContent) {
                mainContent.classList.toggle('expanded');
            }
            // Save state
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
            console.log('💻 Sidebar collapsed:', isCollapsed);
        }
    }

    // Open sidebar (mobile only)
    function openSidebar() {
        if (window.innerWidth <= 768 && sidebar) {
            sidebar.classList.add('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.add('active');
            }
            document.body.style.overflow = 'hidden';
            console.log('📱 Sidebar opened');
        }
    }

    // Close sidebar (mobile only)
    function closeSidebar() {
        if (window.innerWidth <= 768 && sidebar) {
            sidebar.classList.remove('open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('active');
            }
            document.body.style.overflow = '';
            console.log('❌ Sidebar closed');
        }
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================

    // 1. Sidebar toggle button
    if (sidebarToggle) {
        console.log('✅ Sidebar toggle button found');
        sidebarToggle.addEventListener('click', toggleSidebar);
        // Better mobile touch support
        sidebarToggle.addEventListener('touchstart', function(e) {
            toggleSidebar(e);
        }, { passive: false });
    } else {
        console.error('❌ Sidebar toggle button NOT found! Check id="sidebarToggle"');
    }

    // 2. Sidebar close button (mobile)
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    // 3. Sidebar overlay click (mobile)
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // 4. Close sidebar on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });

    // 5. Handle window resize with debounce
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            initSidebar();
            if (window.innerWidth > 768 && sidebar && sidebar.classList.contains('open')) {
                closeSidebar();
            }
        }, 250);
    });

    // ============================================
    // MENU ITEM CLICK HANDLER
    // ============================================
    document.querySelectorAll('.menu-item').forEach(function(item) {
        item.addEventListener('click', function(e) {
            // Remove active from all menu items
            document.querySelectorAll('.menu-item').forEach(function(i) {
                i.classList.remove('active');
            });
            // Add active to clicked item
            this.classList.add('active');
            
            // Close sidebar on mobile after clicking
            if (window.innerWidth <= 768) {
                setTimeout(closeSidebar, 300);
            }
        });
    });

    // ============================================
    // NOTIFICATION DROPDOWN
    // ============================================
    if (notificationIcon) {
        notificationIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            
            // Remove existing dropdown
            const existingDropdown = document.querySelector('.notification-dropdown');
            if (existingDropdown) {
                existingDropdown.remove();
                return;
            }
            
            // Create dropdown
            const dropdown = document.createElement('div');
            dropdown.className = 'notification-dropdown show';
            dropdown.innerHTML = `
                <div class="dropdown-header">
                    <h5><i class="fas fa-bell"></i> Notifications</h5>
                    <span class="mark-all-read">Mark all as read</span>
                </div>
                <div class="dropdown-body">
                    <div class="notification-item unread">
                        <i class="fas fa-shopping-bag"></i>
                        <div>
                            <p><strong>New order #1234</strong></p>
                            <small>2 minutes ago</small>
                        </div>
                    </div>
                    <div class="notification-item unread">
                        <i class="fas fa-user"></i>
                        <div>
                            <p><strong>New customer registered</strong></p>
                            <small>15 minutes ago</small>
                        </div>
                    </div>
                    <div class="notification-item">
                        <i class="fas fa-box"></i>
                        <div>
                            <p><strong>Product "Water Bottle" low stock</strong></p>
                            <small>1 hour ago</small>
                        </div>
                    </div>
                    <div class="notification-item">
                        <i class="fas fa-truck"></i>
                        <div>
                            <p><strong>Delivery delayed: Order #1230</strong></p>
                            <small>2 hours ago</small>
                        </div>
                    </div>
                </div>
                <div class="dropdown-footer">
                    <a href="#">View all notifications</a>
                </div>
            `;
            
            // Position dropdown
            const rect = this.getBoundingClientRect();
            dropdown.style.position = 'fixed';
            dropdown.style.top = (rect.bottom + 10) + 'px';
            dropdown.style.right = (window.innerWidth - rect.right) + 'px';
            dropdown.style.zIndex = '9999';
            
            document.body.appendChild(dropdown);
            
            // Mark all as read
            dropdown.querySelector('.mark-all-read')?.addEventListener('click', function() {
                dropdown.querySelectorAll('.notification-item.unread').forEach(function(item) {
                    item.classList.remove('unread');
                });
                this.textContent = 'All read ✓';
                this.style.color = '#27ae60';
            });
            
            // Close on outside click
            setTimeout(function() {
                document.addEventListener('click', function closeDropdown(e) {
                    if (!dropdown.contains(e.target) && !notificationIcon.contains(e.target)) {
                        dropdown.remove();
                        document.removeEventListener('click', closeDropdown);
                    }
                });
            }, 10);
        });
    }

    // ============================================
    // ADMIN PROFILE DROPDOWN
    // ============================================
    if (adminProfile) {
        adminProfile.addEventListener('click', function(e) {
            e.stopPropagation();
            e.preventDefault();
            
            // Remove existing dropdown
            const existingDropdown = document.querySelector('.profile-dropdown');
            if (existingDropdown) {
                existingDropdown.remove();
                return;
            }
            
            // Create dropdown
            const dropdown = document.createElement('div');
            dropdown.className = 'profile-dropdown show';
            dropdown.innerHTML = `
                <div class="dropdown-header">
                    <div class="profile-info">
                        <div class="profile-img-large">A</div>
                        <div>
                            <h5>Admin User</h5>
                            <small>admin@superwater.com</small>
                        </div>
                    </div>
                </div>
                <div class="dropdown-body">
                    <a href="#"><i class="fas fa-user"></i> My Profile</a>
                    <a href="#"><i class="fas fa-cog"></i> Settings</a>
                    <a href="#"><i class="fas fa-lock"></i> Change Password</a>
                    <hr>
                    <a href="{% url 'admin_logout' %}" class="logout-link">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            `;
            
            // Position dropdown
            const rect = this.getBoundingClientRect();
            dropdown.style.position = 'fixed';
            dropdown.style.top = (rect.bottom + 10) + 'px';
            dropdown.style.right = (window.innerWidth - rect.right) + 'px';
            dropdown.style.zIndex = '9999';
            
            document.body.appendChild(dropdown);
            
            // Close on outside click
            setTimeout(function() {
                document.addEventListener('click', function closeDropdown(e) {
                    if (!dropdown.contains(e.target) && !adminProfile.contains(e.target)) {
                        dropdown.remove();
                        document.removeEventListener('click', closeDropdown);
                    }
                });
            }, 10);
        });
    }

    // ============================================
    // DATE TIME UPDATE
    // ============================================
    function updateDateTime() {
        if (!currentDateTime) return;
        
        const now = new Date();
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        };
        currentDateTime.textContent = now.toLocaleDateString('en-US', options);
    }
    
    updateDateTime();
    setInterval(updateDateTime, 1000);

    // ============================================
    // SMOOTH SCROLL
    // ============================================
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                e.preventDefault();
                const target = document.querySelector(targetId);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // ============================================
    // KEYBOARD SHORTCUTS
    // ============================================
    document.addEventListener('keydown', function(e) {
        // Ctrl + B: Toggle sidebar
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            toggleSidebar();
        }
        
        // Ctrl + N: Open notifications
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            if (notificationIcon) {
                notificationIcon.click();
            }
        }
    });

    // ============================================
    // CHART.JS - ORDERS CHART (Enhanced)
    // ============================================
    const chartCanvas = document.getElementById('ordersChart');
    if (chartCanvas && typeof Chart !== 'undefined') {
        // Check if chart is already initialized
        if (!chartCanvas._chart) {
            try {
                const ctx = chartCanvas.getContext('2d');
                
                // Get data from data attributes or use default
                let chartData = [2, 1, 3, 0, 2, 0, 0];
                let chartLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                
                // Try to get data from Django template
                if (chartCanvas.dataset.chartData) {
                    try {
                        const parsedData = JSON.parse(chartCanvas.dataset.chartData);
                        if (Array.isArray(parsedData) && parsedData.length > 0) {
                            chartData = parsedData;
                        }
                    } catch (e) {}
                }
                
                if (chartCanvas.dataset.chartLabels) {
                    try {
                        const parsedLabels = JSON.parse(chartCanvas.dataset.chartLabels);
                        if (Array.isArray(parsedLabels) && parsedLabels.length > 0) {
                            chartLabels = parsedLabels;
                        }
                    } catch (e) {}
                }
                
                const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                gradient.addColorStop(0, 'rgba(52, 152, 219, 0.8)');
                gradient.addColorStop(1, 'rgba(52, 152, 219, 0.1)');
                
                chartCanvas._chart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: chartLabels,
                        datasets: [{
                            label: 'Orders',
                            data: chartData,
                            backgroundColor: gradient,
                            borderColor: 'rgba(52, 152, 219, 1)',
                            borderWidth: 2,
                            borderRadius: 8,
                            hoverBackgroundColor: 'rgba(52, 152, 219, 1)',
                            hoverBorderColor: '#2c3e50'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                                labels: {
                                    font: {
                                        size: 12,
                                        weight: 'bold'
                                    },
                                    color: '#2c3e50'
                                }
                            },
                            tooltip: {
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                borderColor: 'rgba(52, 152, 219, 1)',
                                borderWidth: 2,
                                cornerRadius: 8,
                                padding: 10
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1,
                                    font: {
                                        size: 11
                                    }
                                },
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }
                            },
                            x: {
                                grid: {
                                    display: false
                                }
                            }
                        },
                        animation: {
                            duration: 1000,
                            easing: 'easeInOutQuart'
                        }
                    }
                });
                
                console.log('✅ Chart initialized successfully');
            } catch (error) {
                console.error('❌ Error initializing chart:', error);
            }
        }
    }

    // ============================================
    // STATS COUNTER ANIMATION
    // ============================================
    function animateCounters() {
        const statNumbers = document.querySelectorAll('.stat-info h3');
        
        statNumbers.forEach(function(el) {
            const text = el.textContent;
            const number = parseFloat(text.replace(/[^0-9.]/g, ''));
            
            if (isNaN(number) || number === 0) return;
            
            const duration = 1000;
            const startTime = performance.now();
            const startValue = 0;
            
            function updateCounter(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                // Easing function
                const eased = 1 - Math.pow(1 - progress, 3);
                const currentValue = startValue + (number - startValue) * eased;
                
                if (text.includes('৳')) {
                    el.textContent = '৳' + Math.round(currentValue).toLocaleString();
                } else {
                    el.textContent = Math.round(currentValue).toLocaleString();
                }
                
                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                } else {
                    el.textContent = text;
                }
            }
            
            requestAnimationFrame(updateCounter);
        });
    }

    // Animate counters when they come into view
    if ('IntersectionObserver' in window) {
        const statsGrid = document.querySelector('.stats-grid');
        if (statsGrid) {
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        animateCounters();
                        observer.unobserve(entry.target);
                    }
                });
            });
            observer.observe(statsGrid);
        }
    } else {
        // Fallback for older browsers
        animateCounters();
    }

    // ============================================
    // REFRESH BUTTON (Optional)
    // ============================================
    const refreshBtn = document.querySelector('.refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function(e) {
            e.preventDefault();
            this.classList.add('spinning');
            setTimeout(function() {
                location.reload();
            }, 500);
        });
    }

    // ============================================
    // CONSOLE LOG
    // ============================================
    console.log('✅ Admin Dashboard initialized successfully');
    console.log('📐 Window width:', window.innerWidth);
    console.log('📱 Mobile mode:', window.innerWidth <= 768);
    console.log('📂 Sidebar collapsed:', sidebar ? sidebar.classList.contains('collapsed') : 'N/A');

    // ============================================
    // EXPOSE FUNCTIONS GLOBALLY
    // ============================================
    window.toggleSidebar = toggleSidebar;
    window.openSidebar = openSidebar;
    window.closeSidebar = closeSidebar;
    window.initSidebar = initSidebar;
    window.updateDateTime = updateDateTime;
    window.animateCounters = animateCounters;
    window.updateChartData = function(newData) {
        const chartCanvas = document.getElementById('ordersChart');
        if (chartCanvas && chartCanvas._chart) {
            chartCanvas._chart.data.datasets[0].data = newData;
            chartCanvas._chart.update();
            console.log('📊 Chart data updated:', newData);
        }
    };

}); // End of DOMContentLoaded

// ============================================
// JQUERY FALLBACK (if jQuery is loaded)
// ============================================
if (typeof jQuery !== 'undefined') {
    $(document).ready(function() {
        // Sidebar toggle with jQuery
        $('#sidebarToggle').on('click', function(e) {
            e.preventDefault();
            $('#adminSidebar').toggleClass('open');
            $('#sidebarOverlay').toggleClass('active');
            if ($('#adminSidebar').hasClass('open')) {
                $('body').css('overflow', 'hidden');
            } else {
                $('body').css('overflow', '');
            }
        });
        
        // Overlay click
        $('#sidebarOverlay').on('click', function() {
            $('#adminSidebar').removeClass('open');
            $(this).removeClass('active');
            $('body').css('overflow', '');
        });
        
        // Close button
        $('#sidebarClose').on('click', function() {
            $('#adminSidebar').removeClass('open');
            $('#sidebarOverlay').removeClass('active');
            $('body').css('overflow', '');
        });
    });
}

// ============================================
// DROPDOWN STYLES (Auto-injected)
// ============================================
(function() {
    const style = document.createElement('style');
    style.textContent = `
        /* Notification & Profile Dropdown Styles */
        .notification-dropdown,
        .profile-dropdown {
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
            min-width: 320px;
            max-width: 380px;
            overflow: hidden;
            animation: dropdownSlideIn 0.3s ease;
        }

        @keyframes dropdownSlideIn {
            from {
                opacity: 0;
                transform: translateY(-10px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .dropdown-header {
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .dropdown-header h5 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
            color: #2c3e50;
        }

        .dropdown-header h5 i {
            color: #3498db;
            margin-right: 8px;
        }

        .dropdown-header .mark-all-read {
            font-size: 12px;
            color: #3498db;
            cursor: pointer;
            transition: color 0.3s;
        }

        .dropdown-header .mark-all-read:hover {
            color: #2980b9;
            text-decoration: underline;
        }

        .dropdown-body {
            max-height: 300px;
            overflow-y: auto;
            padding: 5px 0;
        }

        .dropdown-body::-webkit-scrollbar {
            width: 4px;
        }

        .dropdown-body::-webkit-scrollbar-thumb {
            background: #ddd;
            border-radius: 10px;
        }

        .notification-item {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 20px;
            border-bottom: 1px solid #f5f5f5;
            transition: background 0.2s;
            cursor: pointer;
        }

        .notification-item:hover {
            background: #f8f9fa;
        }

        .notification-item.unread {
            background: #f0f7ff;
        }

        .notification-item.unread:hover {
            background: #e3eef9;
        }

        .notification-item i {
            font-size: 16px;
            color: #3498db;
            margin-top: 3px;
            width: 20px;
        }

        .notification-item p {
            margin: 0;
            font-size: 13px;
            color: #2c3e50;
        }

        .notification-item small {
            font-size: 11px;
            color: #999;
        }

        .dropdown-footer {
            padding: 10px 20px;
            border-top: 1px solid #f0f0f0;
            text-align: center;
        }

        .dropdown-footer a {
            color: #3498db;
            font-size: 13px;
            text-decoration: none;
            transition: color 0.3s;
        }

        .dropdown-footer a:hover {
            color: #2980b9;
            text-decoration: underline;
        }

        /* Profile Dropdown */
        .profile-info {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .profile-img-large {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 18px;
            font-weight: 700;
        }

        .profile-info h5 {
            margin: 0;
            font-size: 14px;
            font-weight: 600;
            color: #2c3e50;
        }

        .profile-info small {
            font-size: 12px;
            color: #999;
        }

        .profile-dropdown .dropdown-body a {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 20px;
            color: #2c3e50;
            text-decoration: none;
            font-size: 13px;
            transition: background 0.2s;
        }

        .profile-dropdown .dropdown-body a:hover {
            background: #f8f9fa;
        }

        .profile-dropdown .dropdown-body a i {
            width: 18px;
            color: #666;
        }

        .profile-dropdown .dropdown-body hr {
            margin: 5px 20px;
            border: none;
            border-top: 1px solid #f0f0f0;
        }

        .profile-dropdown .dropdown-body .logout-link {
            color: #e74c3c;
        }

        .profile-dropdown .dropdown-body .logout-link i {
            color: #e74c3c;
        }

        /* Refresh button spinning */
        .refresh-btn.spinning i {
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 576px) {
            .notification-dropdown,
            .profile-dropdown {
                min-width: 280px;
                max-width: 320px;
                right: 10px !important;
            }
        }

        /* Badge animation */
        .notification-icon .badge {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    `;
    document.head.appendChild(style);
})();

// ============================================
// EXPOSE CHART UPDATE FUNCTION
// ============================================
window.updateChartData = function(newData) {
    const chartCanvas = document.getElementById('ordersChart');
    if (chartCanvas && chartCanvas._chart) {
        chartCanvas._chart.data.datasets[0].data = newData;
        chartCanvas._chart.update();
        console.log('📊 Chart data updated:', newData);
    }
};

// ============================================
// READY STATE CHECK
// ============================================
console.log('📦 admin_dashboard.js loaded successfully');
console.log('🔄 Document ready state:', document.readyState);