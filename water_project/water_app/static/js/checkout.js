// ===== Load Checkout Data =====
function loadCheckoutData() {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    renderOrderItems(cart);
    loadDeliveryCharges();
    updatePriceSummary(cart);
    updateItemCount(cart);
    loadUserData();
    updateSummaryInfo();
}

// ===== Load Delivery Charges from Server =====
function loadDeliveryCharges() {
    fetch('/api/delivery-charges/')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data && data.length > 0) {
                var districtSelect = document.getElementById('customerDistrict');
                while (districtSelect.options.length > 1) {
                    districtSelect.remove(1);
                }
                
                for (var i = 0; i < data.length; i++) {
                    var option = document.createElement('option');
                    option.value = data[i].district;
                    option.textContent = data[i].district_name;
                    option.dataset.charge = data[i].charge;
                    option.dataset.deliveryTime = data[i].delivery_time;
                    districtSelect.appendChild(option);
                }
                
                var userData = JSON.parse(localStorage.getItem('userData')) || {};
                if (userData.district) {
                    districtSelect.value = userData.district;
                    var event = new Event('change');
                    districtSelect.dispatchEvent(event);
                }
                
                updateSummaryInfo();
            }
        })
        .catch(function(error) {
            console.error('Error loading delivery charges:', error);
        });
}

// ===== Update Summary Info =====
function updateSummaryInfo() {
    var name = document.getElementById('customerName').value || '-';
    var phone = document.getElementById('customerPhone').value || '-';
    var address = document.getElementById('customerAddress').value || '-';
    var district = document.getElementById('customerDistrict');
    var districtName = district.options[district.selectedIndex] ? district.options[district.selectedIndex].text : '-';
    
    var paymentOption = document.querySelector('.payment-option.active');
    var paymentMethod = paymentOption ? paymentOption.dataset.payment || paymentOption.querySelector('.option-name').textContent : 'Cash on Delivery';
    
    document.getElementById('summaryName').textContent = name;
    document.getElementById('summaryPhone').textContent = phone;
    document.getElementById('summaryAddress').textContent = address;
    document.getElementById('summaryDistrict').textContent = districtName;
    document.getElementById('summaryPayment').textContent = paymentMethod;
}

// ===== Load User Data from LocalStorage =====
function loadUserData() {
    var userData = JSON.parse(localStorage.getItem('userData')) || {};
    if (userData.name) document.getElementById('customerName').value = userData.name;
    if (userData.phone) document.getElementById('customerPhone').value = userData.phone;
    if (userData.email) document.getElementById('customerEmail').value = userData.email;
    if (userData.address) document.getElementById('customerAddress').value = userData.address;
    if (userData.district) document.getElementById('customerDistrict').value = userData.district;
    updateSummaryInfo();
}

// ===== Save User Data =====
function saveUserData() {
    var userData = {
        name: document.getElementById('customerName').value,
        phone: document.getElementById('customerPhone').value,
        email: document.getElementById('customerEmail').value,
        address: document.getElementById('customerAddress').value,
        district: document.getElementById('customerDistrict').value
    };
    localStorage.setItem('userData', JSON.stringify(userData));
    updateSummaryInfo();
}

// ===== Render Order Items (শুধু Discounted Price দেখাবে) =====
function renderOrderItems(cart) {
    var container = document.getElementById('orderItems');
    if (!container) return;
    
    if (cart.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999; padding: 20px 0;">Your cart is empty</p>';
        return;
    }
    
    var html = '';
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var currentPrice = parseFloat(item.price) || 0;
        var originalPrice = parseFloat(item.original_price) || currentPrice;
        var hasDiscount = originalPrice > currentPrice;
        var quantity = parseInt(item.quantity) || 1;
        var itemTotal = currentPrice * quantity;
        
        html += '<div class="order-item">';
        html += '<div class="item-info">';
        html += '<div class="item-image">';
        if (item.image) {
            html += '<img src="' + item.image + '" alt="' + item.name + '" />';
        } else {
            html += '<span style="font-size: 20px;">💧</span>';
        }
        html += '</div>';
        html += '<div>';
        html += '<div class="item-name">' + item.name + '</div>';
        html += '<div class="item-quantity">' + quantity + 'x</div>';
        // ✅ Discount Badge দেখাবে (যদি Discount থাকে)
        if (hasDiscount) {
            var discountPercent = Math.round(((originalPrice - currentPrice) / originalPrice) * 100);
            html += '<span class="item-discount-badge">' + discountPercent + '% OFF</span>';
        }
        if (item.special_offer) {
            html += '<div class="item-special-offer">🎉 ' + item.special_offer + '</div>';
        }
        html += '</div>';
        html += '</div>';
        // ✅ শুধু Discounted Price দেখাবে (Original Price দেখাবে না)
        html += '<div class="item-price">৳' + itemTotal.toFixed(2) + '</div>';
        html += '</div>';
    }
    
    container.innerHTML = html;
}

