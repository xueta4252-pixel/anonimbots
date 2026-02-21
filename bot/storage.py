import json
import os
import time

# где хранятся наши данные и текстовые записи
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
STORAGE_FILE = os.path.join(DATA_DIR, "storage.json")
LOG_FILE = os.path.join(LOGS_DIR, "messages.txt")

# создаем нужные папки для файлов если их еще нет
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# тут мы храним важную информацию в памяти пока программа работает
pending_replies = {}
user_admin = {}
last_message_time = {}
stats = {}

# эта функция читает прошлые данные из файла при запуске
def load_data():
    global pending_replies, user_admin, last_message_time, stats
    # проверяем есть ли уже такой файл
    if os.path.exists(STORAGE_FILE):
        # открываем файл и переносим информацию в память
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            pending_replies = data.get("pending_replies", {})
            user_admin = data.get("user_admin", {})
            last_message_time = data.get("last_message_time", {})
            stats = data.get("stats", {})
    else:
        # если файла нет, сохраняем пустые данные чтобы создать его сразу со правильной структурой
        save_data()

# эта функция обновляет содержимое файла новыми данными
def save_data():
    data = {
        "pending_replies": pending_replies,
        "user_admin": user_admin,
        "last_message_time": last_message_time,
        "stats": stats
    }
    # открываем файл и записываем все текущие данные
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# эта функция делает текстовую запись о новом событии
def log_message(text):
    # открываем файл с текстом и добавляем новую строчку в конец
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")

# запускаем чтение данных прямо сейчас
load_data()

# эта функция проверяет не слишком ли часто участник пишет
def check_spam(user_id):
    user_id_str = str(user_id)
    current_time = time.time()
    
    # проверяем писал ли участник нам раньше
    if user_id_str in last_message_time:
        import config
        time_passed = current_time - last_message_time[user_id_str]
        # проверяем прошло ли достаточно времени
        if time_passed < config.SPAM_DELAY:
            return False
            
    # запоминаем время последнего сообщения
    last_message_time[user_id_str] = current_time
    save_data()
    return True

# эта функция запоминает по чьей ссылке пришел участник
def set_user_admin(user_id, admin_id):
    user_admin[str(user_id)] = admin_id
    save_data()

# эта функция отдает нам владельца ссылки для конкретного участника
def get_user_admin(user_id):
    return user_admin.get(str(user_id))

# эта функция запоминает кому собирается ответить организатор
def save_message(admin_id, user_id):
    pending_replies[str(admin_id)] = user_id
    save_data()

# эта функция отдает того кому сейчас отвечает организатор
def get_user(admin_id):
    return pending_replies.get(str(admin_id))

# эта функция удаляет ожидание ответа когда он уже был отправлен
def delete_message(admin_id):
    admin_id_str = str(admin_id)
    # проверяем есть ли такой человек в списке
    if admin_id_str in pending_replies:
        del pending_replies[admin_id_str]
        save_data()

# эта функция добавляет одно сообщение к общей статистике человека
def add_stat(admin_id):
    admin_id_str = str(admin_id)
    # проверяем есть ли уже записи для этого человека
    if admin_id_str not in stats:
        stats[admin_id_str] = 0
    # добавляем единицу к числу получаемых сообщений
    stats[admin_id_str] += 1
    save_data()

# эта функция отдает все цифры активности
def get_stats():
    return stats
