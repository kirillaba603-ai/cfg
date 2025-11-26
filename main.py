import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

# ==========================================
# НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ СЮДА)
# ==========================================
BOT_TOKEN = "8262913636:AAGn7tdqJ1JuzSYhpti-M1aERfPyVWEawYQ"
CHANNEL_ID = "@hyp9x"  # ID или юзернейм канала
CHANNEL_URL = "https://t.me/hyp9x" # Ссылка для кнопки

# Текст конфига с HTML форматированием
CONFIG_TEXT = """
<b>🎉 Привет, спасибо за подписку! Вот твой конфиг:</b>

📹 <b>Настройки видео:</b>
<code>- Шейдеры: выс.
- Текстуры: выс.
- Модели: выс.
- Остальное: низкое.
(Иногда меняю по настроению)</code>

🎯 <b>Чувствительность:</b>
<code>- Обычная: 1.60
- В прицеле: 1.60
- Ускорение: 0</code>

🌀 <b>Гироскоп:</b>
<code>- Чувствительность: 1.20
- В прицеле: 1.20</code>

🔫 <b>Прицел:</b>
<code>- Тип: Точка
- Размер: 9.0</code>

🎮 <b>Код раскладки:</b>
<code>AaWmIbDULZ</code>

<b>УДАЧИ В ИГРЕ!</b> 🍀
"""

# Включаем логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Функция проверки подписки
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Статусы, которые считаются "подписанными"
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        # Если бот не админ канала, он не сможет проверить подписку
        return False

# 1. Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем кнопку
    builder = InlineKeyboardBuilder()
    builder.button(text="Получить конфиг ⚙️", callback_data="check_sub")
    
    await message.answer(
        "👋 Привет! Я помогу тебе получить конфиг.\n\n👇 Нажми на кнопку ниже, чтобы продолжить.",
        reply_markup=builder.as_markup()
    )

# 2. Обработчик нажатия на кнопки (проверка подписки)
@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)

    if is_subscribed:
        # Если подписан - добавляем кнопку и шлем конфиг
        builder = InlineKeyboardBuilder()
        builder.button(text="Голда за 10 рублей 🪙", url="https://t.me/gamecourse_golda_bot?start=98")
        await callback.message.answer(CONFIG_TEXT, parse_mode=ParseMode.HTML, reply_markup=builder.as_markup())
        await callback.answer("✅ Готово!") # Убираем часики загрузки
    else:
        # Если НЕ подписан - формируем клавиатуру с подпиской
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="Подписаться ↗️", url=CHANNEL_URL)
        )
        builder.row(
            InlineKeyboardButton(text="Проверить подписку 🔄", callback_data="check_sub")
        )
        
        await callback.message.answer(
            f"❌ <b>Доступ закрыт!</b>\n\nЧтобы получить конфиг, ты должен быть подписан на канал {CHANNEL_ID}.\n\nПодпишись и нажми кнопку проверки 👇",
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer("🔒 Сначала подпишись!")

# Запуск процесса поллинга (прослушивания обновлений)
async def main():
    print("🚀 Бот запущен...")
    # Удаляем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")
