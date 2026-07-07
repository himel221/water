import json
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import DistrictDeliveryCharge, Order, Product


class CheckoutTests(TestCase):
    def test_order_edit_page_updates_order_details(self):
        user = User.objects.create_user(username='admin', password='pass1234', is_staff=True, is_superuser=True)
        order = Order.objects.create(
            order_id='ORD-TEST-1',
            customer_name='Rahim',
            customer_email='rahim@example.com',
            customer_address='House 1',
            customer_district='dhaka',
            subtotal=Decimal('100.00'),
            total_discount=Decimal('0.00'),
            total_amount=Decimal('100.00'),
            status='pending',
            payment_status='pending',
            payment_method='Cash on Delivery',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('edit_order', args=[order.order_id]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('edit_order', args=[order.order_id]),
            {
                'customer_name': 'Karim',
                'customer_email': 'karim@example.com',
                'customer_phone': '01711111111',
                'customer_address': 'House 2',
                'customer_district': 'dhaka',
                'status': 'processing',
                'payment_status': 'completed',
                'payment_method': 'Online',
                'delivery_charge': '50',
                'subtotal': '100',
                'total_discount': '10',
                'total_amount': '140',
            },
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.customer_name, 'Karim')
        self.assertEqual(order.status, 'processing')
        self.assertEqual(order.payment_status, 'completed')

    def test_product_percentage_discount_uses_effective_price(self):
        product = Product.objects.create(
            name='Filter',
            description='Test product',
            price=Decimal('100.00'),
            discount_percentage=20,
            is_on_sale=True,
        )

        self.assertEqual(product.get_effective_price(), Decimal('80.00'))
        self.assertEqual(product.get_discount_amount(), Decimal('20.00'))

    def test_create_order_uses_total_from_checkout_payload(self):
        DistrictDeliveryCharge.objects.create(
            district='dhaka',
            district_name='Dhaka',
            charge=50,
            delivery_time='2-3 days',
            is_active=True,
        )

        payload = {
            'customer_name': 'Rahim',
            'customer_email': 'rahim@example.com',
            'customer_phone': '01700000000',
            'customer_address': 'House 1, Road 2, Dhaka',
            'customer_district': 'dhaka',
            'delivery_charge': 50,
            'subtotal': 200,
            'total': 250,
            'items': [
                {
                    'name': 'Water Purifier',
                    'price': 200,
                    'original_price': 200,
                    'quantity': 1,
                }
            ],
        }

        response = self.client.post(
            reverse('create_order'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['order_id'])

        from .models import Order
        order = Order.objects.get(order_id=data['order_id'])
        self.assertEqual(float(order.total_amount), 250)
        self.assertEqual(float(order.subtotal), 200)
