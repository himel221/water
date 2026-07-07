from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
import re

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Filters', 'Filters'),
        ('Sensors', 'Sensors'),
        ('Purifiers', 'Purifiers'),
        ('Testing Kits', 'Testing Kits'),
        ('Softening Systems', 'Softening Systems'),
        ('Meters', 'Meters'),
        ('Pitchers', 'Pitchers'),
        ('Monitors', 'Monitors'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Filters')
    benefits = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, null=True)
    reviews = models.IntegerField(default=0, blank=True, null=True)
    stock_quantity = models.IntegerField(default=0, help_text="Number of items in stock")
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.IntegerField(blank=True, null=True)
    special_offer = models.CharField(max_length=200, blank=True, null=True)
    is_on_sale = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_benefits_list(self):
        if not self.benefits:
            return []
        return [b.strip() for b in self.benefits.split(',') if b.strip()]
    
    def is_in_stock(self):
        return self.stock_quantity > 0

    def get_effective_price(self):
        """Return the effective user-visible price after applying discounts."""
        if not self.is_on_sale:
            return self.price

        if self.discount_price is not None:
            return self.discount_price

        discount_percentage = self.discount_percentage or 0
        if discount_percentage > 0:
            return self.price - (self.price * Decimal(discount_percentage) / Decimal('100'))

        return self.price

    def get_discount_amount(self):
        """Return the absolute discount amount for the product."""
        if not self.is_on_sale:
            return Decimal('0.00')
        return self.price - self.get_effective_price()

    @property
    def is_eligible_for_offer(self):
        """Check if product is eligible for special offer"""
        return bool(self.special_offer and self.is_on_sale and self.is_active)


