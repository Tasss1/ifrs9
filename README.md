# IFRS9 Ledger (Django)

Учёт баланса по МСФО 9 c принципом двойной записи.

## Запуск (локально, SQLite)

```bash
python -m venv .venv && . .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
# или: pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata ledger/fixtures/accounts_min.json
python manage.py runserver
