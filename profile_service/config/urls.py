from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/profiles/', admin.site.urls),
    path('api/profiles/', include('profiles_app.urls')),
]
