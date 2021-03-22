from django.urls import path

from .views import UpdateTokensView

app_name = 'jwt_helper'

urlpatterns = [
    path('update-tokens/', UpdateTokensView.as_view(), name='update-tokens'),
]