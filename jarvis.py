# Sergey Nazarov 26.03.2020

import serial
import serial.tools.list_ports
from time import sleep
import time
import sys
from datetime import datetime
import threading
import queue
import socket
import telebot
from telebot import apihelper
import requests
from RPi import GPIO
import copy

path = '/home/pi/jarvis/'
arduino_config_name = 'config.txt'
arduino_pinstate = 'arduino_pinstate.txt'
good_proxylist = 'good_proxylist.txt'
telegram_users = [] # telegram users list
API_TOKEN = '1123277123:AAFz7b_joMY-4yGavFAE5o5MKstU5cz5Cfw'
bot = telebot.TeleBot(API_TOKEN, threaded=False) # Конструктор бота
NotImportantWords = ['в','на','к','у','для','за']
StartTime = datetime.now()
Run = True

def DifferenceBetweenDate(date1,date2):
    duration = date2 - date1
    duration_in_s = duration.total_seconds() # Total number of seconds between dates
    days = divmod(duration_in_s, 86400)        # Get days (without [0]!)
    hours = divmod(days[1], 3600)               # Use remainder of days to calc hours
    minutes = divmod(hours[1], 60)                # Use remainder of hours to calc minutes
    seconds = divmod(minutes[1], 1)               # Use remainder of minutes to calc seconds
    return "%d дней, %d часов, %d минут и %d секунд" % (days[0], hours[0], minutes[0], seconds[0]) 

def ArrayMA(array):
    try:
        summ = 0
        for el in array:
            summ += el
        return summ/len(array)
    except:
        return 0

