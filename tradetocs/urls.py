from django.contrib import admin
from django.urls import include, path
from apps.accounts.urls import auth_urlpatterns, user_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include(auth_urlpatterns)),
    path("api/v1/users/", include(user_urlpatterns)),
]
