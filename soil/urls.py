# smart_sheti/soil/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='soil_home'),
]