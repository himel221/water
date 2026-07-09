// ============================================
// SIDEBAR FUNCTIONALITY
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // ----- DOM Elements -----
    const sidebar = document.getElementById('adminSidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarToggle = document.getElementById('sidebarToggle'); // From navbar

    // ----- Open Sidebar -----
    function openSidebar() {
        if (sidebar) {
            sidebar.classList.add('open');
        }
        if (sidebarOverlay) {
            sidebarOverlay.classList.add('active');
        }
        document.body.style.overflow = 'hidden';
    }

    // ----- Close Sidebar -----
    function closeSidebar() {
        if (sidebar) {
            sidebar.classList.remove('open');
        }
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('active');
        }
        document.body.style.overflow = '';
    }

    // ----- Toggle Sidebar -----
    function toggleSidebar() {
        if (sidebar && sidebar.classList.contains('open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }

    // ----- Event Listeners -----
    
    // Toggle button (from navbar)
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }

    // Close button (inside sidebar)
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }

    // Overlay click
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', closeSidebar);
    }

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });

    // Auto-close on window resize (desktop)
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && sidebar && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });

    // ----- Active Menu Item -----
    // Highlight current page based on URL
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        const link = item.closest('a');
        if (link) {
            const href = link.getAttribute('href');
            if (href && href !== '#' && currentPath.includes(href)) {
                menuItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
            }
        }
    });

    // ----- Console Log for Debug -----
    console.log('✅ Sidebar initialized successfully');
});

// ============================================
// EXPOSE FUNCTIONS GLOBALLY (if needed)
// ============================================
window.openSidebar = openSidebar;
window.closeSidebar = closeSidebar;
window.toggleSidebar = toggleSidebar;