from telebot.async_telebot import AsyncTeleBot
from telebot import types
import aiosqlite
import sqlite3
from excRates import coinRate, rateState  # Импорт функций для работы с курсами криптовалют
import asyncio

# Инициализация бота с токеном
bot = AsyncTeleBot('6560618446:AAGPuABQdK-sDLc6eXt1xJ1xDtbiyoxP2-M')

# функция запуска двух корутин
async def main():
    await asyncio.gather(sendReminder(), bot.polling())

# Функция для создания новой кнопки
def newButton(txt, cb_data):
    return types.InlineKeyboardButton(txt, callback_data=cb_data)

# Функция для вывода активных и завершенных оповещений
async def reminders(message):
    global tg_id, count_completed_reminders, mes_text, mes_text1
    markup = types.InlineKeyboardMarkup()
    markup.add(newButton('Создать новое оповещение', 'new_reminder_from_remiders'))
    in_process = []
    # Получение всех уведомлений пользователя
    async with aiosqlite.connect('alerterbot.sql') as db:
        async with db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)) as cursor:
            count_completed_reminders = 0
            in_process_data = []
            for user in await cursor.fetchall():
                if user[-1] == 0:
                    count_completed_reminders += 1
                else:
                    in_process_data.append(user)

    if in_process_data == []:
        in_process_data = "нет"
    
    if in_process_data != "нет":
        in_process = []
        # Форматирование данных из БД для отправки пользователю
        for el in in_process_data:
            
            el = list(el[3:-1])
            if el[0] == 0: el[0] = "<b>💎BTC</b>"
            elif el[0] == 1: el[0] = "<b>💎ETH</b>"
            elif el[0] == 2: el[0] = "<b>💎SOL</b>"

            if el[1] == 'up': el[1] = "📈"
            else: el[1] = "📉"

            el[2] = f"<b>{el[2]}%</b>" 
            el[3] = f"<b>📊 {el[3]}$</b>"
            el = ' '.join(el)
            in_process.append(f'{el}\n')
            
        mes_text = f"Активные оповещения:\n{''.join(str(el) for el in in_process)}\nЗавершенных оповещений: {count_completed_reminders}"
    else:
        mes_text = f"Активные оповещения: {in_process_data}\nЗавершенных оповещений: {count_completed_reminders}"
        
    await bot.send_message(message.chat.id, mes_text, reply_markup=markup, parse_mode="HTML")
    
# Функция для создания нового оповещения
async def newReminder(message):
    markup = types.InlineKeyboardMarkup()
    button1 = newButton('Bitcoin (BTC)', 'BTC')
    button2 = newButton('Ethereum (ETH)', 'ETH')
    button3 = newButton('Solana (SOL)', 'SOL')
    markup.row(button1, button2, button3)
    await bot.send_message(message.chat.id, "Выберете криптовалюту для которой вам нужно оповещение", reply_markup=markup)
    # Установка состояния пользователя в "waiting_for_choice"

# Функция для отправки оповещений
async def sendReminder():
    global rate0, rate1, rate2
    while True:
        async with aiosqlite.connect('alerterbot.sql') as db:
            async with db.execute("SELECT * FROM users WHERE in_process = 1") as cursor:
                tasks = []
                rate0 = await coinRate(0)
                rate1 = await coinRate(1)
                rate2 = await coinRate(2)

                async for user in cursor:
                    if user[3] == 0:
                        tasks.append(rateState(bot, user[3], user[5], user[4], user[6], user[2], rate0))
                    if user[3] == 1:
                        tasks.append(rateState(bot, user[3], user[5], user[4], user[6], user[2], rate1))
                    if user[3] == 2:
                        tasks.append(rateState(bot, user[3], user[5], user[4], user[6], user[2], rate2))
                await asyncio.gather(*tasks)
                await asyncio.sleep(300)

# Функция вывода курса на данный момент
async def rateNow(call, chat_id):
        global coin, choice, rate0, rate1, rate2
    # Удаляем сообщение с кнопками
        await bot.delete_message(chat_id, call.message.message_id)
        if call.data == 'BTC':
            coin = 0
            await bot.send_message(chat_id, f"Курс BTC/USD на данный момент: ${rate0}")
        elif call.data == 'ETH':
            coin = 1
            await bot.send_message(chat_id, f"Курс ETH/USD на данный момент: ${rate1}")
        elif call.data == 'SOL':
            coin = 2
            await bot.send_message(chat_id, f"Курс SOL/USD на данный момент: ${rate2}")
        

