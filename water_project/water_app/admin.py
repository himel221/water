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
            return format_html(
                '<span style="background: #fff3cd; color: #856404; padding: 2px 10px; border-radius: 12px; font-size: 12px;">🎉 {}</span>',
                obj.special_offer
            )
        return '-'
    special_offer_display.short_description = 'Special Offer'
    
    def is_eligible_for_offer(self, obj):
        if obj.special_offer and obj.is_on_sale:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">✅ Eligible</span>'
            )
        elif obj.special_offer and not obj.is_on_sale:
            return format_html(
                '<span style="background: #ffc107; color: #856404; padding: 2px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">⚠️ Offer not active</span>'
            )
        else:
            return format_html(
                '<span style="background: red; color: white; padding: 2px 12px; border-radius: 12px; font-size: 12px;">❌ Not Eligible</span>'
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
    
    # ✅ সব ফিল্ড দেখানোর জন্য
    fields = [
        'product_name', 
        'quantity', 
        'product_price', 
        'original_price', 
        'discount_percentage', 
        'special_offer',
        'offer_eligibility_status',
        'total_price'
    ]
    
    # ✅ readonly_fields এ সব ফিল্ড যোগ করুন
    readonly_fields = [
        'product_name', 
        'quantity', 
        'product_price', 
        'original_price', 
        'discount_percentage', 
        'special_offer',
        'offer_eligibility_status',
        'total_price'
    ]
    
    def offer_eligibility_status(self, obj):
        """Check if this specific order item is eligible for offer"""
        if not obj.special_offer:
            return format_html(
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
                return format_html(
                    '<span style="background: #28a745; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600;">✅ Eligible</span>'
                )
            else:
                min_qty = requirements.get('min_quantity', 2)
                return format_html(
                    '<span style="background: red; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600;">⚠️ Not Eligible</span>',
                    min_qty
                )
        except:
            return format_html(
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
        'total_amount_display',
        'total_savings_display',
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
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_items(self, obj):
        return obj.get_total_items()
    get_total_items.short_description = 'Total Items'
    
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
        """Show short version of special offers in list display"""
        offers = []
        for item in obj.order_items.all():
            if item.special_offer:
                offers.append(f"🎉{item.special_offer}")
        if offers:
            return format_html(
                '<span style="background: #fff3cd; color: #856404; padding: 2px 8px; border-radius: 10px; font-size: 11px; display: inline-block; margin: 2px 0;">{}</span>',
                ' '.join(offers[:2]) + ('...' if len(offers) > 2 else '')
            )
        return '-'
    special_offers_short.short_description = 'Special Offers'
    
    def offer_eligibility_status(self, obj):
        """Show offer eligibility status"""
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
                        '<span style="background: red; color: white; padding: 2px 10px; border-radius: 10px; font-size: 11px; font-weight: 600; display: inline-block;">⚠️ Not Eligible</span>'
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
            'Customer Address', 'District', 'Total Items', 'Subtotal', 
            'Total Savings', 'Total Amount', 'Delivery Charge', 'Payment Method',
            'Status', 'Special Offers', 'Offer Eligibility', 'Created At'
        ])
        
        for order in queryset:
            offers = []
            for item in order.order_items.all():
                if item.special_offer:
                    offers.append(f"{item.product_name}: {item.special_offer}")
            special_offers = '; '.join(offers) if offers else 'None'
            
            if order.is_eligible_for_offer():
                eligibility = '✅ Eligible'
            else:
                eligibility = '❌ Not Eligible'
            
            writer.writerow([
                order.order_id,
                order.customer_name,
                order.customer_email,
                order.customer_phone or '',
                order.customer_address,
                order.customer_district or '',
                order.get_total_items(),
                float(order.subtotal),
                float(order.total_savings),
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
        
        eligible_orders = []
        non_eligible_orders = []
        
        for order in queryset:
            if order.is_eligible_for_offer():
                eligible_orders.append(order)
            else:
                non_eligible_orders.append(order)
        
        total_eligible = len(eligible_orders)
        total_non_eligible = len(non_eligible_orders)
        
        summary_data = [
            ['📊 Summary Statistics', 'Value'],
            ['Total Orders', str(queryset.count())],
            ['Total Revenue', f"৳ {total_orders_amount:.2f}"],
            ['Total Savings', f"৳ {total_orders_savings:.2f}"],
            ['✅ Eligible Orders', str(total_eligible)],
            ['❌ Not Eligible Orders', str(total_non_eligible)],
            ['Pending Orders', str(queryset.filter(status='pending').count())],
            ['Processing', str(queryset.filter(status='processing').count())],
            ['Shipped', str(queryset.filter(status='shipped').count())],
            ['Delivered', str(queryset.filter(status='delivered').count())],
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
            ['Order ID', 'Customer', 'District', 'Items', 'Subtotal', 'Savings', 'Total', 'Eligibility', 'Status', 'Date']
        ]
        
        for order in queryset:
            if order.is_eligible_for_offer():
                eligibility = '✅ Eligible'
            else:
                eligibility = '❌ Not Eligible'
            
            table_data.append([
                order.order_id,
                order.customer_name[:20] + ('...' if len(order.customer_name) > 20 else ''),
                order.customer_district or '-',
                str(order.get_total_items()),
                f"৳ {float(order.subtotal):.2f}",
                f"৳ {float(order.total_savings):.2f}",
                f"৳ {float(order.total_amount):.2f}",
                eligibility,
                order.status.title(),
                order.created_at.strftime('%d/%m/%Y')
            ])
        
        table = Table(table_data, colWidths=[1.9*inch, 1.2*inch, 0.8*inch, 0.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.8*inch, 0.8*inch])
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
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
            ('ALIGN', (7, 1), (7, -1), 'CENTER'),
            ('ALIGN', (8, 1), (8, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("🎯 Eligible Offer Orders Details (Summary)", heading_style))
        
        if eligible_orders:
            for order in eligible_orders[:10]:
                offers = []
                for item in order.order_items.all():
                    if item.special_offer:
                        offers.append(f"• {item.product_name}: 🎉 {item.special_offer}")
                if offers:
                    offer_text = f"<b>Order {order.order_id}</b> - {order.customer_name}<br/>" + '<br/>'.join(offers)
                    story.append(Paragraph(offer_text, styles['Normal']))
                    story.append(Spacer(1, 0.05*inch))
        else:
            story.append(Paragraph("No eligible orders found.", styles['Normal']))
        
        if non_eligible_orders:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("❌ Not Eligible Offer Orders Details (Summary)", heading_style))
            for order in non_eligible_orders[:5]:
                story.append(Paragraph(
                    f"<b>{order.order_id}</b> - {order.customer_name}",
                    styles['Normal']
                ))
            if len(non_eligible_orders) > 5:
                story.append(Paragraph(f"... and {len(non_eligible_orders) - 5} more Not Eligible orders", styles['Normal']))
        
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