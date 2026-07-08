from django.urls import path
from . import views

urlpatterns = [
    # Page Views
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('science/', views.science, name='science'),
    path('explore/', views.explore, name='explore'),
    
    # API Views
    path('api/products/', views.product_list, name='product_list'),
    path('checkout/', views.checkout, name='checkout'),
    path('api/delivery-charges/', views.district_delivery_charges, name='delivery_charges'),
    path('api/delivery-charge/<str:district>/', views.get_delivery_charge, name='get_delivery_charge'),
    path('api/create-order/', views.create_order, name='create_order'),
    path('api/orders/', views.order_list, name='order_list'),
    path('api/invoice/<str:order_id>/', views.download_invoice, name='download_invoice'),
    path('cart/', views.cart, name='cart'),

    #Admin Views
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('api/orders/<str:order_id>/delete/', views.delete_order, name='delete_order'),
    path('api/orders/<str:order_id>/update/', views.update_order, name='update_order'),

    #  Export URLs
    path('api/orders/export/excel/', views.export_orders_excel, name='export_orders_excel'),
    path('api/orders/export/pdf/', views.export_orders_pdf, name='export_orders_pdf'),

        # ===== Admin Products =====
    path('admin-products/', views.admin_products, name='admin_products'),
    
    # ===== API - Products =====
    path('api/products/', views.get_products, name='get_products'),
    path('api/products/create/', views.create_product, name='create_product'),
    path('api/products/<int:product_id>/update/', views.update_product, name='update_product'),
    path('api/products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('api/products/<int:product_id>/toggle/', views.toggle_product_status, name='toggle_product_status'),
    path('api/products/<int:product_id>/', views.get_product_detail, name='get_product_detail'),
    path('api/products/export/excel/', views.export_products_excel, name='export_products_excel'),
    path('api/products/export/pdf/', views.export_products_pdf, name='export_products_pdf'),

    #-------------Admin Delivery_______________#
    path('admin-delivery/', views.admin_delivery, name='admin_delivery'),
    path('api/delivery/create/', views.create_district, name='create_district'),
    path('api/delivery/<int:district_id>/update/', views.update_district, name='update_district'),
    path('api/delivery/<int:district_id>/delete/', views.delete_district, name='delete_district'),
    path('api/delivery/<int:district_id>/toggle/', views.toggle_district_status, name='toggle_district_status'),
    path('api/delivery/export/excel/', views.export_districts_excel, name='export_districts_excel'),
    path('api/delivery/export/pdf/', views.export_districts_pdf, name='export_districts_pdf'),

    # Add these URLs to water_app/urls.py

    path('admin-inventory/', views.admin_inventory, name='admin_inventory'),
    path('api/inventory/<int:product_id>/add-stock/', views.add_stock, name='add_stock'),
    path('api/inventory/export/excel/', views.export_inventory_excel, name='export_inventory_excel'),
    path('api/inventory/export/pdf/', views.export_inventory_pdf, name='export_inventory_pdf'),

                    # Customer URLs
    path('customer/add/', views.customer_form, name='customer_form'),
    path('customer/success/', views.customer_success, name='customer_success'),
    path('customer/list/', views.customer_list, name='customer_list'),
    path('customer/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customer/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),
]