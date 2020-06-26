# Sergey Nazarov 17.05.2020
import sys
sys.path.append('../')
from time import sleep
from modules.class_jarvis import Jarvis

import logging

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s (%(levelname)s) %(asctime)s: %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.WARNING

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL, datefmt='%d.%m.%y %H:%M:%S')

if __name__ == '__main__':

    jarvis = Jarvis()

     # Telegram bot
    @jarvis.bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        _user = None
        for user in jarvis.bot.users:
            if str(message.from_user.id) == user.id:
                _user = user
                break
        if message.text == "привет":
            jarvis.bot.reply_to(message, "Привет, чем я могу тебе помочь?")
        elif message.text == "/help" or message.text == "help":
            if _user is not None:
                helpmessage = 'Help:\n'
                helpmessage += 'getmyid - получить свой telegram ID\n'
                helpmessage += '\n'
                helpmessage += 'pinstate - посмотреть список пинов\n'
                helpmessage += '\n'
                helpmessage += 'bind <pin1> <pin2> <...> - привязать к входному пину pin1 пины pin2 ..\n'
                helpmessage += '\n'
                helpmessage += 'unbind <pin1> <pin2> <...> - отвязать к входному пину pin1 пины pin2 ..\n'

                jarvis.bot.reply_to(message, helpmessage)
            else:
                jarvis.bot.reply_to(message, "Кто ты чудовище?")
        elif message.text == 'getmyid':
            jarvis.bot.reply_to(message, "Ваш ID: %s" % message.from_user.id)
        elif message.text == 'getconfig':
            if _user != None:
                doc = open(jarvis.arduino.config_path, 'rb')
                jarvis.bot.send_document(message.from_user.id, doc)
            else:
                jarvis.bot.reply_to(message, "Кто ты чудовище?")
        else:
            if _user is not None:
                jarvis.input_queue.put((message.text, _user, message))  # Поместили сообщение в оцередь на обработку
                __answe_wait_time = 5
                while __answe_wait_time > 0:
                    if (jarvis.telegram_answer_queue.qsize() > 0):
                        queue_typle = jarvis.telegram_answer_queue.get()
                        get_message = queue_typle[0]
                        answer = queue_typle[1]
                        if get_message == message:
                            jarvis.bot.reply_to(message, answer)
                            break
                        else:
                            jarvis.telegram_answer_queue.put((get_message, answer))

                    __answe_wait_time -= 1
                    sleep(1)
            else:
                jarvis.bot.reply_to(message, "Кто ты чудовище?")

    @jarvis.bot.message_handler(content_types=["sticker", 'document'])
    def handle_docs_audio(message):
        _user = None
        for user in jarvis.bot.users:
            if str(message.from_user.id) == user.id:
                _user = user
                break
        if _user != None:
            if message.content_type == 'sticker':
                # Получим id Стикера
                sticker_id = message.sticker.file_id
                jarvis.bot.send_message(message.from_user.id, str(sticker_id))
            elif message.content_type == 'document':
                if message.document.file_name == 'config.txt':
                    file_info = jarvis.bot.get_file(message.document.file_id)
                    downloaded_file = jarvis.bot.download_file(file_info.file_path)
                    with open(jarvis.arduino.config_path, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    test_config = jarvis.arduino.load_config(False)
                    if test_config == 'config loaded!':
                        jarvis.bot.reply_to(message, "конфиг загрузил и применил")
                    else:
                        jarvis.bot.reply_to(message, "почему-то не вышло загрузить конфиг")
                else:
                    jarvis.bot.send_message(message.from_user.id,
                                     'Не знаю что за файл такой ты мне шлешь. Мне нужен config.txt.')
        else:
            jarvis.bot.reply_to(message, "Кто ты чудовище?")

        # ****** MAIN ******
        jarvis.main_loop()
        while True:
            sleep(1)