from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
import re

# ============================================
# 1. USER MANAGER
# ============================================
# models.py - সরলীকৃত UserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        
        # 🔥 এটা যোগ করুন
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        return self.create_user(email, password, **extra_fields)
       

# ============================================
# 2. USER MODEL
# ============================================

class User(AbstractUser):
    """Custom User model for Superwater application"""
    
    # 🔥 username ফিল্ড - email দিয়ে পূরণ হবে
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,
        null=False
    )
    
    email = models.EmailField(
        unique=True,
        max_length=255,
        db_index=True
    )
    
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    
    USER_TYPE_CHOICES = [
        ('user', 'Regular User'),
        ('admin', 'Administrator'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='user'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        swappable = 'AUTH_USER_MODEL'
    
    def __str__(self):
        return f"{self.email}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def save(self, *args, **kwargs):
        # 🔥 username হিসেবে email সেট করুন
        if not self.username:
            self.username = self.email
        self.email = self.email.lower().strip()
        super().save(*args, **kwargs)


# ============================================
# 3. USER PROFILE MODEL
# ============================================

class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    preferred_delivery_time = models.CharField(max_length=50, blank=True)
    receive_newsletter = models.BooleanField(default=True)
    receive_promotions = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Profile for {self.user.full_name}"


# ============================================
# 4. USER VERIFICATION MODEL
# ============================================

class UserVerification(models.Model):
    VERIFICATION_TYPES = [
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('password_reset', 'Password Reset'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    token = models.CharField(max_length=100, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'verification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.verification_type}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


# ============================================
# 5. PRODUCT MODEL
# ============================================

# models.py
# models.py

from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator

# models.py

from decimal import Decimal
from django.db import models
from django.core.validators import RegexValidator

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
    
    # ✅ শর্ট ডেসক্রিপশন - এটা যোগ করুন
    short_description = models.CharField(
        max_length=300, 
        blank=True, 
        null=True,
        help_text="Brief description shown in product cards and dropdown menus (max 300 chars)"
    )
    
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Filters')
    benefits = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, null=True)
    reviews = models.IntegerField(default=0, blank=True, null=True)
    stock_quantity = models.IntegerField(default=0)
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
        return self.get_inventory_total() > 0

    def get_effective_price(self):
        if not self.is_on_sale:
            return self.price
        if self.discount_price is not None:
            return self.discount_price
        discount_percentage = self.discount_percentage or 0
        if discount_percentage > 0:
            return self.price - (self.price * Decimal(discount_percentage) / Decimal('100'))
        return self.price

    def get_discount_amount(self):
        if not self.is_on_sale:
            return Decimal('0.00')
        return self.price - self.get_effective_price()

    @property
    def is_eligible_for_offer(self):
        return bool(self.special_offer and self.is_on_sale and self.is_active)
    
    def get_stock_value(self):
        return self.price * self.stock_quantity
    
    # ============================================
    # 🔥 INVENTORY RELATED METHODS
    # ============================================
    
    def get_inventory_total(self):
        """Get total inventory from Inventory model"""
        try:
            from django.db import models
            # Try to get from Inventory model
            total = self.inventory_movements.aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            return total
        except:
            # If Inventory model doesn't exist, return stock_quantity
            return self.stock_quantity or 0
    
    @property
    def inventory_total(self):
        """Property to get total inventory"""
        return self.get_inventory_total()
    
    @property
    def inventory_value(self):
        """Total inventory value"""
        return float(self.price) * self.inventory_total
    
    def get_inventory_movements(self):
        """Get all inventory movements for this product"""
        try:
            return self.inventory_movements.all().order_by('-created_at')
        except:
            return []
    
    # ✅ শর্ট ডেসক্রিপশন পাওয়ার জন্য হেল্পার মেথড
    def get_short_description(self, max_length=150):
        """Return short description or truncated description"""
        if self.short_description:
            return self.short_description
        if self.description:
            # যদি শর্ট ডেসক্রিপশন না থাকে, তাহলে ডেসক্রিপশনের প্রথম 150 অক্ষর
            return self.description[:max_length] + ('...' if len(self.description) > max_length else '')
        return "No description available"

# models.py
class Inventory(models.Model):
    """Inventory management - Admin only"""
    MOVEMENT_TYPE_CHOICES = [
        ('add', 'Add Stock'),
        ('remove', 'Remove Stock'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
    ]
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL,  # 🔥 SET_NULL ব্যবহার করুন (CASCADE নয়)
        null=True,  # 🔥 null=True যোগ করুন
        blank=True,  # 🔥 blank=True যোগ করুন
        related_name='inventory_movements'
    )
    quantity = models.IntegerField(help_text="Positive = Add, Negative = Remove")
    previous_stock = models.IntegerField(default=0)
    new_stock = models.IntegerField(default=0)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES, default='add')
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inventory Movement'
        verbose_name_plural = 'Inventory Movements'
    
    def __str__(self):
        if self.product:
            return f"{self.product.name} - {self.movement_type}: {self.quantity}"
        return f"Deleted Product - {self.movement_type}: {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Auto calculate previous and new stock
        if self.product and not self.previous_stock:
            # Get current stock from inventory
            current_stock = self.product.get_inventory_total()
            self.previous_stock = current_stock
            self.new_stock = current_stock + self.quantity
        super().save(*args, **kwargs)
# ============================================
# 6. DISTRICT DELIVERY CHARGE MODEL
# ============================================

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


# ============================================
# 7. ORDER ITEM MODEL
# ============================================

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.IntegerField(default=1)
    discount_percentage = models.IntegerField(default=0)
    special_offer = models.CharField(max_length=200, blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


# ============================================
# 8. ORDER MODEL
# ============================================

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
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
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

    def is_eligible_for_offer(self):
        """Check if order is eligible for special offer"""

        if hasattr(self, 'total_amount') and self.total_amount:
            return self.total_amount > 1000
        return False
    
    def get_total_items(self):
        """Get total number of items in the order"""
        return self.order_items.count()
    
    def get_total_quantity(self):
        """Get total quantity of all items"""
        return sum(item.quantity for item in self.order_items.all())


# ============================================
# 9. INVENTORY MODEL
# ============================================

class Inventory(models.Model):
    INVENTORY_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('restock', 'Restock'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True,related_name='inventory_movements')
    quantity = models.IntegerField()
    previous_stock = models.IntegerField(default=0)
    new_stock = models.IntegerField(default=0)
    movement_type = models.CharField(max_length=20, choices=INVENTORY_TYPE_CHOICES, default='adjustment')
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_movements'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inventory Movement'
        verbose_name_plural = 'Inventory Movements'
    
    def __str__(self):
        return f"{self.product.name} - {self.movement_type}: {self.quantity}"


# ============================================
# 10. CUSTOMER MODEL
# ============================================

class Customer(models.Model):
    DIABETES_CHOICES = [
        ('none', 'None'),
        ('type1', 'Type 1 Diabetes'),
        ('type2', 'Type 2 Diabetes'),
        ('gestational', 'Gestational Diabetes'),
    ]
    
    BLOOD_PRESSURE_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('low', 'Low'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customer_profile'
    )
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    is_diabetic = models.BooleanField(default=False)
    diabetes_type = models.CharField(max_length=20, choices=DIABETES_CHOICES, default='none')
    has_high_blood_pressure = models.BooleanField(default=False)
    blood_pressure_status = models.CharField(max_length=20, choices=BLOOD_PRESSURE_CHOICES, default='normal')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.name} - {self.email}"
    
    def get_full_name(self):
        return self.name
    
    def get_health_summary(self):
        summary = []
        if self.is_diabetic:
            summary.append(f"Diabetic ({self.get_diabetes_type_display()})")
        if self.has_high_blood_pressure:
            summary.append(f"Blood Pressure: {self.get_blood_pressure_status_display()}")
        return summary if summary else ['No health issues recorded']