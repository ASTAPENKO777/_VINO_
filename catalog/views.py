from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError
from .models import Wine, WineType, Country
from reviews.models import Review
import logging

logger = logging.getLogger(__name__)


class WineListView(ListView):
    model = Wine
    template_name = 'catalog/wine_list.html'
    context_object_name = 'wines'
    paginate_by = 12

    def get_queryset(self):
        queryset = Wine.objects.filter(is_active=True)

        wine_type = self.request.GET.get('wine_type')
        if wine_type:
            queryset = queryset.filter(wine_type__id=wine_type)

        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country__id=country)

        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == 'year_desc':
            queryset = queryset.order_by('-year')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wine_types'] = WineType.objects.all()
        context['countries'] = Country.objects.all()
        context['total_wines'] = Wine.objects.filter(is_active=True).count()
        context['total_countries'] = Country.objects.count()
        context['total_types'] = WineType.objects.count()
        return context


class AboutView(TemplateView):
    template_name = 'catalog/about.html'


class ContactsView(TemplateView):
    template_name = 'catalog/contacts.html'


class WineDetailView(DetailView):
    model = Wine
    template_name = 'catalog/wine_detail.html'
    context_object_name = 'wine'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.filter(is_approved=True)
        if self.request.user.is_authenticated:
            context['user_has_review'] = Review.objects.filter(
                user=self.request.user, wine=self.object
            ).exists()
        return context


@staff_member_required
@require_POST
def delete_wine(request, slug):
    wine = get_object_or_404(Wine, slug=slug)
    name = str(wine)
    try:
        wine.delete()
        messages.success(request, f'Вино "{name}" успішно видалено.')
    except ProtectedError:
        messages.error(
            request,
            f'Не можна видалити "{name}" — воно є в замовленнях. '
            f'Щоб прибрати з каталогу, деактивуйте товар у адмінці.'
        )
        return redirect('catalog:wine_detail', slug=slug)
    return redirect('catalog:wine_list')