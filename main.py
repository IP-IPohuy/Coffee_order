import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


bot = telebot.TeleBot('huy')

# Подключение к базе данных
conn = sqlite3.connect('c0ffee-0rder.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы users, если её нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    is_admin BOOLEAN NOT NULL
)
''')

# Создание таблицы products, если её нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный идентификатор для каждого товара
    name TEXT NOT NULL,                     -- Название товара
    price REAL NOT NULL,                    -- Цена товара
    availability BOOLEAN NOT NULL           -- Доступность товара
)
''')

conn.commit()

# Создаем таблицу cart
cursor.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Уникальный идентификатор записи в корзине
    user_id INTEGER NOT NULL,              -- ID пользователя
    product_id INTEGER NOT NULL,           -- ID продукта
    quantity INTEGER DEFAULT 1,            -- Количество выбранных товаров
    FOREIGN KEY (product_id) REFERENCES products(id)  -- Связь с таблицей products
)
''')
conn.commit()

'''Для админских прав при первом запуске'''
# def initialize_db():

#     cursor.execute('SELECT COUNT(*) FROM users')
#     count = cursor.fetchone()[0]
    
#     if count == 0:
#         first_user_id = '1949116700'  
#         cursor.execute('INSERT INTO users (user_id, is_admin) VALUES (?, ?)', (first_user_id, True))
#         conn.commit()
# initialize_db()

# Проверка прав администратора
def is_admin(user_id):
    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result is not None and result[0]

# Функция для получения списка пользователей
def get_users():
    cursor.execute('SELECT user_id, is_admin FROM users')
    users = cursor.fetchall()
    return users

def get_products():
    cursor.execute('SELECT name, price, availability FROM products')
    products = cursor.fetchall()
    return products

def add_to_cart(user_id, product_id, quantity=1):
    # Проверяем, есть ли товар уже в корзине пользователя
    cursor.execute('SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    result = cursor.fetchone()

    if result:
        # Если товар уже в корзине, увеличиваем его количество
        new_quantity = result[0] + quantity
        cursor.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?', (new_quantity, user_id, product_id))
    else:
        # Если товара еще нет в корзине, добавляем его
        cursor.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
    
    conn.commit()

# Команды для бота

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет, я бот ООО Три долбоеба! Я помогу Вам сделать заказ и буду уведомлять об акциях.\n"
        "Список команд:\n\n"
        "/start - Запустить бота\n"
        "/catalogue - Показать товары\n"
        "/worker - Команды для работников"
    )
    chat_id = message.chat.id
    bot.send_message(chat_id, welcome_text)

@bot.message_handler(commands=['catalogue'])
def show_catalogue(message):
    chat_id = message.chat.id
    markup = InlineKeyboardMarkup()

    # Получаем список продуктов из базы данных
    cursor.execute('SELECT id, name, price, availability FROM products WHERE availability = 1')  # Только доступные товары
    products = cursor.fetchall()

    # Проверяем, есть ли продукты в базе данных
    if not products:
        bot.send_message(chat_id, "В каталоге нет доступных товаров.")
        return

    # Добавляем кнопки для каждого доступного товара
    for product in products:
        product_id, product_name, product_price, product_availability = product
        button = InlineKeyboardButton(f"{product_name} - {product_price} руб.", callback_data=str(product_id))
        markup.add(button)

    # Отправляем сообщение с каталогом
    bot.send_message(chat_id, "Выберите товар для добавления в корзину:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_product_selection(call):
    user_id = call.from_user.id
    product_id = int(call.data)  # Получаем id товара

    # Получаем информацию о товаре из базы данных
    cursor.execute('SELECT name FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()

    if product:
        product_name = product[0]
        add_to_cart(user_id, product_id)
        bot.answer_callback_query(call.id, f"Товар '{product_name}' добавлен в корзину.")
    else:
        bot.answer_callback_query(call.id, "Товар не найден.")


# Команда для отображения содержимого корзины
@bot.message_handler(commands=['cart'])
def view_cart(message):
    user_id = message.from_user.id

    cursor.execute('''
        SELECT products.name, cart.quantity 
        FROM cart 
        JOIN products ON cart.product_id = products.id 
        WHERE cart.user_id = ?
    ''', (user_id,))
    
    cart_items = cursor.fetchall()

    if cart_items:
        response = "Ваша корзина:\n\n"
        for product_name, quantity in cart_items:
            response += f"{product_name} - {quantity} шт.\n"
    else:
        response = "Ваша корзина пуста."
    
    bot.reply_to(message, response)


@bot.message_handler(commands=['worker'])
def worker_commands(message):
    chat_id = message.chat.id
    worker_commands_text = (
        "Список команд:\n\n"
        "/setadmin - Установить права\n"
        "/list_users - Вывести всех пользователей и их права\n"
        "/add_product - Добавить товар\n"
        "/delete_product - Удалить товар"
    )
    if is_admin(message.from_user.id):
        bot.send_message(chat_id, worker_commands_text)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

@bot.message_handler(commands=['setadmin'])
def request_user_id(message):
    chat_id = message.chat.id
    if is_admin(message.from_user.id):
        bot.send_message(chat_id, "Введите ID пользователя, которого вы хотите сделать администратором.")
        bot.register_next_step_handler(message, process_admin_id)
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

@bot.message_handler(commands=['getid'])
def send_user_id(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    bot.send_message(chat_id, f"Ваш User ID: {user_id}")

@bot.message_handler(commands=['list_users'])
def list_users(message):
    chat_id = message.chat.id
    if is_admin(message.from_user.id):
        users = get_users()
        if users:
            response = "Список пользователей и их права администратора:\n\n"
            for user_id, rights in users:
                admin_status = "Администратор" if rights else "Пользователь"
                response += f"User ID: {user_id} - {admin_status}\n"
        else:
            response = "В базе данных пока нет пользователей."
        bot.send_message(chat_id, response)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

@bot.message_handler(commands=['add_product'])
def add_product_start(message):
    chat_id = message.chat.id
    if is_admin(message.from_user.id):
        bot.send_message(chat_id, "Введите название товара:")
        bot.register_next_step_handler(message, process_product_name)
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

@bot.message_handler(commands=['delete_product'])
def delete_product_start(message):
    chat_id = message.chat.id
    if is_admin(message.from_user.id):
        bot.send_message(chat_id, "Введите название товара, который вы хотите удалить:")
        bot.register_next_step_handler(message, process_product_deletion)
    else:
        bot.send_message(chat_id, "У вас нет прав для выполнения этой команды.")

def process_product_deletion(message):
    chat_id = message.chat.id
    product_name = message.text

    # Проверка, существует ли товар с таким именем
    cursor.execute('SELECT * FROM products WHERE name = ?', (product_name,))
    product = cursor.fetchone()

    if product:
        cursor.execute('DELETE FROM products WHERE name = ?', (product_name,))
        conn.commit()
        bot.send_message(chat_id, f"Товар '{product_name}' успешно удален.")
    else:
        bot.send_message(chat_id, f"Товар с именем '{product_name}' не найден.")

bot.polling()
