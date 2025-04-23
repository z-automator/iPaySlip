from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('employees/', include('employees.urls')),
    path('payroll/', include('payroll.urls')),
    path('loans/', include('lending.urls')),
    path('accounts/', include('allauth.urls')),
    path('api/leaves/', include('leaves.urls')),
    path('user-management/', include('user_management.urls')),
    path('portal/', include('portal.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)