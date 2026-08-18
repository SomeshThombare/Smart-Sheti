
# Create your views here.
from django.http import HttpResponse

def index(request):
    return HttpResponse("""
        <h1>Marketplace Module</h1>
        <p>Welcome to Marketplace Management!</p>
    """)