from django.http import HttpResponse

def index(request):
    return HttpResponse("<h1>Farmer Module</h1><p>Welcome to Farmer Management!</p>")