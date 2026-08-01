"""Tests for the orders app: cart, checkout, pricing and stock handling."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalog.tests import make_wine
from orders import pricing
from orders.models import Cart, CartItem, Order, OrderItem

CHECKOUT_DATA = {
    'last_name': 'Шевченко',
    'first_name': 'Іван',
    'phone_number': '+380501234567',
    'shipping_address': 'вул. Хрещатик, 1',
    'shipping_city': 'Київ',
    'shipping_country': 'Україна',
    'shipping_postal_code': 'Відділення №1',
}


class PricingTests(TestCase):
    def test_tax_is_ten_percent_rounded_to_cents(self):
        self.assertEqual(pricing.tax_for(Decimal('100')), Decimal('10.00'))
        self.assertEqual(pricing.tax_for(Decimal('333.33')), Decimal('33.33'))

    def test_shipping_is_charged_below_the_threshold(self):
        self.assertEqual(pricing.shipping_for(Decimal('1999.99')), Decimal('150.00'))

    def test_shipping_is_free_at_and_above_the_threshold(self):
        self.assertEqual(pricing.shipping_for(Decimal('2000')), Decimal('0.00'))
        self.assertEqual(pricing.shipping_for(Decimal('5000')), Decimal('0.00'))

    def test_total_combines_subtotal_tax_and_shipping(self):
        self.assertEqual(pricing.total_for(Decimal('1000')), Decimal('1250.00'))
        self.assertEqual(pricing.total_for(Decimal('2000')), Decimal('2200.00'))


class CartModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine(price=Decimal('200.00'), stock_quantity=50)

    def test_cart_is_created_automatically_for_every_new_user(self):
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

    def test_totals_of_an_empty_cart(self):
        self.assertEqual(self.user.cart.get_total_price(), 0)
        self.assertEqual(self.user.cart.get_total_items(), 0)

    def test_cart_item_total_multiplies_price_by_quantity(self):
        item = CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=3)

        self.assertEqual(item.get_total_price(), Decimal('600.00'))

    def test_cart_totals_sum_every_item(self):
        other = make_wine(name='Other', price=Decimal('50.00'))
        CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=2)
        CartItem.objects.create(cart=self.user.cart, wine=other, quantity=4)

        self.assertEqual(self.user.cart.get_total_price(), Decimal('600.00'))
        self.assertEqual(self.user.cart.get_total_items(), 6)

    def test_clear_removes_every_item(self):
        CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=2)

        self.user.cart.clear()

        self.assertEqual(self.user.cart.items.count(), 0)

    def test_the_same_wine_cannot_be_added_twice(self):
        from django.db import IntegrityError

        CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=1)

        with self.assertRaises(IntegrityError):
            CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=1)


class OrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine(price=Decimal('500.00'), stock_quantity=100)

    def _order(self):
        return Order.objects.create(
            user=self.user,
            shipping_address='вул. Хрещатик, 1',
            shipping_city='Київ',
            shipping_country='Україна',
            shipping_postal_code='01001',
            phone_number='+380501234567',
        )

    def test_order_number_is_generated(self):
        order = self._order()

        self.assertTrue(order.order_number.startswith('ORD-'))
        self.assertEqual(len(order.order_number), 14)

    def test_order_numbers_are_unique(self):
        self.assertNotEqual(self._order().order_number, self._order().order_number)

    def test_order_number_is_kept_on_update(self):
        order = self._order()
        original = order.order_number

        order.status = 'shipped'
        order.save()

        self.assertEqual(order.order_number, original)

    def test_recipient_full_name_without_patronymic(self):
        order = self._order()
        order.last_name, order.first_name = 'Шевченко', 'Іван'

        self.assertEqual(order.recipient_full_name, 'Шевченко Іван')

    def test_recipient_full_name_with_patronymic(self):
        order = self._order()
        order.last_name, order.first_name = 'Шевченко', 'Іван'
        order.patronymic = 'Петрович'

        self.assertEqual(order.recipient_full_name, 'Шевченко Іван Петрович')

    def test_order_item_total(self):
        order = self._order()
        item = OrderItem.objects.create(
            order=order, wine=self.wine, quantity=3, price=Decimal('500.00')
        )

        self.assertEqual(item.get_total_price(), Decimal('1500.00'))

    def test_calculate_totals_charges_shipping_below_the_threshold(self):
        order = self._order()
        OrderItem.objects.create(
            order=order, wine=self.wine, quantity=2, price=Decimal('500.00')
        )

        order.calculate_totals()

        self.assertEqual(order.subtotal, Decimal('1000.00'))
        self.assertEqual(order.tax, Decimal('100.00'))
        self.assertEqual(order.shipping_cost, Decimal('150.00'))
        self.assertEqual(order.total, Decimal('1250.00'))

    def test_calculate_totals_gives_free_shipping_above_the_threshold(self):
        order = self._order()
        OrderItem.objects.create(
            order=order, wine=self.wine, quantity=4, price=Decimal('500.00')
        )

        order.calculate_totals()

        self.assertEqual(order.subtotal, Decimal('2000.00'))
        self.assertEqual(order.shipping_cost, Decimal('0.00'))
        self.assertEqual(order.total, Decimal('2200.00'))

    def test_calculate_totals_on_an_order_without_items(self):
        order = self._order()

        order.calculate_totals()

        self.assertEqual(order.subtotal, Decimal('0.00'))
        self.assertEqual(order.total, Decimal('150.00'))


class StockSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine(stock_quantity=10)
        self.order = Order.objects.create(
            user=self.user,
            shipping_address='a', shipping_city='b', shipping_country='c',
            shipping_postal_code='d', phone_number='+380501234567',
        )

    def test_creating_an_order_item_reduces_stock_once(self):
        OrderItem.objects.create(
            order=self.order, wine=self.wine, quantity=3, price=Decimal('1')
        )
        self.wine.refresh_from_db()

        self.assertEqual(self.wine.stock_quantity, 7)

    def test_deleting_an_order_item_restores_stock(self):
        item = OrderItem.objects.create(
            order=self.order, wine=self.wine, quantity=3, price=Decimal('1')
        )

        item.delete()
        self.wine.refresh_from_db()

        self.assertEqual(self.wine.stock_quantity, 10)


class CartViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine(price=Decimal('200.00'), stock_quantity=5)
        self.add_url = reverse('orders:add_to_cart', kwargs={'slug': self.wine.slug})

    def test_cart_requires_login(self):
        response = self.client.get(reverse('orders:cart'))

        self.assertEqual(response.status_code, 302)

    def test_add_to_cart(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.post(self.add_url, {'quantity': 2})

        item = self.user.cart.items.get()
        self.assertEqual(item.wine, self.wine)
        self.assertEqual(item.quantity, 2)

    def test_adding_the_same_wine_twice_accumulates_quantity(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.post(self.add_url, {'quantity': 2})
        self.client.post(self.add_url, {'quantity': 1})

        self.assertEqual(self.user.cart.items.get().quantity, 3)

    def test_cannot_add_more_than_stock(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.post(self.add_url, {'quantity': 99})

        self.assertEqual(self.user.cart.items.count(), 0)

    def test_cannot_exceed_stock_by_accumulating(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.post(self.add_url, {'quantity': 4})
        self.client.post(self.add_url, {'quantity': 4})

        self.assertEqual(self.user.cart.items.get().quantity, 4)

    def test_inactive_wine_cannot_be_added(self):
        hidden = make_wine(name='Hidden', is_active=False)
        self.client.login(username='alice', password='pw12345678')

        response = self.client.post(
            reverse('orders:add_to_cart', kwargs={'slug': hidden.slug}),
            {'quantity': 1},
        )

        self.assertEqual(response.status_code, 404)

    def test_get_request_is_rejected(self):
        self.client.login(username='alice', password='pw12345678')

        self.assertEqual(self.client.get(self.add_url).status_code, 405)

    def test_update_quantity(self):
        self.client.login(username='alice', password='pw12345678')
        item = CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=1)

        self.client.post(
            reverse('orders:update_cart_item', kwargs={'item_id': item.id}),
            {'quantity': 3},
        )
        item.refresh_from_db()

        self.assertEqual(item.quantity, 3)

    def test_updating_to_zero_removes_the_item(self):
        self.client.login(username='alice', password='pw12345678')
        item = CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=1)

        self.client.post(
            reverse('orders:update_cart_item', kwargs={'item_id': item.id}),
            {'quantity': 0},
        )

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_remove_from_cart(self):
        self.client.login(username='alice', password='pw12345678')
        item = CartItem.objects.create(cart=self.user.cart, wine=self.wine, quantity=1)

        self.client.post(
            reverse('orders:remove_from_cart', kwargs={'item_id': item.id})
        )

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_a_user_cannot_touch_another_users_cart_item(self):
        other = User.objects.create_user(username='bob', password='pw12345678')
        item = CartItem.objects.create(cart=other.cart, wine=self.wine, quantity=1)
        self.client.login(username='alice', password='pw12345678')

        response = self.client.post(
            reverse('orders:remove_from_cart', kwargs={'item_id': item.id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine(price=Decimal('300.00'), stock_quantity=10)
        self.url = reverse('orders:checkout')
        self.client.login(username='alice', password='pw12345678')

    def _fill_cart(self, quantity=2):
        return CartItem.objects.create(
            cart=self.user.cart, wine=self.wine, quantity=quantity
        )

    def test_checkout_requires_login(self):
        self.client.logout()

        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_empty_cart_redirects_back_to_the_cart(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('orders:cart'))

    def test_checkout_page_shows_the_same_totals_that_get_saved(self):
        self._fill_cart(quantity=2)  # 600 -> tax 60, shipping 150

        context = self.client.get(self.url).context

        self.assertEqual(context['subtotal'], Decimal('600.00'))
        self.assertEqual(context['tax'], Decimal('60.00'))
        self.assertEqual(context['shipping'], Decimal('150.00'))
        self.assertEqual(context['total'], Decimal('810.00'))

    def test_successful_checkout_creates_an_order(self):
        self._fill_cart(quantity=2)

        response = self.client.post(self.url, CHECKOUT_DATA)

        order = Order.objects.get()
        self.assertRedirects(
            response,
            reverse(
                'orders:order_confirmation',
                kwargs={'order_number': order.order_number},
            ),
        )
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.get().price, Decimal('300.00'))

    def test_order_total_matches_what_the_checkout_page_showed(self):
        self._fill_cart(quantity=2)

        self.client.post(self.url, CHECKOUT_DATA)

        order = Order.objects.get()
        self.assertEqual(order.subtotal, Decimal('600.00'))
        self.assertEqual(order.tax, Decimal('60.00'))
        self.assertEqual(order.shipping_cost, Decimal('150.00'))
        self.assertEqual(order.total, Decimal('810.00'))

    def test_checkout_reduces_stock_exactly_once(self):
        """Regression: the view and the OrderItem signal both used to decrement."""
        self._fill_cart(quantity=3)

        self.client.post(self.url, CHECKOUT_DATA)
        self.wine.refresh_from_db()

        self.assertEqual(self.wine.stock_quantity, 7)

    def test_cart_is_emptied_after_checkout(self):
        self._fill_cart(quantity=2)

        self.client.post(self.url, CHECKOUT_DATA)

        self.assertEqual(self.user.cart.items.count(), 0)

    def test_checkout_is_blocked_when_stock_dropped_below_the_cart_quantity(self):
        self._fill_cart(quantity=5)
        self.wine.stock_quantity = 2
        self.wine.save()

        response = self.client.post(self.url, CHECKOUT_DATA)

        self.assertRedirects(response, reverse('orders:cart'))
        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_form_does_not_create_an_order(self):
        self._fill_cart()
        bad = dict(CHECKOUT_DATA, phone_number='abc')

        self.client.post(self.url, bad)

        self.assertEqual(Order.objects.count(), 0)

    def test_missing_last_name_is_rejected(self):
        self._fill_cart()
        bad = dict(CHECKOUT_DATA, last_name='   ')

        self.client.post(self.url, bad)

        self.assertEqual(Order.objects.count(), 0)


class OrderAccessTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='pw12345678')
        self.bob = User.objects.create_user(username='bob', password='pw12345678')
        self.order = Order.objects.create(
            user=self.alice,
            shipping_address='a', shipping_city='b', shipping_country='c',
            shipping_postal_code='d', phone_number='+380501234567',
        )

    def test_owner_can_open_the_order(self):
        self.client.login(username='alice', password='pw12345678')

        response = self.client.get(
            reverse(
                'orders:order_detail',
                kwargs={'order_number': self.order.order_number},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_another_user_gets_404(self):
        self.client.login(username='bob', password='pw12345678')

        response = self.client.get(
            reverse(
                'orders:order_detail',
                kwargs={'order_number': self.order.order_number},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_order_list_only_shows_your_own_orders(self):
        self.client.login(username='bob', password='pw12345678')

        orders = self.client.get(reverse('orders:order_list')).context['orders']

        self.assertEqual(list(orders), [])


class NovaPoshtaEndpointTests(TestCase):
    """The proxy endpoints must fail closed when no API key is configured."""

    def test_short_query_returns_an_empty_list_without_calling_the_api(self):
        response = self.client.get(reverse('orders:np_cities'), {'q': 'a'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': []})

    def test_missing_city_ref_returns_an_empty_list(self):
        response = self.client.get(reverse('orders:np_warehouses'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': []})

    def test_missing_api_key_is_reported_without_crashing(self):
        with self.settings(NOVA_POSHTA_API_KEY=''):
            response = self.client.get(reverse('orders:np_cities'), {'q': 'Київ'})

        self.assertEqual(response.json()['error'], 'no_api_key')
