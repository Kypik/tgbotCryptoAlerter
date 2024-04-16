import requests
import aiosqlite
import telebot

# Функция для получения текущего курса криптовалюты
async def coinRate(coin):
    url = "https://api.binance.com/api/v3/ticker/price?symbol=" # Часть URL которое возвращает JSON с данными о монете
    coins = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'] # Вторая часть URL из доступных монет
    user_url = url + coins[coin]
    response = requests.get(user_url)
    
    if response.status_code == 200:
        data = response.json()
        coin_price = float(data['price']) # Получение стоимости монеты
        return coin_price
    else:
        return "Ошибка при запросе:", response.status_code

# Функция для обработки изменения курса криптовалюты и отправки уведомлений
async def rateState(bot, coin, pers, choice, rate, chat_id, new_rate):
    async with aiosqlite.connect('alerterbot.sql') as db:
        async with db.cursor() as cursor:      
            pers_change = ((new_rate - rate) / rate) * 100
            
            # Обработка случаев, когда курс криптовалюты изменился в соответствии с выбранными параметрами
            if choice == "up":
                if pers_change < pers or rate > new_rate:
                    # Если изменение не соответствует заданному порогу, не делаем ничего
                    print(coin, pers, choice, rate, new_rate, pers_change)
                else:
                    # Обновляем состояние в базе данных и отправляем уведомление
                    await cursor.execute("UPDATE users SET in_process = 0 WHERE in_process = 1 AND start_rate = ?", (rate, ))
                    await db.commit()
                    try:
                        await bot.send_message(chat_id, f"Курс увеличился на %{pers}!\nКурс на данный момент: ${new_rate}")
                    except telebot.asyncio_helper.ApiTelegramException:
                        print("Не удалось отправить сообщение")

            elif choice == "down":
                if pers_change > -pers or rate < new_rate:
                    # Если изменение не соответствует заданному порогу, не делаем ничего
                    print(coin, pers, choice, rate, new_rate, pers_change)
                else:
                    # Обновляем состояние в базе данных и отправляем уведомление
                    await cursor.execute("UPDATE users SET in_process = 0 WHERE in_process = 1 AND start_rate = ?", (rate, ))
                    await db.commit()
                    try:
                        await bot.send_message(chat_id, f"Курс уменьшился на %{pers}!\nКурс на данный момент: ${new_rate}")
                    except telebot.asyncio_helper.ApiTelegramException:
                        print("Не удалось отправить сообщение")