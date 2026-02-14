from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.WineListView.as_view(), name='wine_list'),
    path('wine/<slug:slug>/', views.WineDetailView.as_view(), name='wine_detail'),
]
