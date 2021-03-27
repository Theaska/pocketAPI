import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework.test import APITestCase

from pocket.models import Pocket


@override_settings(REDIS_PREFIX='pocketapi-test')
class PocketTest(APITestCase):
    fixtures = ['pocket/pockets.json', ]

    def setUp(self) -> None:
        self.UserModel = get_user_model()
        self.user_1 = self.UserModel.objects.get(pk=1)
        self.user_2 = self.UserModel.objects.get(pk=2)
        self.pocket_detail_url = lambda **x: resolve_url('pocket:pocket-detail', **x)

    def generate_validation_code(self, pocket_uuid):
        send_code_url = resolve_url('pocket:send-deletion-code', uuid=pocket_uuid)
        return self.client.get(send_code_url)

    def test_get_pockets(self):
        self.client.force_authenticate(self.user_1)
        url = resolve_url('pocket:pocket-list')
        response = self.client.get(url)
        self.assertEquals([1, 2], list(p['id'] for p in response.json()))

    def test_get_pocket_owner(self):
        self.client.force_authenticate(self.user_1)
        pocket = Pocket.objects.get(id=1)
        response = self.client.get(self.pocket_detail_url(uuid=pocket.uuid)).json()
        self.assertEquals(response['id'], pocket.id)
        self.assertEquals(response['uuid'], str(pocket.uuid))
        self.assertEquals(response['name'], pocket.name)
        self.assertEquals(response['balance'], 0.0)
        self.assertEquals(response['description'], pocket.description)

    def test_get_pocket_not_owner(self):
        self.client.force_authenticate(self.user_1)
        pocket = Pocket.objects.get(id=3)
        response = self.client.get(self.pocket_detail_url(uuid=pocket.uuid))
        self.assertEquals(response.status_code, 404)

    def test_get_pocket_not_auth(self):
        pocket = Pocket.objects.get(id=3)
        response = self.client.get(self.pocket_detail_url(uuid=pocket.uuid))
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
        self.assertEquals(response_json['balance'], 0.0)
        self.assertEquals(response_json['id'], 5)

    @patch('pocket.views.generate_code', return_value='11111')
    def test_delete_pocket_valid_code(self, *mocks):
        pocket = Pocket.objects.get(id=1)
        self.client.force_authenticate(self.user_1)

        response = self.generate_validation_code(pocket.uuid)
        self.assertContains(response, 'We sent confirmation code')

        response = self.client.delete(self.pocket_detail_url(uuid=pocket.uuid), data={'code': '11111'})
        self.assertEquals(response.status_code, 204)

        pocket.refresh_from_db()
        self.assertEquals(pocket.is_archived, True)

    def test_delete_pocket_invalid_code(self, *mocks):
        pocket = Pocket.objects.get(id=2)
        self.client.force_authenticate(self.user_1)

        response = self.generate_validation_code(pocket.uuid)
        self.assertContains(response, 'We sent confirmation code')

        response = self.client.delete(self.pocket_detail_url(uuid=pocket.uuid), data={'code': '11231'})
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json(), {'errors': ['Invalid code']})

        pocket.refresh_from_db()
        self.assertEquals(pocket.is_archived, False)

    def test_delete_pocket_not_owner(self, *mocks):
        pocket = Pocket.objects.get(id=3)
        self.client.force_authenticate(self.user_1)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)

        response = self.generate_validation_code(pocket.uuid)
        self.assertEquals(response.status_code, 403)

        response = self.client.delete(url, data={'code': '11111'})
        self.assertEquals(response.status_code, 404)

        pocket.refresh_from_db()
        self.assertEquals(pocket.is_archived, False)

    @override_settings(VALIDATION_CODE_LIFETIME=5)
    @patch('pocket.views.generate_code', return_value='11111')
    def test_delete_pocket_code_lifetime_ended(self, *mocks):
        pocket = Pocket.objects.get(id=1)
        self.client.force_authenticate(self.user_1)

        response = self.generate_validation_code(pocket.uuid)
        self.assertEquals(response.status_code, 200)

        time.sleep(6)
        url = resolve_url('pocket:pocket-detail', uuid=pocket.uuid)
        response = self.client.delete(url, data={'code': '11111'})
        self.assertEquals(response.status_code, 400)

        pocket.refresh_from_db()
        self.assertEquals(pocket.is_archived, False)

    @patch('pocket.views.generate_code', return_value='11111')
    def test_doesnt_show_archived_pocket(self, *mocks):
        pocket = Pocket.objects.get(id=1)
        self.client.force_authenticate(self.user_1)

        self.generate_validation_code(pocket.uuid)
        response = self.client.delete(self.pocket_detail_url(uuid=pocket.uuid), data={'code': '11111'})
        self.assertEquals(response.status_code, 204)

        response = self.client.get(resolve_url('pocket:pocket-list'))
        self.assertEquals(len(response.json()), 1)
        self.assertEquals(response.json()[0]['id'], 2)


        

