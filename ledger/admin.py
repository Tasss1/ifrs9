from django.contrib import admin
from .models import BalanceArticle, BalanceGroup, Account, Transaction

@admin.register(BalanceArticle)
class BalanceArticleAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(BalanceGroup)
class BalanceGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "article")
    search_fields = ("name",)
    list_filter = ("article",)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "type", "group", "balance")
    list_filter = ("type", "group__article")
    search_fields = ("number", "name")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "description", "debit_account", "credit_account", "amount", "is_reversal", "annulled")
    list_filter = ("is_reversal", "annulled", "created_at")
    search_fields = ("description",)
