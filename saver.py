import os
import time
from shutil import copyfile
import telebot

BOT = telebot.TeleBot('<TOKEN>')
CHAT_ID = <ID>

SRC_FOLDER = "PATH"
DST_FOLDER = "PATH"
TMP_FOLDER = "PATH"

DAYS = 31                   # максимальный возраст файлов оставляемых в tmp
CUT_SIZE = 15000            # 15 КБ максимально возможное уменьшение для файла

checkMassive = []           # массив проверенных файлов
moveMassive = []            # массив файлов перемещённых из dst в tmp
copyMassive = []            # массив скопированных из src в dst файлов
deleteMassive = []          # массив удалённых из tmp файлов
smallFilesMassive = []      # массив файлов подозрительного размера

def tryes(func):
    """Декоратор оборачивает функцию в try/except и совершает 4 попытки выполнения, в случае возникновения ошибки"""
    def inner(*args, **kwargs):                     # неопределенное количество позиционных или именованных аргументов
        count = 0                                   # объясляю счётчик попыток
        while count <= 3:
            try:
                func(*args, **kwargs)               # неопределенное количество позиционных или именованных аргументов
                count = 4                           # если функция отработает, мы выйдем из цикла
            except:
                count += 1                          # если функция не отработает, увеличим счётчик попыток
    return inner                                    # возвращаю вложенную функцию, без её вызова т.к. не добавлены круглые скобки

@tryes
def deleteEmptyDir(folder):
    """Функция рекурсивно удаляет пустые директории"""
    emptyFolders = 0                                # счётчик пустых директорий в данной итерации запуска функции
    for path, dirs, files in os.walk(folder):       # os.walk проходит по всем директориям и возвращает путь, названия самих директорий и названия файлов
        if (not dirs) and (not files):              # если в самой директории нет других директорий или файлов
            emptyFolders += 1                       # увеличиваю счётчик найденных директорий в данной итерации запуска функции
            os.rmdir(path)                          # удаляю директорию
    if emptyFolders > 0:                            # если была найденна директория из которой были удалены файлы или другие дирктории
        deleteEmptyDir(folder)                      # вызываю функцию ещё раз

@tryes
def deleteOldFiles(folder):
    """Функция удаляет файлы старше чем DAYS"""
    for path, dirs, files in os.walk(folder):           # walk ходит по всем директориям и возвращает путь к директории, название самой директории и названия файлов
        for file in files:                              # для каждого файла из всех найденных files которые вернёт walk
            fileName = os.path.join(path, file)         # соединяю части walk для получения полного названия файла (с расположением)
            fileTime = os.path.getmtime(fileName)       # время воздания файла в секундах
            nowTime = time.time()                       # текущее время в секундах от начала эпохи
            ageTime = nowTime - 60*60*24*DAYS           # текущее время в секундах минус 5 дней в секундах
            if fileTime < ageTime:                      # если файл старше ageTime в секундах
                os.remove(fileName)                     # удаляю файл
                deleteMassive.append(fileName)          # добавляю имя удалённого файла в список

@tryes
def copyFolders(srcFolder, dstFolder):
    """Функция создаёт создаёт копии директорий SCR в DST"""
    for path, dirs, files in os.walk(srcFolder):                    # walk ходит по всем директориям и возвращает путь к директории, название самой директории и названия файлов
        for dir in dirs:                                            # для каждого файла из всех найденных files которые вернёт walk
            srcDirPath = os.path.join(path, dir)                    # полный путь к директории источника
            dstDirPath = srcDirPath.replace(srcFolder, dstFolder)   # получаю полный путь который должен быть у директории получателя
            if not os.path.exists(dstDirPath):                      # если директории получателя не существует
                os.makedirs(dstDirPath)                             # создаю директорию получателя

@tryes
def moveToTMP(dstFolder, tmpFolder):
    """Функция перемещает файл из DST в TMP, если оригинал файла в SRC не существует"""
    for path, dirs, files in os.walk(dstFolder):                                        # walk ходит по всем директориям и возвращает путь к директории, название самой директории и названия файлов
        for file in files:                                                              # для каждого файла из всех найденных files которые вернёт walk
            dstFile = os.path.join(file)                                                # имя файла в DST
            dstFilePath = os.path.join(path, file)                                      # соединяю части walk для получения полного названия файла (с расположением)
            srcFilePath = dstFilePath.replace(dstFolder, SRC_FOLDER)                    # получаю полный путь к файлу источника, заменив путь к директории с dst на src
            tmpPath = tmpFolder + dstFile                                               # получаю полный путь к временному расположению файла
            try:
                if not os.path.exists(srcFilePath) and not os.path.exists(tmpPath):     # если файл источника не существует и он же не существует в tmp
                    copyfile(dstFilePath, tmpPath)                                      # копирую файл из dst в tmp
                    os.remove(dstFilePath)                                              # удаляю файл из dst
                    moveMassive.append(dstFile)                                         # добавляю перемещённый файл в массив
                elif not os.path.exists(srcFilePath) and os.path.exists(tmpPath):           # если файл источника не существует, но он уже есть в tmp
                    timeMark = time.time()                                                  # ставлю временную метку
                    cloneTmpPath = tmpFolder + str(timeMark) + str('_') + dstFile           # формирую имя для нового дубликата экземпляра файла
                    copyfile(dstFilePath, cloneTmpPath)                                     # копирую файл из dst в tmp
                    os.remove(dstFilePath)                                                  # удаляю файл из dst
                    moveMassive.append(cloneTmpPath)                                        # добавляю перемещённый файл в массив
            except:
                pass

