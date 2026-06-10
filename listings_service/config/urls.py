from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/listings/', admin.site.urls),

    # All listings app routes live under /api/listings/
    # This includes: listings, units, agents, images
    path('api/listings/', include('listings.urls')),
]