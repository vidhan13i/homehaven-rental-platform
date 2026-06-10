from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/applications/', admin.site.urls),
    path('api/applications/', include('application.urls')),
]
