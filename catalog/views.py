from django.views.generic import ListView, DetailView
from .models import Wine
import logging

logger = logging.getLogger(__name__)


class WineListView(ListView):
    """List all wines with filtering"""
    model = Wine
    template_name = 'catalog/wine_list.html'
    context_object_name = 'wines'
    paginate_by = 12

    def get_queryset(self):
        queryset = Wine.objects.filter(is_active=True)

        # Filter by wine type
        wine_type = self.request.GET.get('wine_type')
        if wine_type:
            queryset = queryset.filter(wine_type__id=wine_type)

        # Filter by country
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country__id=country)

        return queryset


class WineDetailView(DetailView):
    """Wine detail page"""
    model = Wine
    template_name = 'catalog/wine_detail.html'
    context_object_name = 'wine'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.filter(is_approved=True)
        return context
