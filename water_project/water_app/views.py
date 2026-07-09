from django.shortcuts import render, get_object_or_404, redirect 
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Product, DistrictDeliveryCharge, Order, OrderItem
import json
import io
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.contrib import messages
from .forms import CustomerForm


import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime

# ReportLab Import
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
        original_price = float(product.price)
        effective_price = product.get_effective_price()
        discount_price = float(effective_price)
        discount_percent = product.discount_percentage or 0
        has_discount = product.is_on_sale and (product.discount_price is not None or discount_percent > 0)
        
        products_json.append({
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price': float(effective_price if has_discount else original_price),
            'discount_price': float(discount_price) if has_discount else None,
            'original_price': float(original_price),
            'discount_percentage': int(discount_percent) if has_discount else 0,
            'is_on_sale': bool(has_discount),
            'savings': float(original_price - discount_price) if has_discount else 0,
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
        effective_price = product.get_effective_price()
        discount_price = float(effective_price)
        discount_percent = product.discount_percentage or 0
        has_discount = product.is_on_sale and (product.discount_price is not None or discount_percent > 0)
        
        data.append({
            'id': product.id,
            'name': product.name,
            'description': product.description or '',
            'price': float(effective_price if has_discount else original_price),
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


from django.db import transaction

from django.db import transaction

@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    """API: Create a new order - Only product stock reduces, NOT inventory"""
    try:
        data = json.loads(request.body)
        
        district = data.get('customer_district', '')
        delivery_charge_obj = DistrictDeliveryCharge.objects.filter(
            district__iexact=district, 
            is_active=True
        ).first()
        delivery_charge = float(delivery_charge_obj.charge) if delivery_charge_obj else 0
        delivery_zone = delivery_charge_obj.district_name if delivery_charge_obj else 'Unknown District'
        
        items_data = data.get('items', [])
        subtotal = 0
        total_savings = 0
        total_discount = 0
        
        with transaction.atomic():
            # Validate stock availability from PRODUCT (not inventory)
            for item in items_data:
                product_id = item.get('id')
                quantity = int(item.get('quantity', 1))
                
                if product_id:
                    try:
                        product = Product.objects.select_for_update().get(id=product_id)
                        if product.stock_quantity < quantity:
                            return JsonResponse({
                                'status': 'error',
                                'message': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'
                            }, status=400)
                    except Product.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': f'Product not found: {item.get("name", "Unknown")}'
                        }, status=400)
            
            # Calculate totals and REDUCE product stock ONLY
            for item in items_data:
                product_id = item.get('id')
                price = float(item.get('price', 0))
                original_price = float(item.get('original_price', price))
                quantity = int(item.get('quantity', 1))
                
                subtotal += original_price * quantity
                savings = (original_price - price) * quantity
                if savings > 0:
                    total_savings += savings
                    total_discount += savings
                
                # 👇 ONLY product stock reduces (NOT inventory)
                if product_id:
                    try:
                        product = Product.objects.get(id=product_id)
                        product.stock_quantity -= quantity
                        product.save()
                        print(f"✅ Product stock reduced: {product.name} - New stock: {product.stock_quantity}")
                    except Product.DoesNotExist:
                        pass
            
            total_amount = subtotal - total_savings + delivery_charge
            
            # Create order
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
                total_discount=total_discount,
                total_amount=total_amount,
                payment_method=data.get('payment_method', 'Cash on Delivery'),
                transaction_id=data.get('transaction_id', ''),
                status='pending',
                payment_status='pending'
            )
            
            # Create order items
            for item in items_data:
                price = float(item.get('price', 0))
                original_price = float(item.get('original_price', price))
                quantity = int(item.get('quantity', 1))
                product_id = item.get('id')
                
                product = None
                if product_id:
                    try:
                        product = Product.objects.get(id=product_id)
                    except Product.DoesNotExist:
                        pass
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
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
            'message': 'Order created successfully. Product stock has been reduced.',
            'subtotal': subtotal,
            'total_savings': total_savings,
            'total_discount': total_discount,
            'total_amount': total_amount
        })
        
    except Exception as e:
        print(f"❌ Order Creation Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
            'total_discount': float(order.total_discount or 0),
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


# ===== Admin Views =====

def admin_dashboard(request):
    """Admin Dashboard View"""
    from .models import Order, Product, OrderItem, DistrictDeliveryCharge
    
    context = {
        'active_page': 'admin_dashboard',
        'total_orders': Order.objects.count(),
        'total_products': Product.objects.count(),
        'total_customers': Order.objects.values('customer_email').distinct().count(),
        'total_districts': DistrictDeliveryCharge.objects.filter(is_active=True).count(),
        'total_revenue': sum(float(o.total_amount) for o in Order.objects.all()),
        'recent_orders': Order.objects.all().order_by('-created_at')[:5],
        'pending_orders': Order.objects.filter(status='pending').count(),
        'shipped_orders': Order.objects.filter(status='shipped').count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'total_items': OrderItem.objects.count(),
        'districts': DistrictDeliveryCharge.objects.filter(is_active=True),
        'products': Product.objects.filter(is_active=True)[:5],
    }
    return render(request, 'admin_dashboard.html', context)


def admin_orders(request):
    """Admin Orders Management View"""
    from .models import Order, OrderItem, Product
    import json
    
    orders = Order.objects.all().order_by('-created_at')
    
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    shipped_orders = orders.filter(status='shipped').count()
    delivered_orders = orders.filter(status='delivered').count()
    cancelled_orders = orders.filter(status='cancelled').count()
    
    orders_json = []
    for order in orders:
        total_discount = float(order.total_discount) if order.total_discount else 0
        
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
            'total_discount': total_discount,
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


# ===== Export Functions =====

import io
import openpyxl
from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Q
from django.contrib.admin.views.decorators import staff_member_required
import json

from water_app.models import Order, OrderItem, Product  # Removed SpecialOffer

# Try to import ReportLab
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4, portrait
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@staff_member_required
def export_orders_excel(request):
    """Export orders as Excel file with ALL fields"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return HttpResponse("⚠️ openpyxl not installed. Please install: pip install openpyxl", status=500)
    
    # Get orders based on filters
    orders = Order.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status = request.GET.get('status')
    date = request.GET.get('date')
    ids = request.GET.get('ids')
    
    if ids:
        order_ids = ids.split(',')
        orders = orders.filter(order_id__in=order_ids)
    elif status and status != 'all':
        orders = orders.filter(status=status)
    
    # Date filter
    if date and date != 'all':
        now = datetime.now().date()
        if date == 'today':
            orders = orders.filter(created_at__date=now)
        elif date == 'week':
            week_ago = now - timedelta(days=7)
            orders = orders.filter(created_at__date__gte=week_ago)
        elif date == 'month':
            orders = orders.filter(created_at__year=now.year, created_at__month=now.month)
    
    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders Report"
    
    # Styles
    header_font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1a5276', end_color='1a5276', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    sub_header_fill = PatternFill(start_color='2e86c1', end_color='2e86c1', fill_type='solid')
    
    border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    # ===== Title Section =====
    ws.merge_cells('A1:S1')
    title_cell = ws['A1']
    title_cell.value = "📦 Aquanimity SuperWater - Complete Orders Report"
    title_cell.font = Font(name='Arial', size=18, bold=True, color='1a5276')
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    ws.merge_cells('A2:S2')
    subtitle_cell = ws['A2']
    subtitle_cell.value = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Total Orders: {orders.count()}"
    subtitle_cell.font = Font(name='Arial', size=10, color='666666')
    subtitle_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # ===== Summary Statistics =====
    summary_row = 4
    ws.merge_cells(f'A{summary_row}:F{summary_row}')
    summary_title = ws.cell(row=summary_row, column=1)
    summary_title.value = "📊 Summary Statistics"
    summary_title.font = Font(name='Arial', size=12, bold=True, color='1a5276')
    
    total_revenue = sum(float(o.total_amount) for o in orders)
    total_discount = sum(float(o.total_discount or 0) for o in orders)
    total_savings = sum(float(o.total_savings or 0) for o in orders)
    
    # Check if orders have is_eligible_for_offer method
    eligible_count = 0
    for o in orders:
        try:
            if o.is_eligible_for_offer():
                eligible_count += 1
        except:
            pass
    
    summary_data = [
        ['Total Orders', str(orders.count())],
        ['Total Revenue', f"৳ {total_revenue:.2f}"],
        ['Total Discount Given', f"৳ {total_discount:.2f}"],
        ['Total Savings', f"৳ {total_savings:.2f}"],
        ['Eligible for Offer', str(eligible_count)],
        ['Not Eligible', str(orders.count() - eligible_count)],
    ]
    
    for idx, (label, value) in enumerate(summary_data):
        row = summary_row + idx + 1
        label_cell = ws.cell(row=row, column=1, value=label)
        label_cell.font = Font(bold=True)
        label_cell.fill = PatternFill(start_color='eaf2f8', end_color='eaf2f8', fill_type='solid')
        label_cell.border = border
        label_cell.alignment = Alignment(horizontal='left', vertical='center')
        
        value_cell = ws.cell(row=row, column=2, value=value)
        value_cell.border = border
        value_cell.alignment = Alignment(horizontal='left', vertical='center')
        if '৳' in value:
            value_cell.font = Font(color='007bff', bold=True)
    
    # ===== Main Headers - ALL FIELDS =====
    header_row = summary_row + len(summary_data) + 3
    
    # Complete headers list with ALL fields
    headers = [
        'Sl No', 
        'Order ID', 
        'Customer Name', 
        'Customer Email', 
        'Customer Phone', 
        'Customer Address', 
        'District', 
        'Total Items', 
        'Products Details',
        'Subtotal', 
        'Total Savings', 
        'Total Discount', 
        'Total Amount',
        'Status', 
        'Payment Method',
        'Payment Status',
        'Delivery Address',
        'Special Offers Applied',
        'Offer Eligibility',
        'Created Date',
        'Created Time'
    ]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # ===== Data Rows =====
    row_num = header_row + 1
    sl_no = 1
    
    for order in orders:
        # Get products details
        products = []
        special_offers = []
        
        for item in order.order_items.all():
            product_name = item.product_name or (item.product.name if item.product else 'Unknown')
            qty = item.quantity
            price = float(item.product_price or 0)
            original_price = float(item.original_price or price)
            discount_percent = float(item.discount_percentage or 0)
            
            product_detail = f"{product_name} x{qty}"
            if discount_percent > 0:
                product_detail += f" ({discount_percent}% OFF)"
            products.append(product_detail)
            
            # Special offers - check if field exists
            if hasattr(item, 'special_offer') and item.special_offer:
                special_offers.append(f"{product_name}: {item.special_offer}")
        
        products_text = '\n'.join(products[:10]) + ('\n...' if len(products) > 10 else '')
        special_offers_text = '\n'.join(special_offers) if special_offers else 'None'
        
        # Check eligibility - handle if method doesn't exist
        try:
            is_eligible = order.is_eligible_for_offer()
            eligibility = '✓ Eligible' if is_eligible else '✗ Not Eligible'
        except:
            eligibility = 'N/A'
        
        # Format date and time
        created_datetime = order.created_at
        created_date = created_datetime.strftime('%d %b %Y') if created_datetime else ''
        created_time = created_datetime.strftime('%I:%M %p') if created_datetime else ''
        
        # Payment status - check if field exists
        payment_status = 'N/A'
        if hasattr(order, 'payment_status') and order.payment_status:
            payment_status = order.payment_status
        
        row_data = [
            sl_no,
            order.order_id,
            order.customer_name,
            order.customer_email,
            order.customer_phone or '',
            order.customer_address or '',
            order.customer_district or '',
            order.get_total_items(),
            products_text,
            f"৳{float(order.subtotal or 0):.2f}",
            f"৳{float(order.total_savings or 0):.2f}",
            f"৳{float(order.total_discount or 0):.2f}",
            f"৳{float(order.total_amount):.2f}",
            order.get_status_display(),
            order.payment_method or 'Cash on Delivery',
            payment_status,
            getattr(order, 'delivery_address', '') or order.customer_address or '',
            special_offers_text,
            eligibility,
            created_date,
            created_time
        ]
        
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.alignment = Alignment(
                horizontal='left' if col not in [1, 8, 10, 11, 12, 13] else 'center',
                vertical='center',
                wrap_text=True
            )
            cell.border = border
            
            # Color coding for status
            if col == 14:  # Status column
                status_colors = {
                    'pending': 'ffc107',
                    'processing': '17a2b8',
                    'shipped': '007bff',
                    'delivered': '28a745',
                    'cancelled': 'dc3545'
                }
                status_value = order.status
                if status_value in status_colors:
                    cell.fill = PatternFill(
                        start_color=status_colors[status_value],
                        end_color=status_colors[status_value],
                        fill_type='solid'
                    )
                    cell.font = Font(color='FFFFFF', bold=True)
            
            # Color coding for eligibility
            if col == 19:  # Eligibility column
                if 'Eligible' in value:
                    cell.fill = PatternFill(start_color='d4edda', end_color='d4edda', fill_type='solid')
                    cell.font = Font(color='155724', bold=True)
                elif 'Not' in value:
                    cell.fill = PatternFill(start_color='f8d7da', end_color='f8d7da', fill_type='solid')
                    cell.font = Font(color='721c24', bold=True)
            
            # Amount formatting
            if col in [10, 11, 12, 13]:  # Amount columns
                cell.alignment = Alignment(horizontal='right', vertical='center')
                if col == 13:  # Total Amount - bold
                    cell.font = Font(bold=True, color='007bff')
                if col == 12 and float(order.total_discount or 0) > 0:  # Discount - red
                    cell.font = Font(color='dc3545')
        
        row_num += 1
        sl_no += 1
    
    # ===== Adjust Column Widths =====
    column_widths = {
        'A': 5,   # Sl No
        'B': 18,  # Order ID
        'C': 20,  # Customer Name
        'D': 28,  # Customer Email
        'E': 16,  # Customer Phone
        'F': 35,  # Customer Address
        'G': 14,  # District
        'H': 11,  # Total Items
        'I': 45,  # Products Details
        'J': 14,  # Subtotal
        'K': 16,  # Total Savings
        'L': 16,  # Total Discount
        'M': 16,  # Total Amount
        'N': 14,  # Status
        'O': 18,  # Payment Method
        'P': 16,  # Payment Status
        'Q': 35,  # Delivery Address
        'R': 30,  # Special Offers
        'S': 14,  # Eligibility
        'T': 14,  # Created Date
        'U': 12,  # Created Time
    }
    
    for col, width in column_widths.items():
        ws.column_dimensions[col].width = width
    
    # ===== Freeze Panes =====
    ws.freeze_panes = f'A{header_row + 1}'
    
    # ===== Footer =====
    footer_row = row_num + 2
    ws.merge_cells(f'A{footer_row}:U{footer_row}')
    footer_cell = ws.cell(row=footer_row, column=1)
    footer_cell.value = "© 2026 Aquanimity Super Water. All rights reserved. | Report generated from Admin Dashboard"
    footer_cell.font = Font(name='Arial', size=9, color='999999')
    footer_cell.alignment = Alignment(horizontal='center')
    
    # ===== Response =====
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'orders_complete_report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response


@staff_member_required
def export_orders_pdf(request):
    """Export orders as PDF file with ALL fields"""
    if not REPORTLAB_AVAILABLE:
        return HttpResponse("⚠️ ReportLab not installed. Please install: pip install reportlab", status=500)
    
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    # Get orders based on filters
    orders = Order.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    status = request.GET.get('status')
    date = request.GET.get('date')
    ids = request.GET.get('ids')
    
    if ids:
        order_ids = ids.split(',')
        orders = orders.filter(order_id__in=order_ids)
    elif status and status != 'all':
        orders = orders.filter(status=status)
    
    # Date filter
    if date and date != 'all':
        now = datetime.now().date()
        if date == 'today':
            orders = orders.filter(created_at__date=now)
        elif date == 'week':
            week_ago = now - timedelta(days=7)
            orders = orders.filter(created_at__date__gte=week_ago)
        elif date == 'month':
            orders = orders.filter(created_at__year=now.year, created_at__month=now.month)
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    filename = f'orders_complete_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5276'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=16
    )
    
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#1a5276'),
        alignment=TA_LEFT,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=7,
        leading=9
    )
    
    header_cell_style = ParagraphStyle(
        'HeaderCellStyle',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    )
    
    # Build story
    story = []
    
    # ===== Title =====
    story.append(Paragraph("📦 Aquanimity SuperWater - Complete Orders Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    story.append(Paragraph(f"Total Orders: {orders.count()} | Filter: {status if status != 'all' else 'All'} | Date: {date if date != 'all' else 'All Time'}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # ===== Summary Statistics =====
    total_revenue = sum(float(o.total_amount) for o in orders)
    total_discount = sum(float(o.total_discount or 0) for o in orders)
    total_savings = sum(float(o.total_savings or 0) for o in orders)
    
    # Check eligibility safely
    eligible_count = 0
    for o in orders:
        try:
            if o.is_eligible_for_offer():
                eligible_count += 1
        except:
            pass
    
    summary_data = [
        ['📊 SUMMARY STATISTICS', ''],
        ['Total Orders', str(orders.count())],
        ['Total Revenue', f"৳ {total_revenue:,.2f}"],
        ['Total Discount Given', f"৳ {total_discount:,.2f}"],
        ['Total Savings', f"৳ {total_savings:,.2f}"],
        ['Eligible for Offer', str(eligible_count)],
        ['Not Eligible', str(orders.count() - eligible_count)],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#eaf2f8')),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#eaf2f8')),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== Main Table Headers - ALL FIELDS =====
    # Complete headers with ALL fields
    headers = [
        'Sl', 'Order ID', 'Customer', 'Email', 'Phone', 'Address', 'District', 
        'Items', 'Products', 'Subtotal', 'Savings', 'Discount', 'Total', 
        'Status', 'Payment', 'Offers', 'Eligibility', 'Date'
    ]
    
    # Prepare table data
    table_data = [headers]
    
    # Track if we need pagination
    max_rows_per_page = 20
    total_orders = orders.count()
    display_orders = orders[:100] if total_orders > 100 else orders
    
    for idx, order in enumerate(display_orders, 1):
        # Get products
        products = []
        for item in order.order_items.all()[:5]:
            product_name = item.product_name or (item.product.name if item.product else 'Unknown')
            qty = item.quantity
            discount = f"({item.discount_percentage}%)" if item.discount_percentage > 0 else ''
            products.append(f"{product_name} x{qty}{discount}")
        products_text = ', '.join(products) + ('...' if order.order_items.count() > 5 else '')
        
        # Get offers - safely check if field exists
        offers = []
        for item in order.order_items.all():
            if hasattr(item, 'special_offer') and item.special_offer:
                offers.append(item.special_offer)
        offers_text = ', '.join(offers[:2]) + ('...' if len(offers) > 2 else '') if offers else '-'
        
        # Check eligibility safely
        try:
            is_eligible = order.is_eligible_for_offer()
            eligibility = '✓ Eligible' if is_eligible else '✗ Not'
        except:
            eligibility = 'N/A'
        
        # Format date
        created_date = order.created_at.strftime('%d/%m/%Y') if order.created_at else ''
        
        # Truncate long text
        address = (order.customer_address or '')[:25] + ('...' if len(order.customer_address or '') > 25 else '')
        
        table_data.append([
            str(idx),
            order.order_id,
            order.customer_name[:18] + ('...' if len(order.customer_name) > 18 else ''),
            order.customer_email[:20] + ('...' if len(order.customer_email) > 20 else ''),
            order.customer_phone or '-',
            address or '-',
            order.customer_district or '-',
            str(order.get_total_items()),
            products_text[:35] + ('...' if len(products_text) > 35 else ''),
            f"৳{float(order.subtotal or 0):.2f}",
            f"৳{float(order.total_savings or 0):.2f}",
            f"৳{float(order.total_discount or 0):.2f}",
            f"৳{float(order.total_amount):.2f}",
            order.get_status_display(),
            order.payment_method or 'COD',
            offers_text,
            eligibility,
            created_date
        ])
    
    if total_orders > 100:
        table_data.append([
            '...', f'... and {total_orders - 100} more orders', '', '', '', '', '', 
            '', '', '', '', '', '', '', '', '', '', ''
        ])
    
    # Calculate column widths
    col_widths = [
        0.7*inch, 0.5*inch, 0.7*inch, 1.0*inch, 0.7*inch, 0.9*inch, 0.4*inch,
        0.3*inch, .9*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch,
        0.7*inch, 0.6*inch, 0.5*inch, 0.6*inch, 0.6*inch
    ]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Apply table styles
    table_style = TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 4),
        
        # Data rows
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 3),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ccc')),
        
        # Alternating row colors
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (0, 2), (-1, -1), colors.HexColor('#ffffff')),
    ])
    
    # Add color coding for status column (column 13)
    for row_idx in range(1, len(table_data)):
        if len(table_data[row_idx]) > 13:
            status = table_data[row_idx][13]
            status_colors = {
                'Pending': '#ffc107',
                'Processing': '#17a2b8',
                'Shipped': '#007bff',
                'Delivered': '#28a745',
                'Cancelled': '#dc3545'
            }
            if status in status_colors:
                table_style.add('BACKGROUND', (13, row_idx), (13, row_idx), colors.HexColor(status_colors[status]))
                table_style.add('TEXTCOLOR', (13, row_idx), (13, row_idx), colors.white)
    
    # Color coding for eligibility (column 16)
    for row_idx in range(1, len(table_data)):
        if len(table_data[row_idx]) > 16:
            eligibility = table_data[row_idx][16]
            if 'Eligible' in eligibility:
                table_style.add('BACKGROUND', (16, row_idx), (16, row_idx), colors.HexColor('#d4edda'))
                table_style.add('TEXTCOLOR', (16, row_idx), (16, row_idx), colors.HexColor('#155724'))
            elif 'Not' in eligibility:
                table_style.add('BACKGROUND', (16, row_idx), (16, row_idx), colors.HexColor('#f8d7da'))
                table_style.add('TEXTCOLOR', (16, row_idx), (16, row_idx), colors.HexColor('#721c24'))
    
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # ===== Footer =====
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    story.append(Paragraph("© 2026 Aquanimity Super Water. All rights reserved. | Generated from Admin Dashboard", footer_style))
    story.append(Paragraph(f"Page 1 of 1 | Report includes {min(total_orders, 100)} of {total_orders} total orders", footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    response.write(buffer.getvalue())
    return response


@staff_member_required
def download_invoice(request, order_id):
    """Download invoice as PDF for a specific order"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        # Assuming you have a function to generate invoice PDF
        from water_app.utils import generate_invoice_pdf
        return generate_invoice_pdf(order)
    except ImportError:
        # Fallback if utils doesn't exist
        return HttpResponse("Invoice generation not available", status=501)
    except Exception as e:
        return HttpResponse(f"Error generating invoice: {str(e)}", status=500)


@staff_member_required
@require_http_methods(["DELETE"])
def delete_order(request, order_id):
    """Delete an order"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        order.delete()
        return JsonResponse({'status': 'success', 'message': 'Order deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required
def get_order_detail(request, order_id):
    """Get order details as JSON"""
    try:
        order = get_object_or_404(Order, order_id=order_id)
        data = {
            'order_id': order.order_id,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'customer_phone': order.customer_phone,
            'customer_address': order.customer_address,
            'customer_district': order.customer_district,
            'total_amount': float(order.total_amount),
            'total_discount': float(order.total_discount or 0),
            'total_savings': float(order.total_savings or 0),
            'subtotal': float(order.subtotal or 0),
            'status': order.status,
            'status_display': order.get_status_display(),
            'payment_method': order.payment_method,
            'created_at': order.created_at.isoformat(),
            'is_eligible_for_offer': order.is_eligible_for_offer() if hasattr(order, 'is_eligible_for_offer') else False,
            'items': [
                {
                    'product_name': item.product_name or (item.product.name if item.product else 'Unknown'),
                    'quantity': item.quantity,
                    'product_price': float(item.product_price or 0),
                    'original_price': float(item.original_price or item.product_price or 0),
                    'discount_percentage': float(item.discount_percentage or 0),
                    'special_offer': getattr(item, 'special_offer', None),
                }
                for item in order.order_items.all()
            ],
            'special_offers_list': [
                getattr(item, 'special_offer', None) for item in order.order_items.all() 
                if getattr(item, 'special_offer', None)
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

import json
import io
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from decimal import Decimal

from water_app.models import Order, OrderItem, Product


# ============================================
# PRODUCT MANAGEMENT VIEWS
# ============================================

@staff_member_required
def admin_products(request):
    """Admin Products Management Page"""
    products = Product.objects.all().order_by('-created_at')
    
    context = {
        'products': products,
        'products_json': json.dumps([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': float(p.price),
            'discount_price': float(p.discount_price) if p.discount_price else None,
            'discount_percentage': p.discount_percentage if p.discount_percentage else None,
            'stock_quantity': p.stock_quantity if hasattr(p, 'stock_quantity') else 0,
            'is_active': p.is_active,
            'special_offer': p.special_offer if hasattr(p, 'special_offer') else None,
            'image_url': p.image.url if p.image else None,
            'created_at': p.created_at.isoformat() if p.created_at else None,
        } for p in products]),
        'total_products': products.count(),
        'active_products': products.filter(is_active=True).count(),
        'inactive_products': products.filter(is_active=False).count(),
        'low_stock_products': products.filter(stock_quantity__lte=10, stock_quantity__gt=0).count() if hasattr(Product, 'stock_quantity') else 0,
        'total_orders': Order.objects.count(),
        'total_customers': 0,
    }
    return render(request, 'admin_products.html', context)

# ===== Custom Admin Edit Views =====

@csrf_exempt
@staff_member_required
def update_order(request, order_id):
    """Update an existing order via API"""
    if request.method not in ['POST', 'PUT']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        # Get form data
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_address = request.POST.get('customer_address', '').strip()
        customer_district = request.POST.get('customer_district', '').strip()
        status = request.POST.get('status', 'pending')
        payment_status = request.POST.get('payment_status', 'pending')
        
        # Validate required fields
        if not customer_name:
            return JsonResponse({'status': 'error', 'message': 'Customer name is required'}, status=400)
        if not customer_email:
            return JsonResponse({'status': 'error', 'message': 'Customer email is required'}, status=400)
        
        # Update order
        order.customer_name = customer_name
        order.customer_email = customer_email
        order.customer_phone = customer_phone if customer_phone else None
        order.customer_address = customer_address if customer_address else None
        order.customer_district = customer_district if customer_district else None
        order.status = status
        order.payment_status = payment_status
        
        order.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Order updated successfully',
            'order_id': order.order_id
        })
        
    except Exception as e:
        print(f"❌ Error updating order: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@staff_member_required
def admin_product_edit(request, product_id):
    """Custom Product Edit Page"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Update product logic here
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.discount_price = request.POST.get('discount_price', product.discount_price)
        product.discount_percentage = request.POST.get('discount_percentage', product.discount_percentage)
        product.stock_quantity = request.POST.get('stock_quantity', product.stock_quantity)
        product.is_active = request.POST.get('is_active', 'on') == 'on'
        product.special_offer = request.POST.get('special_offer', product.special_offer)
        product.save()
        
        messages.success(request, f'Product {product.name} updated successfully!')
        return redirect('admin_products')
    
    context = {
        'product': product,
    }
    return render(request, 'admin_product_edit.html', context)


@staff_member_required
def get_products(request):
    """Get products as JSON"""
    products = Product.objects.all().order_by('-created_at')
    data = [{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': float(p.price),
        'discount_price': float(p.discount_price) if p.discount_price else None,
        'discount_percentage': p.discount_percentage if p.discount_percentage else None,
        'stock_quantity': p.stock_quantity if hasattr(p, 'stock_quantity') else 0,
        'is_active': p.is_active,
        'special_offer': p.special_offer if hasattr(p, 'special_offer') else None,
        'image_url': p.image.url if p.image else None,
        'created_at': p.created_at.isoformat() if p.created_at else None,
    } for p in products]
    return JsonResponse(data, safe=False)


@staff_member_required
def get_product_detail(request, product_id):
    """Get single product detail as JSON"""
    try:
        product = get_object_or_404(Product, id=product_id)
        data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'discount_percentage': product.discount_percentage if product.discount_percentage else None,
            'stock_quantity': product.stock_quantity if hasattr(product, 'stock_quantity') else 0,
            'is_active': product.is_active,
            'special_offer': product.special_offer if hasattr(product, 'special_offer') else None,
            'image_url': product.image.url if product.image else None,
            'created_at': product.created_at.isoformat() if product.created_at else None,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def create_product(request):
    """Create a new product - Inventory stock REDUCES"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price', '').strip()
        discount_percentage = request.POST.get('discount_percentage', '').strip()
        stock_quantity = request.POST.get('stock_quantity', 0)
        is_active = request.POST.get('is_active', 'true') == 'true'
        special_offer = request.POST.get('special_offer', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Product name is required'}, status=400)
        if not price:
            return JsonResponse({'status': 'error', 'message': 'Price is required'}, status=400)
        
        try:
            price = float(price)
            if price < 0:
                return JsonResponse({'status': 'error', 'message': 'Price cannot be negative'}, status=400)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid price format'}, status=400)
        
        # Validate stock quantity
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity < 0:
                return JsonResponse({'status': 'error', 'message': 'Stock cannot be negative'}, status=400)
        except ValueError:
            stock_quantity = 0
        
        # Check if product has discount
        is_on_sale = False
        discount_price_value = None
        discount_percentage_value = None
        
        if discount_price and discount_price != '':
            try:
                discount_price_value = float(discount_price)
                if discount_price_value > 0 and discount_price_value < price:
                    is_on_sale = True
            except:
                pass
        
        if not is_on_sale and discount_percentage and discount_percentage != '':
            try:
                discount_percentage_value = int(discount_percentage)
                if discount_percentage_value > 0 and discount_percentage_value <= 100:
                    is_on_sale = True
            except:
                pass
        
        # Create product
        product = Product(
            name=name,
            description=description,
            price=price,
            discount_price=discount_price_value,
            discount_percentage=discount_percentage_value,
            stock_quantity=stock_quantity,
            is_active=is_active,
            special_offer=special_offer if special_offer else None,
            is_on_sale=is_on_sale,
        )
        
        # Handle image upload
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            if image_file.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                return JsonResponse({'status': 'error', 'message': 'Invalid image format. Only JPEG, PNG, GIF, WEBP allowed.'}, status=400)
            if image_file.size > 2 * 1024 * 1024:
                return JsonResponse({'status': 'error', 'message': 'Image size must be less than 2MB'}, status=400)
            product.image = image_file
        
        product.save()
        
        # ✅ Inventory stock REDUCES (if stock_quantity > 0)
        if stock_quantity > 0:
            try:
                from water_app.models import Inventory
                from django.db import models

                # Get current inventory total
                inventory_total = Inventory.objects.filter(product=product).aggregate(
                    total=models.Sum('quantity')
                )['total'] or 0

                # Prevent creating product with more stock than available in inventory
                if inventory_total < stock_quantity:
                    product.delete()
                    return JsonResponse({'status': 'error', 'message': f'Insufficient inventory. Available inventory: {inventory_total}'}, status=400)

                # Create inventory movement - STOCK TAKEN FROM INVENTORY
                Inventory.objects.create(
                    product=product,
                    quantity=-stock_quantity,  # Negative: Stock taken from inventory
                    previous_stock=inventory_total,
                    new_stock=inventory_total - stock_quantity,
                    movement_type='adjustment',
                    reference=f'Product Created: {product.id}',
                    notes=f'Stock TAKEN from inventory for product: {product.name}. Quantity: {stock_quantity}',
                    user=request.user if request.user.is_authenticated else None
                )

                print(f"✅ Inventory stock REDUCED by {stock_quantity} for product: {product.name}")
                print(f"   New inventory total: {inventory_total - stock_quantity}")

            except Exception as e:
                print(f"⚠️ Inventory update skipped: {str(e)}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Product "{name}" created successfully. Stock taken from inventory: {stock_quantity}',
            'product_id': product.id,
        })
        
    except Exception as e:
        print(f"❌ Error creating product: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

@csrf_exempt
@staff_member_required
def update_product(request, product_id):
    """Update an existing product - Inventory adjusts accordingly"""
    if request.method not in ['PUT', 'POST']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price', '').strip()
        discount_percentage = request.POST.get('discount_percentage', '').strip()
        stock_quantity = request.POST.get('stock_quantity', 0)
        is_active = request.POST.get('is_active', 'true') == 'true'
        special_offer = request.POST.get('special_offer', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Product name is required'}, status=400)
        if not price:
            return JsonResponse({'status': 'error', 'message': 'Price is required'}, status=400)
        
        try:
            price = float(price)
            if price < 0:
                return JsonResponse({'status': 'error', 'message': 'Price cannot be negative'}, status=400)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid price format'}, status=400)
        
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity < 0:
                return JsonResponse({'status': 'error', 'message': 'Stock cannot be negative'}, status=400)
        except ValueError:
            stock_quantity = 0
        
        # Store old stock
        old_stock = product.stock_quantity
        
        # Check if product has discount
        is_on_sale = False
        discount_price_value = None
        discount_percentage_value = None
        
        if discount_price and discount_price != '':
            try:
                discount_price_value = float(discount_price)
                if discount_price_value > 0 and discount_price_value < price:
                    is_on_sale = True
            except:
                pass
        
        if not is_on_sale and discount_percentage and discount_percentage != '':
            try:
                discount_percentage_value = int(discount_percentage)
                if discount_percentage_value > 0 and discount_percentage_value <= 100:
                    is_on_sale = True
            except:
                pass
        
        # Determine quantity difference before saving
        quantity_diff = stock_quantity - old_stock

        # If product stock would increase, ensure inventory has enough BEFORE saving
        if quantity_diff > 0:
            try:
                from water_app.models import Inventory
                inventory_total_check = Inventory.objects.filter(product=product).aggregate(
                    total=models.Sum('quantity')
                )['total'] or 0
                if inventory_total_check < quantity_diff:
                    return JsonResponse({'status': 'error', 'message': f'Insufficient inventory. Available inventory: {inventory_total_check}'}, status=400)
            except Exception as e:
                print(f"⚠️ Inventory check skipped: {str(e)}")

        # Update product
        product.name = name
        product.description = description
        product.price = price
        product.discount_price = discount_price_value
        product.discount_percentage = discount_percentage_value
        product.stock_quantity = stock_quantity
        product.is_active = is_active
        product.special_offer = special_offer if special_offer else None
        product.is_on_sale = is_on_sale
        
        # Handle image upload
        if 'image' in request.FILES:
            if product.image:
                try:
                    default_storage.delete(product.image.path)
                except:
                    pass
            product.image = request.FILES['image']
        elif 'remove_image' in request.POST and request.POST.get('remove_image') == 'true':
            if product.image:
                try:
                    default_storage.delete(product.image.path)
                except:
                    pass
                product.image = None
        
        product.save()
        
        # 👇 Inventory adjusts when product stock changes
        if stock_quantity != old_stock:
            try:
                from water_app.models import Inventory
                quantity_diff = stock_quantity - old_stock

                # Get current inventory total
                inventory_total = Inventory.objects.filter(product=product).aggregate(
                    total=models.Sum('quantity')
                )['total'] or 0

                # If product stock increases (quantity_diff > 0), ensure inventory has enough
                if quantity_diff > 0 and inventory_total < quantity_diff:
                    return JsonResponse({'status': 'error', 'message': f'Insufficient inventory. Available inventory: {inventory_total}'}, status=400)

                # Inventory changes opposite to product stock
                # If product stock increases, inventory decreases (stock taken)
                # If product stock decreases, inventory increases (stock returned)
                inventory_change = -quantity_diff

                Inventory.objects.create(
                    product=product,
                    quantity=inventory_change,
                    previous_stock=inventory_total,
                    new_stock=inventory_total + inventory_change,
                    movement_type='adjustment',
                    reference=f'Product Updated: {product.id}',
                    notes=f'Stock changed from {old_stock} to {stock_quantity}. Inventory adjusted by {inventory_change}',
                    user=request.user if request.user.is_authenticated else None
                )

                print(f"✅ Inventory adjusted: {product.name} - Change: {inventory_change}")

            except Exception as e:
                print(f"⚠️ Inventory update skipped: {str(e)}")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Product "{name}" updated successfully.',
            'product_id': product.id
        })
        
    except Exception as e:
        print(f"❌ Error updating product: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@csrf_exempt
@staff_member_required
def delete_product(request, product_id):
    """Delete a product"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Delete image if exists
        if product.image:
            try:
                default_storage.delete(product.image.path)
            except:
                pass
        
        product.delete()
        return JsonResponse({'status': 'success', 'message': 'Product deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def toggle_product_status(request, product_id):
    """Toggle product active status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body)
        is_active = data.get('is_active', not product.is_active)
        
        product.is_active = is_active
        product.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Product {"activated" if is_active else "deactivated"} successfully',
            'is_active': is_active
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required
def export_products_excel(request):
    """Export products as Excel file"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return HttpResponse("⚠️ openpyxl not installed. Please install: pip install openpyxl", status=500)
    
    products = Product.objects.all().order_by('-created_at')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products Report"
    
    # Styles
    header_font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1a5276', end_color='1a5276', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    # Title
    ws.merge_cells('A1:J1')
    title_cell = ws['A1']
    title_cell.value = "📦 Aquanimity SuperWater - Products Report"
    title_cell.font = Font(name='Arial', size=18, bold=True, color='1a5276')
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    ws.merge_cells('A2:J2')
    subtitle_cell = ws['A2']
    subtitle_cell.value = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Total Products: {products.count()}"
    subtitle_cell.font = Font(name='Arial', size=10, color='666666')
    subtitle_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Headers
    headers = ['Sl No', 'Product Name', 'Description', 'Price', 'Discount Price', 'Discount %', 'Stock', 'Status', 'Special Offer', 'Created At']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Data
    row_num = 5
    for idx, product in enumerate(products, 1):
        row_data = [
            idx,
            product.name,
            product.description[:50] + ('...' if product.description and len(product.description) > 50 else '') or '-',
            f"৳{float(product.price):.2f}",
            f"৳{float(product.discount_price):.2f}" if product.discount_price else '-',
            f"{product.discount_percentage}%" if product.discount_percentage else '-',
            product.stock_quantity if hasattr(product, 'stock_quantity') else 0,
            'Active' if product.is_active else 'Inactive',
            product.special_offer if hasattr(product, 'special_offer') and product.special_offer else '-',
            product.created_at.strftime('%Y-%m-%d %H:%M') if product.created_at else '-'
        ]
        
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = border
        
        row_num += 1
    
    # Column widths
    widths = {'A': 6, 'B': 30, 'C': 35, 'D': 12, 'E': 14, 'F': 10, 'G': 10, 'H': 10, 'I': 25, 'J': 18}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    
    ws.freeze_panes = 'A5'
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'products_report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@staff_member_required
def export_products_pdf(request):
    """Export products as PDF file"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        return HttpResponse("⚠️ ReportLab not installed. Please install: pip install reportlab", status=500)
    
    products = Product.objects.all().order_by('-created_at')
    
    response = HttpResponse(content_type='application/pdf')
    filename = f'products_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1a5276'), alignment=TA_CENTER, spaceAfter=12, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#666666'), alignment=TA_CENTER, spaceAfter=16)
    
    story = []
    story.append(Paragraph("📦 Aquanimity SuperWater - Products Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    story.append(Paragraph(f"Total Products: {products.count()}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Table
    table_data = [['Sl', 'Product Name', 'Price', 'Discount Price', 'Discount %', 'Stock', 'Status']]
    for idx, product in enumerate(products[:100], 1):
        table_data.append([
            str(idx),
            product.name[:25] + ('...' if len(product.name) > 25 else ''),
            f"৳{float(product.price):.2f}",
            f"৳{float(product.discount_price):.2f}" if product.discount_price else '-',
            f"{product.discount_percentage}%" if product.discount_percentage else '-',
            str(product.stock_quantity if hasattr(product, 'stock_quantity') else 0),
            'Active' if product.is_active else 'Inactive'
        ])
    
    if products.count() > 100:
        table_data.append(['...', f'... and {products.count() - 100} more products', '', '', '', '', ''])
    
    table = Table(table_data, colWidths=[0.4*inch, 2.0*inch, 0.8*inch, 0.9*inch, 0.7*inch, 0.6*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 3),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
    story.append(Paragraph("© 2026 Aquanimity Super Water. All rights reserved.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    response.write(buffer.getvalue())
    return response


# ============================================
# DELIVERY MANAGEMENT VIEWS
# ============================================


@staff_member_required
def admin_delivery(request):
    """Admin Delivery Charges Management Page"""
    districts = DistrictDeliveryCharge.objects.all().order_by('district_name')
    
    context = {
        'districts': districts,
        'districts_json': json.dumps([{
            'id': d.id,
            'district': d.district,
            'district_name': d.district_name,
            'charge': float(d.charge),
            'delivery_time': d.delivery_time,
            'is_active': d.is_active,
            'created_at': d.created_at.isoformat() if d.created_at else None,
        } for d in districts]),
        'total_districts': districts.count(),
        'active_districts': districts.filter(is_active=True).count(),
        'inactive_districts': districts.filter(is_active=False).count(),
        'avg_charge': districts.aggregate(avg_charge=models.Avg('charge'))['avg_charge'] or 0,
        'total_orders': Order.objects.count(),
        'total_products': Product.objects.count(),
        'total_customers': 0,
    }
    return render(request, 'admin_delivery.html', context)


@csrf_exempt
@staff_member_required
def create_district(request):
    """Create a new district delivery charge"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        district_name = request.POST.get('district_name', '').strip()
        district = request.POST.get('district', '').strip().lower()
        charge = request.POST.get('charge')
        delivery_time = request.POST.get('delivery_time', '2-3 days').strip()
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        # Validate required fields
        if not district_name:
            return JsonResponse({'status': 'error', 'message': 'District name is required'}, status=400)
        if not charge:
            return JsonResponse({'status': 'error', 'message': 'Delivery charge is required'}, status=400)
        
        try:
            charge = float(charge)
            if charge < 0:
                return JsonResponse({'status': 'error', 'message': 'Charge cannot be negative'}, status=400)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid charge format'}, status=400)
        
        # Auto-generate district code if not provided
        if not district:
            district = district_name.lower().replace(' ', '_')
        
        # Check if district already exists
        if DistrictDeliveryCharge.objects.filter(district=district).exists():
            return JsonResponse({'status': 'error', 'message': f'District "{district}" already exists'}, status=400)
        
        # Create district
        district_obj = DistrictDeliveryCharge(
            district_name=district_name,
            district=district,
            charge=charge,
            delivery_time=delivery_time,
            is_active=is_active,
        )
        district_obj.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'District added successfully',
            'district_id': district_obj.id
        })
        
    except Exception as e:
        print(f"Error creating district: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def update_district(request, district_id):
    """Update an existing district delivery charge"""
    if request.method not in ['POST', 'PUT']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        district_obj = get_object_or_404(DistrictDeliveryCharge, id=district_id)
        
        district_name = request.POST.get('district_name', '').strip()
        district = request.POST.get('district', '').strip().lower()
        charge = request.POST.get('charge')
        delivery_time = request.POST.get('delivery_time', '2-3 days').strip()
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        # Validate required fields
        if not district_name:
            return JsonResponse({'status': 'error', 'message': 'District name is required'}, status=400)
        if not charge:
            return JsonResponse({'status': 'error', 'message': 'Delivery charge is required'}, status=400)
        
        try:
            charge = float(charge)
            if charge < 0:
                return JsonResponse({'status': 'error', 'message': 'Charge cannot be negative'}, status=400)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid charge format'}, status=400)
        
        # Check if district code already exists (excluding current)
        if district and DistrictDeliveryCharge.objects.filter(district=district).exclude(id=district_id).exists():
            return JsonResponse({'status': 'error', 'message': f'District "{district}" already exists'}, status=400)
        
        # Update district
        district_obj.district_name = district_name
        district_obj.district = district if district else district_name.lower().replace(' ', '_')
        district_obj.charge = charge
        district_obj.delivery_time = delivery_time
        district_obj.is_active = is_active
        district_obj.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'District updated successfully',
            'district_id': district_obj.id
        })
        
    except Exception as e:
        print(f"Error updating district: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def delete_district(request, district_id):
    """Delete a district delivery charge"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        district_obj = get_object_or_404(DistrictDeliveryCharge, id=district_id)
        district_obj.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'District deleted successfully'
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def toggle_district_status(request, district_id):
    """Toggle district active status"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        district_obj = get_object_or_404(DistrictDeliveryCharge, id=district_id)
        data = json.loads(request.body)
        is_active = data.get('is_active', not district_obj.is_active)
        
        district_obj.is_active = is_active
        district_obj.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'District {"activated" if is_active else "deactivated"} successfully',
            'is_active': is_active
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required
def export_districts_excel(request):
    """Export districts as Excel file"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return HttpResponse("⚠️ openpyxl not installed. Please install: pip install openpyxl", status=500)
    
    districts = DistrictDeliveryCharge.objects.all().order_by('district_name')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Districts Report"
    
    # Styles
    header_font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1a5276', end_color='1a5276', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    border = Border(
        left=Side(style='thin', color='000000'),
        right=Side(style='thin', color='000000'),
        top=Side(style='thin', color='000000'),
        bottom=Side(style='thin', color='000000')
    )
    
    # Title
    ws.merge_cells('A1:F1')
    title_cell = ws['A1']
    title_cell.value = "📦 Aquanimity SuperWater - Delivery Charges Report"
    title_cell.font = Font(name='Arial', size=18, bold=True, color='1a5276')
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    ws.merge_cells('A2:F2')
    subtitle_cell = ws['A2']
    subtitle_cell.value = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Total Districts: {districts.count()}"
    subtitle_cell.font = Font(name='Arial', size=10, color='666666')
    subtitle_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Headers
    headers = ['Sl No', 'District Name', 'District Code', 'Charge (৳)', 'Delivery Time', 'Status']
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Data
    row_num = 5
    for idx, district in enumerate(districts, 1):
        row_data = [
            idx,
            district.district_name,
            district.district,
            float(district.charge),
            district.delivery_time or '2-3 days',
            'Active' if district.is_active else 'Inactive'
        ]
        
        for col, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col, value=value)
            cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            cell.border = border
        
        row_num += 1
    
    # Column widths
    widths = {'A': 6, 'B': 30, 'C': 18, 'D': 14, 'E': 16, 'F': 10}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    
    ws.freeze_panes = 'A5'
    
    # Summary Statistics
    summary_row = row_num + 2
    ws.merge_cells(f'A{summary_row}:D{summary_row}')
    summary_title = ws.cell(row=summary_row, column=1)
    summary_title.value = "📊 Summary Statistics"
    summary_title.font = Font(name='Arial', size=12, bold=True)
    
    summary_data = [
        ['Total Districts', str(districts.count())],
        ['Active Districts', str(districts.filter(is_active=True).count())],
        ['Inactive Districts', str(districts.filter(is_active=False).count())],
        ['Average Charge', f"৳ {districts.aggregate(avg_charge=models.Avg('charge'))['avg_charge'] or 0:.2f}"],
    ]
    
    for idx, (label, value) in enumerate(summary_data):
        row = summary_row + idx + 1
        ws.cell(row=row, column=1, value=label).font = Font(bold=True)
        ws.cell(row=row, column=2, value=value)
    
    # Footer
    footer_row = summary_row + len(summary_data) + 2
    ws.merge_cells(f'A{footer_row}:F{footer_row}')
    footer_cell = ws.cell(row=footer_row, column=1)
    footer_cell.value = "© 2026 Aquanimity Super Water. All rights reserved."
    footer_cell.font = Font(name='Arial', size=9, color='999999')
    footer_cell.alignment = Alignment(horizontal='center')
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'districts_report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@staff_member_required
def export_districts_pdf(request):
    """Export districts as PDF file"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        return HttpResponse("⚠️ ReportLab not installed. Please install: pip install reportlab", status=500)
    
    districts = DistrictDeliveryCharge.objects.all().order_by('district_name')
    
    response = HttpResponse(content_type='application/pdf')
    filename = f'districts_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1a5276'), alignment=TA_CENTER, spaceAfter=12, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#666666'), alignment=TA_CENTER, spaceAfter=16)
    
    story = []
    story.append(Paragraph("📦 Aquanimity SuperWater - Delivery Charges Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
    story.append(Paragraph(f"Total Districts: {districts.count()}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Table
    table_data = [['Sl', 'District Name', 'District Code', 'Charge (৳)', 'Delivery Time', 'Status']]
    for idx, district in enumerate(districts[:100], 1):
        table_data.append([
            str(idx),
            district.district_name[:25] + ('...' if len(district.district_name) > 25 else ''),
            district.district,
            f"৳{float(district.charge):.2f}",
            district.delivery_time or '2-3 days',
            'Active' if district.is_active else 'Inactive'
        ])
    
    if districts.count() > 100:
        table_data.append(['...', f'... and {districts.count() - 100} more districts', '', '', '', ''])
    
    table = Table(table_data, colWidths=[0.4*inch, 2.2*inch, 1.0*inch, 0.8*inch, 0.8*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 3),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle('FooterStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#999999'), alignment=TA_CENTER)
    story.append(Paragraph("© 2026 Aquanimity Super Water. All rights reserved.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    response.write(buffer.getvalue())
    return response


@staff_member_required
def admin_inventory(request):
    """Admin Inventory Management Page"""
    from water_app.models import Inventory
    from django.db import models
    
    products = Product.objects.all().order_by('-created_at')
    
    products_with_inventory = []
    for product in products:
        # Calculate inventory total
        inventory_total = Inventory.objects.filter(product=product).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        # Calculate inventory value (price × inventory total)
        inventory_value = float(product.price) * inventory_total
        
        products_with_inventory.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'stock_quantity': product.stock_quantity,
            'inventory_total': inventory_total,
            'inventory_value': inventory_value,  # 👈 Added
            'is_on_sale': product.is_on_sale,
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_url': product.image.url if product.image else None,
            'created_at': product.created_at.isoformat() if product.created_at else None,
        })
    
    context = {
        'products': products,
        'products_json': json.dumps(products_with_inventory),
        'total_products': products.count(),
        'in_stock_products': products.filter(stock_quantity__gt=20).count(),
        'low_stock_products': products.filter(stock_quantity__gte=1, stock_quantity__lte=20).count(),
        'out_of_stock_products': products.filter(stock_quantity=0).count(),
        'total_orders': Order.objects.count(),
        'total_districts': DistrictDeliveryCharge.objects.count(),
        'total_customers': 0,
    }
    return render(request, 'admin_inventory.html', context)

@csrf_exempt
@staff_member_required
def add_stock(request, product_id):
    """Add stock to inventory - ONLY Inventory stock INCREASES"""
    print("=" * 50)
    print("🔵 add_stock called")
    print(f"   Product ID: {product_id}")
    print(f"   Request method: {request.method}")
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get product
        product = get_object_or_404(Product, id=product_id)
        print(f"   Product: {product.name}")
        
        # Get quantity from request body
        try:
            data = json.loads(request.body)
            quantity = data.get('quantity', 0)
            print(f"   Quantity from JSON: {quantity}")
        except json.JSONDecodeError:
            # If JSON parsing fails, try form data
            quantity = request.POST.get('quantity', 0)
            print(f"   Quantity from POST: {quantity}")
        
        try:
            quantity = int(quantity)
        except:
            quantity = 0
        
        print(f"   Final quantity: {quantity}")
        
        if quantity <= 0:
            return JsonResponse({'status': 'error', 'message': 'Quantity must be greater than 0'}, status=400)
        
        # ============================================
        # ✅ Update Inventory
        # ============================================
        from water_app.models import Inventory
        from django.db import models
        
        # Get current inventory total
        inventory_total = Inventory.objects.filter(product=product).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        print(f"   Current inventory total: {inventory_total}")
        
        # Create inventory movement
        inventory_movement = Inventory.objects.create(
            product=product,
            quantity=quantity,
            previous_stock=inventory_total,
            new_stock=inventory_total + quantity,
            movement_type='restock',
            reference=f'Manual Restock: {product.id}',
            notes=f'Added {quantity} units to inventory. Product stock: {product.stock_quantity}',
            user=request.user if request.user.is_authenticated else None
        )
        
        print(f"   Inventory movement created: ID {inventory_movement.id}")
        
        # Verify
        new_inventory_total = Inventory.objects.filter(product=product).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        print(f"✅ Success!")
        print(f"   Old inventory: {inventory_total}")
        print(f"   New inventory: {new_inventory_total}")
        print(f"   Product stock: {product.stock_quantity} (unchanged)")
        print("=" * 50)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Added {quantity} units to inventory',
            'product_stock': product.stock_quantity,
            'inventory_added': quantity,
            'inventory_total': new_inventory_total,
            'movement_id': inventory_movement.id
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=400)
    
@staff_member_required
def export_inventory_excel(request):
    """Export inventory as Excel file with Inventory Value"""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return HttpResponse("⚠️ openpyxl not installed. Please install: pip install openpyxl", status=500)
    
    try:
        from water_app.models import Inventory
        from django.db import models
        
        products = Product.objects.all().order_by('-created_at')
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventory Report"
        
        # Styles
        header_font = Font(name='Arial', size=10, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='1a5276', end_color='1a5276', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )
        
        # Title
        ws.merge_cells('A1:I1')
        title_cell = ws['A1']
        title_cell.value = "📦 Aquanimity SuperWater - Inventory Report"
        title_cell.font = Font(name='Arial', size=18, bold=True, color='1a5276')
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        ws.merge_cells('A2:I2')
        subtitle_cell = ws['A2']
        subtitle_cell.value = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | Total Products: {products.count()}"
        subtitle_cell.font = Font(name='Arial', size=10, color='666666')
        subtitle_cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Headers - Added Inventory Value column
        headers = ['Sl No', 'Product Name', 'Price (৳)', 'Stock Quantity', 'Inventory Stock', 'Inventory Value (৳)', 'Stock Value (৳)', 'Status', 'Created At']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border
        
        # Data
        row_num = 5
        total_stock_value = 0
        total_stock_quantity = 0
        total_inventory = 0
        total_inventory_value = 0
        
        for idx, product in enumerate(products, 1):
            # Calculate inventory total for this product
            inventory_total = Inventory.objects.filter(product=product).aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            
            # Calculate inventory value
            inventory_value = float(product.price) * inventory_total
            
            stock_value = float(product.price) * product.stock_quantity
            total_stock_value += stock_value
            total_stock_quantity += product.stock_quantity
            total_inventory += inventory_total
            total_inventory_value += inventory_value
            
            # Determine status
            if product.stock_quantity > 20:
                status = 'In Stock'
            elif product.stock_quantity > 0:
                status = 'Low Stock'
            else:
                status = 'Out of Stock'
            
            row_data = [
                idx,
                product.name,
                float(product.price),
                product.stock_quantity,
                inventory_total,
                inventory_value,  # 👈 Inventory Value column
                stock_value,
                status,
                product.created_at.strftime('%Y-%m-%d %H:%M') if product.created_at else '-'
            ]
            
            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col, value=value)
                cell.alignment = Alignment(horizontal='left' if col not in [1, 4, 5] else 'center', vertical='center', wrap_text=True)
                cell.border = border
                
                # Color coding for stock status
                if col == 8:  # Status column
                    if value == 'In Stock':
                        cell.fill = PatternFill(start_color='d4edda', end_color='d4edda', fill_type='solid')
                        cell.font = Font(color='155724')
                    elif value == 'Low Stock':
                        cell.fill = PatternFill(start_color='fff3cd', end_color='fff3cd', fill_type='solid')
                        cell.font = Font(color='856404')
                    else:
                        cell.fill = PatternFill(start_color='f8d7da', end_color='f8d7da', fill_type='solid')
                        cell.font = Font(color='721c24')
                
                # Highlight Inventory Value column
                if col == 6:
                    cell.font = Font(color='6f42c1', bold=True)
            
            row_num += 1
        
        # Column widths
        widths = {'A': 6, 'B': 35, 'C': 14, 'D': 12, 'E': 14, 'F': 16, 'G': 16, 'H': 12, 'I': 18}
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        
        ws.freeze_panes = 'A5'
        
        # Summary Statistics
        summary_row = row_num + 2
        ws.merge_cells(f'A{summary_row}:D{summary_row}')
        summary_title = ws.cell(row=summary_row, column=1)
        summary_title.value = "📊 Summary Statistics"
        summary_title.font = Font(name='Arial', size=12, bold=True)
        
        in_stock_count = products.filter(stock_quantity__gt=20).count()
        low_stock_count = products.filter(stock_quantity__gte=1, stock_quantity__lte=20).count()
        out_of_stock_count = products.filter(stock_quantity=0).count()
        
        summary_data = [
            ['Total Products', str(products.count())],
            ['Total Stock Quantity', str(total_stock_quantity)],
            ['Total Inventory Stock', str(total_inventory)],
            ['Total Inventory Value', f"৳ {total_inventory_value:.2f}"],  # 👈 Added
            ['Total Stock Value', f"৳ {total_stock_value:.2f}"],
            ['In Stock', str(in_stock_count)],
            ['Low Stock', str(low_stock_count)],
            ['Out of Stock', str(out_of_stock_count)],
        ]
        
        for idx, (label, value) in enumerate(summary_data):
            row = summary_row + idx + 1
            ws.cell(row=row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=row, column=2, value=value)
        
        # Footer
        footer_row = summary_row + len(summary_data) + 2
        ws.merge_cells(f'A{footer_row}:I{footer_row}')
        footer_cell = ws.cell(row=footer_row, column=1)
        footer_cell.value = "© 2026 Aquanimity Super Water. All rights reserved."
        footer_cell.font = Font(name='Arial', size=9, color='999999')
        footer_cell.alignment = Alignment(horizontal='center')
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response
        
    except Exception as e:
        print(f"❌ Excel Export Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error generating Excel: {str(e)}", status=500)

@staff_member_required
def export_inventory_pdf(request):
    """Export inventory as PDF file with Inventory Value"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        return HttpResponse("⚠️ ReportLab not installed. Please install: pip install reportlab", status=500)
    
    try:
        from water_app.models import Inventory
        from django.db import models
        
        products = Product.objects.all().order_by('-created_at')
        
        response = HttpResponse(content_type='application/pdf')
        filename = f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'TitleStyle', 
            parent=styles['Heading1'], 
            fontSize=18, 
            textColor=colors.HexColor('#1a5276'), 
            alignment=TA_CENTER, 
            spaceAfter=12, 
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle', 
            parent=styles['Normal'], 
            fontSize=10, 
            textColor=colors.HexColor('#666666'), 
            alignment=TA_CENTER, 
            spaceAfter=16
        )
        
        story = []
        
        # Title
        story.append(Paragraph("📦 Aquanimity SuperWater - Inventory Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        story.append(Paragraph(f"Total Products: {products.count()}", subtitle_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Summary
        total_stock_value = sum(float(p.price) * p.stock_quantity for p in products)
        total_stock = sum(p.stock_quantity for p in products)
        
        # Calculate total inventory and inventory value
        total_inventory = 0
        total_inventory_value = 0
        for product in products:
            inventory_total = Inventory.objects.filter(product=product).aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            total_inventory += inventory_total
            total_inventory_value += float(product.price) * inventory_total
        
        in_stock = products.filter(stock_quantity__gt=20).count()
        low_stock = products.filter(stock_quantity__gte=1, stock_quantity__lte=20).count()
        out_of_stock = products.filter(stock_quantity=0).count()
        
        summary_data = [
            ['📊 INVENTORY SUMMARY', ''],
            ['Total Products', str(products.count())],
            ['Total Stock Quantity', str(total_stock)],
            ['Total Inventory Stock', str(total_inventory)],
            ['Total Inventory Value', f"৳ {total_inventory_value:.2f}"],  # 👈 Added
            ['Total Stock Value', f"৳ {total_stock_value:.2f}"],
            ['In Stock (20+)', str(in_stock)],
            ['Low Stock (1-20)', str(low_stock)],
            ['Out of Stock', str(out_of_stock)],
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 1), (-1, -1), 1, colors.HexColor('#ddd')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#eaf2f8')),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#eaf2f8')),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Table - Added "Inventory Value" column
        table_data = [
            ['Sl', 'Product Name', 'Price (৳)', 'Stock', 'Inventory', 'Inventory Value (৳)', 'Stock Value (৳)', 'Status']
        ]
        
        for idx, product in enumerate(products[:100], 1):
            # Calculate inventory total
            inventory_total = Inventory.objects.filter(product=product).aggregate(
                total=models.Sum('quantity')
            )['total'] or 0
            
            # Calculate inventory value
            inventory_value = float(product.price) * inventory_total
            
            stock_value = float(product.price) * product.stock_quantity
            
            if product.stock_quantity > 20:
                status = 'In Stock'
            elif product.stock_quantity > 0:
                status = 'Low Stock'
            else:
                status = 'Out of Stock'
            
            table_data.append([
                str(idx),
                product.name[:25] + ('...' if len(product.name) > 25 else ''),
                f"{float(product.price):.2f}",
                str(product.stock_quantity),
                str(inventory_total),
                f"{inventory_value:.2f}",  # 👈 Inventory Value column
                f"{stock_value:.2f}",
                status
            ])
        
        if products.count() > 100:
            table_data.append(['...', f'... and {products.count() - 100} more products', '', '', '', '', '', ''])
        
        # Updated column widths with new column
        table = Table(table_data, colWidths=[0.4*inch, 1.8*inch, 0.7*inch, 0.5*inch, 0.6*inch, 0.9*inch, 0.9*inch, 0.7*inch])
        
        # Apply table styles
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 2),
        ])
        
        # Color coding for status column (column index 7)
        for row_idx in range(1, len(table_data)):
            if len(table_data[row_idx]) > 7:
                status = table_data[row_idx][7]
                if status == 'In Stock':
                    table_style.add('BACKGROUND', (7, row_idx), (7, row_idx), colors.HexColor('#d4edda'))
                    table_style.add('TEXTCOLOR', (7, row_idx), (7, row_idx), colors.HexColor('#155724'))
                elif status == 'Low Stock':
                    table_style.add('BACKGROUND', (7, row_idx), (7, row_idx), colors.HexColor('#fff3cd'))
                    table_style.add('TEXTCOLOR', (7, row_idx), (7, row_idx), colors.HexColor('#856404'))
                else:
                    table_style.add('BACKGROUND', (7, row_idx), (7, row_idx), colors.HexColor('#f8d7da'))
                    table_style.add('TEXTCOLOR', (7, row_idx), (7, row_idx), colors.HexColor('#721c24'))
        
        # Highlight Inventory Value column (index 5)
        for row_idx in range(1, len(table_data)):
            if len(table_data[row_idx]) > 5:
                table_style.add('TEXTCOLOR', (5, row_idx), (5, row_idx), colors.HexColor('#6f42c1'))
                table_style.add('FONTNAME', (5, row_idx), (5, row_idx), 'Helvetica-Bold')
        
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'FooterStyle', 
            parent=styles['Normal'], 
            fontSize=9, 
            textColor=colors.HexColor('#999999'), 
            alignment=TA_CENTER
        )
        story.append(Paragraph("© 2026 Aquanimity Super Water. All rights reserved.", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        response.write(buffer.getvalue())
        return response
        
    except Exception as e:
        print(f"❌ PDF Export Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
    
# ============================================
# CUSTOMER MANAGEMENT VIEWS
# ============================================

from water_app.models import Customer, Order

@staff_member_required
def admin_customers(request):
    """Admin Customers Management Page"""
    customers = Customer.objects.all().order_by('-created_at')
    
    customers_json = []
    total_revenue = 0
    total_orders = 0
    
    for customer in customers:
        # Get customer orders
        orders = Order.objects.filter(customer_email=customer.email)
        order_count = orders.count()
        total_spent = sum(float(o.total_amount) for o in orders)
        
        total_revenue += total_spent
        total_orders += order_count
        
        customers_json.append({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'district': customer.district,
            'is_active': customer.is_active,
            'is_diabetic': customer.is_diabetic,
            'diabetes_type': customer.diabetes_type,
            'has_high_blood_pressure': customer.has_high_blood_pressure,
            'blood_pressure_status': customer.blood_pressure_status,
            'order_count': order_count,
            'total_spent': total_spent,
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
        })
    
    context = {
        'active_page': 'admin_customers',
        'customers': customers,
        'customers_json': json.dumps(customers_json),
        'total_customers': customers.count(),
        'active_customers': customers.filter(is_active=True).count(),
        'inactive_customers': customers.filter(is_active=False).count(),
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': Product.objects.count(),
        'total_districts': DistrictDeliveryCharge.objects.count(),
    }
    return render(request, 'admin_customer.html', context)


@staff_member_required
def get_customers(request):
    """Get customers as JSON"""
    customers = Customer.objects.all().order_by('-created_at')
    data = []
    for customer in customers:
        orders = Order.objects.filter(customer_email=customer.email)
        data.append({
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'district': customer.district,
            'is_active': customer.is_active,
            'is_diabetic': customer.is_diabetic,
            'diabetes_type': customer.diabetes_type,
            'has_high_blood_pressure': customer.has_high_blood_pressure,
            'blood_pressure_status': customer.blood_pressure_status,
            'order_count': orders.count(),
            'total_spent': sum(float(o.total_amount) for o in orders),
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
        })
    return JsonResponse(data, safe=False)


@staff_member_required
def get_customer_detail(request, customer_id):
    """Get single customer detail as JSON"""
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        orders = Order.objects.filter(customer_email=customer.email).order_by('-created_at')
        
        data = {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'district': customer.district,
            'is_active': customer.is_active,
            'is_diabetic': customer.is_diabetic,
            'diabetes_type': customer.diabetes_type,
            'has_high_blood_pressure': customer.has_high_blood_pressure,
            'blood_pressure_status': customer.blood_pressure_status,
            'order_count': orders.count(),
            'total_spent': sum(float(o.total_amount) for o in orders),
            'created_at': customer.created_at.isoformat() if customer.created_at else None,
            'orders': [
                {
                    'order_id': o.order_id,
                    'total_amount': float(o.total_amount),
                    'status': o.status,
                    'status_display': o.get_status_display(),
                    'created_at': o.created_at.isoformat() if o.created_at else None,
                    'items_count': o.get_total_items(),
                }
                for o in orders[:10]
            ]
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def create_customer(request):
    """Create a new customer"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()
        district = data.get('district', '').strip()
        is_active = data.get('is_active', True)
        is_diabetic = data.get('is_diabetic', False)
        diabetes_type = data.get('diabetes_type', 'none')
        has_high_blood_pressure = data.get('has_high_blood_pressure', False)
        blood_pressure_status = data.get('blood_pressure_status', 'normal')
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'Name is required'}, status=400)
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Email is required'}, status=400)
        
        # Check if customer already exists
        if Customer.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'Customer with this email already exists'}, status=400)
        
        customer = Customer.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address,
            district=district,
            is_active=is_active,
            is_diabetic=is_diabetic,
            diabetes_type=diabetes_type,
            has_high_blood_pressure=has_high_blood_pressure,
            blood_pressure_status=blood_pressure_status,
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Customer created successfully',
            'customer_id': customer.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def update_customer(request, customer_id):
    """Update an existing customer"""
    if request.method not in ['PUT', 'POST']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        data = json.loads(request.body)
        
        customer.name = data.get('name', customer.name).strip()
        customer.email = data.get('email', customer.email).strip()
        customer.phone = data.get('phone', customer.phone).strip()
        customer.address = data.get('address', customer.address).strip()
        customer.district = data.get('district', customer.district).strip()
        customer.is_active = data.get('is_active', customer.is_active)
        customer.is_diabetic = data.get('is_diabetic', customer.is_diabetic)
        customer.diabetes_type = data.get('diabetes_type', customer.diabetes_type)
        customer.has_high_blood_pressure = data.get('has_high_blood_pressure', customer.has_high_blood_pressure)
        customer.blood_pressure_status = data.get('blood_pressure_status', customer.blood_pressure_status)
        customer.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Customer updated successfully',
            'customer_id': customer.id
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def delete_customer(request, customer_id):
    """Delete a customer"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        customer.delete()
        return JsonResponse({'status': 'success', 'message': 'Customer deleted successfully'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@staff_member_required
def get_customer_orders(request, customer_id):
    """Get customer orders"""
    try:
        customer = get_object_or_404(Customer, id=customer_id)
        orders = Order.objects.filter(customer_email=customer.email).order_by('-created_at')
        
        data = [{
            'order_id': o.order_id,
            'total_amount': float(o.total_amount),
            'status': o.status,
            'status_display': o.get_status_display(),
            'payment_status': o.payment_status,
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'items_count': o.get_total_items(),
            'items': [
                {
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'total_price': float(item.total_price),
                }
                for item in o.order_items.all()
            ]
        } for o in orders]
        
        return JsonResponse({
            'status': 'success',
            'customer_name': customer.name,
            'orders': data,
            'total_orders': orders.count(),
            'total_spent': sum(float(o.total_amount) for o in orders)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    

# ============================================
# CUSTOMER EXPORT VIEWS
# ============================================



@staff_member_required
def export_customers_excel(request):
    """
    Export all customers to Excel file
    """
    try:
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Customers"

        # Define headers
        headers = [
            'ID', 'Name', 'Email', 'Phone', 'Address', 'District', 
            'Status', 'Diabetes', 'Diabetes Type', 'Blood Pressure',
            'BP Status', 'Order Count', 'Total Spent', 'Created At'
        ]

        # Style for header
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        border = Border(
            left=Side(style='thin', color='CCCCCC'),
            right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'),
            bottom=Side(style='thin', color='CCCCCC')
        )

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border

        # Get customers with order data
        customers = Customer.objects.all().order_by('-created_at')
        
        # Write data
        for row_idx, customer in enumerate(customers, 2):
            # Get customer orders
            orders = Order.objects.filter(customer_email=customer.email)
            order_count = orders.count()
            total_spent = sum(float(o.total_amount) for o in orders)
            
            row_data = [
                customer.id,
                customer.name,
                customer.email,
                customer.phone or '',
                customer.address or '',
                customer.district or '',
                'Active' if customer.is_active else 'Inactive',
                'Yes' if customer.is_diabetic else 'No',
                customer.diabetes_type or 'none',
                'Yes' if customer.has_high_blood_pressure else 'No',
                customer.blood_pressure_status or 'normal',
                order_count,
                f"{total_spent:.2f}",
                customer.created_at.strftime('%Y-%m-%d %H:%M') if customer.created_at else ''
            ]

            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.alignment = Alignment(horizontal="left", vertical="center")
                cell.border = border

        # Auto-adjust column widths
        for col in range(1, len(headers) + 1):
            column_letter = get_column_letter(col)
            max_length = 0
            for row in range(1, ws.max_row + 1):
                cell_value = ws.cell(row=row, column=col).value
                if cell_value:
                    length = len(str(cell_value))
                    if length > max_length:
                        max_length = length
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Freeze header row
        ws.freeze_panes = 'A2'

        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=customers_export_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        
        wb.save(response)
        return response

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to export customers to Excel: {str(e)}'
        }, status=500)


@staff_member_required
def export_customers_pdf(request):
    """
    Export all customers to PDF file
    """
    try:
        # Create buffer for PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Get customers with order data
        customers = Customer.objects.all().order_by('-created_at')
        
        # Calculate totals
        total_customers = customers.count()
        total_orders = 0
        total_revenue = 0
        
        customer_data = []
        for customer in customers:
            orders = Order.objects.filter(customer_email=customer.email)
            order_count = orders.count()
            total_spent = sum(float(o.total_amount) for o in orders)
            total_orders += order_count
            total_revenue += total_spent
            
            customer_data.append({
                'customer': customer,
                'order_count': order_count,
                'total_spent': total_spent
            })

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        cell_style = ParagraphStyle(
            'CellStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            leading=10
        )

        # Build story
        story = []
        
        # Title
        story.append(Paragraph("Customer Report", title_style))
        story.append(Spacer(1, 10))
        
        # Summary
        summary_style = ParagraphStyle(
            'SummaryStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#34495E'),
            alignment=TA_LEFT,
            spaceAfter=8
        )
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", summary_style))
        story.append(Paragraph(f"Total Customers: {total_customers}", summary_style))
        story.append(Paragraph(f"Total Orders: {total_orders}", summary_style))
        story.append(Paragraph(f"Total Revenue: ৳{total_revenue:,.2f}", summary_style))
        story.append(Spacer(1, 15))

        # Prepare table data
        headers = [
            'ID', 'Name', 'Email', 'Phone', 'District', 
            'Status', 'Diabetes', 'BP', 'Orders', 'Total Spent', 'Created'
        ]
        
        table_data = [headers]
        
        for data in customer_data:
            customer = data['customer']
            row = [
                str(customer.id),
                customer.name[:25] if customer.name else '',
                customer.email[:25] if customer.email else '',
                customer.phone or '',
                customer.district or '',
                'Active' if customer.is_active else 'Inactive',
                'Diabetic' if customer.is_diabetic else 'Normal',
                'High BP' if customer.has_high_blood_pressure else 'Normal',
                str(data['order_count']),
                f"৳{data['total_spent']:.2f}",
                customer.created_at.strftime('%Y-%m-%d') if customer.created_at else ''
            ]
            table_data.append(row)

        # Create table
        table = Table(table_data, repeatRows=1)
        
        # Table style
        table_style = TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            
            # Alternate row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
        ])
        
        # Column widths
        col_widths = [
            0.4*inch, 0.9*inch, 1.7*inch, 1.0*inch, 
            0.6*inch, 0.5*inch, 0.6*inch, 0.5*inch,
            0.5*inch, 0.8*inch, 0.7*inch
        ]
        table._argW = col_widths
        
        table.setStyle(table_style)
        story.append(table)
        
        # Footer
        story.append(Spacer(1, 15))
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7F8C8D'),
            alignment=TA_CENTER
        )
        story.append(Paragraph("Generated by SuperWater Admin Panel", footer_style))

        # Build PDF
        doc.build(story)
        buffer.seek(0)

        # Create response
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=customers_export_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        return response

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': f'Failed to export customers to PDF: {str(e)}'
        }, status=500)