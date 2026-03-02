import requests as _requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django.db import transaction
from catalog.models import Wine
from .models import Cart, CartItem, Order, OrderItem
from .forms import CheckoutForm

_NP_URL = 'https://api.novaposhta.ua/v2.0/json/'


def _np_api(model, method, props):
    resp = _requests.post(_NP_URL, json={
        'apiKey': settings.NOVA_POSHTA_API_KEY,
        'modelName': model,
        'calledMethod': method,
        'methodProperties': props,
    }, timeout=10)
    resp.raise_for_status()
    return resp.json()


def nova_poshta_cities(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'data': []})
    if not settings.NOVA_POSHTA_API_KEY:
        return JsonResponse({'error': 'no_api_key', 'data': []})
    try:
        result = _np_api('Address', 'getCities', {
            'FindByString': q,
            'Limit': '20',
        })
        cities = [
            {
                'ref': c['Ref'],
                'name': c['Description'],
                'area': c.get('AreaDescription', ''),
                'region': c.get('RegionsDescription', ''),
            }
            for c in result.get('data', [])
        ]
        return JsonResponse({'data': cities})
    except Exception as e:
        return JsonResponse({'error': str(e), 'data': []}, status=502)


def nova_poshta_warehouses(request):
    city_ref = request.GET.get('city_ref', '').strip()
    if not city_ref:
        return JsonResponse({'data': []})
    if not settings.NOVA_POSHTA_API_KEY:
        return JsonResponse({'error': 'no_api_key', 'data': []})
    try:
        result = _np_api('Address', 'getWarehouses', {
            'CityRef': city_ref,
            'Limit': '500',
        })
        warehouses = [
            {
                'ref': w['Ref'],
                'number': w.get('Number', ''),
                'description': w.get('Description', ''),
                'short_address': w.get('ShortAddress', ''),
            }
            for w in result.get('data', [])
        ]
        return JsonResponse({'data': warehouses})
    except Exception as e:
        return JsonResponse({'error': str(e), 'data': []}, status=502)


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('wine', 'wine__wine_type', 'wine__country').all()
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'items': items,
    })


@login_required
@require_POST
def add_to_cart(request, slug):
    wine = get_object_or_404(Wine, slug=slug, is_active=True)
    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        quantity = 1
    if quantity > wine.stock_quantity:
        messages.error(request, f'На складі лише {wine.stock_quantity} пляшок.')
        return redirect('catalog:wine_detail', slug=slug)

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, wine=wine)

    if not created:
        new_qty = cart_item.quantity + quantity
        if new_qty > wine.stock_quantity:
            messages.error(request, f'На складі лише {wine.stock_quantity} пляшок.')
            return redirect('catalog:wine_detail', slug=slug)
        cart_item.quantity = new_qty
    else:
        cart_item.quantity = quantity

    cart_item.save()
    messages.success(request, f'"{wine.name}" додано в кошик.')
    return redirect('orders:cart')


@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        cart_item.delete()
        messages.success(request, 'Товар видалено з кошика.')
    elif quantity > cart_item.wine.stock_quantity:
        messages.error(request, f'На складі лише {cart_item.wine.stock_quantity} пляшок.')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Кількість оновлено.')

    return redirect('orders:cart')


@login_required
@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Товар видалено з кошика.')
    return redirect('orders:cart')


@login_required
def checkout_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('wine').all()

    if not items.exists():
        messages.error(request, 'Ваш кошик порожній.')
        return redirect('orders:cart')

    initial = {}
    try:
        profile = request.user.profile
        initial = {
            'phone_number': profile.phone_number or '',
            'shipping_address': profile.address or '',
            'shipping_city': profile.city or '',
            'shipping_country': profile.country or 'Україна',
            'shipping_postal_code': profile.postal_code or '',
        }
    except Exception:
        initial = {'shipping_country': 'Україна'}

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            stock_error = False
            for item in items:
                if item.quantity > item.wine.stock_quantity:
                    messages.error(
                        request,
                        f'На складі лише {item.wine.stock_quantity} пляшок "{item.wine.name}". '
                        f'Будь ласка, оновіть кошик.'
                    )
                    stock_error = True
            if stock_error:
                return redirect('orders:cart')

            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.save()

                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        wine=item.wine,
                        quantity=item.quantity,
                        price=item.wine.price,
                    )
                    item.wine.stock_quantity -= item.quantity
                    item.wine.save()

                order.calculate_totals()
                cart.clear()

            messages.success(request, f'Замовлення {order.order_number} успішно оформлено!')
            return redirect('orders:order_confirmation', order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    subtotal = cart.get_total_price()
    from decimal import Decimal, ROUND_HALF_UP
    tax = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    shipping = Decimal('0') if subtotal >= 2000 else Decimal('150')
    total = subtotal + tax + shipping

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping,
        'total': total,
    })


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )
    items = order.items.select_related('wine').all()
    return render(request, 'orders/order_confirmation.html', {
        'order': order,
        'items': items,
    })


@login_required
def order_list_view(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__wine')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    items = order.items.select_related('wine', 'wine__wine_type', 'wine__country').all()
    return render(request, 'orders/order_detail.html', {
        'order': order,
        'items': items,
    })
