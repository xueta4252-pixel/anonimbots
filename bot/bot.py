import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import config
import handlers

# эта команда включает показ ошибок в черном окне чтобы мы их видели
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# эта настройка отключает ненужные текстовые сообщения от самой системы
logging.getLogger("httpx").setLevel(logging.WARNING)

# это главная функция которая подготавливает и запускает всю нашу программу
def main():
    # создаем каркас программы с указанием специального пароля
    application = Application.builder().token(config.TOKEN).build()

    # говорим программе какую часть кода вызывать если пришло слово старт
    application.add_handler(CommandHandler("start", handlers.start_handler))
    
    # говорим программе какую часть кода вызывать если пришло слово статистика
    application.add_handler(CommandHandler("stats", handlers.stats_handler))
    
    # говорим программе какую часть кода вызывать если кто-то нажал кнопку
    application.add_handler(CallbackQueryHandler(handlers.reply_handler))
    
    # говорим программе какую часть кода вызывать когда приходит любой текст
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.message_handler))
    
    # говорим программе какую часть кода вызывать на все остальные непонятные слова
    application.add_handler(MessageHandler(filters.COMMAND, handlers.unknown_handler))

    # выводим сообщение что все хорошо и запускаем бесконечный процесс ожидания
    print("Бот успешно запущен!")
    application.run_polling()

# этот блок делает так чтобы программа запускалась только когда мы ее вызываем напрямую
if __name__ == "__main__":
    main()
