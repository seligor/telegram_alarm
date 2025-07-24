import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from database import init_db, add_user, get_users_in_group, get_user_group
from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# Состояния FSM
class AlarmStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_message = State()
    waiting_for_media = State()


# Клавиатуры
def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚨 Отправить тревогу")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )


def get_text_skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Без текста")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )


def get_media_skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼 Без медиа")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )


def get_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


# Форматированное сообщение помощи
def get_help_message(user_id: int, bot_username: str) -> str:
    group_id = get_user_group(user_id) or "не установлен"
    return (
        "🔔 <b>Справка по боту тревожных сигналов</b>\n\n"
        "📌 <b>Номер группы</b> можно установить или изменить командой\n"
        "👉 <code>/change_grp</code>\n\n"
        "🔢 Это девятизначный номер группы, который вам должен сообщить\n"
        "тот, кто дал ссылку на этого бота.\n\n"
        "📡 В зависимости от номера группы производится рассылка\n"
        "только участникам этой группы.\n\n"
        "🔷 <b>Ваш номер группы:</b> <code>{group_id}</code>\n\n"
        "👥 Чтобы добавить нового пользователя в оповещения,\n"
        "сообщите ему:\n"
        "1. Ссылку на бота @{bot_username}\n"
        "2. Номер группы для уведомлений <code>{group_id}</code>\n\n"
        "🚨 Для отправки тревоги используйте кнопку меню"
    ).format(group_id=group_id, bot_username=bot_username)


# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🚨 <b>Бот тревожной сигнализации</b>\n\n"
        "Используйте кнопки меню или команду /help для справки.",
        reply_markup=get_main_kb()
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    bot_username = (await bot.get_me()).username
    help_text = get_help_message(message.from_user.id, bot_username)
    await message.answer(
        help_text,
        reply_markup=get_main_kb(),
        disable_web_page_preview=True
    )


@dp.message(Command("change_grp"))
async def cmd_change_group(message: Message, state: FSMContext):
    await state.set_state(AlarmStates.waiting_for_group)
    await message.answer(
        "🔢 Введите новый 9-значный групповой код:",
        reply_markup=get_cancel_kb()
    )


@dp.message(F.text == "❌ Отмена")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=get_main_kb()
    )


@dp.message(F.text == "ℹ️ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


# Регистрация группы
@dp.message(AlarmStates.waiting_for_group, F.text.regexp(r'^\d{9}$'))
async def register_group(message: Message, state: FSMContext):
    group_id = message.text
    try:
        add_user(message.from_user.id, message.from_user.username, group_id)
        await state.clear()
        await message.answer(
            f"✅ Группа успешно изменена на <code>{group_id}</code>!",
            reply_markup=get_main_kb()
        )
    except Exception as e:
        logger.error(f"Ошибка изменения группы: {e}")
        await message.answer(
            "⚠️ Ошибка при изменении группы. Попробуйте позже.",
            reply_markup=get_main_kb()
        )


# Тревожный сигнал
@dp.message(F.text == "🚨 Отправить тревогу")
async def alarm_start(message: Message, state: FSMContext):
    if not get_user_group(message.from_user.id):
        await message.answer(
            "⚠️ Сначала установите номер группы командой /change_grp",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    await state.set_state(AlarmStates.waiting_for_message)
    await message.answer(
        "✏️ Введите сообщение тревоги или нажмите «Без текста»:",
        reply_markup=get_text_skip_kb()
    )


@dp.message(AlarmStates.waiting_for_message, F.text == "📝 Без текста")
@dp.message(AlarmStates.waiting_for_message, F.text)
async def alarm_message(message: Message, state: FSMContext):
    text = "" if message.text == "📝 Без текста" else message.html_text
    await state.update_data(text=text)
    await state.set_state(AlarmStates.waiting_for_media)
    await message.answer(
        "🖼️ Прикрепите фото/видео или нажмите «Без медиа»:",
        reply_markup=get_media_skip_kb()
    )


@dp.message(AlarmStates.waiting_for_media, F.text == "🖼 Без медиа")
@dp.message(AlarmStates.waiting_for_media, F.photo | F.video)
async def alarm_media(message: Message, state: FSMContext):
    media = None
    if message.photo:
        media = ("photo", message.photo[-1].file_id)
    elif message.video:
        media = ("video", message.video.file_id)

    await state.update_data(media=media)
    await send_alarm(message, state)


async def send_alarm(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_group = get_user_group(message.from_user.id)

        if not user_group:
            await message.answer("Ошибка: группа не найдена!", reply_markup=get_main_kb())
            await state.clear()
            return

        alarm_msg = (
            f"🚨 <b>ТРЕВОГА от @{message.from_user.username} (группа {user_group})!</b>"
            f"\n\n{data.get('text', '')}"
        )

        users = [
            (uid, uname) for uid, uname in get_users_in_group(user_group)
            if uid != message.from_user.id
        ]

        if not users:
            await message.answer("В вашей группе нет других пользователей!")
            await state.clear()
            return

        success_sent = 0
        media = data.get('media')

        for user_id, username in users:
            try:
                if media:
                    media_type, file_id = media
                    if media_type == "photo":
                        await bot.send_photo(
                            user_id,
                            photo=file_id,
                            caption=alarm_msg,
                            reply_markup=get_main_kb()
                        )
                    else:
                        await bot.send_video(
                            user_id,
                            video=file_id,
                            caption=alarm_msg,
                            reply_markup=get_main_kb()
                        )
                else:
                    await bot.send_message(
                        user_id,
                        alarm_msg,
                        reply_markup=get_main_kb()
                    )

                success_sent += 1
            except Exception as e:
                logger.error(f"Ошибка отправки {username} ({user_id}): {e}")

        await message.answer(
            f"✅ Тревога отправлена {success_sent}/{len(users)} участникам группы!",
            reply_markup=get_main_kb()
        )

    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        await message.answer(
            "⚠️ Ошибка отправки. Попробуйте позже.",
            reply_markup=get_main_kb()
        )
    finally:
        await state.clear()


# Запуск бота
async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
