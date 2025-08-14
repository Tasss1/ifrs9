from decimal import Decimal
import pytest
from django.test import TestCase
from ledger.models import Account, BalanceArticle, BalanceGroup, Transaction
from ledger.choices import AccountType

class PostingTest(TestCase):
    def setUp(self):
        art = BalanceArticle.objects.create(name="A")
        g = BalanceGroup.objects.create(article=art, name="G")
        self.asset1 = Account.objects.create(name="Касса", type=AccountType.ASSET, group=g, number="1000000001")
        self.asset2 = Account.objects.create(name="Клиенты", type=AccountType.MIXED, group=g, number="2211000001")
        self.liab = Account.objects.create(name="Уставной капитал", type=AccountType.LIABILITY, group=g, number="5000000001")

    def test_asset_to_asset(self):
        t = Transaction(debit_account=self.asset2, credit_account=self.asset1, amount=Decimal("100.00"))
        t.post()
        self.asset1.refresh_from_db(); self.asset2.refresh_from_db()
        self.assertEqual(self.asset1.balance, Decimal("-100.00"))
        self.assertEqual(self.asset2.balance, Decimal("100.00"))

    def test_asset_to_liability(self):
        t = Transaction(debit_account=self.asset1, credit_account=self.liab, amount=Decimal("50.00"))
        t.post()
        self.asset1.refresh_from_db(); self.liab.refresh_from_db()
        self.assertEqual(self.asset1.balance, Decimal("50.00"))
        self.assertEqual(self.liab.balance, Decimal("50.00"))

    def test_liability_to_asset(self):
        t = Transaction(debit_account=self.liab, credit_account=self.asset1, amount=Decimal("25.00"))
        t.post()
        self.asset1.refresh_from_db(); self.liab.refresh_from_db()
        self.assertEqual(self.liab.balance, Decimal("-25.00"))
        self.assertEqual(self.asset1.balance, Decimal("-25.00"))

    def test_annul(self):
        t = Transaction.objects.create(debit_account=self.asset1, credit_account=self.liab, amount=Decimal("10.00"))
        t.post()
        bal_asset_before = self.asset1.balance
        bal_liab_before = self.liab.balance
        rev = t.annul()
        self.asset1.refresh_from_db(); self.liab.refresh_from_db()
        self.assertTrue(t.annulled)
        self.assertTrue(rev.is_reversal)
        self.assertEqual(self.asset1.balance, Decimal("0.00"))
        self.assertEqual(self.liab.balance, Decimal("0.00"))
