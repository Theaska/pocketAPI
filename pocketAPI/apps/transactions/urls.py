from django.urls import path
from rest_framework import routers

from transactions.views import TransactionViewSet, ConfirmTransaction, SendConfirmationCode

app_name = 'transactions'

router = routers.SimpleRouter()

router.register('', TransactionViewSet, basename='transactions')

urlpatterns = [
    path('<uuid:uuid>/confirm-transaction/', ConfirmTransaction.as_view(), name='confirm-transaction'),
    path('<uuid:uuid>/send-confirm-code/', SendConfirmationCode.as_view(), name='send-confirm-code'),
]

urlpatterns += router.urls
