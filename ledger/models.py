from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from .choices import AccountType
import random

def gen_account_number():
    return ''.join(random.choices('0123456789', k=10))

class BalanceArticle(models.Model):
    """Статья бухгалтерского баланса (верхний уровень)."""
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Статья баланса"
        verbose_name_plural = "Статьи баланса"

    def __str__(self):
        return self.name

class BalanceGroup(models.Model):
    """Балансовая группа внутри статьи."""
    article = models.ForeignKey(BalanceArticle, on_delete=models.PROTECT, related_name="groups")
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Балансовая группа"
        verbose_name_plural = "Балансовые группы"
        unique_together = ("article", "name")

    def __str__(self):
        return f"{self.article} — {self.name}"

class Account(models.Model):
    """Счёт бухгалтерского учёта (минимальный набор полей)."""
    number = models.CharField(max_length=10, unique=True, default=gen_account_number)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=16, choices=AccountType.choices)
    group = models.ForeignKey(BalanceGroup, on_delete=models.PROTECT, related_name="accounts")
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name = "Счёт"
        verbose_name_plural = "Счета"
        ordering = ("number",)

    def __str__(self):
        return f'{self.number} — {self.name}'

    # Унифицированные правила изменения баланса:
    # Актив:     Дт +, Кт -
    # Пассив:    Дт -, Кт +
    # Смешанный: Дт => как актив; Кт => как пассив
    def apply_debit(self, amount: Decimal):
        if self.type in (AccountType.ASSET, AccountType.MIXED):
            self.balance += amount
        else:  # liability
            self.balance -= amount

    def apply_credit(self, amount: Decimal):
        if self.type in (AccountType.ASSET, AccountType.MIXED):
            self.balance -= amount
        else:  # liability
            self.balance += amount

class Transaction(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    description = models.CharField(max_length=500, blank=True)
    debit_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="debit_entries")
    credit_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="credit_entries")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    is_reversal = models.BooleanField(default=False)
    reversed_transaction = models.ForeignKey("self", null=True, blank=True,
                                             on_delete=models.SET_NULL, related_name="reversals")
    annulled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"
        ordering = ("-created_at", "-id")

    def clean(self):
        errors = {}
        if not self.debit_account_id or not self.credit_account_id:
            errors["debit_account"] = "Выберите дебет и кредит."
        if self.debit_account_id == self.credit_account_id and self.debit_account_id:
            errors["credit_account"] = "Дебет и кредит не могут совпадать."
        if self.amount is None or self.amount <= 0:
            errors["amount"] = "Сумма должна быть положительной."
        if errors:
            raise ValidationError(errors)

    def _rounded_amount(self) -> Decimal:
        return Decimal(self.amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @transaction.atomic
    def post(self):
        """Проводка (применение двойной записи) с блокировкой счетов."""
        self.clean()

        # Блокируем строки счетов на время обновления
        debit_acc = Account.objects.select_for_update().get(pk=self.debit_account_id)
        credit_acc = Account.objects.select_for_update().get(pk=self.credit_account_id)

        amt = self._rounded_amount()

        # применяем
        debit_acc.apply_debit(amt)
        credit_acc.apply_credit(amt)

        # сохраняем всё
        debit_acc.save(update_fields=["balance"])
        credit_acc.save(update_fields=["balance"])
        self.save()

    @transaction.atomic
    def annul(self):
        """Сторно: помечаем исходную + создаём обратную, откатывая балансы."""
        if self.annulled:
            raise ValidationError("Транзакция уже сторнирована.")
        # блокируем вовлечённые счета
        d = Account.objects.select_for_update().get(pk=self.debit_account_id)
        c = Account.objects.select_for_update().get(pk=self.credit_account_id)

        amt = self._rounded_amount()

        # создаём обратную транзакцию (переворачиваем Дт/Кт)
        reversal = Transaction(
            created_at=timezone.now(),
            description=f"Сторно транзакции #{self.pk}",
            debit_account=self.credit_account,
            credit_account=self.debit_account,
            amount=amt,
            is_reversal=True,
            reversed_transaction=self,
        )

        # применяем как обычную проводку
        # Дт по исходному кредитному счёту
        c.apply_debit(amt)
        # Кт по исходному дебетному счёту
        d.apply_credit(amt)

        c.save(update_fields=["balance"])
        d.save(update_fields=["balance"])

        reversal.save()
        self.annulled = True
        self.save(update_fields=["annulled"])

        return reversal
