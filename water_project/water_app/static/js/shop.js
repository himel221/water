// ============================================
// SHOP PAGE - Complete JavaScript
// ============================================

// ===== Product Data =====
let productData = [];

// ===== Initialize Shop =====
function initializeShop(products) {
    productData = products || [];
    console.log('🛒 Shop initialized with', productData.length, 'products');
    
    loadCart();
    setupFilters();
    setupAddToCart();
}

// ===== Setup Filters =====
function setupFilters() {
    // Category filter
    document.querySelectorAll('.filter-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(function(b) {
                b.classList.remove('active');
            });
            this.classList.add('active');
            
            var category = this.dataset.category;
            filterProducts(category);
        });
    });
    
    // Search filter
    var searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterProducts();
        });
    }
    
    // Sort filter
    var sortSelect = document.getElementById('sortSelect');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            sortProducts(this.value);
        });
    }
}

// ===== Filter Products =====
function filterProducts(category) {
    var searchInput = document.getElementById('searchInput');
    var search = searchInput ? searchInput.value.toLowerCase() : '';
    var cards = document.querySelectorAll('.product-card');
    
    cards.forEach(function(card) {
        var cardCategory = card.dataset.category;
        var cardName = card.querySelector('.product-name').textContent.toLowerCase();
        var cardDesc = card.querySelector('.product-desc').textContent.toLowerCase();
        
        var matchCategory = !category || category === 'all' || cardCategory === category;
        var matchSearch = !search || cardName.includes(search) || cardDesc.includes(search);
        
        if (matchCategory && matchSearch) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// ===== Sort Products =====
function sortProducts(sortType) {
    var grid = document.getElementById('productGrid');
    if (!grid) return;
    
    var cards = Array.from(grid.querySelectorAll('.product-card'));
    
    cards.sort(function(a, b) {
        var priceA = parseFloat(a.dataset.price) || 0;
        var priceB = parseFloat(b.dataset.price) || 0;
        var discountA = parseFloat(a.dataset.discount) || 0;
        var discountB = parseFloat(b.dataset.discount) || 0;
        
        if (sortType === 'price-low') return priceA - priceB;
        if (sortType === 'price-high') return priceB - priceA;
        if (sortType === 'discount') return discountB - discountA;
        return 0;
    });
    
    cards.forEach(function(card) {
        grid.appendChild(card);
    });
}

// ===== Setup Add to Cart =====
function setupAddToCart() {
    document.querySelectorAll('.btn-add-cart:not(.disabled)').forEach(function(button) {
        // Remove existing event listeners to avoid duplicates
        button.removeEventListener('click', handleAddToCart);
        button.addEventListener('click', handleAddToCart);
    });
}

function handleAddToCart(e) {
    var button = e.currentTarget;
    var productId = button.dataset.productId;
    var productName = button.dataset.productName;
    var productPrice = parseFloat(button.dataset.productPrice);
    var productImage = button.dataset.productImage;
    var stock = parseInt(button.dataset.stock);
    var specialOffer = button.dataset.specialOffer || '';
    var originalPrice = parseFloat(button.dataset.originalPrice) || productPrice;
    var discount = parseFloat(button.dataset.discount) || 0;
    
    addToCart(productId, productName, productPrice, productImage, stock, specialOffer, originalPrice, discount);
}

// ===== Cart Functions =====

// Load cart from localStorage
function loadCart() {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    updateCartUI(cart);
    updateCartBadge(cart);
}

// Add to cart
function addToCart(id, name, price, image, stock, specialOffer, originalPrice, discount) {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    // Check if product already in cart
    var existingItem = null;
    for (var i = 0; i < cart.length; i++) {
        if (cart[i].id == id) {
            existingItem = cart[i];
            break;
        }
    }
    
    if (existingItem) {
        if (existingItem.quantity < stock) {
            existingItem.quantity += 1;
            showNotification(name + ' quantity updated!');
        } else {
            showNotification('Sorry, only ' + stock + ' items available!');
            return;
        }
    } else {
        cart.push({
            id: id,
            name: name,
            price: price,
            original_price: originalPrice,
            image: image,
            quantity: 1,
            special_offer: specialOffer,
            discount: discount
        });
        if (discount > 0) {
            showNotification(name + ' added! Save ৳' + discount.toFixed(2));
        } else {
            showNotification(name + ' added to cart!');
        }
    }
    
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI(cart);
    updateCartBadge(cart);
    
    // Open cart sidebar
    var cartSidebar = document.getElementById('cartSidebar');
    if (cartSidebar) {
        cartSidebar.classList.add('open');
    }
    
    // Dispatch event for other pages
    document.dispatchEvent(new CustomEvent('cart:updated'));
}

// Update cart UI in sidebar
function updateCartUI(cart) {
    var cartItems = document.getElementById('cartItems');
    var cartCount = document.getElementById('cartCount');
    var cartTotal = document.getElementById('cartTotal');
    
    if (!cartItems) return;
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<div class="empty-cart-state"><i class="fas fa-shopping-bag"></i><p>Your cart is empty</p><span class="empty-sub">Start shopping to add items</span></div>';
        if (cartCount) cartCount.textContent = '0';
        if (cartTotal) cartTotal.textContent = '৳0.00';
        return;
    }
    
    var html = '';
    var total = 0;
    var itemCount = 0;
    
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var hasDiscount = item.original_price && item.original_price > item.price;
        var itemTotal = item.price * item.quantity;
        var originalTotal = item.original_price ? item.original_price * item.quantity : itemTotal;
        var savings = originalTotal - itemTotal;
        total += itemTotal;
        itemCount += item.quantity;
        
        html += '<div class="cart-item" data-index="' + i + '">';
        html += '<div class="cart-item-image"><img src="' + item.image + '" alt="' + item.name + '" /></div>';
        html += '<div class="cart-item-details">';
        html += '<h4 class="cart-item-name">' + item.name + '</h4>';
        html += '<div class="cart-item-price">';
        html += '<span class="current-price">৳' + item.price.toFixed(2) + '</span>';
        if (hasDiscount) {
            html += '<span class="original-price">৳' + item.original_price.toFixed(2) + '</span>';
            html += '<span class="savings-badge">Save ৳' + (item.original_price - item.price).toFixed(2) + '</span>';
        }
        html += '</div>';
        if (item.special_offer) {
            html += '<div class="cart-item-offer">🎉 ' + item.special_offer + '</div>';
        }
        html += '<div class="cart-item-quantity">';
        html += '<button class="cart-qty-btn minus" data-index="' + i + '">-</button>';
        html += '<span class="cart-qty">' + item.quantity + '</span>';
        html += '<button class="cart-qty-btn plus" data-index="' + i + '">+</button>';
        html += '<button class="cart-remove" data-index="' + i + '"><i class="fas fa-trash"></i></button>';
        html += '</div></div>';
        html += '<div class="cart-item-subtotal">';
        if (hasDiscount) {
            html += '<span class="item-original-total">৳' + originalTotal.toFixed(2) + '</span>';
            html += '<span class="item-savings">Save ৳' + savings.toFixed(2) + '</span>';
        }
        html += '<span class="item-total">৳' + itemTotal.toFixed(2) + '</span>';
        html += '</div></div>';
    }
    
    cartItems.innerHTML = html;
    if (cartCount) cartCount.textContent = itemCount;
    if (cartTotal) cartTotal.textContent = '৳' + total.toFixed(2);
    
    // Add event listeners to cart items
    document.querySelectorAll('.cart-qty-btn.minus').forEach(function(btn) {
        btn.removeEventListener('click', handleCartMinus);
        btn.addEventListener('click', handleCartMinus);
    });
    
    document.querySelectorAll('.cart-qty-btn.plus').forEach(function(btn) {
        btn.removeEventListener('click', handleCartPlus);
        btn.addEventListener('click', handleCartPlus);
    });
    
    document.querySelectorAll('.cart-remove').forEach(function(btn) {
        btn.removeEventListener('click', handleCartRemove);
        btn.addEventListener('click', handleCartRemove);
    });
}

// Cart event handlers
function handleCartMinus(e) {
    var index = parseInt(this.dataset.index);
    updateCartQuantity(index, -1);
}

function handleCartPlus(e) {
    var index = parseInt(this.dataset.index);
    updateCartQuantity(index, 1);
}

function handleCartRemove(e) {
    var index = parseInt(this.dataset.index);
    if (confirm('Are you sure you want to remove this item?')) {
        removeFromCart(index);
    }
}

// Update cart quantity
function updateCartQuantity(index, change) {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    if (cart[index]) {
        var newQuantity = cart[index].quantity + change;
        if (newQuantity > 0) {
            cart[index].quantity = newQuantity;
        } else {
            cart.splice(index, 1);
        }
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartUI(cart);
        updateCartBadge(cart);
        document.dispatchEvent(new CustomEvent('cart:updated'));
    }
}

// Remove from cart
function removeFromCart(index) {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartUI(cart);
    updateCartBadge(cart);
    showNotification('Item removed from cart!');
    document.dispatchEvent(new CustomEvent('cart:updated'));
}

// Update cart badge
function updateCartBadge(cart) {
    var totalItems = 0;
    for (var i = 0; i < cart.length; i++) {
        totalItems += parseInt(cart[i].quantity) || 0;
    }
    
    // Update all cart badges
    document.querySelectorAll('.cart-count, #cartCount').forEach(function(el) {
        el.textContent = totalItems;
    });
    
    // Update floating cart badge if exists
    var floatingBadge = document.querySelector('.floating-cart-badge');
    if (floatingBadge) {
        floatingBadge.textContent = totalItems;
        floatingBadge.style.display = totalItems > 0 ? 'flex' : 'none';
    }
}

// Show notification
function showNotification(message) {
    var notification = document.getElementById('cartNotification');
    if (!notification) return;
    
    var messageEl = document.getElementById('notificationMessage');
    if (messageEl) {
        messageEl.textContent = message;
    }
    
    notification.classList.add('show');
    
    clearTimeout(notification._timeout);
    notification._timeout = setTimeout(function() {
        notification.classList.remove('show');
    }, 3000);
}

// ===== Cart Sidebar Controls =====
function setupCartSidebar() {
    var closeBtn = document.getElementById('closeCart');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('cartSidebar').classList.remove('open');
        });
    }
    
    var checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn) {
        checkoutBtn.addEventListener('click', function() {
            var cart = JSON.parse(localStorage.getItem('cart')) || [];
            if (cart.length === 0) {
                showNotification('Your cart is empty!');
                return;
            }
            window.location.href = '/checkout/';
        });
    }
    
    // Close sidebar on overlay click
    var overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            document.getElementById('cartSidebar').classList.remove('open');
        });
    }
}

// ===== Initialize on DOM ready =====
document.addEventListener('DOMContentLoaded', function() {
    // Get product data from global variable
    if (typeof productData !== 'undefined' && productData.length > 0) {
        initializeShop(productData);
    } else if (window.productData) {
        initializeShop(window.productData);
    }
    
    setupCartSidebar();
    
    // Listen for cart updates
    document.addEventListener('cart:updated', function() {
        loadCart();
    });
});

// ===== Make functions global =====
window.initializeShop = initializeShop;
window.filterProducts = filterProducts;
window.sortProducts = sortProducts;
window.addToCart = addToCart;
window.loadCart = loadCart;
window.updateCartUI = updateCartUI;
window.updateCartQuantity = updateCartQuantity;
window.removeFromCart = removeFromCart;
window.showNotification = showNotification;
window.updateCartBadge = updateCartBadge;

console.log('✅ Shop JavaScript loaded successfully!');