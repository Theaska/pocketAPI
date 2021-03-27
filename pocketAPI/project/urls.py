from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Pocket API",
        default_version='v1',
        description="Pocket API",
        contact=openapi.Contact(email="tach.pu@gmail.com"),
        license=openapi.License(name="Theaska BSD"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', schema_view.with_ui()),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('tokens/', include('jwt_helper.urls', namespace='jwt')),
    path('pocket/', include('pocket.urls', namespace='pocket')),
    path('transactions/', include('transactions.urls', namespace='transactions')),
]