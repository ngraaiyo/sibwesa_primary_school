# sibwesa_project/urls.py

from django.contrib import admin
from django.urls import path, include
from users import views as user_views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')), 
    path('students/', include('students.urls')), 
    path('', user_views.home_view, name='home'),
    path('performance/', include('performance.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    