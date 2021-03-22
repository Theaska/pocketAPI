from django.urls import path

from apps.accounts.views import CreateUserView, ConfirmEmailView, LoginView, SendEmailToken

app_name = "accounts"

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', CreateUserView.as_view(), name='signup'),
    path('confirm-email/', SendEmailToken.as_view(), name='confirm_email'),
    path('confirm-email/<str:token>', ConfirmEmailView.as_view(), name='confirm_email'),
]