def MapFunc(x,in_min,in_max,out_min,out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def ClearStr(str_):
    str_ = str(str_)
    str_ = str_.replace("\\r\\n",'')
    str_ = str_.replace("b'",'')
    str_ = str_.replace("'",'')
    return str_

def SendToSerial(s_port,s):
        try:
            s_port.write(bytes(s,'utf-8'))
        except:
            print('Write error to port '+s_port)

def append_goodproxy(proxy):
    try:
        #in first read the list
        try:
            f = open(path+good_proxylist, 'r')
            exist_proxies = f.read().split('\n')
            f.close()
        except:
            exist_proxies = []
        if proxy in exist_proxies:
            return
        try:
            f = open(path+good_proxylist, 'a')
        except:
            print('good proxylist file is not exist. Im create new.')
            f = open(path+good_proxylist, 'w')
        f.write(proxy+'\n')
        f.close()
    except:
        print(f'cant write {path+good_proxylist}!!!')

def remove_bad_proxy(proxy):
    try:
        try:
            f = open(path+good_proxylist, 'r')
        except:
            return
        p_list = f.read().split('\n')
        f.close()
        good_p_list = []
        for prox in p_list:
            if prox != proxy and prox != '':
                good_p_list.append(prox)
        f = open(path+good_proxylist, 'w')
        for gp in good_p_list:
            f.write(gp+'\n')
        f.close()
    except:
        print(f'cant write {path+good_proxylist}')

def load_good_proxylist():
    try:
        f = open(path+good_proxylist, 'r')
        lst= f.read().split('\n')
        f.close()
        lst2 = []
        for l in lst:
            if l != '':
                lst2.append(l)
        return lst2
    except:
        print(f'cant read {path+good_proxylist}')
        return None

class TelegramUserClass():
    def __init__(self,name,ID,level=3):
        self.name = name
        self.ID = ID
        self.level = level   

class dPin():
    def __init__(self, output, num, BCOD, name, description='', ct=[]):
        self.output = output
        self.num = num
        self.name = name
        self.state = False
        self.prevstate = False
        self.description = description
        self.ConvertibleTerms = ct
        self.binds = []
        self.blocked = False
        self.LastRevTime = datetime(2005, 7, 14, 12, 30)
        self.BCOD = BCOD
        self.BCODReaction = False

class CWatchDog():
    def __init__(self,port):
        self.port = port # порт подключения вотчдога
        print('Try connect to WatchDog at port '+self.port)  
        self.serial=serial.Serial(self.port,9600, timeout=1)  #change ACM number as found from ls /dev/tty/ACM*
        self.serial.flushInput()
        self.serial.flushOutput()
        self.serial.baudrate=9600
        self.serial.timeout=1
        self.serial.write_timeout=1

    def ping(self):
        SendToSerial(self.serial,'~U') # Отправка команды "я в норме" на вотчдог

def PingWatchdog(wd):
    while True:
        wd.ping()
        sleep(1)

class CArduino():
    def __init__(self,config_path,pinstate_file,pins=[]):
        self.port = ''
        self.initialized = False
        self.pins = pins
        self.config_path = config_path
        self.pinstate_file = pinstate_file
        self.DCVolArray = [27 for i in range(20)]
        self.DCVol = 27
        self.DCVolLowAlertSended = False
        self.DCVoltageInPercent = 100
        self.DCCheckTimer = 0
        self.ACCExist = True
        self.ACAlertSended = False
        self.ACNonExistStartTimer = datetime.now()
        self.OutDoorLightPin = 0
        self.LastSetStateOutDoorLight = None
    
    def pin(self,_pin):
        for p in self.pins:
            if str(type(_pin)) == "<class 'str'>":
                _pin = _pin.lower()
                if p.name.lower() == _pin or str(p.num) == _pin:
                    return p
            elif str(type(_pin)) == "<class 'int'>":
                if p.num == _pin:
                    return p

        return None    
    
    def SetPin(self,_pin,state):
        if str(type(_pin)) == "<class 'list'>":
            print("Error (SetPin): _pin is <class 'list'>")
            return None
        if state == True:
            state = 1
        elif state == False:
            state = 0
        if str(type(_pin)) == "<class 'int'>":
            p = self.pin(_pin)
        elif str(type(_pin)) == "<class 'str'>":
            _pin = int(_pin)
            p = self.pin(_pin)
        else:
            p = _pin
            _pin = _pin.num

        p.prevstate = p.state
        answer = None
        if state == 1:
            while answer != 3001 or answer==None:
                answer = self.write('P',_pin,state)
                #print(f'SetPin get answer {answer}')
        elif state == 0:
            while answer != 3000 or answer==None:
                answer = self.write('P',_pin,state)
                #print(f'SetPin get answer {answer}')
        else:
            while answer != 3001 and answer != 3000 or answer==None:
                answer = self.write('P',_pin,state)
                #print(f'SetPin get answer {answer}')

        if answer != None:
            p.LastRevTime = datetime.now()
            if answer==3001:
                p.state = True
            elif answer==3000:
                p.state = False
            self.write_pinstate(p)
            return p.state
        else:
            return None

    def CheckInputPins(self,allpins=False):
        for p in self.pins:
            if not p.output or allpins:
            #if True:
                p.prevstate = p.state
                if self.write('S',p.num,0) == 2001:
                    p.state = True
                else:
                    p.state = False
                if allpins:
                    p.prevstate = p.state
                self.PinReaction(p)
        if self.DCCheckTimer <= 0:
            val = self.write('A',1,0)
            voltage_now = round(MapFunc(val,0,1023,0,40.2),2)
            self.DCVolArray.pop(0)
            self.DCVolArray.append(voltage_now)
            self.DCVol = round(ArrayMA(self.DCVolArray),2)
            percent = round(MapFunc(self.DCVol,21.1,25,0,100),0)
            if percent > 100:
                percent = 100
            elif percent < 0:
                percent = 0 
            self.DCVoltageInPercent = percent
            if self.DCVoltageInPercent == 100:
                self.DCVolLowAlertSended = False

            acc_exist = val = self.write('A',0,0)
            #print(acc_exist)
            if acc_exist > 500:
                self.ACCExist = True
            else:
                if self.ACCExist:
                    self.ACNonExistStartTimer = datetime.now()
                self.ACCExist = False
            #print(self.ACCExist)
            self.DCCheckTimer = 50
        else:
            self.DCCheckTimer -= 1
    
    def PinReaction(self,p):
        # p - swich (S-pin)
        # b - bind (DG-pin)
        if p.state != p.prevstate:
            for b in p.binds:
                if not p.blocked and not b.blocked:
                    print(f'im set pin {b.description} to {p.state} by PinReaction in {datetime.now().strftime("%X")}')
                    self.SetPin(b.num,p.state)
                    p.LastRevTime = datetime.now()
                    b.LastRevTime = datetime.now()
    
    def write(self, cmd, val1, val2):
        answer = None
        try:
            self.port.write((222).to_bytes(1,'big'))        #header byte
            self.port.write((ord(cmd)).to_bytes(1,"big"))
            self.port.write((int(val1)).to_bytes(2,"big"))
            self.port.write((int(val2)).to_bytes(1,"big"))
            self.port.flush()
            sleep(0.001)
            # read answer
            answer = int.from_bytes(self.port.read(2),'big')
        except:
            self.initialized = False
        return answer

    def write_pinstate(self,_pin):
        try:
            f = open(self.pinstate_file, 'w')
            for p in self.pins:
                f.write(f'{p.num} {p.state} {p.blocked}\n')
            f.close()
        except:
            print('error save pinstate')

    def load_pinstate(self):
        try:
            f = open(self.pinstate_file, 'r')
            lines = f.read().split('\n')
            f.close()
            for line in lines:
                s = line.split(' ')
                for p in self.pins:
                    if str(p.num)==s[0]:
                        if p.output:
                            if s[1].lower() == 'true':
                                p.state = True
                            else:
                                p.state = False
                            self.SetPin(p,p.state)
                        try:
                            if s[2].lower() == 'true':
                                p.blocked = True
                            else:
                                p.blocked = False
                        except:
                            pass 
            print('pinstate is loaded')                  
        except:
            print('error load pinstate')

    def initialize(self):
        while not self.initialized: 
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                comport = p.device
                print('Try to find Arduino in '+comport)
                self.port=serial.Serial(comport,57600, timeout=1)  #change ACM number as found from ls /dev/tty/ACM*
                self.port.reset_output_buffer()
                self.port.reset_input_buffer()
                self.port.baudrate=57600
                self.port.timeout=1
                self.port.write_timeout=1
                sleep(3)
                a = self.write('I',666,1)
                #print(a)
                if (a==666):
                    self.initialized = True
                    self.CheckInputPins(True)
                    break
            if not self.initialized:
                print('I have not found the Arduino...')
                print("Sorry, but i can't work whithout Arduino subcontroller :(")
                #print("I'm have to try to find it after one second pause")
            else:
                print('Arduino is initialized on port '+comport)
                self.load_pinstate()

    def LoadConfig(self,first_load = True):
        answer = None
        global Run
        self.pins = []
        try:
            f = open(self.config_path, 'r')
            try:
                file_text = f.read()
                f.close()
                array = file_text.split('\n')
                for a in array:
                    line = a.split(' ')
                    if line[0] == 'pin':
                        _num = line[1]
                        _name = line[2]
                        _output = False
                        if line[3]=='output':
                            _output = True
                        _description = line[4]
                        _BCOD = 0
                        try:
                            _BCOD = int(line[5])
                        except:
                            print(f'cant load BCOD from config for pin {_name}') 
                        _CT = []
                        if len(line)>5:
                            for i in range(6,len(line)):
                                _CT.append(line[i])
                        if not self.pin(_num) in self.pins:    
                            self.pins.append(dPin(_output,int(_num),_BCOD,_name,_description,_CT))
                    elif line[0] == 'bind':
                        _pin = self.pin(line[1])
                        if _pin != None:
                            for i in range(2,len(line)):
                                _pin2 = self.pin(line[i])
                                if _pin2 != None:
                                    if not _pin2 in _pin.binds: 
                                        _pin.binds.append(_pin2)
                    elif line[0] == 'telegram_user':
                        telegram_users.append(TelegramUserClass(line[1],line[2],int(line[3])))                

                answer = 'config loaded!'
                lightpin = self.FindByAuction('свет на улице')
                if str(type(lightpin)) != "<class 'list'>" and lightpin != None:
                    self.OutDoorLightPin = self.FindByAuction('свет на улице')
                else:
                    print('Не могу подобрать пин уличного освещения!')       
            except:
                answer = 'config load faild'
                if first_load:
                    Run = False
        except:
            print("Can't load config")
            Run = False
            # f = open(self.config_path, 'w')
            # f.write('# pin line: pin <arduino pin number> <name> <input/output> <description> <blocked> <convertible terms>' + '\n')
            # f.write('pin 13 led output ledpin false' + '\n')
            # f.write('\n')
            # f.write('# Bind line: bind <arduino pin number / name> <name> <arduino pin number / name> <...>' + '\n')
            # f.write('\n')
            # f.write('# Telegram user line: telegram_user <name> <ID>' + '\n')
            # f.write('telegram_user admin 586035868' + '\n')
            # self.pins = [dPin(True,13,'led','ledpin')]
            # answer = f'config.txt not found. I create new {self.config_path}.'
        print(answer)
        return answer
    def SaveConfig(self):
        try:
            f = open(self.config_path, 'w')
            f.write('# pin line: pin <arduino pin number> <name> <input/output> <description> <blocked> convertible terms' + '\n')
            f.write('# Inputs:' + '\n')
            for p in self.pins:
                if not p.output:
                    ct = ''
                    for c in p.ConvertibleTerms:
                        ct += f' {c}'
                    f.write(f'pin {p.num} {p.name} input {p.description} {p.BCOD}{ct}' + '\n')            
            f.write('\n')
            f.write('# Outputs:' + '\n')
            for p in self.pins:
                if p.output:
                    ct = ''
                    for c in p.ConvertibleTerms:
                        ct += f' {c}'
                    f.write(f'pin {p.num} {p.name} output {p.description} {p.BCOD}{ct}' + '\n')            
            f.write('\n')
            f.write('# Bind line: bind <arduino pin number / name> <name> <arduino pin number / name> <...>' + '\n')
            for p in self.pins:
                if len(p.binds)>0:
                    bindstr = ''
                    for b in p.binds:
                        bindstr += ' '+str(b.num)
                    f.write(f'bind {p.num}'+ bindstr + '\n')
            f.write('\n')    
            f.write('# Telegram user line: telegram_user <name> <ID>' + '\n')
            for u in telegram_users:
                f.write(f'telegram_user {u.name} {u.ID}' + '\n')    

            answer = None
        except:
            answer = 'error save config'
        return answer 
    def FindByAuction(self, cmd, allpins=False):
        if str(type(cmd)) != "<class 'list'>":
            cmd = str(cmd)
            _wordlist = cmd.split(' ')
        else:
            _wordlist = cmd
        wordlist = []
        for w in _wordlist:
            if w not in NotImportantWords:
                wordlist.append(w)
        PinAuction = []
        for p in self.pins:
            if p.output or allpins: # добавляем выходы в аукцион
                ct_all = []
                for c in p.ConvertibleTerms:
                    ct_all.append(c)
                ct_all.append(p.description)
                ct_all.append(str(p.num))
                ct_all.append(p.name.lower())
                PinAuction.append([p.num, ct_all, 0])

        for word in wordlist:
            for PA in PinAuction:
                includes = 0;
                #print(f'count points for {PA[0]}')
                for ct in PA[1]:
                    if ct.lower() == word:
                        PA[2] += 2
                        #print(f'word = {word} 2 points')
                    elif ct.lower().find(word) > -1:
                        PA[2] += 1
                        #print(f'word find {word} 1 point')

        MaxIncludes = 0;
        Winners = []
        for PA in PinAuction:
            if PA[2] > MaxIncludes:
                MaxIncludes = PA[2]

        if MaxIncludes > 0:
            for PA in PinAuction:
                if PA[2] == MaxIncludes:
                    Winners.append(self.pin(PA[0]))

        if len(Winners) == 1:
            print(f'winner is {Winners[0].description}')
            print(f'winner get {MaxIncludes} points')
            return Winners[0]
        elif len(Winners) > 1:
            print('Winners more than one')
            print(f'its get {MaxIncludes} points')
            return Winners
        else:
            print('winner not found')
            return None      

  
# Function of input in thread
def read_kbd_input(inputQueue):
    global Run
    while Run:
        # Receive keyboard input from user.
        try:
            input_str = input()
            print('Enter command: '+input_str)
            inputQueue.put((input_str, None, None))
        except:
            continue

def SendToTelegramId(_id,message):
    bot.send_message(_id, message)

def SendToAllTelegram(message):
    for user in telegram_users:
        SendToTelegramId(user.ID, message)

def TelegramBot():
    global Run
    while Run:
        try:
            content = str(requests.get('https://www.proxy-list.download/api/v1/get?type=http').content)
            content = content.replace(r'\r\n',',')
            content = content.replace("b'",'')
            content = content.replace(",'",'')
            a = content.split(',')
            print('Im try load good proxylist')
            gp_list = load_good_proxylist()
            contarr = []
            if gp_list != None:
                contarr.extend(gp_list)
                print('Good proxylist is loaded')
            else:
                print('Cant load good proxylist :(')
            contarr.extend(a)
        except:
            sleep(0.1)
            continue
        for prox in contarr:
            if prox != '':
                apihelper.proxy = {'https': prox}
                try:
                    append_goodproxy(prox)
                    print('Try connect to Telegramm...')
                    bot.polling(none_stop=True)
                except:
                    print('I am have some problem with connect to Telegramm')
                    remove_bad_proxy(prox)
                    sleep(0.1)            

# Telegram bot
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global inputQueue
    global TelegrammAnswerQueue

    _user = None
    for user in telegram_users: 
        if str(message.from_user.id) == user.ID:
            _user = user
            break
    if message.text == "Привет":
        bot.reply_to(message, "Привет, чем я могу тебе помочь?")
    elif message.text == "/help" or message.text == "help":
        if _user != None:
            helpmessage = 'Help:\n'
            helpmessage += 'getmyid - получить свой telegram ID\n'
            helpmessage += '\n'
            helpmessage += 'pinstate - посмотреть список пинов\n'
            helpmessage += '\n'
            helpmessage += 'bind <pin1> <pin2> <...> - привязать к входному пину pin1 пины pin2 ..\n'
            helpmessage += '\n'
            helpmessage += 'unbind <pin1> <pin2> <...> - отвязать к входному пину pin1 пины pin2 ..\n'

            bot.reply_to(message, helpmessage)
        else:
            bot.reply_to(message, "Кто ты чудовище?")        
    elif message.text == 'getmyid':
        bot.reply_to(message, "Ваш ID: %s" % message.from_user.id)
    elif message.text == 'getconfig':
        if _user != None:
            doc = open(arduino.config_path, 'rb')
            bot.send_document(message.from_user.id, doc)
        else:
            bot.reply_to(message, "Кто ты чудовище?")   
    else:
        if _user != None:
            inputQueue.put((message.text, _user,message)) # Поместили сообщение в оцередь на обработку
            AnsweWaitTime = 10
            while AnsweWaitTime > 0:
                if (TelegrammAnswerQueue.qsize() > 0):
                    queue_typle = TelegrammAnswerQueue.get()
                    get_message = queue_typle[0]
                    answer = queue_typle[1]
                    if get_message == message:
                        bot.reply_to(message, answer)
                        break
                    else:
                        TelegrammAnswerQueue.put((get_message, answer))       

                AnsweWaitTime -= 1
                sleep(1)
        else:
            bot.reply_to(message, "Кто ты чудовище?")

@bot.message_handler(content_types=["sticker",'document'])
def handle_docs_audio(message):
    _user = None
    for user in telegram_users: 
        if str(message.from_user.id) == user.ID:
            _user = user
            break
    if _user != None:
        if message.content_type == 'sticker':
            # Получим ID Стикера
            sticker_id = message.sticker.file_id
            bot.send_message(message.from_user.id, str(sticker_id))
        elif message.content_type == 'document':
            if message.document.file_name == 'config.txt': 
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(arduino.config_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                test_config = arduino.LoadConfig(False)
                if test_config == 'config loaded!':
                    bot.reply_to(message,"конфиг загрузил и применил")
                else:
                    bot.reply_to(message,"почему-то не вышло загрузить конфиг")     
            else:
                bot.send_message(message.from_user.id, 'Не знаю что за файл такой ты мне шлешь. Мне нужен config.txt.')   
    else:
        bot.reply_to(message, "Кто ты чудовище?")

def AccessError():
    return 'У вас нет доступа к этой команде\n'

# Command processing module
def CommandProcessing(cmd,telegramuser,message):
    global TelegrammAnswerQueue
    global Run
    cmd = cmd.lower()
    print_lst = f'first command: {cmd}'
    if telegramuser != None:
        print_lst += f' from {telegramuser.name}'    
    print(print_lst)
    global_cmd_list = cmd.split(' ')
    cmdlist_by_and = cmd.split(' и ')
    answer = ''
    for list_by_and in cmdlist_by_and:
        cmd_list = list_by_and.split(' ')

        if 'включи' not in cmd_list and 'включи' in global_cmd_list:
            cmd_list.append('включи')
        elif ('выключи' not in cmd_list and 'выключи' in global_cmd_list) or ('отключи' not in cmd_list and 'отключи' in global_cmd_list):
            cmd_list.append('выключи')
        elif 'заблокируй' not in cmd_list and 'заблокируй' in global_cmd_list:
            cmd_list.append('заблокируй')
        elif 'разблокируй' not in cmd_list and 'разблокируй' in global_cmd_list:
            cmd_list.append('разблокируй')

        if ('свет' not in cmd_list and 'свет' in global_cmd_list) or ('освещение' not in cmd_list and 'освещение' in global_cmd_list):
            cmd_list.append('свет')
        print(f'cmd in loop: {cmd_list}')

        if 'включи' in cmd_list or 'on' in cmd_list:
            if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and 'дом' in p.ConvertibleTerms:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked: 
                                arduino.SetPin(p,1)
                                print(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет везде.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)) :
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'первый' in p.ConvertibleTerms and ('этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.SetPin(p,1)
                                print(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет на первом этаже.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'втором' in p.ConvertibleTerms and ('этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.SetPin(p,1)
                                print(f'Включил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Включил свет на втором этаже.\n'
                else:
                    answer += AccessError()    
            else:
            #elif 'свет' in cmd_list: 
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None: 
                    # Добавим личный флаг пользователя
                    findlist = copy.deepcopy(cmd_list)
                    if telegramuser != None:
                        findlist.append(telegramuser.name)
                    WinnerPin = arduino.FindByAuction(findlist)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно включить. Уточни команду.\n'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                            for p in WinnerPin:
                                if p.output:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.SetPin(p,1)
                                        if a == True:
                                            answer+=f'{p.description} включен\n'
                                        elif a == False:
                                            answer+=f'{p.description} выключен\n'
                                        else:
                                            answer+='Ошибка передачи данных\n'
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                        else:
                            answer += AccessError()
                    else:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (telegramuser != None and telegramuser.name in WinnerPin.ConvertibleTerms):
                            if telegramuser != None and telegramuser.level <= 0 and WinnerPin.blocked or telegramuser == None or not WinnerPin.blocked:
                                a = arduino.SetPin(WinnerPin,1)
                                if a == True:
                                    answer+=f'{WinnerPin.description} включен\n'
                                elif a == False:
                                    answer+=f'{WinnerPin.description} выключен\n'
                                else:
                                    answer+='Ошибка передачи данных\n'
                            else:
                                answer += f'{WinnerPin.description} заблокирован для вас'     
                        else:
                                answer += AccessError()
                else:
                    answer += AccessError()
        elif 'выключи' in cmd_list or 'отключи' in cmd_list or 'off' in cmd_list:
            if 'свет' in cmd_list and ('везде' in cmd_list or 'доме' in cmd_list or 'дома' in cmd_list):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and 'дом' in p.ConvertibleTerms:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.SetPin(p,0)
                                print(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет везде.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('первом' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'первом' in p.ConvertibleTerms and ('этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.SetPin(p,0)
                                print(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет на первом этаже.\n'
                else:
                    answer += AccessError()
            elif 'свет' in cmd_list and ('втором' in cmd_list and ('этаж' in cmd_list or 'этаже' in cmd_list)):
                if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                    for p in arduino.pins:
                        if 'свет' in p.ConvertibleTerms and 'втором' in p.ConvertibleTerms and ('этаж' in p.ConvertibleTerms or 'этаже' in p.ConvertibleTerms) and p.output:
                            if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                arduino.SetPin(p,0)
                                print(f'Выключил свет в {p.description}')
                            else:
                                answer += f'{p.description} заблокирован для вас'
                    answer += 'Выключил свет на втором этаже.\n'
                else:
                    answer += AccessError()
            else:
            #elif 'свет' in cmd_list:
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                    findlist = copy.deepcopy(cmd_list)
                    if telegramuser != None:
                        findlist.append(telegramuser.name)
                    WinnerPin = arduino.FindByAuction(findlist)
                    if WinnerPin == None:
                        answer += 'Не понятно, что нужно выключить. Уточни команду.\n'
                    elif str(type(WinnerPin)) == "<class 'list'>":
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                            for p in WinnerPin:
                                if p.output:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.SetPin(p,0)
                                        if a == True:
                                            answer+=f'{p.description} включен\n'
                                        elif a == False:
                                            answer+=f'{p.description} выключен\n'
                                        else:
                                            answer+='Ошибка передачи данных\n'
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                        else:
                            answer += AccessError()
                    else:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (telegramuser != None and telegramuser.name in WinnerPin.ConvertibleTerms):
                            if telegramuser != None and telegramuser.level <= 0 and WinnerPin.blocked or telegramuser == None or not WinnerPin.blocked:
                                a = arduino.SetPin(WinnerPin,0)
                                if a==True:
                                    answer+=f'{WinnerPin.description} включен\n'
                                elif a==False:
                                    answer+=f'{WinnerPin.description} выключен\n'
                                else:
                                    answer+='Ошибка передачи данных\n'
                            else:
                                answer += f'{WinnerPin.description} заблокирован для вас' 
                        else:
                            answer += AccessError()
                else:
                    answer += AccessError()
        elif ('верни' in cmd_list and ('было' in cmd_list or 'обратно' in cmd_list)) or 'пошутил' in cmd_list or 'шутка' in cmd_list:
            if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                for p in arduino.pins:
                    if (datetime.now()-p.LastRevTime).total_seconds() <= 30:
                        if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                            a = arduino.SetPin(p,p.prevstate) # prev pin state
                            print(f'pin {p.num} is {a}')
                        else:
                            answer += f'{p.description} заблокирован для вас'
                answer += 'Вернул все как было\n'
            else:
                answer += AccessError()
        elif 'оставь' in cmd_list and 'свет' in cmd_list:
            if telegramuser != None and telegramuser.level <= 2 or telegramuser == None:
                WinnerPin = arduino.FindByAuction(cmd_list)
                if WinnerPin == None:
                    answer += 'Не понятно, что нужно оставить включенным. Уточни команду.\n'
                elif str(type(WinnerPin)) == "<class 'list'>":
                    if ('кухне' in cmd_list or 'кухня' in cmd_list) and len(WinnerPin)==2:
                        if telegramuser != None and telegramuser.level <= 1 or telegramuser == None:
                            for p in arduino.pins:
                                if p.output and p in WinnerPin:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        arduino.SetPin(p,1)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                                elif p.output and 'свет' in p.ConvertibleTerms and 'первый' in p.ConvertibleTerms and 'этаж' in p.ConvertibleTerms:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        arduino.SetPin(p,0)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                            answer += 'Оставил включенным только свет на кухне.\n'
                        else:
                            answer += AccessError()
                    else:
                        answer += 'Я нашел более одного объекта для оставления:\n'
                        for w in WinnerPin:
                            answer += f'{w.description}\n'
                        answer += 'Нужно уточнить, что конкретно оставить.\n'
                else:
                    if telegramuser != None and telegramuser.level <= 1 or telegramuser == None or (telegramuser != None and telegramuser.name in WinnerPin.ConvertibleTerms):
                        HouseLevel = 'первый'
                        if 'второй' in WinnerPin.ConvertibleTerms: # Определяем к какому этажу относится команда
                            HouseLevel = 'второй'
                        for p in arduino.pins:
                            if p.output and 'свет' in p.ConvertibleTerms and HouseLevel in p.ConvertibleTerms and 'этаж' in p.ConvertibleTerms:
                                if p == WinnerPin:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.SetPin(p,1)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'
                                else:
                                    if telegramuser != None and telegramuser.level <= 0 and p.blocked or telegramuser == None or not p.blocked:
                                        a = arduino.SetPin(p,0)
                                    else:
                                        answer += f'{p.description} заблокирован для вас'  
                        answer += f'Оставил включенным только {WinnerPin.description}\n'
                    else:
                        answer += AccessError()
            else:
                answer += AccessError()
        elif 'заблокируй' in cmd_list or 'заблокирую' in cmd_list:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                WinnerPin = arduino.FindByAuction(cmd_list,True)
                if WinnerPin == None:
                    answer += 'Не понятно, что нужно заблокировать. Уточни команду.\n'
                elif str(type(WinnerPin)) == "<class 'list'>":
                    for p in WinnerPin:
                        p.blocked = True
                        answer += f'Заблокировал {p.description}\n'
                else:
                    WinnerPin.blocked = True
                    answer += f'Заблокировал {WinnerPin.description}\n'
                arduino.write_pinstate(None)
            else:
                answer += AccessError()
        elif 'разблокируй' in cmd_list or 'разблокирую' in cmd_list:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                WinnerPin = arduino.FindByAuction(cmd_list,True)
                if WinnerPin == None:
                    answer += 'Не понятно, что нужно разблокировать. Уточни команду.\n'
                elif str(type(WinnerPin)) == "<class 'list'>":
                    for p in WinnerPin:
                        p.blocked = False
                        answer += f'Разблокировал {p.description}\n'
                else:
                    WinnerPin.blocked = False
                    answer += f'Разблокировал {WinnerPin.description}\n'
                arduino.write_pinstate(None)
            else:
                answer += AccessError()
        elif cmd.find('pinstate')>-1:
            if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                try:
                    val = cmd.split(' ')[1]
                except:
                    val = -1
                pin = arduino.pin(val)
                if pin != None:
                    if pin.state:
                        answer = f'pin {pin.num} is ON\n'
                    else:
                        answer = f'pin {pin.num} is OFF\n'
                else:
                    answer = f"Can't find the pin with number {val}\n"
            else:
                answer += AccessError()
        elif cmd.find('loadconfig')>-1 or cmd.find('загрузи конфиг')>-1:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                answer = arduino.LoadConfig(False)
            else:
                answer += AccessError()
        elif cmd.find('pinlist')>-1 or cmd.find('list pins')>-1 or cmd.find('listpins')>-1 or cmd.find('список пинов')>-1 or cmd.find('пинлист')>-1:
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                answer += '*** Pin list: ***'+'\n'
                answer += 'Inputs:'+'\n'
                for p in arduino.pins:
                    if not p.output:
                        answer += f'   pin {p.num} ({p.name})'
                        if p.blocked:
                            answer += '(blocked)'
                        if len(p.binds) > 0:
                            answer += ' >>> '
                            k=0
                            for b in p.binds:
                                if k != 0:
                                    answer += ','
                                answer += f' {b.num} ({b.description})'
                                k += 1
                        answer += '\n'
                answer += 'Outputs:'+'\n'
                for p in arduino.pins:
                    if p.output:
                        answer += f'   pin {p.num} ({p.name})'
                        if p.blocked:
                            answer += '(blocked)'
                        answer += '\n'
            else:
                answer += AccessError()
        elif cmd.startswith('bind '):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                try:
                    val = cmd.split(' ')
                    bindto = arduino.pin(val[1])
                    if not bindto.output:
                        for i in range(2,len(val)):
                            addpin = arduino.pin(val[i])
                            if addpin.output:
                                if not addpin in bindto.binds: 
                                    bindto.binds.append(addpin)
                                else:
                                    answer += f'pin {addpin.name} is already in {bindto.name}.binds'+'\n' 
                            else:
                                answer += f'pin {addpin.name} is INPUT pin and connot binded to pin {bindto.name}\n'   
                        answer += 'pins is binded!\n'
                        if arduino.SaveConfig() == None:
                            answer += 'config is saved\n'
                        else:
                            answer += 'error save config\n'
                    else:
                        answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.\n'   
                except:
                    answer += 'error bind pins\n'
            else:
                answer += AccessError()
        elif cmd.startswith('unbind '):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                try:
                    val = cmd.split(' ')
                    bindto = arduino.pin(val[1])
                    if not bindto.output:
                        for i in range(2,len(val)):
                            bindto.binds.remove(arduino.pin(val[i]))
                        answer = 'pins is unbinded!\n'
                        if arduino.SaveConfig() == None:
                            answer += 'config is saved\n'
                        else:
                            answer += 'error save config\n'
                    else:
                        answer += f'pin {bindto.name} is OUTPUT pin and you cant bind to it.\n'    
                except:
                    answer == 'error unbind pins\n'
            else:
                answer += AccessError()
        elif (cmd.find('print')>-1 and cmd.find('config')>-1) or (cmd.find('покажи')>-1 and cmd.find('конфиг')>-1):
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                f = open(arduino.config_path, 'r')
                try:
                    answer += f.read()
                    f.close()
                except:
                    answer += 'не могу прочесть конфиг\n'
            else:
                answer += AccessError()
        elif cmd == 'state' or cmd == 'status' or 'статус' in cmd_list:
            if telegramuser != None and telegramuser.level <= 3 or telegramuser == None:
                uptime = DifferenceBetweenDate(StartTime,datetime.now())
                answer += f'uptime {uptime}\n'
                if telegramuser != None and telegramuser.level <= 2 or telegramuser == None: 
                    answer += 'Включенный свет:\n'
                    k = 0
                    for p in arduino.pins:
                        if p.output and 'свет' in p.ConvertibleTerms and p.state:
                            if k > 0:
                                answer += ' ,'   
                            answer += f'{p.description}'
                            k += 1
                    if k == 0:
                        answer += 'весь свет выключен\n'
                    answer += '\n'
                answer += '\n'

                ACNet = 'есть'
                if not arduino.ACCExist:
                    ACNet = 'НЕТ'
                answer += f'Напряжение в сети {ACNet}\n' 
                answer += f'Напряжение аккумулятора {arduino.DCVol} V ({arduino.DCVoltageInPercent} %)\n'
            else:
                answer += AccessError()
        elif cmd == 'exit':
            if telegramuser != None and telegramuser.level <= 0 or telegramuser == None:
                print('bye...')
                Run = False
            else:
                answer += AccessError()    
        else:
            answer += 'неизвестная команда\n'     

    if message != None:
        TelegrammAnswerQueue.put((message, answer)) # Поместили сообщение в оцередь на обработку
    return answer    

def ReglamentWork():
    global ReglamentWorkTimer
    if ReglamentWorkTimer <= 0:
        if datetime.now().hour >= 19 or datetime.now().hour <= 6: # включим свет на улице
            if not arduino.LastSetStateOutDoorLight or arduino.LastSetStateOutDoorLight == None:
                arduino.SetPin(arduino.OutDoorLightPin,1)
                arduino.LastSetStateOutDoorLight = True
        else:
            if arduino.LastSetStateOutDoorLight or arduino.LastSetStateOutDoorLight == None:
                arduino.SetPin(arduino.OutDoorLightPin,0)
                arduino.LastSetStateOutDoorLight = False

        # Сообщим, что пропало напряжение на входе
        if not arduino.ACCExist and not arduino.ACAlertSended:
            for user in telegram_users:
                if user.level == 0 or user.level == 3 or True: 
                    SendToTelegramId(user.ID,'Отключилось напряжение на входе в дом!\n')
            arduino.ACAlertSended = True
        elif arduino.ACCExist and arduino.ACAlertSended:
            for user in telegram_users:
                if user.level == 0 or user.level == 3 or True:
                    SendToTelegramId(user.ID,'Ура! Появилось напряжение на входе в дом!\n')
            arduino.ACAlertSended = False

        # Сообщить, что напряжение аккумулятора низкое
        if arduino.DCVoltageInPercent <=20 and not arduino.DCVolLowAlertSended:
            for user in telegram_users:
                if user.level == 0 or user.level == 3 or True:
                    SendToTelegramId(user.ID,'Напряжение аккумулятора ниже 20% !!! Электричество скоро отключится.\n')
            arduino.DCVolLowAlertSended = True

        # Реакция пинов на заряд аккумулятора без входного напряжения
        if not arduino.ACCExist:
            for p in arduino.pins:
                if p.output and not p.BCODReaction and arduino.DCVoltageInPercent <= p.BCOD:
                    arduino.SetPin(p,0)
                    print(f'Отключил {p.description} по разряду аккумулятора')
                    p.BCODReaction = True   
        else:
            for p in arduino.pins:
                if p.output and p.BCODReaction and arduino.DCVoltageInPercent > p.BCOD:
                    p.BCODReaction = False 

        ReglamentWorkTimer = 100
    else:
        ReglamentWorkTimer -= 1
        
# ****** MAIN ******

# init watchdog
watchdog = CWatchDog('/dev/ttyACM0')
WDThread = threading.Thread(target=PingWatchdog, args=(watchdog,), daemon=True)
WDThread.start()

# init arduino
arduino = CArduino(path+arduino_config_name,path+arduino_pinstate)
arduino.LoadConfig()

# Start keyboart queue thread
inputQueue = queue.Queue()
inputThread = threading.Thread(target=read_kbd_input, args=(inputQueue,), daemon=True)
inputThread.start()

#Start Telegram bot thread
TelegramBotThread = threading.Thread(target=TelegramBot, args=(), daemon=True)
TelegramBotThread.start()

TelegrammAnswerQueue = queue.Queue()

# Main loop dunction
ReglamentWorkTimer = 100
while Run:
    if arduino.initialized:
        if (inputQueue.qsize() > 0):
            queue_typle = inputQueue.get()
            input_str = queue_typle[0]
            user = queue_typle[1]
            message = queue_typle[2]
            answer = CommandProcessing(input_str,user,message)
            print(answer)
        arduino.CheckInputPins()
        ReglamentWork()
    else:
        arduino.initialize()
    sleep(0.02)