/**
 * ========================================
 * Superwater - Main JavaScript
 * ড্রপডাউন, কার্ট, মোবাইল মেনু কন্ট্রোল
 * ========================================
 */

// ========================================
// 1. ড্রপডাউন প্রোডাক্ট লোড (সব প্রোডাক্ট, কিন্তু ৩টি দেখাবে)
// ========================================

async function loadDropdownProducts() {
    const container = document.getElementById('dropdownProducts');
    const mobileContainer = document.getElementById('mobileDropdownProducts');
    
    if (!container) return;
    
    try {
        // সব প্রোডাক্ট লোড করুন
        const response = await fetch('/api/dropdown-products/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const products = await response.json();
        
        if (!products || products.length === 0) {
            const emptyHtml = `
                <div class="dropdown-empty">
                    <i class="fas fa-box-open"></i>
                    <p>No products available</p>
                    <small>Check back later for new products</small>
                </div>
            `;
            container.innerHTML = emptyHtml;
            if (mobileContainer) mobileContainer.innerHTML = emptyHtml;
            return;
        }
        
        // প্রথম ৩টি প্রোডাক্ট
        const initialProducts = products.slice(0, 3);
        const remainingProducts = products.slice(3);
        
        // HTML তৈরি - ডেস্কটপ
        let html = '';
        initialProducts.forEach(product => {
            html += createProductItem(product);
        });
        
        if (remainingProducts.length > 0) {
            html += `
                <div class="dropdown-divider"></div>
                <div class="dropdown-more-products">
                    <div class="dropdown-more-header">
                        <span><i class="fas fa-chevron-down"></i> More Products (${remainingProducts.length})</span>
                    </div>
                    <div class="dropdown-more-list">
            `;
            remainingProducts.forEach(product => {
                html += createProductItem(product);
            });
            html += `
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
        
        // ✅ মোবাইলের জন্য HTML তৈরি
        if (mobileContainer) {
            let mobileHtml = '';
            products.forEach(product => {
                mobileHtml += createProductItem(product);
            });
            mobileContainer.innerHTML = mobileHtml;
        }
        
    } catch (error) {
        console.error('Error loading products:', error);
        const errorHtml = `
            <div class="dropdown-empty">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load products</p>
                <small>${error.message || 'Please try again later'}</small>
            </div>
        `;
        container.innerHTML = errorHtml;
        if (mobileContainer) mobileContainer.innerHTML = errorHtml;
    }
}

// ========================================
// 2. প্রোডাক্ট আইটেম HTML তৈরি
// ========================================

function createProductItem(product) {
    const price = parseFloat(product.price).toFixed(2);
    const image = product.image || '/static/images/default-product.jpg';
    const discount = product.discount_percentage || 0;
    const name = escapeHtml(product.name);
    const desc = escapeHtml(product.short_description || 'Premium water product');
    
    // ✅ Shop URL - প্রোডাক্ট ক্লিক করলে Shop পেজে যাবে
    return `
        <a href="/shop/?product=${product.id}" class="dropdown-product-item" data-product-id="${product.id}">
            <img src="${image}" alt="${name}" loading="lazy" 
                 onerror="this.src='/static/images/default-product.jpg'" />
            <div class="product-info">
                <div class="product-name">${name}</div>
                <div class="product-desc">${desc}</div>
            </div>
            <div class="product-price">
                ৳${price}
                ${discount > 0 && product.compare_price ? 
                    `<span class="original">৳${parseFloat(product.compare_price).toFixed(2)}</span>` : ''}
            </div>
            ${discount > 0 ? `<span class="product-badge sale">${discount}%</span>` : ''}
            ${product.is_new ? `<span class="product-badge new">NEW</span>` : ''}
        </a>
    `;
}

// ========================================
// 3. HTML এস্কেপ (XSS প্রতিরোধ)
// ========================================

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ========================================
// 4. মোবাইল ড্রপডাউন টগল
// ========================================

function setupMobileDropdown() {
    const toggleBtn = document.getElementById('mobileShopToggle');
    const dropdown = document.getElementById('mobileShopDropdown');
    
    if (!toggleBtn || !dropdown) return;
    
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // টগল ক্লাস
        this.classList.toggle('open');
        dropdown.classList.toggle('open');
    });
    
    // ড্রপডাউনের ভিতরে ক্লিক করলে বন্ধ না হয়
    dropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
    
    // মোবাইল মেনু বন্ধ হলে ড্রপডাউনও বন্ধ করুন
    const menuOverlay = document.getElementById('mobileMenuOverlay');
    const closeBtn = document.getElementById('mobileMenuClose');
    
    function closeMobileDropdown() {
        toggleBtn.classList.remove('open');
        dropdown.classList.remove('open');
    }
    
    if (menuOverlay) {
        menuOverlay.addEventListener('click', closeMobileDropdown);
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', closeMobileDropdown);
    }
}

// ========================================
// 5. কার্ট ফাংশন
// ========================================

function getCartFromStorage() {
    try {
        return JSON.parse(localStorage.getItem('cart')) || [];
    } catch (error) {
        console.error('Error reading cart from storage:', error);
        return [];
    }
}

function updateGlobalCartPanel() {
    const cart = getCartFromStorage();
    const itemsContainer = document.getElementById('globalCartItems');
    const countLabel = document.getElementById('globalCartCount');
    const totalLabel = document.getElementById('globalCartTotal');
    const badge = document.getElementById('cartBadge');
    
    if (!itemsContainer || !countLabel || !totalLabel) return;
    
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    if (badge) {
        badge.textContent = totalItems;
        badge.style.display = totalItems > 0 ? 'flex' : 'none';
    }
    
    if (cart.length === 0) {
        itemsContainer.innerHTML = '<p class="empty-cart-panel">Your cart is empty</p>';
        countLabel.textContent = '0';
        totalLabel.textContent = 'Tk0.00';
        return;
    }
    
    let html = '';
    let total = 0;
    let itemCount = 0;
    
    cart.forEach((item, index) => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        itemCount += item.quantity;
        const imageUrl = item.image || '/static/images/default-product.jpg';
        const name = escapeHtml(item.name);
        
        html += `
            <div class="cart-panel-item" data-index="${index}">
                <div class="cart-panel-item-image">
                    <img src="${imageUrl}" alt="${name}" 
                         onerror="this.src='/static/images/default-product.jpg'" />
                </div>
                <div class="cart-panel-item-details">
                    <h4>${name}</h4>
                    <p>৳${item.price.toFixed(2)} × ${item.quantity}</p>
                </div>
            </div>
        `;
    });
    
    itemsContainer.innerHTML = html;
    countLabel.textContent = itemCount;
    totalLabel.textContent = `$${total.toFixed(2)}`;
}

// ========================================
// 6. প্যানেল কন্ট্রোল
// ========================================

function openGlobalCartPanel() {
    const panel = document.getElementById('globalCartPanel');
    const overlay = document.getElementById('cartPanelOverlay');
    if (panel) { 
        updateGlobalCartPanel(); 
        panel.classList.add('open'); 
    }
    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeGlobalCartPanel() {
    const panel = document.getElementById('globalCartPanel');
    const overlay = document.getElementById('cartPanelOverlay');
    if (panel) panel.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
}

function openMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileMenuOverlay');
    if (menu) menu.classList.add('open');
    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    const overlay = document.getElementById('mobileMenuOverlay');
    if (menu) menu.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
}

// ========================================
// 7. ইভেন্ট লিসেনার সেটআপ
// ========================================

function setupEventListeners() {
    // কার্ট প্যানেল
    document.getElementById('openGlobalCartBtn')?.addEventListener('click', openGlobalCartPanel);
    document.getElementById('closeGlobalCartPanel')?.addEventListener('click', closeGlobalCartPanel);
    document.getElementById('cartPanelOverlay')?.addEventListener('click', closeGlobalCartPanel);
    
    // মোবাইল মেনু
    document.getElementById('hamburgerBtn')?.addEventListener('click', openMobileMenu);
    document.getElementById('mobileMenuClose')?.addEventListener('click', closeMobileMenu);
    document.getElementById('mobileMenuOverlay')?.addEventListener('click', closeMobileMenu);
    
    // মোবাইল ড্রপডাউন
    setupMobileDropdown();
    
    // Escape Key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeGlobalCartPanel();
            closeMobileMenu();
        }
    });
    
    // Storage Event
    window.addEventListener('storage', function(event) {
        if (event.key === 'cart') {
            updateGlobalCartPanel();
        }
    });
    
    // কার্ট আপডেট ইভেন্ট
    document.addEventListener('cart:updated', updateGlobalCartPanel);
}

// ========================================
// 8. DOM লোড হলে
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    loadDropdownProducts();
    updateGlobalCartPanel();
    setupEventListeners();
    
    console.log('✅ Superwater App initialized successfully!');
});

// ========================================
// 9. গ্লোবাল এক্সপোজ
// ========================================

window.Superwater = {
    loadProducts: loadDropdownProducts,
    openCart: openGlobalCartPanel,
    closeCart: closeGlobalCartPanel,
    openMenu: openMobileMenu,
    closeMenu: closeMobileMenu,
    updateCart: updateGlobalCartPanel
};

// ব্যাকওয়ার্ড কম্প্যাটিবিলিটি
window.loadDropdownProducts = loadDropdownProducts;
window.openGlobalCartPanel = openGlobalCartPanel;
window.closeGlobalCartPanel = closeGlobalCartPanel;
window.openMobileMenu = openMobileMenu;
window.closeMobileMenu = closeMobileMenu;