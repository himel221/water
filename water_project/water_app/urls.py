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
]