@tryes
def copyFiles(srcFolder, dstFolder):
    """Функция копирует файлы из SRC в DST"""
    for path, dirs, files in os.walk(srcFolder):                    # walk ходит по всем директориям и возвращает путь к директории, название самой директории и названия файлов
        for file in files:                                          # для каждого файла из всех найденных files которые вернёт walk
            srcFile = os.path.join(file)                            # имя файла источника
            srcPath = os.path.join(path, file)                      # полный путь к файлу источнику
            srcSize = os.path.getsize(srcPath)                      # размер файла источника
            dstPath = srcPath.replace(srcFolder, dstFolder)         # получаю полный путь к файлу получателя
            folderName = dstPath.replace(srcFile, '')               # получаю путь к файлу получателя, без имени самого файла
            if os.path.exists(dstPath):                                         # если файл получателя существует
                dstSize = os.path.getsize(dstPath)                              # запрашиваю размер файла получателя
                changeSize = dstSize - srcSize                                  # получаю разницу между размерами файла источника и файла получателя
                if srcSize == dstSize:                                          # если размер файла получателя равен размеру файла источнику
                    checkMassive.append(srcFile)                                # добавляю файл к списку проверенных
                elif srcSize < dstSize and changeSize > CUT_SIZE:               # если файл источника уменьшился по отношению к файлу получателя больше чем на CUT_SIZE КБ
                    smallFilesMassive.append(srcFile)                           # добавляю файл к списку файлов подозрительного размера
                else:                                                           # если файл источника увеличился по отношению к файлу получателя
                    copyfile(srcPath, dstPath)                                  # перезаписываю файл из src в dst
                    copyMassive.append(srcFile)                                 # добавляю файл к списку скопированных из src в dst файлов
            elif not os.path.exists(dstPath) and os.path.exists(folderName):        # если файл получателя не существует, но директория в которой он должен лежать существует
                copyfile(srcPath, dstPath)                                          # копирую файл из src в dsr
                copyMassive.append(srcFile)                                         # добавляю файл к списку скопированных
            elif not os.path.exists(dstPath) and not os.path.exists(folderName):    # если файл получателя не существует и директория в которой он должен лежать не существует
                os.makedirs(folderName)                                             # создаю директорию (со всеми промежуточными директориями)
                copyfile(srcPath, dstPath)                                          # копирую файл из src в dst
                copyMassive.append(srcFile)                                         # добавляю файл к списку спопированных их src в dst

if os.path.exists(SRC_FOLDER):                      # выполняю код в случае наличия примонтированного источника
    moveToTMP(DST_FOLDER, TMP_FOLDER)               # перемещаю файлы из DST в tmp, если нет оригинала в SRC
    deleteEmptyDir(DST_FOLDER)                      # удаляю ВСЕ пустые директории из DST
    copyFolders(SRC_FOLDER, DST_FOLDER)             # копирую директории из SRC в DST
    copyFiles(SRC_FOLDER, DST_FOLDER)               # копирую файлы из SRC в DST
    deleteOldFiles(TMP_FOLDER)                      # удаляю старые файлы из TMP

    message = 'SAVER: \n\n'                         # формирую сообщение боту

    messageDel = 'Удалил состарившиеся файлы: '
    for x in deleteMassive:
        messageDel = str(messageDel) + '\n' + str(x)        # формирую список удалённых файлов
    if not messageDel == 'Удалил состарившиеся файлы: ':    # если список удалённых файлов не пуст
        message += messageDel + '\n\n'                      # добавляю его в сообщение

    messageMove = 'Переместил из DST в TMP: '
    for x in moveMassive:
        messageMove = str(messageMove) + '\n' + str(x)                  # формирую список перемещённых файлов
    if not messageMove == 'Переместил из DST в TMP: ':                  # если список перемещённых файлов не пуст
        message += messageMove + '\n\n'                                 # добавляю его в сообщение

    messageCheck = 'Проверил файлов: ' + str(len(checkMassive)) + '\n'      # считаю количество проверенных файлов
    message += messageCheck + '\n\n'                                        # добавляю его в сообщение

    messageCopy = 'Скопировал файлы: '
    for x in copyMassive:
        messageCopy = str(messageCopy) + '\n' + str(x)          # формирую список скопированных файлов
    if not messageCopy == 'Скопировал файлы: ':                 # если список скопированных файлов не пуст
        message += messageCopy + '\n\n'                         # добавляю его в сообщение

    messageSmallFiles = 'Размер уменьшения файла больше 15 КБ. Проверь сам: '
    for x in smallFilesMassive:
        messageSmallFiles = str(messageSmallFiles) + '\n' + str(x)                          # формирую список подозрительных файлов
    if not messageSmallFiles == 'Размер уменьшения файла больше 15 КБ. Проверь сам: ':      # если подозрительных файлов не пуст
        message += messageSmallFiles + '\n\n'                                               # добавляю его в сообщение

    BOT.send_message(CHAT_ID, message)
else:
    pass
