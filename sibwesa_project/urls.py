# sibwesa_project/urls.py

from django.contrib import admin
from django.urls import path, include
from users import views as user_views 
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')), 
    path('students/', include('students.urls')), 
    path('', user_views.home_view, name='home'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('performance/', include('performance.urls')),
    path('reports/', include('reports.urls', namespace='reports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    