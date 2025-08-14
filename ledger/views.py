from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from .forms import TransactionForm
from .models import Account, Transaction

class AccountListView(View):
    def get(self, request):
        accounts = Account.objects.select_related("group", "group__article").order_by("number")
        return render(request, "ledger/account_list.html", {"accounts": accounts})

class TransactionCreateView(View):
    def get(self, request):
        return render(request, "ledger/transaction_create.html", {"form": TransactionForm()})

    def post(self, request):
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            try:
                tx.post()
            except Exception as e:
                form.add_error(None, str(e))
            else:
                messages.success(request, f"Транзакция #{tx.pk} успешно создана.")
                return redirect(reverse("ledger:transactions"))
        return render(request, "ledger/transaction_create.html", {"form": form})

class TransactionListView(View):
    def get(self, request):
        txs = Transaction.objects.select_related("debit_account", "credit_account").all()
        return render(request, "ledger/transaction_list.html", {"transactions": txs})

class TransactionAnnulView(View):
    def post(self, request, pk: int):
        tx = get_object_or_404(Transaction, pk=pk)
        try:
            rev = tx.annul()
        except Exception as e:
            messages.error(request, f"Невозможно сторнировать: {e}")
        else:
            messages.success(request, f"Создано сторно #{rev.pk} для транзакции #{tx.pk}.")
        return redirect(reverse("ledger:transactions"))
