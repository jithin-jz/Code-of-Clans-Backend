from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth.urls')),
    path('api/rewards/', include('rewards.urls')),
    path('api/profiles/', include('users.urls')),
]
