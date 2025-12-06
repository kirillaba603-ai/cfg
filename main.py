import asyncio
import logging
import json
import os
import time
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ==========================================
# НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ СЮДА)
# ==========================================
BOT_TOKEN = "8262913636:AAGn7tdqJ1JuzSYhpti-M1aERfPyVWEawYQ"
CHANNEL_ID = "@hyp9x"  # ID или юзернейм канала
CHANNEL_URL = "https://t.me/hyp9x"  # Ссылка для кнопки
ADMIN_ID = 6530644564  # <-- ЗАМЕНИ НА СВОЙ TELEGRAM ID

# Файл для хранения данных
DATA_FILE = "bot_data.json"

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

# ==========================================
# ХРАНИЛИЩЕ ДАННЫХ
# ==========================================
def load_data():
    """Загрузить данные из файла"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "secret_key": "1234",  # Ключ по умолчанию
        "video_url": "https://youtube.com",  # Ссылка на видео по умолчанию
        "total_users": 0,
        "successful_keys": 0,
        "pending_notifications": []  # Очередь рассылки
    }

def save_data(data):
    """Сохранить данные в файл"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Загружаем данные при старте
bot_data = load_data()

# ==========================================
# FSM СОСТОЯНИЯ
# ==========================================
class KeyInput(StatesGroup):
    waiting_for_key = State()

class AdminStates(StatesGroup):
    waiting_for_new_key = State()
    waiting_for_new_video = State()

# Включаем логирование, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

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

# ==========================================
# ФОНОВАЯ ЗАДАЧА: РАССЫЛКА
# ==========================================
async def notification_worker():
    """Проверяет очередь и отправляет сообщения"""
    print("[WORKER] Запущен процесс проверки рассылок...")
    while True:
        try:
            current_time = time.time()
            # Копируем список, чтобы безопасно удалять из оригинала
            # Используем get() для безопасности, если поле еще не создано
            notifications = bot_data.get("pending_notifications", [])
            remaining_notifications = []
            
            data_changed = False
            
            for note in notifications:
                if current_time >= note["send_time"]:
                    # Время пришло! Отправляем сообщение
                    user_id = note["user_id"]
                    try:
                        builder = InlineKeyboardBuilder()
                        builder.button(text="💰 Купить голду", url="https://t.me/gamecourse_golda_bot?start=98")
                        
                        await bot.send_message(
                            chat_id=user_id,
                            text=(
                                "⏳ <b>Ты успел купить голду за 10 рублей?</b>\n\n"
                                "Завтра уже не будет такой возможности! 😱\n"
                                "<b>Сегодня последний день акции.</b>"
                            ),
                            reply_markup=builder.as_markup(),
                            parse_mode=ParseMode.HTML
                        )
                        print(f"[WORKER] Отправлено напоминание пользователю {user_id}")
                    except Exception as e:
                        # Если пользователь заблокировал бота, просто логируем
                        print(f"[WORKER] Ошибка отправки {user_id}: {e}")
                    
                    # Не добавляем в remaining_notifications -> удаляем из очереди
                    data_changed = True
                else:
                    # Время еще не пришло, оставляем
                    remaining_notifications.append(note)
            
            if data_changed:
                bot_data["pending_notifications"] = remaining_notifications
                save_data(bot_data)
                
        except Exception as e:
            logging.error(f"[WORKER] Ошибка в цикле рассылки: {e}")
            
        # Проверяем каждые 5 секунд
        await asyncio.sleep(5)

