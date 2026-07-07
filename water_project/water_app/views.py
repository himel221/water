from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Product, DistrictDeliveryCharge, Order, OrderItem
import json
import io
from decimal import Decimal
from datetime import datetime, timedelta

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
        
        items_data = data.get('items', [])
        subtotal = 0
        total_savings = 0
        total_discount = 0
        
        for item in items_data:
            price = float(item.get('price', 0))
            original_price = float(item.get('original_price', price))
            quantity = int(item.get('quantity', 1))
            
            subtotal += original_price * quantity
            savings = (original_price - price) * quantity
            if savings > 0:
                total_savings += savings
                total_discount += savings
        
        total_amount = subtotal - total_savings + delivery_charge
        
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
            'total_discount': total_discount,
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
    """Create a new product"""
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
        
        # Validate discount price - handle empty string properly
        discount_price_value = None
        if discount_price and discount_price != '':
            try:
                discount_price_value = float(discount_price)
                if discount_price_value < 0:
                    return JsonResponse({'status': 'error', 'message': 'Discount price cannot be negative'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid discount price format'}, status=400)
        
        # Validate discount percentage - handle empty string properly
        discount_percentage_value = None
        if discount_percentage and discount_percentage != '':
            try:
                discount_percentage_value = int(discount_percentage)
                if discount_percentage_value < 0 or discount_percentage_value > 100:
                    return JsonResponse({'status': 'error', 'message': 'Discount percentage must be between 0 and 100'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid discount percentage format'}, status=400)
        
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity < 0:
                return JsonResponse({'status': 'error', 'message': 'Stock cannot be negative'}, status=400)
        except ValueError:
            stock_quantity = 0
        
        # Check if product has discount
        is_on_sale = False
        if (discount_price_value is not None and discount_price_value > 0 and discount_price_value < price) or \
           (discount_percentage_value is not None and discount_percentage_value > 0):
            is_on_sale = True
        
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
            is_on_sale=is_on_sale,  # 👈 Added this
        )
        
        # Handle image upload
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            # Validate file type
            if image_file.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                return JsonResponse({'status': 'error', 'message': 'Invalid image format. Only JPEG, PNG, GIF, WEBP allowed.'}, status=400)
            # Validate file size (2MB)
            if image_file.size > 2 * 1024 * 1024:
                return JsonResponse({'status': 'error', 'message': 'Image size must be less than 2MB'}, status=400)
            
            product.image = image_file
        
        product.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Product created successfully',
            'product_id': product.id
        })
        
    except Exception as e:
        print(f"Error creating product: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@staff_member_required
def update_product(request, product_id):
    """Update an existing product"""
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
        
        # Validate discount price - handle empty string properly
        discount_price_value = None
        if discount_price and discount_price != '':
            try:
                discount_price_value = float(discount_price)
                if discount_price_value < 0:
                    return JsonResponse({'status': 'error', 'message': 'Discount price cannot be negative'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid discount price format'}, status=400)
        
        # Validate discount percentage - handle empty string properly
        discount_percentage_value = None
        if discount_percentage and discount_percentage != '':
            try:
                discount_percentage_value = int(discount_percentage)
                if discount_percentage_value < 0 or discount_percentage_value > 100:
                    return JsonResponse({'status': 'error', 'message': 'Discount percentage must be between 0 and 100'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid discount percentage format'}, status=400)
        
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity < 0:
                return JsonResponse({'status': 'error', 'message': 'Stock cannot be negative'}, status=400)
        except ValueError:
            stock_quantity = 0
        
        # Check if product has discount
        is_on_sale = False
        if (discount_price_value is not None and discount_price_value > 0 and discount_price_value < price) or \
           (discount_percentage_value is not None and discount_percentage_value > 0):
            is_on_sale = True
        
        # Update product
        product.name = name
        product.description = description
        product.price = price
        product.discount_price = discount_price_value
        product.discount_percentage = discount_percentage_value
        product.stock_quantity = stock_quantity
        product.is_active = is_active
        product.special_offer = special_offer if special_offer else None
        product.is_on_sale = is_on_sale  # 👈 Added this
        
        # Handle image upload
        if 'image' in request.FILES:
            # Delete old image if exists
            if product.image:
                try:
                    default_storage.delete(product.image.path)
                except:
                    pass
            
            image_file = request.FILES['image']
            # Validate file type
            if image_file.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                return JsonResponse({'status': 'error', 'message': 'Invalid image format. Only JPEG, PNG, GIF, WEBP allowed.'}, status=400)
            # Validate file size (2MB)
            if image_file.size > 2 * 1024 * 1024:
                return JsonResponse({'status': 'error', 'message': 'Image size must be less than 2MB'}, status=400)
            
            product.image = image_file
        elif 'remove_image' in request.POST and request.POST.get('remove_image') == 'true':
            # Remove image
            if product.image:
                try:
                    default_storage.delete(product.image.path)
                except:
                    pass
                product.image = None
        
        product.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Product updated successfully',
            'product_id': product.id
        })
        
    except Exception as e:
        print(f"Error updating product: {str(e)}")
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