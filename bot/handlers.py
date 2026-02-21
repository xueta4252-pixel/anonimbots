from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
import storage

# эта функция дает ответ если человек ошибся или пришел не по ссылке
async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ты пришёл не по ссылке, попроси у нужного человека его ссылку")

# эта функция срабатывает когда человек из интернета переходит по ссылке
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    args = context.args
    
    # проверяем указал ли человек правильное слово в ссылке
    if args and args[0] in config.ADMIN_LINKS:
        admin_id = config.ADMIN_LINKS[args[0]]
        # запоминаем какому человеку в итоге будет писать этот гость
        storage.set_user_admin(user.id, admin_id)
        # отправляем приветственное сообщение
        await update.message.reply_text("Привет! Напиши свой анонимный вопрос 👇")
    else:
        # если ссылка неправильная — говорим что нужна правильная
        await unknown_handler(update, context)

# эта функция обрабатывает все входящие текстовые сообщения
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    # проверяем является ли отправитель одним из организаторов бота
    if user.id in [config.ALICE_ID, config.MAC_ID, config.OIBOI_ID]:
        # проверяем ждет ли бот от этого организатора ответ кому-то
        target_user_id = storage.get_user(user.id)
        if target_user_id:
            # пробуем отправить ответ нужному человеку
            try:
                await context.bot.send_message(chat_id=target_user_id, text=f"💬 Ответ от получателя:\n\n{text}")
                await update.message.reply_text("✅ Твой ответ отправлен!")
            except Exception:
                await update.message.reply_text("❌ Ошибка отправки. Возможно человек заблокировал бота.")
            
            # убираем организатора из списка ожидающих
            storage.delete_message(user.id)
            return

    # ищем к какому организатору привязан этот человек
    admin_id = storage.get_user_admin(user.id)
    
    # если человек не привязан ни к кому — он пришел не по ссылке
    if not admin_id:
        await unknown_handler(update, context)
        return

    # проверяем не пишет ли человек сообщения слишком часто
    if not storage.check_spam(user.id):
        await update.message.reply_text(f"⏳ Подожди немного! Писать можно раз в {config.SPAM_DELAY} секунд.")
        return

    # определяем как будет выглядеть имя отправителя
    if user.username:
        sender_name = f"@{user.username}"
    else:
        sender_name = f"Аноним (ID: {user.id})"

    # определяем имя организатора для записи в лог файл
    admin_name = "Неизвестно"
    if admin_id == config.ALICE_ID:
        admin_name = "Алиса"
    elif admin_id == config.MAC_ID:
        admin_name = "Мацукевич"

    # записываем сообщение в лог файл
    storage.log_message(f"{sender_name} (ID: {user.id}) → админ {admin_name}: {text}")

    # готовим текст который увидит организатор
    admin_text = f"👀 Кто отправил: {sender_name}\n✏️ Что написал: {text}"
    
    # создаем кнопку для быстрого ответа
    keyboard = [[InlineKeyboardButton("Ответить 💬", callback_data=f"reply_{user.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # отправляем вопрос нужному организатору
    try:
        await context.bot.send_message(chat_id=admin_id, text=admin_text, reply_markup=reply_markup)
        # увеличиваем счетчик сообщений этого организатора
        storage.add_stat(admin_id)
    except Exception as e:
        storage.log_message(f"Ошибка отправки админу {admin_id}: {e}")

    # отправляем копию главному начальнику (он видит всё)
    if admin_id != config.OIBOI_ID:
        try:
            await context.bot.send_message(chat_id=config.OIBOI_ID, text=admin_text, reply_markup=reply_markup)
        except Exception:
            pass

    # показываем человеку кнопку чтобы он мог задать ещё один вопрос
    user_keyboard = [[InlineKeyboardButton("Отправить ещё ✉️", callback_data="send_more")]]
    user_reply_markup = InlineKeyboardMarkup(user_keyboard)
    await update.message.reply_text("✅ Вопрос отправлен!", reply_markup=user_reply_markup)

# эта функция срабатывает когда кто-то нажимает кнопку под сообщением
async def reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # если человек нажал кнопку "отправить ещё" — просим написать новый вопрос
    if data == "send_more":
        await query.message.reply_text("Привет! Напиши свой анонимный вопрос 👇")
        return
        
    # если организатор нажал кнопку "ответить" — запоминаем кому он хочет ответить
    if data.startswith("reply_"):
        user_id = data.split("_")[1]
        admin_id = query.from_user.id
        
        # запоминаем что организатор собирается написать ответ этому человеку
        storage.save_message(admin_id, user_id)
        await query.message.reply_text("Напиши свой ответ текстом, и я перешлю его анонимно ✉️")

# эта функция показывает статистику когда организаторы пишут /stats
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    current_stats = storage.get_stats()
    
    # если это главный начальник — показываем статистику по всем
    if user_id == config.OIBOI_ID:
        alice_count = current_stats.get(str(config.ALICE_ID), 0)
        mac_count = current_stats.get(str(config.MAC_ID), 0)
        total = alice_count + mac_count
        
        text = (
            f"📊 Общая статистика:\n\n"
            f"Алиса получено вопросов: {alice_count}\n"
            f"Мацукевич получено вопросов: {mac_count}\n"
            f"Всего вопросов: {total}"
        )
        await update.message.reply_text(text)
        
    # если это обычный организатор — показываем только его статистику
    elif user_id in [config.ALICE_ID, config.MAC_ID]:
        my_count = current_stats.get(str(user_id), 0)
        await update.message.reply_text(f"📊 Твоя статистика:\n\nКоличество полученных вопросов: {my_count}")
        
    else:
        # если обычный пользователь написал /stats — он не имеет доступа
        await unknown_handler(update, context)
