from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse

def index(request):
    return HttpResponse("<h1>Soil Module</h1><p>Welcome to Soil Health Monitoring!</p>")