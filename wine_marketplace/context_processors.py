from orders.models import Cart


def cart_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.get_total_items()
        except Cart.DoesNotExist:
            count = 0
    else:
        count = 0
    return {'cart_count': count}
