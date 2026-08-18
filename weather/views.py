from django.shortcuts import render

# Create your views here.
# smart_sheti/weather/views.py
from django.http import HttpResponse

def index(request):
    return HttpResponse("<h1>Weather Module</h1><p>Welcome to Weather Forecast Module!</p>")