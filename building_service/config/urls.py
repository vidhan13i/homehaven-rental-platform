from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/buildings/', admin.site.urls),

    # All building app routes live under /api/buildings/
    path('api/buildings/', include('building.urls')),
]
