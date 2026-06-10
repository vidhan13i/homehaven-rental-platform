from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/auth/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
]
