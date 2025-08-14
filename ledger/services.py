from .models import Transaction

def create_transaction(*, debit_account, credit_account, amount, description="") -> Transaction:
    tx = Transaction(
        debit_account=debit_account,
        credit_account=credit_account,
        amount=amount,
        description=description
    )
    tx.post()
    return tx
