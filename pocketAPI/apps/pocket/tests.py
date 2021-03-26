from unittest.mock import patch, Mock

from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from rest_framework.test import APITestCase

from pocket.helpers import generate_code
from pocket.models import Pocket


class PocketTest(APITestCase):
    fixtures = ['pocket/pockets.json', ]

    def setUp(self) -> None:
        self.UserModel = get_user_model()
        self.user_1 = self.UserModel.objects.get(pk=1)
        self.user_2 = self.UserModel.objects.get(pk=2)

    def test_get_pockets(self):
        self.client.force_authenticate(self.user_1)
        url = resolve_url('pocket:pocket-list')
        response = self.client.get(url)
        self.assertEquals([1, 2], list(p['id'] for p in response.json()))

    def test_get_pocket_owner(self):
        self.client.force_authenticate(self.user_1)
        pocket = Pocket.objects.get(id=1)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)
        response = self.client.get(url).json()
        self.assertEquals(response['id'], pocket.id)
        self.assertEquals(response['uuid'], str(pocket.uuid))
        self.assertEquals(response['name'], pocket.name)
        self.assertEquals(response['description'], pocket.description)

    def test_get_pocket_not_owner(self):
        self.client.force_authenticate(self.user_1)
        pocket = Pocket.objects.get(id=3)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_get_pocket_not_auth(self):
        pocket = Pocket.objects.get(id=3)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

    def test_create_pocket_not_auth(self):
        url = resolve_url('pocket:pocket-list')
        response = self.client.post(url, {'name': 'name'})
        self.assertEquals(response.status_code, 401)

    def test_create_pocket(self):
        self.client.force_authenticate(self.user_1)
        url = resolve_url('pocket:pocket-list')
        response = self.client.post(url, {'name': 'name'})
        response_json = response.json()
        self.assertEquals(response_json['name'], 'name')
        self.assertEquals(response_json['id'], 5)

    @patch('pocket.views.save_deletion_pocket_code')
    @patch('pocket.views.generate_code', return_value='11111')
    def test_delete_pocket(self, save_mock, generate_code_mock):
        pocket = Pocket.objects.get(id=1)
        self.client.force_authenticate(self.user_1)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)
        send_code_url = resolve_url('pocket:send-deletion-code', uuid=pocket.uuid)
        response = self.client.get(send_code_url)
        self.assertContains(response, 'We sent confirmation code')
        response = self.client.delete(url, data={'code': '11111'})
        self.assertEquals(response.status_code, 204)
        pocket = Pocket.objects.get(id=1)
        self.assertEquals(pocket.is_archived, True)

    @patch('pocket.views.save_deletion_pocket_code')
    @patch('pocket.views.generate_code', return_value='11111')
    def test_delete_pocket_not_owner(self, save_mock, generate_code_mock):
        pocket = Pocket.objects.get(id=3)
        self.client.force_authenticate(self.user_1)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)
        send_code_url = resolve_url('pocket:send-deletion-code', uuid=pocket.uuid)
        response = self.client.get(send_code_url)
        self.assertEquals(response.status_code, 404)
        response = self.client.delete(url, data={'code': '11111'})
        self.assertEquals(response.status_code, 404)
        pocket = Pocket.objects.get(id=1)
        self.assertEquals(pocket.is_archived, False)
        

