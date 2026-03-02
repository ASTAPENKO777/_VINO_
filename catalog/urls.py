from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.WineListView.as_view(), name='wine_list'),
    path('wine/<slug:slug>/', views.WineDetailView.as_view(), name='wine_detail'),
    path('wine/<slug:slug>/delete/', views.delete_wine, name='wine_delete'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contacts/', views.ContactsView.as_view(), name='contacts'),
]
