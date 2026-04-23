"""Configuration des URLs principales du projet film_platform."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Routes de l'application web movies.
    path('', include('movies.urls')),
    # Routes de l'API REST.
    path('api/', include('movies.api_urls')),
]

if settings.DEBUG:
    # Sert les fichiers medias et statiques uniquement en developpement.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
