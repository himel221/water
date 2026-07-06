from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from .models import Product, DistrictDeliveryCharge, Order, OrderItem
import csv
import io
from datetime import datetime

# ReportLab Import
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("⚠️ ReportLab not installed. Please install: pip install reportlab")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name', 
        'category',
        'price',
        'stock_quantity', 
        'discount_price',
        'discount_percentage',
        'is_on_sale', 
        'special_offer_display',
        'is_eligible_for_offer',
        'is_active'
    ]
    list_filter = ['category', 'is_active', 'is_on_sale']
    search_fields = ['name', 'description', 'special_offer']
    list_editable = ['price', 'stock_quantity', 'discount_price', 'is_on_sale', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'benefits')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'stock_quantity', 'discount_price', 'discount_percentage', 'is_on_sale'),
        }),
        ('Special Offer', {
            'fields': ('special_offer',),
        }),
        ('Ratings & Media', {
            'fields': ('rating', 'reviews', 'image'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    def special_offer_display(self, obj):
        if obj.special_offer:
            return mark_safe(
                f'<span style="background: #fff3cd; color: #856404; padding: 2px 10px; border-radius: 12px; font-size: 12px;">🎉 {obj.special_offer}</span>'
            )
        return '-'
    special_offer_display.short_description = 'Special Offer'
    
    def is_eligible_for_offer(self, obj):
        if obj.special_offer and obj.is_on_sale:
            return mark_safe(
                '<span style="background: #28a745; color: white; padding: 2px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">✅ Eligible</span>'
            )
        elif obj.special_offer and not obj.is_on_sale:
            return mark_safe(
                '<span style="background: #ffc107; color: #856404; padding: 2px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">⚠️ Offer not active</span>'
            )
        else:
            return mark_safe(
                '<span style="background: #dc3545; color: white; padding: 2px 12px; border-radius: 12px; font-size: 12px;">❌ Not Eligible</span>'
            )
    is_eligible_for_offer.short_description = 'Offer Eligibility'


@admin.register(DistrictDeliveryCharge)
class DistrictDeliveryChargeAdmin(admin.ModelAdmin):
    list_display = ['district_name', 'district', 'charge', 'delivery_time', 'is_active']
    list_filter = ['is_active', 'district']
    search_fields = ['district_name', 'district']
    list_editable = ['charge', 'delivery_time', 'is_active']
    readonly_fields = ['created_at', 'updated_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    
    fields = [
        'product_name', 
        'quantity', 
        'product_price_display', 
        'original_price_display', 
        'discount_percentage_display',
        'discount_amount_display',
        'special_offer_display',
        'offer_eligibility_status',
        'total_price_display'
    ]
    
    readonly_fields = [
        'product_name', 
        'quantity', 
        'product_price_display', 
        'original_price_display', 
        'discount_percentage_display',
        'discount_amount_display',
        'special_offer_display',
        'offer_eligibility_status',
        'total_price_display'
    ]
    
    def product_price_display(self, obj):
        if obj.product_price is not None:
            return mark_safe(f'৳ {float(obj.product_price):.2f}')
        return '৳ 0.00'
    product_price_display.short_description = 'Price'
    
    def original_price_display(self, obj):
        if obj.original_price and obj.original_price > 0:
            return mark_safe(
                f'<span style="text-decoration: line-through; color: #999;">৳ {float(obj.original_price):.2f}</span>'
            )
        return '-'
    original_price_display.short_description = 'Original Price'
    
    def discount_percentage_display(self, obj):
        if obj.discount_percentage > 0:
            return mark_safe(
                f'<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{obj.discount_percentage}% OFF</span>'
            )
        return '-'
    discount_percentage_display.short_description = 'Discount %'
    
    def discount_amount_display(self, obj):
        if obj.original_price and obj.original_price > obj.product_price:
            discount_amount = float(obj.original_price) - float(obj.product_price)
            return mark_safe(
                f'<span style="color: #27ae60; font-weight: 600;">-৳ {discount_amount:.2f}</span>'
            )
        return '-'
    discount_amount_display.short_description = 'Discount Amount'
    
    def total_price_display(self, obj):
        if obj.total_price is not None:
            return mark_safe(
                f'<span style="font-weight: 700; color: #007bff;">৳ {float(obj.total_price):.2f}</span>'
            )
        return '৳ 0.00'
    total_price_display.short_description = 'Total'
    
    def special_offer_display(self, obj):
        if obj.special_offer:
            return mark_safe(
                f'<span style="background: #fff3cd; color: #856404; padding: 2px 8px; border-radius: 10px; font-size: 11px;">🎉 {obj.special_offer}</span>'
            )
        return '-'
    special_offer_display.short_description = 'Special Offer'
    
    def offer_eligibility_status(self, obj):
        if not obj.special_offer:
            return mark_safe(
                '<span style="color: #999; font-size: 11px;">❌ No Offer</span>'
            )
        try:
            order = obj.order
            requirements = order.parse_offer_requirements(obj.special_offer)
            is_eligible = False
            
            if requirements['offer_type'] == 'free_shipping':
                is_eligible = True
            elif requirements['offer_type'] == 'buy_x_get_y_free':
                is_eligible = obj.quantity >= requirements.get('min_quantity', 2)
            elif requirements['offer_type'] == 'percent_off':
                is_eligible = obj.quantity >= requirements.get('min_quantity', 1)
            elif requirements['offer_type'] == 'amount_off':
                total_price = obj.product_price * obj.quantity
                is_eligible = total_price >= requirements.get('min_amount', 0)
            elif requirements['offer_type'] == 'combo':
                is_eligible = obj.quantity >= requirements.get('min_quantity', 1)
            elif requirements['offer_type'] == 'flat_discount':
                is_eligible = True
            else:
                is_eligible = obj.quantity > 1
            
            if is_eligible:
                return mark_safe(
                    '<span style="background: #28a745; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600;">✅ Eligible</span>'
                )
            else:
                return mark_safe(
                    '<span style="background: #ffc107; color: #856404; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600;">⚠️ Not Eligible</span>'
                )
        except:
            return mark_safe(
                '<span style="color: #999; font-size: 11px;">❌ Error</span>'
            )
    offer_eligibility_status.short_description = 'Offer Eligible'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]
    
    list_display = [
        'order_id', 
        'customer_name', 
        'customer_district', 
        'get_total_items',
        'get_product_names',
        'total_amount_display',
        'total_savings_display',
        'total_discount_display',
        'special_offers_short',
        'offer_eligibility_status',
        'status', 
        'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_id', 'customer_name', 'customer_email', 'customer_phone', 'customer_district']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    list_editable = ['status']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'status', 'payment_status', 'payment_method')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address', 'customer_district')
        }),
        ('Delivery Details', {
            'fields': ('delivery_zone', 'delivery_charge')
        }),
        ('Order Summary', {
            'fields': ('subtotal', 'total_savings', 'total_amount'),
            'classes': ('wide',)
        }),
        ('Products & Discounts', {
            'fields': ('products_discounts_display',),
            'classes': ('wide',)
        }),
        ('Special Offers', {
            'fields': ('special_offers_display',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
    def get_product_names(self, obj):
        """Show product names with quantities and discounts"""
        products = []
        for item in obj.order_items.all():
            discount_text = f"({item.discount_percentage}%)" if item.discount_percentage > 0 else ''
            products.append(f"{item.product_name} x{item.quantity}{discount_text}")
        return mark_safe(
            f'<span style="font-size: 12px;">{", ".join(products[:3])}{"..." if len(products) > 3 else ""}</span>'
        )
    get_product_names.short_description = 'Products (Qty x Discount)'
    
    def products_discounts_display(self, obj):
        """Show all products with discounts in detail view"""
        html = '<div style="background: #f8f9fa; padding: 12px; border-radius: 8px;">'
        for item in obj.order_items.all():
            discount_percent = f"{item.discount_percentage}%" if item.discount_percentage > 0 else '0%'
            discount_amount = float(item.original_price) - float(item.product_price) if item.original_price and item.original_price > item.product_price else 0
            
            html += f'''
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #eee;">
                    <span><strong>{item.product_name}</strong> x {item.quantity}</span>
                    <span>
                        ৳{float(item.product_price):.2f} 
                        <span style="color: #999; text-decoration: line-through;">৳{float(item.original_price):.2f}</span>
                        <span style="color: #dc3545; font-weight: 600;">(-{discount_percent})</span>
                        <span style="color: #27ae60; font-weight: 600;">Save ৳{discount_amount:.2f}</span>
                    </span>
                </div>
            '''
        html += '</div>'
        return mark_safe(html)
    products_discounts_display.short_description = 'Products & Discounts'
    
    def total_discount_display(self, obj):
        """Calculate total discount for the order"""
        total_discount = 0
        for item in obj.order_items.all():
            if item.original_price and item.original_price > item.product_price:
                total_discount += (float(item.original_price) - float(item.product_price)) * item.quantity
        if total_discount > 0:
            return mark_safe(
                f'<span style="font-weight: 700; color: #dc3545;">-৳ {total_discount:.2f}</span>'
            )
        return '৳ 0.00'
    total_discount_display.short_description = 'Total Discount'
    
    def total_amount_display(self, obj):
        if obj.total_amount is not None:
            amount = float(obj.total_amount)
            return mark_safe(
                f'৳ <span style="font-weight: 700; color: #007bff;">{amount:.2f}</span>'
            )
        return '৳ 0.00'
    total_amount_display.short_description = 'Total Amount'
    total_amount_display.admin_order_field = 'total_amount'
    
    def total_savings_display(self, obj):
        if obj.total_savings and obj.total_savings > 0:
            savings = float(obj.total_savings)
            return mark_safe(
                f'৳ <span style="font-weight: 600; color: #27ae60;">{savings:.2f}</span>'
            )
        return '৳ 0.00'
    total_savings_display.short_description = 'Total Savings'
    total_savings_display.admin_order_field = 'total_savings'
    
    def special_offers_short(self, obj):
        offers = []
        for item in obj.order_items.all():
            if item.special_offer:
                offers.append(f"🎉{item.special_offer}")
        if offers:
            return mark_safe(
                f'<span style="background: #fff3cd; color: #856404; padding: 2px 8px; border-radius: 10px; font-size: 11px; display: inline-block; margin: 2px 0;">{" ".join(offers[:2])}{"..." if len(offers) > 2 else ""}</span>'
            )
        return '-'
    special_offers_short.short_description = 'Special Offers'
    
    def special_offers_display(self, obj):
        offers = []
        for item in obj.order_items.all():
            if item.special_offer:
                offers.append(
                    f'<div style="background: #fff3cd; color: #856404; padding: 4px 12px; border-radius: 8px; margin: 2px 0; border-left: 3px solid #f39c12;">'
                    f'<strong>{item.product_name}</strong>: 🎉 {item.special_offer}'
                    f'</div>'
                )
        if offers:
            return mark_safe('<br>'.join(offers))
        return mark_safe('<span style="color: #999;">No special offers applied</span>')
    special_offers_display.short_description = 'Special Offers Applied'
    
    def offer_eligibility_status(self, obj):
        try:
            if obj.is_eligible_for_offer():
                return mark_safe(
                    '<div style="text-align: center;">'
                    '<span style="background: #28a745; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; display: inline-block;">✅ Eligible</span>'
                    '<br>'
                    '<span style="font-size: 9px; color: #28a745; font-weight: 500;">Requirements met</span>'
                    '</div>'
                )
            else:
                has_offer = any(item.special_offer for item in obj.order_items.all())
                if has_offer:
                    return mark_safe(
                        '<div style="text-align: center;">'
                        '<span style="background: #ffc107; color: #856404; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; display: inline-block;">⚠️ Not Eligible</span>'
                        '<br>'
                        '<span style="font-size: 9px; color: #856404; font-weight: 500;">Requirements not met</span>'
                        '</div>'
                    )
                else:
                    return mark_safe(
                        '<div style="text-align: center;">'
                        '<span style="background: #dc3545; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; display: inline-block;">❌ Not Eligible</span>'
                        '<br>'
                        '<span style="font-size: 9px; color: #dc3545; font-weight: 500;">No special offer</span>'
                        '</div>'
                    )
        except:
            return mark_safe(
                '<div style="text-align: center;">'
                '<span style="background: #dc3545; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; display: inline-block;">❌ Not Eligible</span>'
                '<br>'
                '<span style="font-size: 9px; color: #dc3545; font-weight: 500;">Error</span>'
                '</div>'
            )
    offer_eligibility_status.short_description = 'Offer Status'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['order_id', 'created_at', 'updated_at', 'subtotal', 'total_savings', 'total_amount']
        return self.readonly_fields
    
    actions = [
        'export_orders_csv', 
        'export_orders_pdf', 
        'mark_as_processing', 
        'mark_as_shipped', 
        'mark_as_delivered'
    ]
    
    def export_orders_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="orders_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Customer Name', 'Customer Email', 'Customer Phone',
            'Customer Address', 'District', 'Total Items', 'Products (Qty x Discount)', 
            'Subtotal', 'Total Savings', 'Total Discount', 'Total Amount', 
            'Delivery Charge', 'Payment Method', 'Status', 'Special Offers', 
            'Offer Eligibility', 'Created At'
        ])
        
        for order in queryset:
            products = []
            offers = []
            total_discount = 0
            for item in order.order_items.all():
                discount_text = f"({item.discount_percentage}%)" if item.discount_percentage > 0 else ''
                products.append(f"{item.product_name} x{item.quantity}{discount_text}")
                if item.special_offer:
                    offers.append(f"{item.product_name}: {item.special_offer}")
                if item.original_price and item.original_price > item.product_price:
                    total_discount += (float(item.original_price) - float(item.product_price)) * item.quantity
            
            products_text = '; '.join(products)
            special_offers = '; '.join(offers) if offers else 'None'
            eligibility = 'Eligible' if order.is_eligible_for_offer() else 'Not Eligible'
            
            writer.writerow([
                order.order_id,
                order.customer_name,
                order.customer_email,
                order.customer_phone or '',
                order.customer_address,
                order.customer_district or '',
                order.get_total_items(),
                products_text,
                float(order.subtotal),
                float(order.total_savings),
                total_discount,
                float(order.total_amount),
                float(order.delivery_charge),
                order.payment_method or 'Cash on Delivery',
                order.status,
                special_offers,
                eligibility,
                order.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        return response
    export_orders_csv.short_description = "📊 Export selected orders as CSV"
    
    def export_orders_pdf(self, request, queryset):
        if not REPORTLAB_AVAILABLE:
            self.message_user(request, "⚠️ ReportLab not installed. Please install: pip install reportlab")
            return
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="orders_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#007bff'),
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'SubHeadingStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        story = []
        
        story.append(Paragraph("📦 Aquanimity SuperWater - Orders Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subheading_style))
        story.append(Paragraph(f"Total Orders: {queryset.count()}", subheading_style))
        story.append(Spacer(1, 0.2*inch))
        
        total_orders_amount = sum(float(o.total_amount) for o in queryset)
        total_orders_savings = sum(float(o.total_savings) for o in queryset)
        total_discount = 0
        for order in queryset:
            for item in order.order_items.all():
                if item.original_price and item.original_price > item.product_price:
                    total_discount += (float(item.original_price) - float(item.product_price)) * item.quantity
        
        eligible_count = sum(1 for o in queryset if o.is_eligible_for_offer())
        
        summary_data = [
            ['📊 Summary Statistics', 'Value'],
            ['Total Orders', str(queryset.count())],
            ['Total Revenue', f"৳ {total_orders_amount:.2f}"],
            ['Total Savings', f"৳ {total_orders_savings:.2f}"],
            ['💰 Total Discount', f"৳ {total_discount:.2f}"],
            ['✅ Eligible Orders', str(eligible_count)],
            ['❌ Not Eligible Orders', str(queryset.count() - eligible_count)],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("📋 Order Details", heading_style))
        
        table_data = [
            ['Order ID', 'Customer', 'District', 'Items', 'Products', 'Total', 'Discount', 'Savings', 'Eligibility', 'Status']
        ]
        
        for order in queryset:
            products = []
            for item in order.order_items.all():
                discount_text = f"({item.discount_percentage}%)" if item.discount_percentage > 0 else ''
                products.append(f"{item.product_name} x{item.quantity}{discount_text}")
            products_text = ', '.join(products[:3]) + ('...' if len(products) > 3 else '')
            
            order_discount = 0
            for item in order.order_items.all():
                if item.original_price and item.original_price > item.product_price:
                    order_discount += (float(item.original_price) - float(item.product_price)) * item.quantity
            
            eligibility = '✅ Eligible' if order.is_eligible_for_offer() else '❌ Not Eligible'
            
            table_data.append([
                order.order_id,
                order.customer_name[:20] + ('...' if len(order.customer_name) > 20 else ''),
                order.customer_district or '-',
                str(order.get_total_items()),
                products_text,
                f"৳ {float(order.total_amount):.2f}",
                f"৳ {order_discount:.2f}",
                f"৳ {float(order.total_savings):.2f}",
                eligibility,
                order.status.title(),
            ])
        
        table = Table(table_data, colWidths=[1.0*inch, 1.2*inch, 0.8*inch, 0.5*inch, 1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
            ('ALIGN', (7, 1), (7, -1), 'RIGHT'),
            ('ALIGN', (8, 1), (8, -1), 'CENTER'),
            ('ALIGN', (9, 1), (9, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#999'),
            alignment=TA_CENTER
        )
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("© 2026 Aquanimity Super Water. All rights reserved.", footer_style))
        
        doc.build(story)
        buffer.seek(0)
        response.write(buffer.getvalue())
        return response
    export_orders_pdf.short_description = "📄 Export selected orders as PDF"
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = "⚙️ Mark as Processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "🚚 Mark as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = "✅ Mark as Delivered"