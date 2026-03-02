from django import forms
from .models import Order, CartItem


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'last_name', 'first_name', 'patronymic',
            'phone_number',
            'shipping_address', 'shipping_city', 'shipping_country',
            'shipping_postal_code', 'notes',
        ]
        labels = {
            'last_name': 'Прізвище',
            'first_name': 'Ім\'я',
            'patronymic': 'По батькові',
            'phone_number': 'Номер телефону',
            'shipping_address': 'Адреса доставки',
            'shipping_city': 'Місто',
            'shipping_country': 'Країна',
            'shipping_postal_code': 'Поштовий індекс / Відділення',
            'notes': 'Примітки до замовлення',
        }
        widgets = {
            'last_name': forms.TextInput(attrs={'placeholder': 'Шевченко'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Іван'}),
            'patronymic': forms.TextInput(attrs={'placeholder': 'Петрович'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+380 (50) 123-45-67'}),
            'shipping_address': forms.TextInput(attrs={'placeholder': 'вул. Хрещатик, 1'}),
            'shipping_city': forms.TextInput(attrs={'placeholder': 'Київ'}),
            'shipping_country': forms.TextInput(attrs={'placeholder': 'Україна'}),
            'shipping_postal_code': forms.TextInput(attrs={'placeholder': 'Відділення №1'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Додаткова інформація...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipping_country'].initial = 'Україна'
        self.fields['notes'].required = False
        self.fields['patronymic'].required = False

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '').strip()
        if not value:
            raise forms.ValidationError('Введіть прізвище.')
        return value

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '').strip()
        if not value:
            raise forms.ValidationError('Введіть ім\'я.')
        return value

    def clean_shipping_postal_code(self):
        postal_code = self.cleaned_data.get('shipping_postal_code')
        if postal_code and len(postal_code) < 1:
            raise forms.ValidationError('Введіть коректний поштовий індекс.')
        return postal_code

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        digits = phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if not digits.isdigit() or len(digits) < 7:
            raise forms.ValidationError('Введіть коректний номер телефону.')
        return phone


class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def __init__(self, *args, wine=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.wine = wine

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.wine and quantity > self.wine.stock_quantity:
            raise forms.ValidationError(
                f"Only {self.wine.stock_quantity} bottles available in stock."
            )
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity
