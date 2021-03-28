from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework.test import APITestCase

from pocket.models import Pocket
from transactions.exceptions import TransactionError
from transactions.models import PocketTransaction, ActionTransactions, TransactionStatus


class TestTransactionsModels(APITestCase):
    fixtures = ['transactions/transactions.json', ]

    def setUp(self) -> None:
        self.pocket = Pocket.objects.get(pk=1)
        self.created_transaction = PocketTransaction.objects.get(pk=1)
        self.in_process_transaction = PocketTransaction.objects.get(pk=2)
        self.confirmed_transaction = PocketTransaction.objects.get(pk=3)
        self.finished_transaction = PocketTransaction.objects.get(pk=4)
        self.cancelled_transaction = PocketTransaction.objects.get(pk=5)
        self.debit_transaction = PocketTransaction.objects.get(pk=6)

    def test_activate_created_transaction(self):
        with self.assertRaises(TransactionError) as exc:
            self.created_transaction.activate()
        self.assertEquals('Can activate transaction only with status CONFIRMED', str(exc.exception))
        self.created_transaction.refresh_from_db()
        self.assertEquals(self.created_transaction.status, TransactionStatus.CREATED)
        self.assertEquals(self.created_transaction.pocket.balance, 0.0)

    def test_activate_in_process_transaction(self):
        with self.assertRaises(TransactionError) as exc:
            self.in_process_transaction.activate()
        self.assertEquals('Can activate transaction only with status CONFIRMED', str(exc.exception))
        self.assertEquals(self.in_process_transaction.status, TransactionStatus.IN_PROCESS)
        self.assertEquals(self.in_process_transaction.pocket.balance, 0.0)

    def test_activate_confirmed_transaction(self):
        self.confirmed_transaction.activate()
        self.confirmed_transaction.refresh_from_db()
        self.assertEquals(self.confirmed_transaction.status, TransactionStatus.FINISHED)
        self.assertEquals(self.confirmed_transaction.pocket.balance, self.confirmed_transaction.sum)

    def test_activate_finished_transaction(self):
        with self.assertRaises(TransactionError) as exc:
            self.finished_transaction.activate()
        self.assertEquals('This transaction has finished already', str(exc.exception))
        self.finished_transaction.refresh_from_db()
        self.assertEquals(self.finished_transaction.status, TransactionStatus.FINISHED)
        self.assertEquals(self.finished_transaction.pocket.balance, 0.0)

    def test_activate_cancelled_transaction(self):
        with self.assertRaises(TransactionError) as exc:
            self.cancelled_transaction.activate()
        self.assertEquals('Can activate transaction only with status CONFIRMED', str(exc.exception))
        self.cancelled_transaction.refresh_from_db()
        self.assertEquals(self.cancelled_transaction.status, TransactionStatus.CANCELLED)
        self.assertEquals(self.cancelled_transaction.pocket.balance, 0.0)

    def test_activate_transaction_with_debit_enough_many(self):
        self.pocket.balance = 10000
        self.pocket.save()

        self.debit_transaction.activate()
        self.pocket.refresh_from_db()
        self.debit_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 10000-self.debit_transaction.sum)
        self.assertEquals(self.debit_transaction.status, TransactionStatus.FINISHED)

    def test_activate_transaction_with_debit_not_enough_many(self):
        with self.assertRaises(TransactionError) as exc:
            self.debit_transaction.activate()
        self.assertEquals(str(exc.exception), 'debit value is more than balance')
        self.pocket.refresh_from_db()
        self.debit_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 0.0)
        self.assertEquals(self.debit_transaction.status, TransactionStatus.CANCELLED)

    @patch('transactions.models.PocketTransaction.refund')
    def test_cancel_created_transaction(self, refund_mock):
        self.created_transaction.cancel()
        self.pocket.refresh_from_db()
        self.created_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 0.0)
        self.assertEquals(self.created_transaction.status, TransactionStatus.CANCELLED)
        self.assertEquals(refund_mock.call_count, 0)

    @patch('transactions.models.PocketTransaction.refund')
    def test_cancel_in_process_transaction(self, refund_mock):
        self.in_process_transaction.cancel()
        self.pocket.refresh_from_db()
        self.in_process_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 0.0)
        self.assertEquals(self.in_process_transaction.status, TransactionStatus.CANCELLED)
        self.assertEquals(refund_mock.call_count, 0)

    def test_cancel_confirmed_transaction(self):
        self.confirmed_transaction.cancel()
        self.pocket.refresh_from_db()
        self.confirmed_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 0.0)
        self.assertEquals(self.confirmed_transaction.status, TransactionStatus.CANCELLED)

    def test_cancel_finished_transaction_enough_money(self):
        self.pocket.balance = 1000
        self.pocket.save()
        self.finished_transaction.cancel()
        self.pocket.refresh_from_db()
        self.finished_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 1000-self.finished_transaction.sum)
        self.assertEquals(self.finished_transaction.status, TransactionStatus.CANCELLED)

    def test_cancel_finished_transaction(self):
        with self.assertRaises(TransactionError) as exc:
            self.finished_transaction.cancel()
        self.assertEquals(str(exc.exception), 'Not enough money for refund')
        self.pocket.refresh_from_db()
        self.finished_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, 0.0)
        self.assertEquals(self.finished_transaction.status, TransactionStatus.FINISHED)

    def test_cancel_finished_debit_transaction(self):
        self.debit_transaction.set_finished()
        self.debit_transaction.cancel()
        self.pocket.refresh_from_db()
        self.debit_transaction.refresh_from_db()
        self.assertEquals(self.pocket.balance, self.debit_transaction.sum)
        self.assertEquals(self.debit_transaction.status, TransactionStatus.CANCELLED)

    def test_cancel_cancelled_transaction(self):
        with self.assertRaises(TransactionError) as exc:
            self.cancelled_transaction.cancel()
        self.assertEquals(str(exc.exception), 'Transaction has already cancelled')
        self.assertEquals(self.pocket.balance, 0.0)
        self.assertEquals(self.cancelled_transaction.status, TransactionStatus.CANCELLED)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend', REDIS_PREFIX='pocketapi-test')
@patch('transactions.serializers.get_confirmation_transaction_code', return_value='11111')
@patch('transactions.views.save_confirmation_transaction_code')
class TestTransactions(APITestCase):
    fixtures = ['transactions/transactions_pockets.json', ]

    def setUp(self) -> None:
        self.UserModel = get_user_model()
        self.user_1 = self.UserModel.objects.get(pk=1)
        self.user_2 = self.UserModel.objects.get(pk=2)
        self.user_1.transactions = PocketTransaction.objects.filter(pocket__user=self.user_1)
        self.user_2.transactions = PocketTransaction.objects.filter(pocket__user=self.user_2)

    def test_list_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        url = resolve_url('transactions:transactions-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        transactions_ids = [transaction['id'] for transaction in response.json()]
        self.assertEquals(transactions_ids, list(self.user_1.transactions.visible().values_list('pk', flat=True)))

    def test_list_transaction_doesnt_show_archived_pocket(self, *mocks):
        self.client.force_authenticate(self.user_1)
        archived_pocket = self.user_1.pockets.get(pk=2)
        self.assertEquals(archived_pocket.is_archived, True)
        url = resolve_url('transactions:transactions-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        transactions_ids = [transaction['id'] for transaction in response.json()]
        for archived_transaction in list(archived_pocket.transactions.values_list('pk', flat=True)):
            self.assertNotIn(archived_transaction, transactions_ids)

    def test_list_filter(self, *mocks):
        self.client.force_authenticate(self.user_2)
        pocket = self.user_2.pockets.get(pk=3)
        url = resolve_url('transactions:transactions-list') + '?pocket__uuid={}'.format(pocket.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        transactions_ids = [transaction['id'] for transaction in response.json()]
        self.assertEquals(transactions_ids,
                          list(self.user_2.transactions.filter(pocket=pocket).values_list('pk', flat=True)))

    def test_list_not_auth(self, *mocks):
        url = resolve_url('transactions:transactions-list')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

    def test_transaction_detail(self, *mocks):
        self.client.force_authenticate(self.user_1)
        transaction = self.user_1.transactions.first()
        url = resolve_url('transactions:transactions-detail', uuid=transaction.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        json = response.json()
        self.assertEquals(json['id'], transaction.id)
        self.assertEquals(json['status'], transaction.status_name)
        self.assertEquals(json['sum'], transaction.sum)
        self.assertEquals(json['action_name'], transaction.action_name)

    def test_transaction_detail_not_owner(self, *mocks):
        self.client.force_authenticate(self.user_1)
        transaction = self.user_2.transactions.first()
        url = resolve_url('transactions:transactions-detail', uuid=transaction.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_transaction_detail_archive_pocket(self, *mocks):
        self.client.force_authenticate(self.user_1)
        transaction = self.user_1.transactions.get(pk=7)
        url = resolve_url('transactions:transactions-detail', uuid=transaction.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    def test_transaction_detail_not_auth(self, *mocks):
        transaction = self.user_1.transactions.first()
        url = resolve_url('transactions:transactions-detail', uuid=transaction.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 401)

    def test_create_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        url = resolve_url('transactions:transactions-list')
        response = self.client.post(url, {'action': 1, 'sum': 400, 'comment': 'test', 'pocket': pocket.id})
        self.assertEquals(response.status_code, 201)
        json = response.json()
        self.assertEquals(json['action'], ActionTransactions.REFILL)
        self.assertEquals(json['status'], TransactionStatus.CREATED.name)
        self.assertEquals(json['comment'], 'test')
        self.assertEquals(pocket.balance, 0.0)

    def test_send_confirm_code_for_created_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.first()
        url = resolve_url('transactions:send-confirm-code', uuid=transaction.uuid)
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'We sent confirmation')
        transaction.refresh_from_db()
        self.assertEquals(transaction.status, TransactionStatus.IN_PROCESS)

    def test_confirm_created_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.first()

        confirm_transaction_url = resolve_url('transactions:confirm-transaction', uuid=transaction.uuid)
        response = self.client.post(confirm_transaction_url, {'code': '11111'})
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.json()['detail'], 'Can confirm transaction only with status IN_PROCESS')

    def test_confirm_in_process_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.first()
        transaction.set_in_process()
        transaction.save()

        confirm_transaction_url = resolve_url('transactions:confirm-transaction', uuid=transaction.uuid)
        response = self.client.post(confirm_transaction_url, {'code': '11111'})
        self.assertEquals(response.status_code, 200)
        transaction.refresh_from_db()
        pocket.refresh_from_db()
        self.assertEquals(pocket.balance, transaction.sum)

    def test_confirm_in_progress_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.get(pk=2)

        confirm_transaction_url = resolve_url('transactions:confirm-transaction', uuid=transaction.uuid)
        response = self.client.post(confirm_transaction_url, {'code': '11111'})
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Your transaction have confirmed')
        transaction.refresh_from_db()
        pocket.refresh_from_db()
        self.assertEquals(transaction.status, TransactionStatus.FINISHED)
        self.assertEquals(pocket.balance, transaction.sum)

    def test_confirm_confirmed_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.get(pk=4)

        confirm_transaction_url = resolve_url('transactions:confirm-transaction', uuid=transaction.uuid)
        response = self.client.post(confirm_transaction_url, {'code': '11111'})
        self.assertEquals(response.status_code, 404)

    def test_delete_created_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.first()

        delete_url = resolve_url('transactions:transactions-detail', uuid=transaction.uuid)
        response = self.client.delete(delete_url)
        pocket.refresh_from_db()
        self.assertEquals(response.status_code, 204)
        self.assertEquals(pocket.balance, 0.0)

    def test_delete_finished_transaction(self, *mocks):
        self.client.force_authenticate(self.user_1)
        pocket = self.user_1.pockets.first()
        transaction = pocket.transactions.get(pk=5)

        delete_url = resolve_url('transactions:transactions-detail', uuid=transaction.uuid)
        response = self.client.delete(delete_url)
        pocket.refresh_from_db()
        self.assertEquals(response.status_code, 204)
        self.assertEquals(pocket.balance, transaction.sum)