# Функция для выбора направления изменения курса
async def up_or_down(message):
    markup = types.InlineKeyboardMarkup()
    button1 = newButton('Курс вырастет', 'up')
    button2 = newButton('Курс упадет', 'down')
    markup.row(button1, button2)
    await bot.send_message(message.chat.id, "Уведомления для какого события вам нужно?", reply_markup=markup)                  

# Обработчик команд
@bot.message_handler(commands=['start', 'menu'])
async def start(message):
    global tg_id, name
    tg_id = message.from_user.id
    name = message.from_user.first_name
    async with aiosqlite.connect('alerterbot.sql') as db:
        async with db.execute("SELECT tg_id FROM users WHERE tg_id=?", (tg_id,)) as cursor:
            if not await cursor.fetchone():
                await bot.send_message(message.chat.id, "Это бот для уведомлений об изменениях на рынке!")
                await newReminder(message)
            else:
                await reminders(message)

# Обработчик сообщений, возвращающийся после выбора пользователя
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_percent")
async def percent(message):
    global pers, coin, choice, tg_id, name, mes_text1
    try:
        pers = float(message.text)
        if pers >= 0:
            markup = types.InlineKeyboardMarkup()
            markup.add(newButton('Создать новое оповещение', 'new_reminder_from_persent'))
            markup.add(newButton('Мои оповещения', 'reminders'))
            mes_text1 = f"Уведомление придет вам, как только курс изменится на {pers}%"
            await bot.send_message(message.chat.id, mes_text1, reply_markup=markup)
            
            # Установка состояния пользователя в "None"
            user_states[message.chat.id] = None
            
            async with aiosqlite.connect('alerterbot.sql') as db:
                async with db.execute("INSERT INTO users (tg_id, name, chat_id, coin, choice, persent, start_rate, in_process) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (tg_id, name, message.chat.id, coin, choice, pers, await coinRate(coin), 1)) as cursor:
                    await db.commit()
        else:
            await bot.send_message(message.chat.id, "Введите неотрицательное число")
            await bot.register_next_step_handler(message, percent)
    except ValueError:
        await bot.send_message(message.chat.id, "Неверный ввод. Введите число")
        await bot.register_next_step_handler(message, percent)  # Вызываем функцию percent снова для ожидания нового ввода пользователя

# Обработчик для получения информации о криптовалюте при выборе пользователем
@bot.callback_query_handler(func=lambda call: True)
async def handle_callback(call):
    global count_completed_reminders, mes_text, mes_text1, choice
    chat_id = call.message.chat.id  # Идентификатор чата пользователя
    if call.data == 'new_reminder_from_remiders': # Вызов из reminders
        await newReminder(call.message)
        await bot.edit_message_text(mes_text,  chat_id, call.message.message_id, parse_mode="HTML")
    elif call.data == 'new_reminder_from_persent': # Вызов из persent
        await newReminder(call.message)
        await bot.edit_message_text(mes_text1,  chat_id, call.message.message_id, parse_mode="HTML")
    elif call.data == 'reminders': # Вызов из percent
        await reminders(call.message)
        await bot.edit_message_text(mes_text1,  chat_id, call.message.message_id, parse_mode="HTML")
    elif call.data in ['BTC', 'ETH', 'SOL']: # Вызов из newReminder
        await rateNow(call, chat_id)
        await up_or_down(call.message)
    elif call.data in ['up', 'down']: # Вызов из up_or_down
        # Устанавливаем состояние пользователя в "waiting_for_percent"
        user_states[chat_id] = "waiting_for_percent"
        await bot.delete_message(chat_id, call.message.message_id)
        if call.data == 'up':
            choice = 'up'
        else: 
            choice = 'down'
        await bot.send_message(chat_id, "Введите процент изменения (Например: 10 или 0.1)")
    else:
        await bot.send_message(chat_id, "Неверный ввод")

# Создаем таблицу в базе данных, если ее нет
db = sqlite3.connect('alerterbot.sql')
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users(tg_id TEXT, name TEXT, chat_id INT, coin INT, choice TEXT, persent REAL, start_rate REAL, in_process INT)")
db.commit()
cursor.close()
db.close()

# Словарь для хранения состояний пользователей
user_states = {}

# Запускаем основной цикл асинхронного приложения
asyncio.run(main())