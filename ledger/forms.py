from django import forms
from .models import Transaction, Account

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ("debit_account", "credit_account", "amount", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # компактный список
        self.fields["debit_account"].queryset = Account.objects.all().order_by("number")
        self.fields["credit_account"].queryset = Account.objects.all().order_by("number")

    def clean(self):
        cleaned = super().clean()
        debit = cleaned.get("debit_account")
        credit = cleaned.get("credit_account")
        amount = cleaned.get("amount")
        if debit and credit and debit == credit:
            self.add_error("credit_account", "Дебет и кредит не могут совпадать.")
        if amount is not None and amount <= 0:
            self.add_error("amount", "Сумма должна быть положительной.")
        return cleaned