class DistrictDeliveryCharge(models.Model):
    DISTRICT_CHOICES = [
        ('dhaka', 'Dhaka'),
        ('faridpur', 'Faridpur'),
        ('gazipur', 'Gazipur'),
        ('gopalganj', 'Gopalganj'),
        ('jamalpur', 'Jamalpur'),
        ('kishoreganj', 'Kishoreganj'),
        ('madaripur', 'Madaripur'),
        ('manikganj', 'Manikganj'),
        ('munshiganj', 'Munshiganj'),
        ('mymensingh', 'Mymensingh'),
        ('narayanganj', 'Narayanganj'),
        ('narsingdi', 'Narsingdi'),
        ('netrokona', 'Netrokona'),
        ('rajbari', 'Rajbari'),
        ('shariatpur', 'Shariatpur'),
        ('sherpur', 'Sherpur'),
        ('tangail', 'Tangail'),
        ('bogra', 'Bogra'),
        ('joypurhat', 'Joypurhat'),
        ('naogaon', 'Naogaon'),
        ('natore', 'Natore'),
        ('nawabganj', 'Nawabganj'),
        ('pabna', 'Pabna'),
        ('rajshahi', 'Rajshahi'),
        ('sirajganj', 'Sirajganj'),
        ('dinajpur', 'Dinajpur'),
        ('gaibandha', 'Gaibandha'),
        ('kurigram', 'Kurigram'),
        ('lalmonirhat', 'Lalmonirhat'),
        ('nilphamari', 'Nilphamari'),
        ('panchagarh', 'Panchagarh'),
        ('rangpur', 'Rangpur'),
        ('thakurgaon', 'Thakurgaon'),
        ('bandarban', 'Bandarban'),
        ('brahmanbaria', 'Brahmanbaria'),
        ('chandpur', 'Chandpur'),
        ('chittagong', 'Chittagong'),
        ('comilla', 'Comilla'),
        ('cox_bazar', "Cox's Bazar"),
        ('feni', 'Feni'),
        ('khagrachhari', 'Khagrachhari'),
        ('lakshmipur', 'Lakshmipur'),
        ('noakhali', 'Noakhali'),
        ('rangamati', 'Rangamati'),
        ('barguna', 'Barguna'),
        ('barisal', 'Barisal'),
        ('bhola', 'Bhola'),
        ('jhalokathi', 'Jhalokathi'),
        ('patuakhali', 'Patuakhali'),
        ('pirojpur', 'Pirojpur'),
        ('habiganj', 'Habiganj'),
        ('maulvibazar', 'Maulvibazar'),
        ('sunamganj', 'Sunamganj'),
        ('sylhet', 'Sylhet'),
        ('jashore', 'Jashore'),
        ('jhinaidah', 'Jhinaidah'),
        ('khulna', 'Khulna'),
        ('kushtia', 'Kushtia'),
        ('magura', 'Magura'),
        ('meherpur', 'Meherpur'),
        ('narail', 'Narail'),
        ('satkhira', 'Satkhira'),
    ]
    
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, unique=True)
    district_name = models.CharField(max_length=100)
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    delivery_time = models.CharField(max_length=100, default='2-3 days')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['district_name']
        verbose_name = 'District Delivery Charge'
        verbose_name_plural = 'District Delivery Charges'
    
    def __str__(self):
        return f"{self.district_name} - TK {self.charge}"


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=1)
    discount_percentage = models.IntegerField(default=0)
    special_offer = models.CharField(max_length=200, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_id = models.CharField(max_length=50, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    customer_address = models.TextField()
    customer_district = models.CharField(max_length=100, blank=True, null=True)
    
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_zone = models.CharField(max_length=100, blank=True, null=True)
    
    # ✅ Order Summary Fields
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # ✅ Total Discount যোগ করা হয়েছে
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            import time
            import random
            timestamp = str(int(time.time() * 1000))[-8:]
            random_digits = str(random.randint(1000, 9999))
            self.order_id = f"ORD-{timestamp}-{random_digits}"
        super().save(*args, **kwargs)
    
    def get_total_items(self):
        return sum(item.quantity for item in self.order_items.all())
    
    def calculate_total_discount(self):
        """Calculate total discount for the order"""
        total_discount = 0
        for item in self.order_items.all():
            if item.original_price and item.original_price > item.product_price:
                total_discount += (float(item.original_price) - float(item.product_price)) * item.quantity
        return total_discount
    
    def parse_offer_requirements(self, offer_text):
        """Parse offer text and return requirements dynamically"""
        offer_text = offer_text.lower()
        requirements = {
            'min_quantity': 1,
            'max_quantity': None,
            'min_amount': None,
            'offer_type': 'discount',
            'description': offer_text
        }
        
        # Buy X Get Y Free
        buy_match = re.search(r'buy\s*(\d+)\s*get\s*(\d+)\s*free', offer_text)
        if buy_match:
            requirements['min_quantity'] = int(buy_match.group(1))
            requirements['offer_type'] = 'buy_x_get_y_free'
            requirements['free_items'] = int(buy_match.group(2))
            return requirements
        
        # Buy X Get Y Off
        buy_get_match = re.search(r'buy\s*(\d+)\s*get\s*(\d+)\s*(?:free|off)', offer_text)
        if buy_get_match:
            requirements['min_quantity'] = int(buy_get_match.group(1))
            requirements['offer_type'] = 'buy_x_get_y_free'
            requirements['free_items'] = int(buy_get_match.group(2))
            return requirements
        
        # X% OFF on Y+ items
        percent_match = re.search(r'(\d+)%\s*off\s*on\s*(\d+)\s*\+', offer_text)
        if percent_match:
            requirements['min_quantity'] = int(percent_match.group(2))
            requirements['discount_percent'] = int(percent_match.group(1))
            requirements['offer_type'] = 'percent_off'
            return requirements
        
        # X% OFF
        percent_only = re.search(r'(\d+)%\s*off', offer_text)
        if percent_only:
            requirements['min_quantity'] = 1
            requirements['discount_percent'] = int(percent_only.group(1))
            requirements['offer_type'] = 'percent_off'
            return requirements
        
        # $X OFF on $Y+
        amount_match = re.search(r'\$?(\d+)\s*off\s*on\s*\$?(\d+)\s*\+', offer_text)
        if amount_match:
            requirements['min_amount'] = float(amount_match.group(2))
            requirements['discount_amount'] = float(amount_match.group(1))
            requirements['offer_type'] = 'amount_off'
            return requirements
        
        # Free Shipping
        if 'free shipping' in offer_text or 'free delivery' in offer_text:
            requirements['offer_type'] = 'free_shipping'
            return requirements
        
        # Combo Offers
        if 'combo' in offer_text:
            requirements['offer_type'] = 'combo'
            combo_match = re.search(r'(\d+)\s*for\s*\$?(\d+)', offer_text)
            if combo_match:
                requirements['min_quantity'] = int(combo_match.group(1))
                requirements['combo_price'] = float(combo_match.group(2))
            return requirements
        
        # Flat Discount
        if 'flat' in offer_text:
            flat_match = re.search(r'flat\s*(\d+)%\s*off', offer_text)
            if flat_match:
                requirements['discount_percent'] = int(flat_match.group(1))
                requirements['offer_type'] = 'flat_discount'
            return requirements
        
        return requirements
    
    def is_eligible_for_offer(self):
        """Check if order meets special offer requirements"""
        for item in self.order_items.all():
            if item.special_offer:
                requirements = self.parse_offer_requirements(item.special_offer)
                
                if requirements['offer_type'] == 'free_shipping':
                    return True
                elif requirements['offer_type'] == 'buy_x_get_y_free':
                    if item.quantity >= requirements.get('min_quantity', 2):
                        return True
                elif requirements['offer_type'] == 'percent_off':
                    if item.quantity >= requirements.get('min_quantity', 1):
                        return True
                elif requirements['offer_type'] == 'amount_off':
                    total_price = item.product_price * item.quantity
                    if total_price >= requirements.get('min_amount', 0):
                        return True
                elif requirements['offer_type'] == 'combo':
                    if item.quantity >= requirements.get('min_quantity', 1):
                        return True
                else:
                    if item.quantity > 1:
                        return True
        return False
    
    def get_offer_status(self):
        """Get detailed offer status with eligibility check"""
        offers = []
        for item in self.order_items.all():
            if item.special_offer:
                parsed = self.parse_offer_requirements(item.special_offer)
                is_eligible = False
                
                if parsed['offer_type'] == 'free_shipping':
                    is_eligible = True
                elif parsed['offer_type'] == 'buy_x_get_y_free':
                    is_eligible = item.quantity >= parsed.get('min_quantity', 2)
                elif parsed['offer_type'] == 'percent_off':
                    is_eligible = item.quantity >= parsed.get('min_quantity', 1)
                elif parsed['offer_type'] == 'amount_off':
                    total_price = item.product_price * item.quantity
                    is_eligible = total_price >= parsed.get('min_amount', 0)
                elif parsed['offer_type'] == 'combo':
                    is_eligible = item.quantity >= parsed.get('min_quantity', 1)
                elif parsed['offer_type'] == 'flat_discount':
                    is_eligible = True
                else:
                    is_eligible = item.quantity > 1
                
                offers.append({
                    'product': item.product_name,
                    'offer_text': item.special_offer,
                    'is_eligible': is_eligible,
                    'quantity': item.quantity,
                    'requirements': parsed
                })
        
        return offers
    
    def get_offer_requirements(self):
        """Get offer requirements dynamically"""
        requirements = []
        for item in self.order_items.all():
            if item.special_offer:
                parsed = self.parse_offer_requirements(item.special_offer)
                offer_type = parsed.get('offer_type', 'general')
                is_eligible = False
                
                if offer_type == 'free_shipping':
                    is_eligible = True
                    requirements.append({
                        'product': item.product_name,
                        'offer': item.special_offer,
                        'required': 'Any quantity',
                        'current': f'{item.quantity} items',
                        'eligible': True,
                        'details': '✅ Free shipping applied'
                    })
                elif offer_type == 'buy_x_get_y_free':
                    min_qty = parsed.get('min_quantity', 2)
                    free_items = parsed.get('free_items', 1)
                    is_eligible = item.quantity >= min_qty
                    requirements.append({
                        'product': item.product_name,
                        'offer': item.special_offer,
                        'required': f'{min_qty}+ items (Get {free_items} free)',
                        'current': f'{item.quantity} items',
                        'eligible': is_eligible,
                        'details': f'{"✅" if is_eligible else "❌"} Need {min_qty - item.quantity} more item(s) to qualify' if not is_eligible else '✅ Requirements met!'
                    })
                elif offer_type == 'percent_off':
                    min_qty = parsed.get('min_quantity', 1)
                    percent = parsed.get('discount_percent', 0)
                    is_eligible = item.quantity >= min_qty
                    requirements.append({
                        'product': item.product_name,
                        'offer': item.special_offer,
                        'required': f'{min_qty}+ items ({percent}% off)',
                        'current': f'{item.quantity} items',
                        'eligible': is_eligible,
                        'details': f'{"✅" if is_eligible else "❌"} Need {min_qty - item.quantity} more item(s) to get {percent}% off' if not is_eligible else '✅ Requirements met!'
                    })
                elif offer_type == 'amount_off':
                    min_amount = parsed.get('min_amount', 0)
                    discount_amount = parsed.get('discount_amount', 0)
                    total_price = item.product_price * item.quantity
                    is_eligible = total_price >= min_amount
                    requirements.append({
                        'product': item.product_name,
                        'offer': item.special_offer,
                        'required': f'${min_amount}+ order (Save ${discount_amount})',
                        'current': f'${total_price:.2f}',
                        'eligible': is_eligible,
                        'details': f'{"✅" if is_eligible else "❌"} Need ${min_amount - total_price:.2f} more to qualify' if not is_eligible else '✅ Requirements met!'
                    })
                elif offer_type == 'combo':
                    min_qty = parsed.get('min_quantity', 1)
                    combo_price = parsed.get('combo_price', 0)
                    is_eligible = item.quantity >= min_qty
                    requirements.append({
                        'product': item.product_name,
                        'offer': item.special_offer,
                        'required': f'{min_qty} items (Combo: ${combo_price})',
                        'current': f'{item.quantity} items',
                        'eligible': is_eligible,
                        'details': f'{"✅" if is_eligible else "❌"} Need {min_qty - item.quantity} more item(s) for combo' if not is_eligible else '✅ Requirements met!'
                    })
                else:
                    is_eligible = item.quantity > 1
                    requirements.append({
                        'product': item.product_name,
                        'offer': item.special_offer,
                        'required': '2+ items',
                        'current': f'{item.quantity} items',
                        'eligible': is_eligible,
                        'details': f'{"✅" if is_eligible else "❌"} Need {2 - item.quantity} more item(s) to qualify' if not is_eligible else '✅ Requirements met!'
                    })
        
        return requirements
    @property
    def special_offers_list(self):
        """Get list of special offers applied to this order"""
        offers = []
        for item in self.order_items.all():
            if item.special_offer:
                offers.append(item.special_offer)
        return list(set(offers))  # Remove duplicates