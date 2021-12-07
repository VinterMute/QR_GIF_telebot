import queue
import telebot
import os
from threading import Thread
from MyQR import myqr


bot = telebot.TeleBot("API_KEY")
supported_chars = r"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ··,.:;+-*/\~!@#$%^&`'=<>[]()?_{}|"
q = queue.Queue()


def create_gif(text, path_to_gif, path_out_gif, name_out_gif):
    version, level, qr_name = myqr.run(
        # Add string or a URL (add http(s):// before it)
        words=text,
        # Set the highest fault tolerance rate
        version=1,
        # Control the error correction level,
        # the range is L, M, Q, H, increasing from left to right
        level='H',
        # Combining QR code + Image
        # Add file name eg. your_image.gif
        picture=path_to_gif,
        colorized=True,
        contrast=1.0,
        brightness=1.0,
        save_name=name_out_gif,
        save_dir=path_out_gif,
    )


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        """Привет, я бот который преобразует обычные qr коды в волшебные!
    Отправь мне любую гифку по твоему желанию и ссылку или текст которые нужно закодировать .
    Можно испольовать цифры, латиницу и спецальные символы. Удачных экспериментов! """,
    )


def make_and_send_gif(q: queue.Queue, bot):
    while True:
        message = q.get()
        bot.send_message(
            message.chat.id,
            "Приступил в твоему заданию, большая гифка - долго ждать, но я работаю",
        )
        path_to_gif = f'recive_gif/{message.chat.id}.gif'
        path_out_gif = f'done_gif/'
        name_out_gif = f'{message.chat.id}.gif'
        os.system(
            f"ffmpeg -y -i recive_gif/{message.chat.id}.mp4 recive_gif/{message.chat.id}.gif"
        )
       # os.system(f"rm recive_gif/{message.chat}.mp4")
        create_gif(message.text, path_to_gif, path_out_gif, name_out_gif)
        bot.send_document(
            chat_id=message.chat.id, data=open(path_out_gif + name_out_gif, 'rb')
        )
        q.task_done()


worker = Thread(
    target=make_and_send_gif,
    args=(
        q,
        bot,
    ),
)
worker.start()


@bot.message_handler(content_types=['text'])
def main_work(message):
    # Провряем есть ли запрещенные символы
    if not isinstance(message.text, str) or any(
        i not in supported_chars for i in message.text
    ):
        bot.send_message(
            message.chat.id,
            "Йоу, у тебя в сообщении левые символы. Пиши /help для подробностей",
        )
    else:
        file_in_dir = [
            os.path.splitext(filename)[0] for filename in os.listdir("recive_gif")
        ]
        if str(message.chat.id) in file_in_dir:  # Если есть файл в папке то работаем
            #                 make_and_send_gif(bot,message)
            bot.send_message(
                message.chat.id,
                f"Йоу, вижу текст, вижу гифку, подожди немножко, ты под номером {len(q.queue)} в очереди. ",
            )
            q.put(message)
        else:
            bot.send_message(
                message.chat.id, "Кажись ты, еще не отправлял гифку, скинь еще раз"
            )


@bot.message_handler(func=lambda message: True, content_types=['animation'])
def default_command(message):
    global message_one
    message_one = message
    if message.document.mime_type == "video/mp4":
        file_info = bot.get_file(message_one.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = f'recive_gif/{message_one.chat.id}.mp4'
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, "Принял Гифку, давай текст для закодирования")
    else:
        bot.send_message(message.chat.id, "Кажись, дружище это не гифка")


while True:
    try:
        bot.infinity_polling()
    except Exception as e:
        print(e)
