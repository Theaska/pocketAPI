from django.urls import path
from rest_framework import routers

from .views import PocketAPIView, SendConfirmationDeleteCode

app_name = 'pocket'

router = routers.SimpleRouter()

router.register('', PocketAPIView, basename='pocket')

urlpatterns = [
    path('<uuid:uuid>/send-deletion-code/', SendConfirmationDeleteCode.as_view(), name='send-deletion-code'),
]

urlpatterns += router.urls
