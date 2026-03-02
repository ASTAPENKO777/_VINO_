from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:wine_list')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Реєстрація успішна! Ласкаво просимо!')
            return redirect('catalog:wine_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:wine_list')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Ви успішно увійшли!')
            next_url = request.GET.get('next', 'catalog:wine_list')
            return redirect(next_url)
        else:
            messages.error(request, 'Невірне ім\'я користувача або пароль.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Ви вийшли з акаунту.')
    return redirect('catalog:wine_list')


@login_required
def profile_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)

    orders = request.user.orders.prefetch_related('items').order_by('-created_at')[:5]
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'recent_orders': orders,
    })
