from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.test import TestCase


class AccountsTest(TestCase):
    def setUp(self) -> None:
        self.UserModel = get_user_model()

        self.not_confirmed_user = self.UserModel(username='not_confirmed_user', email='not_confirmed_user')
        self.not_confirmed_user.token = 'email_token_not_confirmed'
        self.not_confirmed_user.set_password('123')
        self.not_confirmed_user.save()

        self.confirmed_user = self.UserModel(username='confirmed_user', email='confirmed_user', is_confirmed=True)
        self.confirmed_user.token = 'email_token_confirmed'
        self.confirmed_user.set_password('123')
        self.confirmed_user.save()

    @patch('apps.accounts.models.User.send_confirmation_email')
    def test_create_new_user_is_not_confirmed(self, *mocks):
        url = resolve_url('accounts:signup')
        response = self.client.post(url, {'username': 'test', 'password': 'test', 'email': 'test@test.com'})
        response_json = response.json()
        self.assertEquals(response_json['username'], 'test')
        self.assertEquals(response_json['email'], 'test@test.com')
        user = self.UserModel.objects.get(id=response_json['id'])
        self.assertEquals(user.is_confirmed, False)

    @patch('apps.accounts.models.User.send_confirmation_email')
    def test_confirm_email_user(self, *mocks):
        url = resolve_url('accounts:signup')
        response = self.client.post(url, {'username': 'test', 'password': 'test', 'email': 'test@test.com'})
        response_json = response.json()
        user = self.UserModel.objects.get(id=response_json['id'])
        token = user.token
        confirm_email_url = resolve_url('accounts:confirm_email', token=token)
        response = self.client.get(confirm_email_url)
        user = self.UserModel.objects.get(id=response_json['id'])
        self.assertContains(response, 'successfully')
        self.assertEquals(user.is_confirmed, True)

    def test_invalid_confirm_token_email_user(self):
        confirm_email_url = resolve_url('accounts:confirm_email', token='123213123123')
        response = self.client.get(confirm_email_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], ['Invalid token'])

    def test_confirmed_user_confirm_token(self):
        confirm_email_url = resolve_url('accounts:confirm_email', token=self.confirmed_user.token)
        response = self.client.get(confirm_email_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], ['You have already confirmed your profile.'])

    @patch('apps.accounts.models.User.send_confirmation_email')
    def test_confirmed_with_old_token(self, *mocks):
        old_token = self.not_confirmed_user.token
        resend_email_url = resolve_url('accounts:confirm_email')
        response = self.client.post(resend_email_url, {
            'username': self.not_confirmed_user.username, 'password': '123'
        })
        self.assertContains(response, 'We sent email to confirm your email address')
        confirm_email_url = resolve_url('accounts:confirm_email', token=old_token)
        response = self.client.get(confirm_email_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], ['Invalid token'])

    def test_login_if_email_not_confirmed(self):
        url = resolve_url('accounts:login')
        response = self.client.post(url, {'username': self.not_confirmed_user.username, 'password': '123'})
        self.assertEquals(response.status_code, 400)
        response_json = response.json()
        self.assertEqual(
            response_json['errors'],
            ['User is inactive. Please, check your email and activate your profile']
        )

    def test_login_if_email_confirmed(self):
        url = resolve_url('accounts:login')
        response = self.client.post(url, {'username': self.confirmed_user.username, 'password': '123'})
        self.assertContains(response, 'access_token')
        self.assertContains(response, 'refresh_token')





