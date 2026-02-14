from django import forms
from .models import Order, CartItem


class CheckoutForm(forms.ModelForm):
    """Checkout form with custom validation"""
    class Meta:
        model = Order
        fields = ['shipping_address', 'shipping_city', 'shipping_country',
                  'shipping_postal_code', 'phone_number', 'notes']

    def clean(self):
        """Validate that all required shipping fields are filled"""
        cleaned_data = super().clean()
        required_fields = ['shipping_address', 'shipping_city', 'shipping_country',
                          'shipping_postal_code', 'phone_number']

        for field in required_fields:
            if not cleaned_data.get(field):
                raise forms.ValidationError("Please fill in all required shipping information.")

        return cleaned_data

    def clean_shipping_postal_code(self):
        """Validate postal code format"""
        postal_code = self.cleaned_data.get('shipping_postal_code')
        if postal_code and len(postal_code) < 3:
            raise forms.ValidationError("Please enter a valid postal code.")
        return postal_code


class CartItemForm(forms.ModelForm):
    """Form for adding/updating cart items"""
    class Meta:
        model = CartItem
        fields = ['quantity']

    def __init__(self, *args, wine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.wine = wine

    def clean_quantity(self):
        """Validate quantity against stock"""
        quantity = self.cleaned_data.get('quantity')
        if self.wine and quantity > self.wine.stock_quantity:
            raise forms.ValidationError(
                f"Only {self.wine.stock_quantity} bottles available in stock."
            )
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity
