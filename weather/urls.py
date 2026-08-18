# smart_sheti/weather/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='weather_home'),
]