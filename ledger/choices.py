from django.db import models

class AccountType(models.TextChoices):
    ASSET = "asset", "Актив"
    LIABILITY = "liability", "Пассив"
    MIXED = "mixed", "Активно-пассивный"

