from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Product, DistrictDeliveryCharge, Order, OrderItem
import json
import io
from decimal import Decimal

# ReportLab Import
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab not installed. Please install: pip install reportlab")


# ===== Page Views =====

def home(request):
    """Home page view"""
    return render(request, 'home.html', {'active_page': 'home'})


def shop(request):
    """Shop page view - shows all active products"""
    products = Product.objects.filter(is_active=True)
    
    # Get unique categories for filter buttons
    categories = Product.objects.filter(is_active=True).values_list('category', flat=True).distinct()
    
    # Convert products to JSON for JavaScript
    products_json = []
    for product in products:
        # Convert Decimal to float
        original_price = float(product.price)
        discount_percent = product.discount_percentage or 0
        discount_price = product.discount_price
        
        # Calculate discount
        has_discount = product.is_on_sale and (discount_price or discount_percent > 0)
        
        # If discount price is not set but percentage is set
        if has_discount and not discount_price and discount_percent > 0:
            discount_price = original_price - (original_price * discount_percent / 100)
            product.discount_price = Decimal(str(discount_price))
            product.save()
        elif has_discount and discount_price:
            discount_price = float(discount_price)
        else:
            discount_price = original_price
            has_discount = False
        
        # Calculate savings
        savings = original_price - discount_price if has_discount else 0
        
        products_json.append({
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price': float(discount_price if has_discount else original_price),
            'discount_price': float(discount_price) if has_discount else None,
            'original_price': float(original_price),
            'discount_percentage': int(discount_percent) if has_discount else 0,
            'is_on_sale': bool(has_discount),
            'savings': float(savings),
            'special_offer': product.special_offer or '',
            'category': product.category,
            'benefits': product.get_benefits_list(),
            'rating': float(product.rating) if product.rating else 4.5,
            'reviews': int(product.reviews) if product.reviews else 0,
            'stock_quantity': int(product.stock_quantity) if product.stock_quantity else 0,
            'is_in_stock': bool(product.stock_quantity > 0) if product.stock_quantity else False,
            'image': product.image.url if product.image else '/static/images/default-product.jpg',
            'is_active': bool(product.is_active),
        })
    
    return render(request, 'shop.html', {
        'active_page': 'shop',
        'products': products,
        'categories': categories,
        'products_json': json.dumps(products_json)
    })


def science(request):
    """Science page view"""
    return render(request, 'science.html', {'active_page': 'science'})


def explore(request):
    """Explore page view"""
    return render(request, 'explore.html', {'active_page': 'explore'})


def cart(request):
    """Cart page view"""
    return render(request, 'cart.html', {'active_page': 'cart'})


# ===== API Views =====

def product_list(request):
    """API: Get all active products as JSON"""
    products = Product.objects.filter(is_active=True)
    data = []
    for product in products:
        original_price = float(product.price)
        discount_price = float(product.discount_price) if product.discount_price else None
        discount_percent = product.discount_percentage or 0
        has_discount = product.is_on_sale and (discount_price or discount_percent > 0)
        
        if has_discount and not discount_price and discount_percent > 0:
            discount_price = original_price - (original_price * discount_percent / 100)
        
        data.append({
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price': float(discount_price if has_discount else original_price),
            'original_price': float(original_price),
            'discount_price': float(discount_price) if has_discount else None,
            'discount_percentage': int(discount_percent) if has_discount else 0,
            'is_on_sale': bool(has_discount),
            'special_offer': product.special_offer or '',
            'category': product.category,
            'benefits': product.get_benefits_list(),
            'rating': float(product.rating) if product.rating else 4.5,
            'reviews': int(product.reviews) if product.reviews else 0,
            'image': product.image.url if product.image else '/static/images/default.jpg',
            'is_active': bool(product.is_active),
        })
    return JsonResponse(data, safe=False)


def checkout(request):
    """Checkout page view"""
    return render(request, 'checkout.html')


def district_delivery_charges(request):
    """API: Get all district delivery charges"""
    charges = DistrictDeliveryCharge.objects.filter(is_active=True)
    data = []
    for charge in charges:
        data.append({
            'id': charge.id,
            'district': charge.district,
            'district_name': charge.district_name,
            'charge': float(charge.charge),
            'delivery_time': charge.delivery_time,
        })
    return JsonResponse(data, safe=False)