// ===== Update Item Count =====
function updateItemCount(cart) {
    var count = 0;
    for (var i = 0; i < cart.length; i++) {
        count = count + (parseInt(cart[i].quantity) || 0);
    }
    var el = document.getElementById('itemCount');
    if (el) el.textContent = count;
}

// ===== Update Price Summary =====
function updatePriceSummary(cart) {
    var subtotal = 0;        // Original Price * Quantity
    var discountedTotal = 0; // Discounted Price * Quantity
    var totalSavings = 0;
    
    for (var i = 0; i < cart.length; i++) {
        var item = cart[i];
        var price = parseFloat(item.price) || 0;
        var originalPrice = parseFloat(item.original_price) || price;
        var qty = parseInt(item.quantity) || 0;
        
        subtotal = subtotal + (originalPrice * qty);
        discountedTotal = discountedTotal + (price * qty);
        var savings = (originalPrice - price) * qty;
        if (savings > 0) {
            totalSavings = totalSavings + savings;
        }
    }
    
    var district = document.getElementById('customerDistrict').value;
    var shipping = 0;
    
    var select = document.getElementById('customerDistrict');
    var selectedOption = select.options[select.selectedIndex];
    if (selectedOption && selectedOption.dataset && selectedOption.dataset.charge) {
        shipping = parseFloat(selectedOption.dataset.charge) || 0;
    }
    
    var total = discountedTotal + shipping;
    
    // ✅ Update UI - Subtotal দেখাবে Original Price, Subtotal2 দেখাবে Discounted Price
    document.getElementById('subtotal').textContent = '৳' + subtotal.toFixed(2);
    document.getElementById('subtotal2').textContent = '৳' + discountedTotal.toFixed(2);
    document.getElementById('shippingCost').textContent = shipping === 0 ? 'Free' : '৳' + shipping.toFixed(2);
    
    var deliveryChargeInput = document.getElementById('deliveryCharge');
    if (deliveryChargeInput) {
        deliveryChargeInput.value = shipping === 0 ? '৳0.00 (Free)' : '৳' + shipping.toFixed(2);
    }
    
    document.getElementById('totalAmount').textContent = '৳' + total.toFixed(2);
}

// ===== Fetch Delivery Charge from API =====
function fetchDeliveryCharge(district) {
    fetch('/api/delivery-charge/' + district + '/')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.status === 'success') {
                var select = document.getElementById('customerDistrict');
                var selectedOption = select.options[select.selectedIndex];
                if (selectedOption) {
                    selectedOption.dataset.charge = data.charge;
                    selectedOption.dataset.deliveryTime = data.delivery_time;
                }
                var cart = JSON.parse(localStorage.getItem('cart')) || [];
                updatePriceSummary(cart);
            }
        })
        .catch(function(error) {
            console.error('Error fetching delivery charge:', error);
        });
}

// ===== District Change Event =====
document.getElementById('customerDistrict')?.addEventListener('change', function() {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    var selectedOption = this.options[this.selectedIndex];
    
    if (selectedOption && selectedOption.dataset && selectedOption.dataset.charge) {
        updatePriceSummary(cart);
        saveUserData();
        updateSummaryInfo();
    } else if (this.value) {
        fetchDeliveryCharge(this.value);
        saveUserData();
        updateSummaryInfo();
    } else {
        updatePriceSummary(cart);
        saveUserData();
        updateSummaryInfo();
    }
});

// ===== Input Change Events =====
document.getElementById('customerName')?.addEventListener('input', function() {
    saveUserData();
    updateSummaryInfo();
});
document.getElementById('customerPhone')?.addEventListener('input', function() {
    saveUserData();
    updateSummaryInfo();
});
document.getElementById('customerEmail')?.addEventListener('input', function() {
    saveUserData();
    updateSummaryInfo();
});
document.getElementById('customerAddress')?.addEventListener('input', function() {
    saveUserData();
    updateSummaryInfo();
});

// ===== Payment Method Selection =====
document.querySelectorAll('.payment-option').forEach(function(option) {
    option.addEventListener('click', function() {
        document.querySelectorAll('.payment-option').forEach(function(opt) {
            opt.classList.remove('active');
            opt.querySelector('.option-left > i:first-child').className = 'far fa-circle';
        });
        this.classList.add('active');
        this.querySelector('.option-left > i:first-child').className = 'fas fa-check-circle';
        updateSummaryInfo();
    });
});

