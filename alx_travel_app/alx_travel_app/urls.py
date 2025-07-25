"""
URL configuration for alx_travel_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URL Configuration for alx_travel_app project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI configuration
schema_view = get_schema_view(
    openapi.Info(
        title="ALX Travel App API",
        default_version='v1',
        description="API documentation for ALX Travel App",
        terms_of_service="https://www.alxtravelapp.com/terms/",
        contact=openapi.Contact(email="contact@alxtravelapp.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def api_root(request):
    """
    Welcome message for the API root
    """
    return JsonResponse({
        'message': 'Welcome to ALX Travel App API',
        'version': 'v1',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'swagger_docs': '/swagger/',
            'redoc_docs': '/redoc/',
        },
        'status': 'active'
    })

urlpatterns = [
    # Root URL - welcome message
    path('', api_root, name='api-root'),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Include listings app URLs
    path('api/', include('listings.urls')),
    
    # Swagger and ReDoc URLs
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)