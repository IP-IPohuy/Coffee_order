import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('')

# Подключение к базе данных
conn = sqlite3.connect('c0ffee-0rder.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    is_admin BOOLEAN NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    availability BOOLEAN NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    FOREIGN KEY (product_id) REFERENCES products(id)
)
''')
conn.commit()

def get_users():
    cursor.execute('SELECT user_id, is_admin FROM users')
    users = cursor.fetchall()
    return users

def is_admin(user_id):
    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result is not None and result[0]

def get_products():
    cursor.execute('SELECT id, name, price, availability FROM products WHERE availability = 1')
    return cursor.fetchall()

def add_to_cart(user_id, product_id, quantity=1):
    cursor.execute('SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    result = cursor.fetchone()

    if result:
        new_quantity = result[0] + quantity
        cursor.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?', (new_quantity, user_id, product_id))
    else:
        cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    
    conn.commit()

def send_main_menu(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup(row_width=2)
    catalogue_button = InlineKeyboardButton("Каталог товаров", callback_data='catalogue')
    cart_button = InlineKeyboardButton("Ваша корзина", callback_data='cart')
    worker_button = InlineKeyboardButton("Команды для работников", callback_data='worker')
    markup.add(catalogue_button, cart_button, worker_button)
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    send_main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data == 'catalogue')
def show_catalogue(call):
    chat_id = call.message.chat.id
    markup = InlineKeyboardMarkup()

    products = get_products()

    if not products:
        bot.send_message(chat_id, "В каталоге нет доступных товаров.")
        return

    for product in products:
        product_id, product_name, product_price, _ = product
        button = InlineKeyboardButton(f"{product_name} - {product_price} руб.", callback_data=f"add_{product_id}")
        markup.add(button)

    bot.send_message(chat_id, "Выберите товар для добавления в корзину:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def handle_product_selection(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[1])

    cursor.execute('SELECT name FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if product:
        product_name = product[0]
        add_to_cart(user_id, product_id)
        bot.answer_callback_query(call.id, f"Товар '{product_name}' добавлен в корзину.")
    else:
        bot.answer_callback_query(call.id, "Товар не найден.")

@bot.callback_query_handler(func=lambda call: call.data == 'cart')
def view_cart(call):
    user_id = call.from_user.id
    cursor.execute('''
        SELECT products.name, cart.quantity
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    ''', (user_id,))
    
    cart_items = cursor.fetchall()
    response = "Ваша корзина:\n\n"

    if cart_items:
        for product_name, quantity in cart_items:
            response += f"{product_name} - {quantity} шт.\n"
    else:
        response = "Ваша корзина пуста."

    bot.send_message(call.message.chat.id, response)

@bot.callback_query_handler(func=lambda call: call.data == 'worker')
def worker_commands(call):
    chat_id = call.message.chat.id
    if is_admin(call.from_user.id):
        markup = InlineKeyboardMarkup(row_width=2)
        setadmin_button = InlineKeyboardButton("Установить права", callback_data='setadmin')
        list_users_button = InlineKeyboardButton("Список пользователей", callback_data='list_users')
        add_product_button = InlineKeyboardButton("Добавить товар", callback_data='add_product')
        delete_product_button = InlineKeyboardButton("Удалить товар", callback_data='delete_product')
        markup.add(setadmin_button, list_users_button, add_product_button, delete_product_button)
        bot.send_message(chat_id, "Выберите команду для работы:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

@bot.callback_query_handler(func=lambda call: call.data == 'setadmin')
def request_user_id(call):
    chat_id = call.message.chat.id
    if is_admin(call.from_user.id):
        bot.send_message(chat_id, "Введите ID пользователя, которого вы хотите сделать администратором.")
        bot.register_next_step_handler(call.message, process_admin_id)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

def process_admin_id(message):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)  
        cursor.execute('INSERT OR REPLACE INTO users (user_id, is_admin) VALUES (?, ?)', (user_id, True))
        conn.commit()
        bot.send_message(chat_id, f"Пользователь {user_id} теперь администратор.")
    except ValueError:
        bot.send_message(chat_id, "Некорректный формат ID. Пожалуйста, введите правильный числовой ID.")

@bot.callback_query_handler(func=lambda call: call.data == 'list_users')
def list_users(call):
    chat_id = call.message.chat.id
    if is_admin(call.from_user.id):
        users = get_users()
        response = "Список пользователей и их права администратора:\n\n"

        if users:
            for user_id, rights in users:
                admin_status = "Администратор" if rights else "Пользователь"
                response += f"User ID: {user_id} - {admin_status}\n"
        else:
            response = "В базе данных пока нет пользователей."

        bot.send_message(chat_id, response)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

@bot.callback_query_handler(func=lambda call: call.data == 'add_product')
def add_product_start(call):
    chat_id = call.message.chat.id
    if is_admin(call.from_user.id):
        bot.send_message(chat_id, "Введите название товара:")
        bot.register_next_step_handler(call.message, process_product_name)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

def process_product_name(message):
    chat_id = message.chat.id
    product = {}
    product['name'] = message.text
    bot.send_message(chat_id, "Введите цену товара (только число):")
    bot.register_next_step_handler(message, process_product_price, product)

def process_product_price(message, product):
    chat_id = message.chat.id
    try:
        product['price'] = float(message.text)
        bot.send_message(chat_id, "Товар доступен? Введите 'Да' или 'Нет':")
        bot.register_next_step_handler(message, process_product_availability, product)
    except ValueError:
        bot.send_message(chat_id, "Некорректный формат цены. Пожалуйста, введите числовое значение.")
        bot.register_next_step_handler(message, process_product_price, product)

def process_product_availability(message, product):
    chat_id = message.chat.id
    availability = message.text.strip().lower()
    if availability in ['да', 'yes']:
        product['availability'] = True
    elif availability in ['нет', 'no']:
        product['availability'] = False
    else:
        bot.send_message(chat_id, "Пожалуйста, введите 'Да' или 'Нет'.")
        bot.register_next_step_handler(message, process_product_availability, product)
        return

    cursor.execute('INSERT INTO products (name, price, availability) VALUES (?, ?, ?)', 
                   (product['name'], product['price'], product['availability']))
    conn.commit()
    bot.send_message(chat_id, f"Товар '{product['name']}' успешно добавлен с ценой {product['price']} и доступностью {'Да' if product['availability'] else 'Нет'}.")

@bot.callback_query_handler(func=lambda call: call.data == 'delete_product')
def delete_product_start(call):
    chat_id = call.message.chat.id
    if is_admin(call.from_user.id):
        bot.send_message(chat_id, "Введите название товара, который вы хотите удалить:")
        bot.register_next_step_handler(call.message, process_product_deletion)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

def process_product_deletion(message):
    chat_id = message.chat.id
    product_name = message.text

    cursor.execute('SELECT * FROM products WHERE name = ?', (product_name,))
    product = cursor.fetchone()

    if product:
        cursor.execute('DELETE FROM products WHERE name = ?', (product_name,))
        conn.commit()
        bot.send_message(chat_id, f"Товар '{product_name}' успешно удален.")
    else:
        bot.send_message(chat_id, f"Товар с именем '{product_name}' не найден.")

bot.polling()

def hui:
    print('hui')
