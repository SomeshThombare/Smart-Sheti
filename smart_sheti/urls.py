from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('farmer/', include('farmer.urls')),
    path('crop/', include('crop.urls')),
    path('fertilizer/', include('fertilizer.urls')),
    path('soil/', include('soil.urls')),
    path('weather/', include('weather.urls')),
    path('disease/', include('disease_detection.urls')),
    # path('ai_engine/', include('ai_engine.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('marketplace/', include('marketplace.urls')),
    path('schemes/', include('government_schemes.urls')),
    path('equipment/', include('equipment_rental.urls')),

    # Pest Detection Module
    path('pest/', include('pest_detection.urls')),
    
    

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )