import telebot
from .gfunctions import *
from time import sleep
import requests
import threading
import queue
import logging

WRITE_LOG_TO_FILE = False
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'
#LOG_LEVEL = logging.DEBUG
LOG_LEVEL = logging.INFO

if WRITE_LOG_TO_FILE:
    logging.basicConfig(filename='jarvis_log.txt', filemode='w', format=LOG_FORMAT, level=LOG_LEVEL)
else:
    logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)

class TelegramUserClass:
    def __init__(self, name, id, level=3):
        self._name = name
        if isinstance(id, str):
            self._id = id
        else:
            raise Exception(f'TelegramUserClass: id ожидается строка. Получено {type(id)}')
        self._level = level

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        if isinstance(id, str):
            self._id = id
        else:
            raise Exception(f'TelegramUserClass: id ожидается строка. Получено {type(id)}')

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if isinstance(name, str):
            self._name = name
        else:
            raise Exception(f'TelegramUserClass: name ожидается строка. Получено {type(name)}')

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        if isinstance(level, int):
            self._level = level
        else:
            raise Exception(f'TelegramUserClass: level ожидается int. Получено {type(level)}')

class Message:
    def __init__(self, message, id=None):
        self._message = message
        self._id = id

    @property
    def message(self):
        return self._message

    @property
    def id(self):
        return self._id


class TelegramBot(telebot.TeleBot, JPrint):
    PROXY_LIST_SITE_LIST = []
    PROXY_LIST_SITE_LIST.append('https://proxy11.com/api/proxy.txt?key=MTI1NA.XskQNw.D_-LUWh32lYWvpZI9Bb_AAHN0Yg')
    PROXY_LIST_SITE_LIST.append('https://www.proxy-list.download/api/v1/get?type=http')
    PROXY_LIST_SITE_LIST.append('https://www.proxy-list.download/api/v1/get?type=http&anon=elite')
    PROXY_LIST_SITE_LIST.append('http://pubproxy.com/api/proxy?format=txt')

    logger = logging.getLogger('Telegram_bot')
    logger.setLevel(logging.INFO)

    @staticmethod
    def set_info():
        TelegramBot.logger.setLevel(logging.INFO)
        print(f'set INFO level in {TelegramBot.logger.name} logger')

    @staticmethod
    def set_debug():
        TelegramBot.logger.setLevel(logging.DEBUG)
        print(f'set DEBUG level in {TelegramBot.logger.name} logger')

    @staticmethod
    def set_warning():
        TelegramBot.logger.setLevel(logging.WARNING)
        print(f'set WARNING level in {TelegramBot.logger.name} logger')

    def __init__(self, path, list_file, token, threaded=False, use_proxy = False):
        super().__init__(token, threaded)
        if isinstance(use_proxy, bool):
            self.use_proxy = use_proxy
        else:
            raise TypeError
        self._name = 'bot'
        self._users = []
        self._prog_path = path
        self._good_proxy_list_file = list_file
        self._started = False
        self._telegram_bot_thread = threading.Thread(target=self._telegram_bot, args=(), daemon=True)
        self._messages_queue = queue.Queue()
        self._send_messages_thread = threading.Thread(target=self._send_messages_with_queue, args=(), daemon=True)

    @property
    def name(self):
        return self._name

    @property
    def users(self):
        return self._users

    def get_users(self):
        return self._users

    def find_user_by_id(self, id):
        for user in self._users:
            if user.id == id:
                return user
        return None

    def add_user(self, name, id, level=3):
        if self.find_user_by_id(id) == None:
            self._users.append(TelegramUserClass(name, id, level))

    def _send_messages_with_queue(self):
        while self._started:
            if (self._messages_queue.qsize() > 0):
                message = self._messages_queue.get()
                if message.id is None:
                    # send to all
                    self.send_to_all(message.message)
                else:
                    # send to id
                    self.send_to_telegram_id(message.id, message.message)
            sleep(0.1)

    def add_to_queue(self, id, message):
        self._messages_queue.put(Message(message, id))

    def send_to_telegram_id(self, id, message):
        try:
            self.send_message(id, message)
        except:
            self.jprint(f'error send to telegramm id {id}')

    def send_to_all(self, message):
        for user in self._users:
            try:
                self.send_to_telegram_id(user.get_id(), message)
            except:
                self.jprint('error send to all telegram ID')

    def _load_good_proxylist(self):
        try:
            f = open(self._prog_path + self._good_proxy_list_file, 'r')
            lst = f.read().split('\n')
            f.close()
            lst2 = []
            for l in lst:
                if l != '':
                    lst2.append(l)
            return lst2
        except:
            self.jprint(f'cant read {self._prog_path + self._good_proxy_list_file}')
            return None

    def _append_goodproxy(self, proxy):
        error = TelegramBot.logger.error
        debug = TelegramBot.logger.debug
        info = TelegramBot.logger.info
        try:
            # in first read the list
            try:
                f = open(self._prog_path + self._good_proxy_list_file, 'r')
                exist_proxies = f.read().split('\n')
                f.close()
            except:
                exist_proxies = []
            if proxy in exist_proxies:
                return
            try:
                f = open(self._prog_path + self._good_proxy_list_file, 'a')
            except:
                self.jprint('good proxylist file is not exist. Im create new.')
                info('good proxylist file is not exist. Im create new.')
                f = open(self._prog_path + self._good_proxy_list_file, 'w')
            f.write(proxy + '\n')
            f.close()
        except:
            error(f'cant write {self._prog_path + self._good_proxy_list_file}!!!')

    def _remove_bad_proxy(self, proxy):
        error = TelegramBot.logger.error
        debug = TelegramBot.logger.debug
        info = TelegramBot.logger.info
        try:
            try:
                f = open(self._prog_path + self._good_proxy_list_file, 'r')
            except:
                return
            p_list = f.read().split('\n')
            f.close()
            good_p_list = []
            for prox in p_list:
                if prox != proxy and prox != '':
                    good_p_list.append(prox)
            f = open(self._prog_path + self._good_proxy_list_file, 'w')
            for gp in good_p_list:
                f.write(gp + '\n')
            f.close()
        except:
            error(f'cant write {self._prog_path + self._good_proxy_list_file}')

    def _telegram_bot(self):
        error = TelegramBot.logger.error
        debug = TelegramBot.logger.debug
        info = TelegramBot.logger.info
        warning = TelegramBot.logger.warning
        while self._started:
            if self.use_proxy:
                try:
                    for _proxy in TelegramBot.PROXY_LIST_SITE_LIST:
                        try:
                            content = str(requests.get(_proxy).content)
                            content = content.replace(r'\r\n', ',')
                            content = content.replace("b'", '')
                            content = content.replace(",'", '')
                            content = content.replace("'", '')
                            if content == '':
                                error(f'empty proxy list in {_proxy}')
                                sleep(11)
                                continue
                            break
                        except:
                            warning(f"can't load {_proxy}")
                            sleep(11)

                    a = content.split(',')
                    self.jprint('Im try load good proxylist')
                    gp_list = self._load_good_proxylist()
                    contarr = []
                    if gp_list != None:
                        contarr.extend(gp_list)
                        self.jprint('Good proxylist is loaded')
                    else:
                        error('Cant load good proxylist from file :(')
                    contarr.extend(a)
                except:
                    error(f"error in parse proxy list content")
                    sleep(0.1)
                    continue

                for prox in contarr:
                    if prox != '':
                        try:
                            telebot.apihelper.proxy = {'https': prox}
                            self._append_goodproxy(prox)
                            self.jprint(f'Try connect to Telegramm with proxy {prox}')
                            self.polling(none_stop=True)
                        except:
                            error('I am have some problem with connect to Telegramm')
                            self._remove_bad_proxy(prox)
                            sleep(0.1)
            else:
                self.logger.info('Connect to telegram without proxy')
                try:
                    self.polling(none_stop=True)
                except:
                    error('I am have some problem with connect to Telegramm')
                    sleep(0.1)

                        
    def start(self):
        # Start Telegram bot thread
        if not self._started:
            self._started = True
            self._telegram_bot_thread.start()
            self._send_messages_thread.start()
            return True
        else:
            return False

    def stop(self):
        self._started = False


if __name__ == '__main__':
    # from config import *
    # API_TOKEN = '1123277123:AAFz7b_joMY-4yGavFAE5o5MKstU5cz5Cfw'
    # bot = TelegramBot(path=JARVIS_PATH, list_file=GOOD_PROXY_LIST, token=API_TOKEN, threaded=False)  # Конструктор бота
    # bot.add_user('ggg', 'fff5555', 0)
    # _user = None
    # for user in bot.users:
    #     if 'fff5555' == user.id:
    #         _user = user
    #         print(_user.name)
    content = str(requests.get('https://proxy11.com/api/proxy.txt?key=MTI1NA.XskQNw.D_-LUWh32lYWvpZI9Bb_AAHN0Yg').content)
    content = content.replace(r'\r\n', ',')
    content = content.replace("b'", '')
    content = content.replace(",'", '')
    content = content.replace("'", '')
    print(content)