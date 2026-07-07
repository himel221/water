import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from .models import DistrictDeliveryCharge, Product


class CheckoutTests(TestCase):
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
