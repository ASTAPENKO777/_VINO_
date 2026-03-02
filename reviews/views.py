from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from catalog.models import Wine
from .forms import ReviewForm
from .models import Review


@login_required
@require_POST
def add_review(request, slug):
    wine = get_object_or_404(Wine, slug=slug, is_active=True)

    if Review.objects.filter(user=request.user, wine=wine).exists():
        messages.error(request, 'Ви вже залишили відгук для цього вина.')
        return redirect('catalog:wine_detail', slug=slug)

    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.wine = wine
        review.save()
        messages.success(request, 'Дякуємо за відгук! Він з\'явиться після модерації.')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

    return redirect('catalog:wine_detail', slug=slug)
