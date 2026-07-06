// ===== Cart Functions =====

// Load cart from localStorage
function loadCart() {
    try {
        var cart = JSON.parse(localStorage.getItem('cart')) || [];
        console.log('Cart loaded:', cart);
        renderCart(cart);
    } catch (e) {
        console.error('Error loading cart:', e);
        renderCart([]);
    }
}

// Format currency - Taka
function formatCurrency(amount) {
    return '৳' + parseFloat(amount || 0).toFixed(2);
}

// Get total items
function getTotalItems(cart) {
    var total = 0;
    for (var i = 0; i < cart.length; i++) {
        total = total + (parseInt(cart[i].quantity) || 0);
    }
    return total;
}

// Get subtotal (original price without any discount)
function getSubtotal(cart) {
    var total = 0;
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var originalPrice = parseFloat(item.original_price) || parseFloat(item.price) || 0;
        var quantity = parseInt(item.quantity) || 0;
        total = total + (originalPrice * quantity);
    }
    return total;
}

// Get discounted subtotal (after product discounts)
function getDiscountedSubtotal(cart) {
    var total = 0;
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var price = parseFloat(item.price) || 0;
        var quantity = parseInt(item.quantity) || 0;
        total = total + (price * quantity);
    }
    return total;
}

// Get total savings from product discounts
function getTotalSavings(cart) {
    var total = 0;
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var originalPrice = parseFloat(item.original_price) || parseFloat(item.price) || 0;
        var currentPrice = parseFloat(item.price) || 0;
        var quantity = parseInt(item.quantity) || 0;
        var discount = (originalPrice - currentPrice) * quantity;
        if (discount > 0) {
            total = total + discount;
        }
    }
    return total;
}

// Get discount percentage for an item
function getDiscountPercentage(item) {
    var originalPrice = parseFloat(item.original_price) || parseFloat(item.price) || 0;
    var currentPrice = parseFloat(item.price) || 0;
    if (originalPrice > currentPrice && originalPrice > 0) {
        return Math.round(((originalPrice - currentPrice) / originalPrice) * 100);
    }
    return 0;
}

// Get discount amount in Taka for an item
function getDiscountAmount(item) {
    var originalPrice = parseFloat(item.original_price) || parseFloat(item.price) || 0;
    var currentPrice = parseFloat(item.price) || 0;
    if (originalPrice > currentPrice && originalPrice > 0) {
        return (originalPrice - currentPrice);
    }
    return 0;
}