// ===== Place Order =====
document.getElementById('placeOrderBtn')?.addEventListener('click', function() {
    var cart = JSON.parse(localStorage.getItem('cart')) || [];
    if (cart.length === 0) {
        showNotification('Your cart is empty!', 'error');
        return;
    }
    
    // Validate form
    var name = document.getElementById('customerName').value.trim();
    var phone = document.getElementById('customerPhone').value.trim();
    var address = document.getElementById('customerAddress').value.trim();
    var district = document.getElementById('customerDistrict').value;
    
    if (!name) {
        showNotification('Please enter your full name', 'error');
        document.getElementById('customerName').focus();
        return;
    }
    if (!phone) {
        showNotification('Please enter your phone number', 'error');
        document.getElementById('customerPhone').focus();
        return;
    }
    if (!address) {
        showNotification('Please enter your delivery address', 'error');
        document.getElementById('customerAddress').focus();
        return;
    }
    if (!district) {
        showNotification('Please select your district', 'error');
        document.getElementById('customerDistrict').focus();
        return;
    }
    
    // Get selected payment
    var paymentOption = document.querySelector('.payment-option.active');
    var paymentMethod = paymentOption ? paymentOption.dataset.payment || paymentOption.querySelector('.option-name').textContent : 'Cash on Delivery';
    
    // ✅ Prepare items with original price and discount info
    var items = cart.map(function(item) {
        var originalPrice = parseFloat(item.original_price) || parseFloat(item.price) || 0;
        var currentPrice = parseFloat(item.price) || 0;
        var discountPercent = 0;
        if (originalPrice > currentPrice && originalPrice > 0) {
            discountPercent = Math.round(((originalPrice - currentPrice) / originalPrice) * 100);
        }
        
        return {
            id: item.id,
            name: item.name,
            price: currentPrice,
            original_price: originalPrice,
            quantity: parseInt(item.quantity) || 1,
            discount_percentage: discountPercent,
            special_offer: item.special_offer || '',
            description: item.description || '',
            category: item.category || '',
            benefits: item.benefits || []
        };
    });
    
    // ✅ Calculate totals
    var subtotal = 0;
    var totalSavings = 0;
    var discountedTotal = 0;
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        subtotal = subtotal + (item.original_price * item.quantity);
        discountedTotal = discountedTotal + (item.price * item.quantity);
        var savings = (item.original_price - item.price) * item.quantity;
        if (savings > 0) {
            totalSavings = totalSavings + savings;
        }
    }
    
    // Get shipping
    var select = document.getElementById('customerDistrict');
    var selectedOption = select.options[select.selectedIndex];
    var shipping = parseFloat(selectedOption.dataset.charge) || 0;
    
    var total = discountedTotal + shipping;
    
    // ✅ Order Data তৈরি করুন
    var orderData = {
        customer_name: name,
        customer_phone: phone,
        customer_email: document.getElementById('customerEmail').value.trim(),
        customer_address: address,
        customer_district: district,
        payment_method: paymentMethod,
        delivery_charge: shipping,
        items: items,
        subtotal: subtotal,
        total_savings: totalSavings,
        total_amount: total
    };
    
    console.log('📦 Order Data:', orderData);
    
    // Send order to server
    fetch('/api/create-order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(orderData)
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        if (data.status === 'success') {
            showSuccessModal(data.order_id);
            localStorage.removeItem('cart');
            localStorage.removeItem('userData');
        } else {
            showNotification('❌ Order failed: ' + data.message, 'error');
        }
    })
    .catch(function(error) {
        console.error('Error placing order:', error);
        showNotification('❌ Something went wrong. Please try again.', 'error');
    });
});

// ===== Show Success Modal =====
function showSuccessModal(orderId) {
    var modal = document.getElementById('successModal');
    document.getElementById('modalOrderId').textContent = 'Order ID: #' + orderId;
    modal.style.display = 'flex';
}

// ===== Modal Continue Button =====
document.getElementById('modalContinueBtn')?.addEventListener('click', function() {
    document.getElementById('successModal').style.display = 'none';
    window.location.href = '/';
});

// ===== Get CSRF Token =====
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== Notification =====
function showNotification(message, type) {
    var notification = document.createElement('div');
    notification.className = 'notification ' + (type || 'success');
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.4s ease';
        setTimeout(function() {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 400);
    }, 3000);
}