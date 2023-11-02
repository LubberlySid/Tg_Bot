import json
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

TOKEN_BOT = "6629042849:AAEi_McqT2hQqCQAmJwdRi5ofQ0uO1SD-OE"
user_data = dict()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class MyTelegramBot:
    EXPENSE_CATEGORIES = ['Food', 'Clothes', 'Shoes', 'Entertainment', 'Shopping']

    def __init__(self, data_file):
        self.data_file = data_file
        self.data = self.load_data()

        # Створення обробника подій
        self.application = ApplicationBuilder().token(TOKEN_BOT).build()

        # Додавання обробників команд
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('add_expense', self.add_expense))
        self.application.add_handler(CommandHandler('list_expense_categories', self.list_expense_categories))
        self.application.add_handler(CommandHandler('add_income', self.add_income))
        self.application.add_handler(CommandHandler('get_expense_in_last_week', self.view_expense_last_week))
        self.application.add_handler(CommandHandler('get_expense_in_last_month', self.view_expense_last_month))
        self.application.add_handler(CommandHandler('get_all_expense', self.view_all_expense))
        self.application.add_handler(CommandHandler('remove_expense', self.remove_expense))
        self.application.add_handler(CommandHandler('delete_income', self.handle_delete_income))
        self.application.add_handler(CommandHandler('category_expense_stats', self.category_expense_stats))
        self.application.add_handler(CommandHandler('category_income_stats', self.category_income_stats))
        self.application.add_handler(CommandHandler('category_income_stats', self.category_income_stats))
        self.application.add_handler(CommandHandler('clear_data', self.clear_data_command))

    def load_data(self):
        try:
            with open(self.data_file, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {
                'expenses': {},
                'income': []
            }
        return data

    def save_data(self):
        with open(self.data_file, 'w') as file:
            json.dump(self.data, file)

    def clear_data(self):
        self.data = {
            'expenses': {},
            'income': []
        }
        self.save_data()

    async def clear_data_command(self, update: Update, context: CallbackContext):
        # Очистити дані при виклику команди
        self.clear_data()
        await update.message.reply_text('Data cleared. You can start fresh.')

    async def start(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        await update.message.reply_text("Welcome to my Income & Expense list Bot!\n"
                                        "Commands:\n"
                                        "Add expense: /add_expense <category> <amount>\n"
                                        "Available expense categories: /list_expense_categories\n"
                                        "Add income: /add_income\n"
                                        "Get expense in the last week: /get_expense_in_last_week\n"
                                        "Get expense in the last month: /get_expense_in_last_month\n"
                                        "Get all expense: /get_all_expense\n"
                                        "Delete expense: /remove_expense <category> <amount>\n"
                                        "Delete income: /delete_income <category> <amount>\n"
                                        "Category expense stats: /category_expense_stats <category> <period>\n"
                                        "Category income stats: /category_income_stats <category> <period>\n"
                                        "Clear data: /clear_data\n"
                                        )

    async def add_expense(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        if 'expenses' not in self.data:
            self.data['expenses'] = {}

        message_text = update.message.text

        if not message_text.startswith('/add_expense'):
            await update.message.reply_text('Please use the /add_expense command followed by the category and amount.')
            return

        parts = message_text.split(' ')
        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. Please use /add_expense <category> <amount>.')
            return

        category = parts[1]
        if category not in self.EXPENSE_CATEGORIES:
            await update.message.reply_text(
                'Invalid category. Available categories are: ' + ', '.join(self.EXPENSE_CATEGORIES))
            return

        amount = parts[2]

        if not category or not amount.isdigit():
            await update.message.reply_text('Invalid category or amount. Please use /add_expense <category> <amount>.')
            return

        amount = int(amount)

        if category not in self.data['expenses']:
            self.data['expenses'][category] = []

        # Додати запис про витрати тільки, якщо категорія вказана
        if category:
            timestamp = datetime.now().timestamp()
            self.data['expenses'][category].append(
                {'user_id': user_id, 'amount': amount, 'timestamp': timestamp, 'category': category})
            self.save_data()
            await update.message.reply_text(f'Expense of {amount} added to category {category}.')

    async def list_expense_categories(self, update: Update, context: CallbackContext):
        categories = self.EXPENSE_CATEGORIES
        await update.message.reply_text('Expense categories: ' + ', '.join(categories))

    async def add_income(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        if 'income' not in self.data:
            self.data['income'] = []

        message_text = update.message.text

        if not message_text.startswith('/add_income'):
            await update.message.reply_text('Please use the /add_income command followed by the category and amount.')
            return

        parts = message_text.split(' ')
        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. Please use /add_income <category> <amount>.')
            return

        category = parts[1]
        amount = parts[2]

        if not amount.isdigit():
            await update.message.reply_text('Invalid amount. Please use /add_income <category> <amount>.')
            return

        amount = int(amount)

        timestamp = datetime.now().timestamp()

        income_entry = {'user_id': user_id, 'amount': amount, 'timestamp': timestamp, 'category': category}
        self.data['income'].append(income_entry)
        self.save_data()
        await update.message.reply_text(f'Income of {amount} added to category {category}.')

    def get_expense_in_last_week(self, user_id):
        if 'expenses' not in self.data:
            return []

        current_date = datetime.now()
        last_week_start = current_date - timedelta(days=current_date.weekday() + 7)

        expenses = []
        for category, amounts in self.data['expenses'].items():
            for amount in amounts:
                if amount['user_id'] == user_id:
                    if datetime.fromtimestamp(amount['timestamp']) >= last_week_start:
                        expenses.append(amount)

        return expenses

    async def view_expense_last_week(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        expenses = self.get_expense_in_last_week(user_id)

        if not expenses:
            await update.message.reply_text('No expenses in the last week.')
            return

        response = 'Expenses in the last week:\n'
        for expense in expenses:
            if 'category' in expense:
                response += f'{expense["category"]}: {expense["amount"]} USD\n'
            else:
                response += f'Unknown Category: {expense["amount"]} USD\n'

        await update.message.reply_text(response)

    def get_expense_in_last_month(self, user_id):
        if 'expenses' not in self.data:
            return []

        current_date = datetime.now()
        last_month_start = current_date - timedelta(days=current_date.day + 30)

        expenses = []
        for category, amounts in self.data['expenses'].items():
            for amount in amounts:
                if amount['user_id'] == user_id:
                    if datetime.fromtimestamp(amount['timestamp']) >= last_month_start:
                        expenses.append(amount)

        return expenses

    async def view_expense_last_month(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        expenses = self.get_expense_in_last_month(user_id)

        if not expenses:
            await update.message.reply_text('No expenses in the last month.')
            return

        response = 'Expenses in the last month:\n'
        for expense in expenses:
            if 'category' in expense:
                response += f'{expense["category"]}: {expense["amount"]} USD\n'
            else:
                response += f'Unknown Category: {expense["amount"]} USD\n'

        await update.message.reply_text(response)

    def get_all_expense(self, user_id):
        if 'expenses' not in self.data:
            return []

        expenses = []
        for category, amounts in self.data['expenses'].items():
            for amount in amounts:
                if amount['user_id'] == user_id:
                    expenses.append(amount)

        return expenses

    async def view_all_expense(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        expenses = self.get_all_expense(user_id)

        if not expenses:
            await update.message.reply_text('No expenses recorded.')
            return

        response = 'All expenses:\n'
        for expense in expenses:
            if 'category' in expense and expense['category']:
                response += f'{expense["category"]}: {expense["amount"]} USD\n'
            else:
                response += f'Unknown Category: {expense["amount"]} USD\n'

        await update.message.reply_text(response)

    def delete_expense(self, user_id, category, amount):
        if 'expenses' not in self.data:
            return

        if category in self.data['expenses']:
            expenses = self.data['expenses'][category]
            for expense in expenses:
                if expense['user_id'] == user_id and expense['amount'] == amount:
                    expenses.remove(expense)
                    self.save_data()
                    return

    async def remove_expense(self, update, context):
        user_id = update.message.from_user.id

        message_text = update.message.text
        parts = message_text.split(' ')

        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. '
                                            'Please use /remove_expense <category> <amount> to delete an expense.')
            return

        category = parts[1]
        amount = int(parts[2])

        self.delete_expense(user_id, category, amount)
        await update.message.reply_text(f'Expense of {amount} in category {category} deleted.')

    def delete_income(self, user_id, category, amount):
        if 'income' not in self.data:
            return

        to_remove = None
        for income_entry in self.data['income']:
            if (income_entry['user_id'] == user_id and income_entry['category'] == category and
                    income_entry['amount'] == amount):
                to_remove = income_entry
                break

        if to_remove:
            self.data['income'].remove(to_remove)
            self.save_data()

    async def handle_delete_income(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        message_text = update.message.text
        parts = message_text.split(' ')

        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. '
                                            'Please use /delete_income <category> <amount> to delete an income entry.')
            return

        category = parts[1]
        amount = int(parts[2])

        self.delete_income(user_id, category, amount)
        await update.message.reply_text(f'Income of {amount} in category {category} deleted.')

    async def category_expense_stats(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        message_text = update.message.text
        parts = message_text.split(' ')

        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. '
                                            'Please use /category_expense_stats <category> <period>.')
            return

        category = parts[1]
        period = parts[2].lower()

        if category not in self.EXPENSE_CATEGORIES:
            await update.message.reply_text(
                'Invalid category. Available categories are: ' + ', '.join(self.EXPENSE_CATEGORIES))
            return

        if period not in ["day", "week", "month", "year"]:
            await update.message.reply_text('Invalid period. Please use one of the following: day, week, month, year.')
            return

        current_date = datetime.now()
        if period == "day":
            start_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = current_date - timedelta(days=current_date.weekday() + 7)
        elif period == "month":
            last_month_start = current_date - relativedelta(months=1)
            start_date = last_month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            last_year_start = current_date - relativedelta(years=1)
            start_date = last_year_start.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        total_expenses = self.calculate_expense(user_id, start_date, end_date, category)
        await update.message.reply_text(f'Total expenses for {category} in the last {period}: {total_expenses} USD')

    async def category_income_stats(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        message_text = update.message.text
        parts = message_text.split(' ')

        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. '
                                            'Please use /category_income_stats <category> <period>.')
            return

        category = parts[1]
        period = parts[2].lower()

        if period not in ["day", "week", "month", "year"]:
            await update.message.reply_text('Invalid period. Please use one of the following: day, week, month, year.')
            return

        current_date = datetime.now()
        if period == "day":
            start_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = current_date - timedelta(days=current_date.weekday() + 7)
        elif period == "month":
            last_month_start = current_date - relativedelta(months=1)
            start_date = last_month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            last_year_start = current_date - relativedelta(years=1)
            start_date = last_year_start.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        total_income = self.calculate_income(user_id, start_date, end_date, category)
        await update.message.reply_text(f'Total income for {category} in the last {period}: {total_income} USD')

    def calculate_expense(self, user_id, start_date, end_date, category=None):
        if 'expenses' not in self.data:
            return 0

        total_expenses = 0
        for exp_category, amounts in self.data['expenses'].items():
            if category and category != exp_category:
                continue

            for amount in amounts:
                if (amount['user_id'] == user_id and
                        start_date.timestamp() <= amount['timestamp'] <= end_date.timestamp()):
                    total_expenses += amount['amount']

        return total_expenses

    def calculate_income(self, user_id, start_date, end_date, category=None):
        if 'income' not in self.data:
            return 0

        total_income = 0
        for inc_entry in self.data['income']:
            if category and category != inc_entry['category']:
                continue

            if (inc_entry['user_id'] == user_id and
                    start_date.timestamp() <= inc_entry['timestamp'] <= end_date.timestamp()):
                total_income += inc_entry['amount']

        return total_income


if __name__ == '__main__':
    bot = MyTelegramBot('data.json')

    bot.application.run_polling()
