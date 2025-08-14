from django.urls import path
from .views import AccountListView, TransactionCreateView, TransactionListView, TransactionAnnulView

app_name = "ledger"

urlpatterns = [
    path("accounts/", AccountListView.as_view(), name="accounts"),
    path("transactions/", TransactionListView.as_view(), name="transactions"),
    path("transactions/new/", TransactionCreateView.as_view(), name="transaction_create"),
    path("transactions/<int:pk>/annul/", TransactionAnnulView.as_view(), name="transaction_annul"),
]