// Render cart items
function renderCart(cart) {
    var container = document.getElementById('cartItemsContainer');
    var cartCount = document.getElementById('cartCount');
    
    if (!container) {
        console.error('Cart container not found!');
        return;
    }
    
    // Calculate totals
    var subtotal = getSubtotal(cart);
    var discountedSubtotal = getDiscountedSubtotal(cart);
    var savings = getTotalSavings(cart);
    var total = discountedSubtotal;

    console.log('Cart Calculations:', {
        subtotal: subtotal,
        discountedSubtotal: discountedSubtotal,
        savings: savings,
        total: total,
        cartItems: cart
    });

    // Update count
    if (cartCount) {
        cartCount.textContent = getTotalItems(cart);
    }

    if (cart.length === 0) {
        container.innerHTML = 
            '<div class="empty-cart">' +
                '<div class="empty-cart-icon">' +
                    '<i class="fas fa-shopping-bag"></i>' +
                '</div>' +
                '<h2>Your Cart is Empty</h2>' +
                '<p>Looks like you haven\'t added any items to your cart yet.</p>' +
                '<p class="empty-suggestion">Browse our products and find something you love!</p>' +
                '<a href="/shop/" class="btn-shop-now">' +
                    '<i class="fas fa-store"></i> Start Shopping' +
                '</a>' +
                '<div class="empty-features">' +
                    '<div class="empty-feature">' +
                        '<i class="fas fa-truck"></i>' +
                        '<span>Free Delivery</span>' +
                    '</div>' +
                    '<div class="empty-feature">' +
                        '<i class="fas fa-undo-alt"></i>' +
                        '<span>Easy Returns</span>' +
                    '</div>' +
                    '<div class="empty-feature">' +
                        '<i class="fas fa-headset"></i>' +
                        '<span>24/7 Support</span>' +
                    '</div>' +
                '</div>' +
            '</div>';
        updateSummary(0, 0, 0);
        return;
    }

    var html = '';
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var originalPrice = parseFloat(item.original_price) || parseFloat(item.price) || 0;
        var currentPrice = parseFloat(item.price) || 0;
        var discountPercent = getDiscountPercentage(item);
        var discountAmount = getDiscountAmount(item);
        var hasDiscount = discountPercent > 0 || discountAmount > 0;
        var quantity = parseInt(item.quantity) || 1;
        var itemTotal = currentPrice * quantity;
        var originalTotal = originalPrice * quantity;

        html += '<div class="cart-item" data-index="' + i + '">';
        html += '<div class="cart-item-product">';
        html += '<div class="cart-item-image">';
        if (item.image) {
            html += '<img src="' + item.image + '" alt="' + item.name + '" />';
        } else {
            html += '<span style="font-size: 30px; display: flex; align-items: center; justify-content: center; height: 100%;">💧</span>';
        }
        html += '</div>';
        html += '<div class="cart-item-details">';
        html += '<h4>' + item.name + '</h4>';
        if (item.description) {
            html += '<p>' + item.description + '</p>';
        }
        if (item.special_offer) {
            html += '<p class="item-special-offer">🎉 ' + item.special_offer + '</p>';
        }
        if (hasDiscount) {
            html += '<span class="item-discount-badge">' + discountPercent + '% OFF (Save ৳' + discountAmount.toFixed(2) + ')</span>';
        }
        html += '</div></div>';

        html += '<div class="cart-item-price">';
        html += '<span class="current-price">' + formatCurrency(currentPrice) + '</span>';
        if (hasDiscount) {
            html += '<span class="original-price">' + formatCurrency(originalPrice) + '</span>';
        }
        html += '</div>';

        html += '<div class="cart-item-quantity">';
        html += '<div class="quantity-control">';
        html += '<button class="qty-minus" data-index="' + i + '">−</button>';
        html += '<input type="number" class="qty-input" value="' + quantity + '" min="1" data-index="' + i + '" />';
        html += '<button class="qty-plus" data-index="' + i + '">+</button>';
        html += '</div></div>';

        html += '<div class="cart-item-total">';
        html += '<span class="item-total">' + formatCurrency(itemTotal) + '</span>';
        if (hasDiscount) {
            html += '<span class="item-original-total">' + formatCurrency(originalTotal) + '</span>';
        }
        html += '</div>';

        html += '<div class="cart-item-remove">';
        html += '<button class="remove-item" data-index="' + i + '">';
        html += '<i class="fas fa-trash-alt"></i>';
        html += '</button></div></div>';
    }

    container.innerHTML = html;
    updateSummary(subtotal, savings, discountedSubtotal);

    // Attach events after rendering
    setTimeout(function() {
        attachCartEvents();
    }, 100);
}

// Update summary
function updateSummary(subtotal, savings, total) {
    var subtotalEl = document.getElementById('summarySubtotal');
    var savingsEl = document.getElementById('summarySavings');
    var savingsRow = document.getElementById('savingsRow');
    var totalEl = document.getElementById('summaryTotal');
    
    if (subtotalEl) subtotalEl.textContent = formatCurrency(subtotal);
    if (totalEl) totalEl.textContent = formatCurrency(total);

    if (savingsRow && savingsEl) {
        if (savings > 0) {
            savingsRow.style.display = 'flex';
            savingsEl.textContent = '-' + formatCurrency(savings);
        } else {
            savingsRow.style.display = 'none';
        }
    }
}

// Attach cart events
function attachCartEvents() {
    console.log('Attaching cart events...');
    
    // Quantity minus
    var minusBtns = document.querySelectorAll('.qty-minus');
    for (var i = 0; i < minusBtns.length; i++) {
        var btn = minusBtns[i];
        btn.removeEventListener('click', handleMinus);
        btn.addEventListener('click', handleMinus);
    }

    // Quantity plus
    var plusBtns = document.querySelectorAll('.qty-plus');
    for (var i = 0; i < plusBtns.length; i++) {
        var btn = plusBtns[i];
        btn.removeEventListener('click', handlePlus);
        btn.addEventListener('click', handlePlus);
    }

    // Quantity input change
    var inputs = document.querySelectorAll('.qty-input');
    for (var i = 0; i < inputs.length; i++) {
        var input = inputs[i];
        input.removeEventListener('change', handleInputChange);
        input.addEventListener('change', handleInputChange);
    }

    // Remove item
    var removeBtns = document.querySelectorAll('.remove-item');
    for (var i = 0; i < removeBtns.length; i++) {
        var btn = removeBtns[i];
        btn.removeEventListener('click', handleRemove);
        btn.addEventListener('click', handleRemove);
    }
}

// Event handlers
function handleMinus(e) {
    e.preventDefault();
    var index = parseInt(this.dataset.index);
    console.log('Minus clicked for index:', index);
    updateQuantity(index, -1);
}

