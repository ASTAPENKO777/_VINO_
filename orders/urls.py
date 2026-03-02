from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('success/<str:order_number>/', views.order_confirmation_view, name='order_confirmation'),
    path('my-orders/', views.order_list_view, name='order_list'),
    path('my-orders/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('np/cities/', views.nova_poshta_cities, name='np_cities'),
    path('np/warehouses/', views.nova_poshta_warehouses, name='np_warehouses'),
]