# ==========================================
# ПРОВЕРКА АДМИНА
# ==========================================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ==========================================
# КОМАНДА /start
# ==========================================
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    global bot_data
    bot_data["total_users"] = bot_data.get("total_users", 0) + 1
    save_data(bot_data)
    
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎬 Видео с ключом", callback_data="show_video")
    )
    builder.row(
        InlineKeyboardButton(text="🔑 Ввести ключ", callback_data="enter_key")
    )
    
    await message.answer(
        "👋 <b>Привет!</b>\n\n"
        "Чтобы получить конфиг, тебе нужно:\n"
        "1️⃣ Посмотреть видео и найти <b>4-значный ключ</b>\n"
        "2️⃣ Ввести ключ и получить конфиг\n\n"
        "👇 Выбери действие:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

# ==========================================
# КНОПКА "ВИДЕО С КЛЮЧОМ"
# ==========================================
@dp.callback_query(F.data == "show_video")
async def show_video(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="▶️ Смотреть видео", url=bot_data["video_url"])
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")
    )
    
    await callback.message.edit_text(
        "🎬 <b>Посмотри видео и найди 4-значный ключ!</b>\n\n"
        "Ключ спрятан в видео. Внимательно смотри! 👀\n\n"
        "После того как найдёшь — возвращайся и вводи ключ.",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ==========================================
# КНОПКА "НАЗАД"
# ==========================================
@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎬 Видео с ключом", callback_data="show_video")
    )
    builder.row(
        InlineKeyboardButton(text="🔑 Ввести ключ", callback_data="enter_key")
    )
    
    await callback.message.edit_text(
        "👋 <b>Привет!</b>\n\n"
        "Чтобы получить конфиг, тебе нужно:\n"
        "1️⃣ Посмотреть видео и найти <b>4-значный ключ</b>\n"
        "2️⃣ Ввести ключ и получить конфиг\n\n"
        "👇 Выбери действие:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ==========================================
# КНОПКА "ВВЕСТИ КЛЮЧ"
# ==========================================
@dp.callback_query(F.data == "enter_key")
async def enter_key(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id)
    
    if not is_subscribed:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_URL)
        )
        builder.row(
            InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="enter_key")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")
        )
        
        await callback.message.edit_text(
            f"❌ <b>Сначала подпишись на канал!</b>\n\n"
            f"Канал: {CHANNEL_ID}\n\n"
            "После подписки нажми «Проверить подписку» 👇",
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer("🔒 Подпишись на канал!")
        return
    
    await state.set_state(KeyInput.waiting_for_key)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="back_to_start")
    )
    
    await callback.message.edit_text(
        "🔑 <b>Введи 4-значный ключ из видео:</b>\n\n"
        "Просто напиши его в чат 👇",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ==========================================
# ОБРАБОТКА ВВОДА КЛЮЧА
# ==========================================
@dp.message(KeyInput.waiting_for_key)
async def process_key_input(message: types.Message, state: FSMContext):
    global bot_data
    user_key = message.text.strip()
    
    if user_key == bot_data["secret_key"]:
        await state.clear()
        bot_data["successful_keys"] = bot_data.get("successful_keys", 0) + 1
        
        # ДОБАВЛЯЕМ В ОЧЕРЕДЬ РАССЫЛКИ (ТЕСТ: 10 СЕКУНД)
        # Потом заменить 10 на 600 (10 минут)
        send_time = time.time() + 10
        
        # Инициализируем список, если его нет
        if "pending_notifications" not in bot_data:
            bot_data["pending_notifications"] = []
            
        bot_data["pending_notifications"].append({
            "user_id": message.from_user.id,
            "send_time": send_time
        })
        
        save_data(bot_data)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="💰 Голда за 10 рублей", url="https://t.me/gamecourse_golda_bot?start=98")
        
        await message.answer(
            "✅ <b>Ключ верный!</b>\n\n" + CONFIG_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=builder.as_markup()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🎬 Посмотреть видео", url=bot_data["video_url"])
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")
        )
        
        await message.answer(
            "❌ <b>Неверный ключ!</b>\n\n"
            "Посмотри видео внимательнее и попробуй снова.",
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )

# ==========================================
# АДМИН-ПАНЕЛЬ
# ==========================================
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У тебя нет доступа к админ-панели.")
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔑 Изменить ключ", callback_data="admin_change_key")
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Изменить видео", callback_data="admin_change_video")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        f"🔑 Текущий ключ: <code>{bot_data['secret_key']}</code>\n"
        f"🎬 Видео: {bot_data['video_url']}\n\n"
        "Выбери действие:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

