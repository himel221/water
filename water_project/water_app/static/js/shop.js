// ===== Filter Products =====
document.querySelectorAll('.filter-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.filter-btn').forEach(function(b) {
            b.classList.remove('active');
        });
        this.classList.add('active');
        
        var category = this.dataset.category;
        var products = document.querySelectorAll('.product-card');
        
        products.forEach(function(product) {
            if (category === 'all' || product.dataset.category === category) {
                product.style.display = 'block';
            } else {
                product.style.display = 'none';
            }
        });
    });
});

// ===== Search Products =====
var searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function() {
        var searchTerm = this.value.toLowerCase();
        var products = document.querySelectorAll('.product-card');
        
        products.forEach(function(product) {
            var nameEl = product.querySelector('.product-name');
            var descEl = product.querySelector('.product-desc');
            var name = nameEl ? nameEl.textContent.toLowerCase() : '';
            var desc = descEl ? descEl.textContent.toLowerCase() : '';
            
            if (name.includes(searchTerm) || desc.includes(searchTerm)) {
                product.style.display = 'block';
            } else {
                product.style.display = 'none';
            }
        });
    });
}

// ===== Sort Products =====
var sortSelect = document.getElementById('sortSelect');
if (sortSelect) {
    sortSelect.addEventListener('change', function() {
        var sortBy = this.value;
        var grid = document.getElementById('productGrid');
        var products = Array.from(document.querySelectorAll('.product-card'));
        
        products.sort(function(a, b) {
            var priceA = parseFloat(a.dataset.price);
            var priceB = parseFloat(b.dataset.price);
            var ratingA = parseFloat(a.dataset.rating);
            var ratingB = parseFloat(b.dataset.rating);
            
            switch(sortBy) {
                case 'price-low':
                    return priceA - priceB;
                case 'price-high':
                    return priceB - priceA;
                case 'rating':
                    return ratingB - ratingA;
                default:
                    return 0;
            }
        });
        
        products.forEach(function(product) {
            grid.appendChild(product);
        });
    });
}

// ===== Quantity Selector =====
document.querySelectorAll('.quantity-selector').forEach(function(selector) {
    var minus = selector.querySelector('.minus');
    var plus = selector.querySelector('.plus');
    var input = selector.querySelector('.qty-input');
    
    if (minus) {
        minus.addEventListener('click', function() {
            var val = parseInt(input.value);
            if (val > 1) {
                input.value = val - 1;
            }
        });
    }
    
    if (plus) {
        plus.addEventListener('click', function() {
            var val = parseInt(input.value);
            if (val < 10) {
                input.value = val + 1;
            }
        });
    }
});

// ===== Add to Cart =====
document.querySelectorAll('.btn-add-cart:not(.disabled)').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var productCard = this.closest('.product-card');
        var nameEl = productCard.querySelector('.product-name');
        var priceEl = productCard.querySelector('.product-price');
        var qtyInput = productCard.querySelector('.qty-input');
        
        var name = nameEl ? nameEl.textContent : 'Product';
        var price = priceEl ? priceEl.textContent.replace(/[^0-9.]/g, '') : '0.00';
        var qty = qtyInput ? qtyInput.value : 1;
        
        // Show cart sidebar
        var sidebar = document.getElementById('cartSidebar');
        if (sidebar) {
            sidebar.classList.add('open');
        }
        
        // Add to cart logic
        console.log('Added: ' + name + ' - ' + price + ' x ' + qty);
        
        // Show notification
        var notification = document.getElementById('cartNotification');
        var messageEl = document.getElementById('notificationMessage');
        if (notification && messageEl) {
            messageEl.textContent = name + ' added to cart!';
            notification.classList.add('show');
            setTimeout(function() {
                notification.classList.remove('show');
            }, 3000);
        }
    });
});

// ===== Cart Sidebar Toggle =====
var closeCartBtn = document.getElementById('closeCart');
if (closeCartBtn) {
    closeCartBtn.addEventListener('click', function() {
        var sidebar = document.getElementById('cartSidebar');
        if (sidebar) {
            sidebar.classList.remove('open');
        }
    });
}

// Clicks inside cart sidebar should not close it unintentionally
function getEventTarget(event) {
    if (event.target && event.target.nodeType === Node.TEXT_NODE) {
        return event.target.parentNode;
    }
    return event.target;
}

// ===== Wishlist Button =====
document.querySelectorAll('.wishlist').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var icon = this.querySelector('i');
        if (icon) {
            icon.classList.toggle('fas');
            icon.classList.toggle('far');
            this.style.color = icon.classList.contains('fas') ? '#e74c3c' : '#2c3e50';
        }
    });
});

// ===== Quick View =====
document.querySelectorAll('.quick-view').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var productCard = this.closest('.product-card');
        var nameEl = productCard ? productCard.querySelector('.product-name') : null;
        var name = nameEl ? nameEl.textContent : 'Product';
        alert('Quick view for: ' + name);
    });
});

// ===== Initialize Shop =====
function initializeShop(products) {
    console.log('Shop initialized with ' + products.length + ' products');
    // Additional initialization logic here
}

// Make function global
window.initializeShop = initializeShop;