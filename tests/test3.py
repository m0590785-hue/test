import csv
import datetime
import json
import os
import statistics
import uuid


DATA_FILE = "finance_data.json"
DEFAULT_CATEGORIES = [
    "Housing",
    "Groceries",
    "Utilities",
    "Transportation",
    "Dining Out",
    "Entertainment",
    "Healthcare",
    "Savings",
    "Salary",
    "Freelance",
    "Investments",
    "Miscellaneous",
]


class Transaction:
    """Represents a single financial transaction."""

    def __init__(
        self,
        amount,
        category,
        t_type,
        description="",
        date=None,
        t_id=None,
    ):
        self.id = t_id if t_id else str(uuid.uuid4())[:8]
        self.amount = float(amount)
        self.category = category.strip().title()
        self.t_type = t_type.lower()  # 'income' or 'expense'
        self.description = description.strip()
        if date:
            self.date = date
        else:
            self.date = datetime.date.today().isoformat()

    def to_dict(self):
        """Serialize transaction to dictionary."""
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "t_type": self.t_type,
            "description": self.description,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize transaction from dictionary."""
        return cls(
            amount=data["amount"],
            category=data["category"],
            t_type=data["t_type"],
            description=data.get("description", ""),
            date=data.get("date"),
            t_id=data.get("id"),
        )

    def __str__(self):
        sign = "+" if self.t_type == "income" else "-"
        return (
            f"[{self.id}] {self.date} | {self.category:<15} | "
            f"{sign}${self.amount:>9.2f} | {self.description}"
        )


class BudgetManager:
    """Manages transactions, category budgets, persistence, and analytics."""

    def __init__(self, filepath=DATA_FILE):
        self.filepath = filepath
        self.transactions = []
        self.budgets = {}  # category -> monthly limit (float)
        self.categories = list(DEFAULT_CATEGORIES)
        self.load_data()

    def load_data(self):
        """Load transactions and budgets from JSON storage."""
        if not os.path.exists(self.filepath):
            self.save_data()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.transactions = [
                    Transaction.from_dict(item)
                    for item in data.get("transactions", [])
                ]
                self.budgets = data.get("budgets", {})
                saved_cats = data.get("categories", [])
                for cat in saved_cats:
                    if cat not in self.categories:
                        self.categories.append(cat)
        except (json.JSONDecodeError, KeyError, IOError) as err:
            print(f"Warning: Could not read data file ({err}). Starting fresh.")
            self.transactions = []
            self.budgets = {}

    def save_data(self):
        """Persist current state to JSON storage."""
        payload = {
            "transactions": [t.to_dict() for t in self.transactions],
            "budgets": self.budgets,
            "categories": self.categories,
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(payload, file, indent=4)
        except IOError as err:
            print(f"Error saving data: {err}")

    def add_category(self, name):
        """Add a custom category if it does not already exist."""
        clean_name = name.strip().title()
        if not clean_name:
            return False, "Category name cannot be empty."
        if clean_name in self.categories:
            return False, f"Category '{clean_name}' already exists."
        self.categories.append(clean_name)
        self.save_data()
        return True, f"Category '{clean_name}' added."

    def add_transaction(self, amount, category, t_type, description="", date=None):
        """Validate and record a new transaction."""
        if amount <= 0:
            raise ValueError("Transaction amount must be positive.")
        if t_type.lower() not in ("income", "expense"):
            raise ValueError("Transaction type must be 'income' or 'expense'.")
        if date:
            datetime.date.fromisoformat(date)  # Validates YYYY-MM-DD

        clean_cat = category.strip().title()
        if clean_cat not in self.categories:
            self.categories.append(clean_cat)

        transaction = Transaction(
            amount=amount,
            category=clean_cat,
            t_type=t_type,
            description=description,
            date=date,
        )
        self.transactions.append(transaction)
        self.transactions.sort(key=lambda x: x.date, reverse=True)
        self.save_data()
        return transaction

    def delete_transaction(self, t_id):
        """Remove a transaction by its ID."""
        for idx, t in enumerate(self.transactions):
            if t.id == t_id:
                removed = self.transactions.pop(idx)
                self.save_data()
                return removed
        return None

    def set_budget(self, category, limit_amount):
        """Set a monthly budget ceiling for a specific category."""
        if limit_amount < 0:
            raise ValueError("Budget limit cannot be negative.")
        clean_cat = category.strip().title()
        if clean_cat not in self.categories:
            self.categories.append(clean_cat)
        self.budgets[clean_cat] = float(limit_amount)
        self.save_data()

    def get_transactions_by_month(self, year, month):
        """Filter transactions matching a specific year and month."""
        prefix = f"{year:04d}-{month:02d}"
        return [t for t in self.transactions if t.date.startswith(prefix)]

    def calculate_totals(self, transactions=None):
        """Compute total income, total expenses, and net balance."""
        target = self.transactions if transactions is None else transactions
        income = sum(t.amount for t in target if t.t_type == "income")
        expense = sum(t.amount for t in target if t.t_type == "expense")
        return {
            "income": income,
            "expense": expense,
            "net": income - expense,
        }

    def get_category_breakdown(self, t_type="expense", transactions=None):
        """Group and sum amounts by category."""
        target = self.transactions if transactions is None else transactions
        breakdown = {}
        for t in target:
            if t.t_type == t_type:
                breakdown[t.category] = breakdown.get(t.category, 0.0) + t.amount
        return dict(sorted(breakdown.items(), key=lambda item: item[1], reverse=True))

    def check_budget_status(self, year, month):
        """Compare actual monthly expenses against configured budgets."""
        monthly_tx = self.get_transactions_by_month(year, month)
        expenses = self.get_category_breakdown("expense", monthly_tx)
        status_report = []

        for category, limit in sorted(self.budgets.items()):
            spent = expenses.get(category, 0.0)
            remaining = limit - spent
            pct = (spent / limit * 100.0) if limit > 0 else 0.0
            status_report.append(
                {
                    "category": category,
                    "limit": limit,
                    "spent": spent,
                    "remaining": remaining,
                    "percent": pct,
                    "over": spent > limit,
                }
            )
        return status_report

    def search_transactions(self, keyword="", category=None, min_amt=None, max_amt=None):
        """Search transactions using multiple optional filters."""
        results = self.transactions
        if keyword:
            kw = keyword.lower()
            results = [
                t
                for t in results
                if kw in t.description.lower() or kw in t.category.lower()
            ]
        if category:
            cat = category.strip().title()
            results = [t for t in results if t.category == cat]
        if min_amt is not None:
            results = [t for t in results if t.amount >= min_amt]
        if max_amt is not None:
            results = [t for t in results if t.amount <= max_amt]
        return results

    def get_spending_statistics(self):
        """Calculate statistical insights across all expense transactions."""
        expenses = [t.amount for t in self.transactions if t.t_type == "expense"]
        if not expenses:
            return None
        stats = {
            "count": len(expenses),
            "total": sum(expenses),
            "mean": statistics.mean(expenses),
            "median": statistics.median(expenses),
            "min": min(expenses),
            "max": max(expenses),
            "stdev": statistics.stdev(expenses) if len(expenses) > 1 else 0.0,
        }
        return stats

    def export_to_csv(self, filename="transactions_export.csv"):
        """Export all transactions to a CSV file."""
        fieldnames = ["id", "date", "t_type", "category", "amount", "description"]
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for t in self.transactions:
                writer.writerow(t.to_dict())
        return filename

    def import_from_csv(self, filename):
        """Import transactions from an external CSV file."""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File '{filename}' not found.")

        imported_count = 0
        with open(filename, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)