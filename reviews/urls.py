from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('wine/<slug:slug>/review/', views.add_review, name='add_review'),
]
