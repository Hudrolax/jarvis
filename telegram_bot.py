import telebot
from gfunctions import JPrint
from time import sleep
import requests
import threading

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

class TelegramBot(telebot.TeleBot, JPrint):
    PROXY_LIST_SITE = 'https://www.proxy-list.download/api/v1/get?type=http'

    def __init__(self, path, list_file, token, threaded=False):
        super().__init__(token, threaded)
        self._users = []
        self._prog_path = path
        self._good_proxy_list_file = list_file
        self._started = False
        self._telegram_bot_thread = threading.Thread(target=self._telegram_bot, args=(), daemon=True)

    @property
    def users(self):
        return self._users

    def get_users(self):
        return self._users

    def find_user_by_id(self, id):
        for user in self._users:
            if user.get_id() == id:
                return user
        return None

    def add_user(self, name, id, level=3):
        if self.find_user_by_id(id) == None:
            self._users.append(TelegramUserClass(name, id, level))

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
                f = open(self._prog_path + self._good_proxy_list_file, 'w')
            f.write(proxy + '\n')
            f.close()
        except:
            self.jprint(f'cant write {self._prog_path + self._good_proxy_list_file}!!!')

    def _remove_bad_proxy(self, proxy):
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
            self.jprint(f'cant write {self._prog_path + self._good_proxy_list_file}')

    def _telegram_bot(self):
        while self._started:
            try:
                content = str(requests.get(TelegramBot.PROXY_LIST_SITE).content)
                content = content.replace(r'\r\n', ',')
                content = content.replace("b'", '')
                content = content.replace(",'", '')
                a = content.split(',')
                self.jprint('Im try load good proxylist')
                gp_list = self._load_good_proxylist()
                contarr = []
                if gp_list != None:
                    contarr.extend(gp_list)
                    self.jprint('Good proxylist is loaded')
                else:
                    self.jprint('Cant load good proxylist :(')
                contarr.extend(a)
            except:
                sleep(0.1)
                continue
            for prox in contarr:
                if prox != '':
                    try:
                        telebot.apihelper.proxy = {'https': prox}
                        self._append_goodproxy(prox)
                        self.jprint('Try connect to Telegramm...')
                        self.polling(none_stop=True)
                    except:
                        self.jprint('I am have some problem with connect to Telegramm')
                        self._remove_bad_proxy(prox)
                        sleep(0.1)
                        
    def start(self):
        # Start Telegram bot thread
        if not self._started:
            self._started = True
            self._telegram_bot_thread.start()
            return True
        else:
            return False

    def stop(self):
        self._started = False
        self.stop_bot()


if __name__ == '__main__':
    from config import *
    API_TOKEN = '1123277123:AAFz7b_joMY-4yGavFAE5o5MKstU5cz5Cfw'
    bot = TelegramBot(path=JARVIS_PATH, list_file=GOOD_PROXY_LIST, token=API_TOKEN, threaded=False)  # Конструктор бота
    bot.add_user('ggg', 'fff5555', 0)
    _user = None
    for user in bot.users:
        if 'fff5555' == user.id:
            _user = user
            print(_user.name)