def get_delivery_charge(request, district):
    """API: Get delivery charge for a specific district"""
    try:
        charge = DistrictDeliveryCharge.objects.filter(
            district__iexact=district, 
            is_active=True
        ).first()
        
        if charge:
            return JsonResponse({
                'status': 'success',
                'district': charge.district,
                'district_name': charge.district_name,
                'charge': float(charge.charge),
                'delivery_time': charge.delivery_time,
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Delivery charge not found for district: {district}',
                'charge': 0,
                'delivery_time': 'Not available'
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'charge': 0,
            'delivery_time': 'Not available'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    """API: Create a new order"""
    try:
        data = json.loads(request.body)
        
        district = data.get('customer_district', '')
        delivery_charge_obj = DistrictDeliveryCharge.objects.filter(
            district__iexact=district, 
            is_active=True
        ).first()
        delivery_charge = float(delivery_charge_obj.charge) if delivery_charge_obj else 0
        delivery_zone = delivery_charge_obj.district_name if delivery_charge_obj else 'Unknown District'
        
        # ✅ Items থেকে Total Calculate করুন
        items_data = data.get('items', [])
        subtotal = 0
        total_savings = 0
        
        for item in items_data:
            price = float(item.get('price', 0))
            original_price = float(item.get('original_price', price))
            quantity = int(item.get('quantity', 1))
            
            subtotal += original_price * quantity
            savings = (original_price - price) * quantity
            if savings > 0:
                total_savings += savings
        
        total_amount = subtotal - total_savings + delivery_charge
        
        # ✅ Debug Print
        print(f"📊 Order Calculation:")
        print(f"  Subtotal: {subtotal}")
        print(f"  Total Savings: {total_savings}")
        print(f"  Delivery Charge: {delivery_charge}")
        print(f"  Total Amount: {total_amount}")
        
        # ✅ Order Create করুন সঠিকভাবে
        order = Order.objects.create(
            customer_name=data.get('customer_name', 'Guest'),
            customer_email=data.get('customer_email', 'guest@email.com'),
            customer_phone=data.get('customer_phone', ''),
            customer_address=data.get('customer_address', ''),
            customer_district=district,
            delivery_charge=delivery_charge,
            delivery_zone=delivery_zone,
            subtotal=subtotal,
            total_savings=total_savings,
            total_amount=total_amount,
            payment_method=data.get('payment_method', 'Cash on Delivery'),
            transaction_id=data.get('transaction_id', ''),
            status='pending',
            payment_status='pending'
        )
        
        # ✅ Order Items Create করুন
        for item in items_data:
            price = float(item.get('price', 0))
            original_price = float(item.get('original_price', price))
            quantity = int(item.get('quantity', 1))
            
            OrderItem.objects.create(
                order=order,
                product_name=item.get('name', 'Unknown'),
                product_price=price,
                original_price=original_price,
                quantity=quantity,
                discount_percentage=int(item.get('discount_percentage', 0)),
                special_offer=item.get('special_offer', ''),
                total_price=price * quantity
            )
        
        return JsonResponse({
            'status': 'success',
            'order_id': order.order_id,
            'message': 'Order created successfully',
            'subtotal': subtotal,
            'total_savings': total_savings,
            'total_amount': total_amount
        })
        
    except Exception as e:
        print(f"❌ Order Creation Error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
def order_list(request):
    """API: Get all orders with items"""
    orders = Order.objects.all()
    data = []
    for order in orders:
        items_data = []
        for item in order.order_items.all():
            items_data.append({
                'product_name': item.product_name,
                'quantity': item.quantity,
                'product_price': float(item.product_price),
                'original_price': float(item.original_price),
                'discount_percentage': item.discount_percentage,
                'special_offer': item.special_offer,
                'total_price': float(item.total_price)
            })
        
        data.append({
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
            'customer_address': order.customer_address,
            'customer_district': order.customer_district,
            'delivery_zone': order.delivery_zone,
            'delivery_charge': float(order.delivery_charge),
            'items': items_data,
            'subtotal': float(order.subtotal),
            'total_savings': float(order.total_savings),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'payment_status': order.payment_status,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return JsonResponse(data, safe=False)


def download_invoice(request, order_id):
    """Download invoice as PDF"""
    if not REPORTLAB_AVAILABLE:
        return HttpResponse("⚠️ ReportLab not installed. Please install: pip install reportlab", status=500)
    
    order = get_object_or_404(Order, order_id=order_id)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#007bff'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10
    )
    
    normal_style = styles['Normal']
    
    story = []
    
    story.append(Paragraph("Aquanimity SuperWater - Invoice", title_style))
    story.append(Paragraph(f"Order ID: {order.order_id}", normal_style))
    story.append(Paragraph(f"Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Customer Details", heading_style))
    story.append(Paragraph(f"Name: {order.customer_name}", normal_style))
    story.append(Paragraph(f"Email: {order.customer_email}", normal_style))
    if order.customer_phone:
        story.append(Paragraph(f"Phone: {order.customer_phone}", normal_style))
    story.append(Paragraph(f"Address: {order.customer_address}", normal_style))
    if order.customer_district:
        story.append(Paragraph(f"District: {order.customer_district}", normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Order Items", heading_style))
    
    # Table Data from Order Items
    table_data = [
        ['#', 'Product', 'Qty', 'Unit Price', 'Original Price', 'Discount', 'Total']
    ]
    
    for idx, item in enumerate(order.order_items.all(), 1):
        discount_text = f"{item.discount_percentage}%" if item.discount_percentage > 0 else '-'
        if item.special_offer:
            discount_text += f" 🎉 {item.special_offer}"
        
        table_data.append([
            str(idx),
            item.product_name,
            str(item.quantity),
            f"৳ {float(item.product_price):.2f}",
            f"৳ {float(item.original_price):.2f}",
            discount_text,
            f"৳ {float(item.total_price):.2f}"
        ])
    
    table = Table(table_data, colWidths=[0.3*inch, 2.2*inch, 0.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
        ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Order Summary", heading_style))
    
    summary_data = [
        ['Subtotal', f"৳ {float(order.subtotal):.2f}"],
    ]
    if order.total_savings > 0:
        summary_data.append(['Total Savings', f"৳ {float(order.total_savings):.2f}"])
    if order.delivery_charge > 0:
        summary_data.append(['Delivery Charge', f"৳ {float(order.delivery_charge):.2f}"])
    summary_data.append(['Total Amount', f"৳ {float(order.total_amount):.2f}"])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4fd')),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Thank you for shopping with Aquanimity SuperWater!", footer_style))
    story.append(Paragraph("© 2026 Aquanimity SuperWater. All rights reserved.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.pdf"'
    return response

#----------------------------------------------ADMIN -----------------------------------------------------------#

def admin_dashboard(request):
    """Admin Dashboard View"""
    from .models import Order, Product, OrderItem, DistrictDeliveryCharge
    
    context = {
        'active_page': 'admin_dashboard',
        'total_orders': Order.objects.count(),
        'total_products': Product.objects.count(),
        'total_customers': Order.objects.values('customer_email').distinct().count(),
        'total_revenue': sum(float(o.total_amount) for o in Order.objects.all()),
        'recent_orders': Order.objects.all().order_by('-created_at')[:5],
        'pending_orders': Order.objects.filter(status='pending').count(),
        'shipped_orders': Order.objects.filter(status='shipped').count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'total_items': OrderItem.objects.count(),
        'districts': DistrictDeliveryCharge.objects.filter(is_active=True),
    }
    return render(request, 'admin_dashboard.html', context)



def admin_orders(request):
    """Admin Orders Management View"""
    from .models import Order, OrderItem, Product
    import json
    
    orders = Order.objects.all().order_by('-created_at')
    
    # Calculate stats
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    shipped_orders = orders.filter(status='shipped').count()
    delivered_orders = orders.filter(status='delivered').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    # Prepare orders for JSON and Template
    orders_json = []
    for order in orders:
        # ✅ Database থেকে total_discount নিন
        total_discount = float(order.total_discount) if order.total_discount else 0
        
        # Get special offers list
        special_offers = []
        for item in order.order_items.all():
            if item.special_offer:
                special_offers.append(item.special_offer)
        special_offers = list(set(special_offers))
        
        orders_json.append({
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone or '',
            'customer_address': order.customer_address,
            'customer_district': order.customer_district or '',
            'get_total_items': order.get_total_items(),
            'total_amount': float(order.total_amount) if order.total_amount else 0,
            'total_savings': float(order.total_savings) if order.total_savings else 0,
            'total_discount': total_discount,  # ✅ Database থেকে
            'status': order.status,
            'special_offers_list': special_offers,
            'is_eligible_for_offer': order.is_eligible_for_offer(),
            'created_at': order.created_at.isoformat(),
            'items': [
                {
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'product_price': float(item.product_price),
                    'original_price': float(item.original_price),
                    'discount_percentage': item.discount_percentage,
                    'special_offer': item.special_offer or '',
                }
                for item in order.order_items.all()
            ]
        })
    
    context = {
        'active_page': 'admin_orders',
        'orders': orders,
        'orders_json': json.dumps(orders_json) if orders_json else '[]',
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_products': Product.objects.count(),
        'total_customers': orders.values('customer_email').distinct().count(),
    }
    return render(request, 'admin_orders.html', context)