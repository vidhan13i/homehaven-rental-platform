from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/reviews/', admin.site.urls),
    path('api/reviews/', include('reviews.urls')),
]
