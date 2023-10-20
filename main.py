import json
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, Updater

TOKEN_BOT = "6629042849:AAEi_McqT2hQqCQAmJwdRi5ofQ0uO1SD-OE"
user_data = dict()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

updater = Updater(bot=TOKEN_BOT, update_queue=True)


class MyTelegramBot:
    EXPENSE_CATEGORIES = ['Food', 'Clothes', 'Shoes', 'Entertainment', 'Transport expenses', 'Shopping',
                          'Something else']

    def __init__(self, token, data_file):
        self.token = token
        self.data_file = data_file
        self.data = self.load_data()
        self.updater = Updater(self.token)
        self.dispatcher = self.updater.dispatcher

        # Додавання обробників команд
        self.dispatcher.add_handler(CommandHandler('start', self.start))
        self.dispatcher.add_handler(CommandHandler('add_expense', self.add_expense))
        self.dispatcher.add_handler(CommandHandler('list_categories', self.list_categories))

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

    async def start(self, update: Update, context: CallbackContext) -> None:
        user_id = update.message.from_user.id
        logging.info('Command "start" was triggered!')
        await update.message.reply_text(
            "Welcome to my Income & Expenses list Bot!\n"
            "Commands:\n"
            "Add expenses: /expenses <category> | amount\n"
            "Available expenses categories: /available_expenses_categories\n"
            "Add income: /income <category> | amount\n"
            "View expenses: /view_all_expenses, /view_expenses_per_month, /view_expenses_per_week\n"
            "Delete expenses: /delete_expense <index>\n"
            "Delete income: /delete_income <index>\n"
            "Category expenses stats: /category_expenses_stats_day, /category_expenses_stats_week, "
            "/category_expenses_stats_month, /category_expenses_stats_year\n"
            "Category income stats: /day_category_income_stats, /week_category_income_stats, "
            "/month_category_income_stats, /year_category_income_stats\n"
            "Help: /help"
        )

    async def add_expense(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        if 'expenses' not in self.data:
            self.data['expenses'] = {}

        # Отримання тексту повідомлення від користувача
        message_text = update.message.text

        # Перевірка, чи команда правильно сформована
        if not message_text.startswith('/add_expense'):
            await update.message.reply_text('Please use the /add_expense command followed by the category and amount.')
            return

        # Розділення повідомлення на аргументи (категорію і суму)
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

        # Перевірка, чи категорія і сума вказані правильно
        if not category or not amount.isdigit():
            await update.message.reply_text('Invalid category or amount. Please use /add_expense <category> <amount>.')
            return

        amount = int(amount)

        # Додавання витрати до списку витрат
        if category not in self.data['expenses']:
            self.data['expenses'][category] = []
        self.data['expenses'][category].append(amount)
        self.save_data()
        await update.message.reply_text(f'Expense of {amount} added to category {category}.')

    def list_expense_categories(self):
        return self.EXPENSE_CATEGORIES

    async def list_categories(self, update: Update, context: CallbackContext):
        # Обробка команди /list_categories
        # Відправка списку категорій користувачеві
        categories = self.list_expense_categories()
        await update.message.reply_text('Expense categories: ' + ', '.join(categories))

    def add_income(self, user_id, category, amount):
        if 'income' not in self.data:
            self.data['income'] = []

        # Додавання доходу до списку доходів
        self.data['income'].append({'user_id': user_id, 'category': category, 'amount': amount})

        self.save_data()

    async def handle_income(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        # Отримання текстового повідомлення від користувача
        message_text = update.message.text

        # Розділення повідомлення на аргументи (категорію і суму)
        parts = message_text.split(' ')
        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. Please use /add_income <category> <amount>.')
            return

        category = parts[1]
        amount = parts[2]

        # Перевірка, чи сума вказана правильно
        if not amount.isdigit():
            await update.message.reply_text('Invalid amount. Please use /add_income <category> <amount>.')
            return

        amount = int(amount)

        # Додавання доходу та збереження даних
        self.add_income(user_id, category, amount)
        await update.message.reply_text(f'Income of {amount} added to category {category}.')

    def get_expenses_in_last_week(self, user_id):
        if 'expenses' not in self.data:
            return []

        # Поточна дата
        current_date = datetime.now()

        # Дата, яка вказує на початок останнього тижня
        last_week_start = current_date - timedelta(days=current_date.weekday() + 7)

        # Фільтруємо витрати, які належать до останнього тижня
        expenses = []
        for category, amounts in self.data['expenses'].items():
            for amount in amounts:
                if amount['user_id'] == user_id:
                    if datetime.fromtimestamp(amount['timestamp']) >= last_week_start:
                        expenses.append(amount)

        return expenses

    async def view_expenses_last_week(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id

        # Отримуємо витрати за останній тиждень
        expenses = self.get_expenses_in_last_week(user_id)

        if not expenses:
            await update.message.reply_text('No expenses in the last week.')
            return

        # Відправка витрат користувачеві
        response = 'Expenses in the last week:\n'
        for expense in expenses:
            response += f'{expense["category"]}: {expense["amount"]} USD\n'

        await update.message.reply_text(response)

    def get_expenses_in_last_month(self, user_id):
        if 'expenses' not in self.data:
            return []

        # Поточна дата
        current_date = datetime.now()

        # Дата, яка вказує на початок останнього місяця
        last_month_start = current_date - timedelta(days=current_date.day + 30)

        # Фільтруємо витрати, які належать до останнього місяця
        expenses = []
        for category, amounts in self.data['expenses'].items():
            for amount in amounts:
                if amount['user_id'] == user_id:
                    if datetime.fromtimestamp(amount['timestamp']) >= last_month_start:
                        expenses.append(amount)

        return expenses

    async def view_expenses_last_month(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id

        # Отримуємо витрати за останній місяць
        expenses = self.get_expenses_in_last_month(user_id)

        if not expenses:
            await update.message.reply_text('No expenses in the last month.')
            return

        # Відправка витрат користувачеві
        response = 'Expenses in the last month:\n'
        for expense in expenses:
            response += f'{expense["category"]}: {expense["amount"]} USD\n'

        await update.message.reply_text(response)

    def get_all_expenses(self, user_id):
        if 'expenses' not in self.data:
            return []

        expenses = []
        for category, amounts in self.data['expenses'].items():
            for amount in amounts:
                if amount['user_id'] == user_id:
                    expenses.append(amount)

        return expenses

    async def view_all_expenses(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id

        # Отримуємо всі витрати користувача
        expenses = self.get_all_expenses(user_id)

        if not expenses:
            await update.message.reply_text('No expenses recorded.')
            return

        # Відправка витрат користувачеві
        response = 'All expenses:\n'
        for expense in expenses:
            response += f'{expense["category"]}: {expense["amount"]} USD\n'

        await update.message.reply_text(response)

    def delete_expense(self, user_id, category, amount):
        if 'expenses' not in self.data:
            return

        # Пошук витрати для видалення за категорією та сумою
        if category in self.data['expenses'] and amount in self.data['expenses'][category]:
            self.data['expenses'][category].remove(amount)

            # Видалення категорії, якщо вона більше не має витрат
            # if not self.data['expenses'][category]:
                # del self.data['expenses'][category]

            self.save_data()

    async def handle_delete_expense(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        # Отримання текстового повідомлення від користувача
        message_text = update.message.text

        # Розділення повідомлення на аргументи (категорію і суму)
        parts = message_text.split(' ')
        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. '
                                            'Please use /delete_expense <category> <amount> to delete an expense.')
            return

        category = parts[1]
        amount = parts[2]

        # Перевірка, чи сума вказана правильно
        if not amount.isdigit():
            await update.message.reply_text('Invalid amount. '
                                            'Please use /delete_expense <category> <amount> to delete an expense.')
            return

        amount = int(amount)

        # Видалення витрати та збереження даних
        self.delete_expense(user_id, category, amount)
        await update.message.reply_text(f'Expense of {amount} in category {category} deleted.')

    def delete_income(self, user_id, category, amount):
        if 'income' not in self.data:
            return

        # Пошук доходу для видалення за категорією та сумою
        to_remove = None
        for income_entry in self.data['income']:
            if income_entry['user_id'] == user_id and income_entry['category'] == category and income_entry['amount'] == amount:
                to_remove = income_entry
                break

        if to_remove:
            self.data['income'].remove(to_remove)
            self.save_data()

    async def handle_delete_income(self, update: Update, context):
        user_id = update.effective_user.id
        chat_id = update.message.chat_id

        # Отримання текстового повідомлення від користувача
        message_text = update.message.text

        # Розділення повідомлення на аргументи (категорію і суму)
        parts = message_text.split(' ')
        if len(parts) != 3:
            await update.message.reply_text('Invalid command format. '
                                            'Please use /delete_income <category> <amount> to delete an income entry.')
            return

        category = parts[1]
        amount = parts[2]

        # Перевірка, чи сума вказана правильно
        if not amount.isdigit():
            await update.message.reply_text('Invalid amount. '
                                            'Please use /delete_income <category> <amount> to delete an income entry.')
            return

        amount = int(amount)

        # Видалення доходу та збереження даних
        self.delete_income(user_id, category, amount)
        await update.message.reply_text(f'Income of {amount} in category {category} deleted.')

    async def category_expenses_stats_day(self, update: Update, context: CallbackContext):
        pass

    async def category_expenses_stats_week(self, update: Update, context: CallbackContext):
        pass

    async def category_expenses_stats_month(self, update: Update, context: CallbackContext):
        pass

    async def category_expenses_stats_year(self, update: Update, context: CallbackContext):
        pass

    async def category_income_stats_day(self, update: Update, context: CallbackContext):
        pass

    async def category_income_stats_week(self, update: Update, context: CallbackContext):
        pass

    async def category_income_stats_month(self, update: Update, context: CallbackContext):
        pass

    async def category_income_stats_year(self, update: Update, context: CallbackContext):
        pass

    async def bot_help(self, update: Update, context: CallbackContext):
        pass


if __name__ == '__main__':
    bot = MyTelegramBot(TOKEN_BOT, 'data.json')

    # Додавання обробників команд до диспетчера бота
    bot.updater.dispatcher.add_handler(CommandHandler('start', bot.start))
    bot.updater.dispatcher.add_handler(CommandHandler('add_expense', bot.add_expense))
    bot.updater.dispatcher.add_handler(CommandHandler('list_categories', bot.list_categories))
    bot.updater.dispatcher.add_handler(CommandHandler('add_income', bot.handle_income))
    bot.updater.dispatcher.add_handler(CommandHandler('get_expenses_in_last_week', bot.view_expenses_last_week))
    bot.updater.dispatcher.add_handler(CommandHandler('get_expenses_in_last_month', bot.view_expenses_last_month))
    bot.updater.dispatcher.add_handler(CommandHandler('get_all_expenses', bot.view_all_expenses))
    bot.updater.dispatcher.add_handler(CommandHandler('delete_expense', bot.handle_delete_expense))
    bot.updater.dispatcher.add_handler(CommandHandler('delete_income', bot.handle_delete_income))

    # Запуск бота та підтримка його активності
    bot.updater.start_polling()
    bot.updater.idle()