# ==========================================
# АДМИН: ИЗМЕНИТЬ КЛЮЧ
# ==========================================
@dp.callback_query(F.data == "admin_change_key")
async def admin_change_key(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!")
        return
    
    await state.set_state(AdminStates.waiting_for_new_key)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_cancel")
    )
    
    await callback.message.edit_text(
        "🔑 <b>Введи новый 4-значный ключ:</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_new_key)
async def process_new_key(message: types.Message, state: FSMContext):
    global bot_data
    
    if not is_admin(message.from_user.id):
        return
    
    new_key = message.text.strip()
    
    if len(new_key) != 4 or not new_key.isdigit():
        await message.answer("❌ Ключ должен состоять из 4 цифр! Попробуй ещё раз:")
        return
    
    bot_data["secret_key"] = new_key
    save_data(bot_data)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Ключ успешно изменён!</b>\n\n"
        f"Новый ключ: <code>{new_key}</code>",
        parse_mode=ParseMode.HTML
    )

# ==========================================
# АДМИН: ИЗМЕНИТЬ ВИДЕО
# ==========================================
@dp.callback_query(F.data == "admin_change_video")
async def admin_change_video(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!")
        return
    
    await state.set_state(AdminStates.waiting_for_new_video)
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_cancel")
    )
    
    await callback.message.edit_text(
        "🎬 <b>Отправь ссылку на новое видео:</b>",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.message(AdminStates.waiting_for_new_video)
async def process_new_video(message: types.Message, state: FSMContext):
    global bot_data
    
    if not is_admin(message.from_user.id):
        return
    
    new_url = message.text.strip()
    
    if not new_url.startswith("http"):
        await message.answer("❌ Это не похоже на ссылку! Отправь корректный URL:")
        return
    
    bot_data["video_url"] = new_url
    save_data(bot_data)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Ссылка на видео обновлена!</b>\n\n"
        f"Новая ссылка: {new_url}",
        parse_mode=ParseMode.HTML
    )

# ==========================================
# АДМИН: СТАТИСТИКА
# ==========================================
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!")
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    )
    
    await callback.message.edit_text(
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{bot_data.get('total_users', 0)}</b>\n"
        f"✅ Успешных вводов ключа: <b>{bot_data.get('successful_keys', 0)}</b>\n"
        f"🔑 Текущий ключ: <code>{bot_data['secret_key']}</code>\n"
        f"🎬 Видео: {bot_data['video_url']}",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ==========================================
# АДМИН: ОТМЕНА / НАЗАД
# ==========================================
@dp.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.answer()

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!")
        return
    
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔑 Изменить ключ", callback_data="admin_change_key")
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Изменить видео", callback_data="admin_change_video")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\n"
        f"🔑 Текущий ключ: <code>{bot_data['secret_key']}</code>\n"
        f"🎬 Видео: {bot_data['video_url']}\n\n"
        "Выбери действие:",
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

# ==========================================
# БЫСТРЫЕ КОМАНДЫ ДЛЯ АДМИНА
# ==========================================
@dp.message(Command("setkey"))
async def cmd_setkey(message: types.Message):
    global bot_data
    
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: /setkey 1234")
        return
    
    new_key = args[1].strip()
    if len(new_key) != 4 or not new_key.isdigit():
        await message.answer("❌ Ключ должен быть 4-значным числом!")
        return
    
    bot_data["secret_key"] = new_key
    save_data(bot_data)
    
    await message.answer(f"✅ Ключ изменён на: <code>{new_key}</code>", parse_mode=ParseMode.HTML)

@dp.message(Command("setvideo"))
async def cmd_setvideo(message: types.Message):
    global bot_data
    
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Использование: /setvideo https://youtube.com/...")
        return
    
    new_url = args[1].strip()
    if not new_url.startswith("http"):
        await message.answer("❌ Это не похоже на ссылку!")
        return
    
    bot_data["video_url"] = new_url
    save_data(bot_data)
    
    await message.answer(f"✅ Видео изменено на: {new_url}")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "� <b>Статистика</b>\n\n"
        f"👥 Пользователей: {bot_data.get('total_users', 0)}\n"
        f"✅ Успешных ключей: {bot_data.get('successful_keys', 0)}\n"
        f"🔑 Ключ: <code>{bot_data['secret_key']}</code>\n"
        f"🎬 Видео: {bot_data['video_url']}",
        parse_mode=ParseMode.HTML
    )

# Запуск процесса поллинга (прослушивания обновлений)
async def main():
    print("[BOT] Бот запущен...")
    # Удаляем вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем фоновую задачу рассылки параллельно с ботом
    asyncio.create_task(notification_worker())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[BOT] Бот остановлен")
