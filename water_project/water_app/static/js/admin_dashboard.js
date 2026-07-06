// ===== Admin Dashboard JavaScript =====

// ===== Sidebar Toggle for Mobile =====
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (window.innerWidth <= 768) {
        sidebar.classList.add('mobile');
    }
    
    sidebarToggle.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
        } else {
            sidebar.classList.toggle('collapsed');
            document.getElementById('mainContent').classList.toggle('expanded');
        }
    });
});

// ===== Menu Item Click =====
document.querySelectorAll('.menu-item').forEach(function(item) {
    item.addEventListener('click', function() {
        document.querySelectorAll('.menu-item').forEach(function(i) {
            i.classList.remove('active');
        });
        this.classList.add('active');
    });
});

// ===== Notification Click =====
document.querySelector('.notification-icon')?.addEventListener('click', function() {
    alert('You have 3 new notifications!');
});

// ===== Admin Profile Click =====
document.querySelector('.admin-profile')?.addEventListener('click', function() {
    // Show profile dropdown
});

// ===== Chart.js - Orders Chart =====
// (Chart already initialized in HTML)

// ===== Smooth Scroll =====
document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});