function handlePlus(e) {
    e.preventDefault();
    var index = parseInt(this.dataset.index);
    console.log('Plus clicked for index:', index);
    updateQuantity(index, 1);
}

function handleInputChange(e) {
    var index = parseInt(this.dataset.index);
    var value = parseInt(this.value);
    if (isNaN(value) || value < 1) {
        this.value = 1;
        value = 1;
    }
    console.log('Input changed for index:', index, 'value:', value);
    updateQuantity(index, 0, value);
}

function handleRemove(e) {
    e.preventDefault();
    var index = parseInt(this.dataset.index);
    console.log('Remove clicked for index:', index);
    if (confirm('Are you sure you want to remove this item?')) {
        removeFromCart(index);
    }
}

// Update quantity
function updateQuantity(index, change, newValue) {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    
    if (!cart[index]) {
        console.log('Item not found at index:', index);
        return;
    }

    var quantity = parseInt(cart[index].quantity) || 1;
    
    if (newValue !== undefined) {
        quantity = parseInt(newValue);
    } else {
        quantity = quantity + parseInt(change);
    }

    if (isNaN(quantity) || quantity < 1) {
        quantity = 1;
    }

    cart[index].quantity = quantity;
    localStorage.setItem('cart', JSON.stringify(cart));
    console.log('Updated cart:', cart);
    
    // Re-render cart
    renderCart(cart);
    
    // Update floating cart badge if exists
    if (typeof updateFloatingCartBadge === 'function') {
        updateFloatingCartBadge();
    }
}

// Remove from cart
function removeFromCart(index) {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    cart.splice(index, 1);
    localStorage.setItem('cart', JSON.stringify(cart));
    console.log('Removed item, new cart:', cart);
    
    // Re-render cart
    renderCart(cart);
    
    // Update floating cart badge if exists
    if (typeof updateFloatingCartBadge === 'function') {
        updateFloatingCartBadge();
    }
}

// Apply coupon
var applyCouponBtn = document.getElementById('applyCouponBtn');
if (applyCouponBtn) {
    applyCouponBtn.addEventListener('click', function() {
        var couponInput = document.getElementById('couponInput');
        var code = couponInput ? couponInput.value.toUpperCase() : '';
        var cart = JSON.parse(localStorage.getItem('cart')) || [];
        var discountedSubtotal = getDiscountedSubtotal(cart);
        var savings = getTotalSavings(cart);
        
        var discount = 0;
        var discountRow = document.getElementById('discountRow');
        var discountEl = document.getElementById('summaryDiscount');
        var totalEl = document.getElementById('summaryTotal');
        
        if (code === 'SAVE10') {
            discount = discountedSubtotal * 0.10;
            if (discountRow) discountRow.style.display = 'flex';
            if (discountEl) discountEl.textContent = '-' + formatCurrency(discount);
            alert('🎉 Coupon applied! You saved 10%');
        } else if (code === 'SAVE20') {
            discount = discountedSubtotal * 0.20;
            if (discountRow) discountRow.style.display = 'flex';
            if (discountEl) discountEl.textContent = '-' + formatCurrency(discount);
            alert('🎉 Coupon applied! You saved 20%');
        } else {
            alert('❌ Invalid coupon code. Try SAVE10 or SAVE20');
            return;
        }
        
        // Update total with discount
        var total = discountedSubtotal - discount;
        if (totalEl) totalEl.textContent = formatCurrency(total);
    });
}

// Checkout button
var checkoutBtn = document.getElementById('checkoutBtn');
if (checkoutBtn) {
    checkoutBtn.addEventListener('click', function() {
        var cart = JSON.parse(localStorage.getItem('cart')) || [];
        if (cart.length === 0) {
            alert('Your cart is empty!');
            return;
        }
        window.location.href = '/checkout/';
    });
}

// Also attach events when page loads completely
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, loading cart...');
    loadCart();
    
    // Update floating cart badge if exists
    if (typeof updateFloatingCartBadge === 'function') {
        updateFloatingCartBadge();
    }
});

// Listen for cart updates from other pages
document.addEventListener('cart:updated', function() {
    console.log('Cart updated event received, reloading...');
    loadCart();
});

// Make functions global
window.loadCart = loadCart;
window.renderCart = renderCart;
window.updateQuantity = updateQuantity;
window.removeFromCart = removeFromCart;
window.formatCurrency = formatCurrency;
window.getTotalItems = getTotalItems;
window.getSubtotal = getSubtotal;
window.getDiscountedSubtotal = getDiscountedSubtotal;
window.getTotalSavings = getTotalSavings;
window.getDiscountPercentage = getDiscountPercentage;
window.getDiscountAmount = getDiscountAmount;
window.attachCartEvents = attachCartEvents;