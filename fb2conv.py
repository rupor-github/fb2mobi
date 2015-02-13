#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os 
import sys
import logging

import tempfile 
import subprocess 
import platform
import argparse 
import zipfile
import time
import datetime
import traceback
import locale
import shutil
import codecs
import version

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'modules'))
from fb2html import Fb2XHTML, transliterate
from config import ConverterConfig
from sendtokindle import SendKindle

from mobi_split import mobi_split

reload(sys)
sys.setdefaultencoding(locale.getpreferredencoding())

def get_executable_path():
    if getattr(sys, 'frozen', False):
        executable_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        executable_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    return executable_path

def create_epub(rootdir, epubname):
    ''' Генерация epub
    '''
    epub = zipfile.ZipFile(epubname, "w")
    epub.write(os.path.join(rootdir, 'mimetype'), 'mimetype', zipfile.ZIP_STORED)

    for root, dirs, files in os.walk(rootdir):
        relpath = os.path.relpath(root, rootdir)
        if relpath != '.':
            epub.write(root, relpath)
        
        for filename in files:
            if filename != 'mimetype':
                epub.write(os.path.join(root, filename), os.path.join(relpath, filename), zipfile.ZIP_DEFLATED)

    epub.close()

def get_mobi_filename(filename, translit=False):
    '''Формирует имя выходного файла mobi из имени файла fb2 с учетом 
    параметра транслитерации имени выходного файла
    '''    
    
    out_file = os.path.splitext(filename)[0]

    if os.path.splitext(out_file)[1].lower() == '.fb2':
        out_file = os.path.splitext(out_file)[0]
    
    if translit:
        out_file = transliterate(out_file)

    return u'{0}.mobi'.format(out_file)
    
def unzip(filename, tempdir):
    '''Разархивация файла.
    Возвращает имя разархивированного файла, либо None, если произошла ошибка
    '''
    
    unzipped_file = None
    
    zfile = zipfile.ZipFile(filename)
    zname = zfile.namelist()[0]
    zdirname, zfilename = os.path.split(zname)
    if zfilename:
        unzipped_file = os.path.join(tempdir, '_unzipped.fb2') 
        f = open(unzipped_file, 'w')
        f.write(zfile.read(zname))
        f.close()
    else:
        unzipped_file = None
        
    zfile.close()
    
    return unzipped_file
    
def rm_tmp_files(dir, deleteroot=True):
    '''Рекурсивное удаление файлов и подкаталогов в указанном каталоге,
    а также и самого каталога, переданного в качестве параметра
    '''
    
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    
    if deleteroot:        
        os.rmdir(dir)
  
    
def process_file(config, infile, outfile=None):
    '''Конвертация одного файла fb2, fb2.zip'''
    critical_error = False

    start_time = time.clock()
    temp_dir = tempfile.mkdtemp()
    
    if not os.path.exists(infile):
        config.log.critical(u'Файл {0} не найден'.format(infile))
        return
    
    if isinstance(infile, str):
        infile = infile.decode(sys.getfilesystemencoding())
    if outfile:
        if isinstance(outfile, str):
            outfile = outfile.decode(sys.getfilesystemencoding())
        
    config.log.info(u'Конвертируем "{0}"...'.format(os.path.split(infile)[1]))
    config.log.info(u'Используется профиль "{0}".'.format(config.current_profile['name']))

    # Проверка корректности параметров
    if infile:
        if not infile.lower().endswith((u'.fb2', '.fb2.zip', '.zip')):
            config.log.critical(u'"{0}" not *.fb2, *.fb2.zip or *.zip'.format(infile))
            return -1
    if not config.current_profile['css']:
        config.log.warning(u'В профиле не указан файл css.')

    if config.kindle_compression_level < 0 or config.kindle_compression_level > 2:
        config.log.warning(u'Значение параметра kindleCompressionLevel должно быть от 0 до 2, используем значение по умолчанию (1).')
        config.kindle_compression_level = 1
        
    # Если не задано имя выходного файла - вычислим
    if not outfile:
        outdir, outputfile = os.path.split(infile)
        outputfile = get_mobi_filename(outputfile, config.transliterate)

        if config.output_dir:
            if not os.path.exists(config.output_dir):
                os.makedirs(config.output_dir)
            if config.input_dir and config.save_structure:
                rel_path = os.path.join(config.output_dir, os.path.split(os.path.relpath(infile, config.input_dir))[0])
                if not os.path.exists(rel_path):
                    os.makedirs(rel_path)
                outfile = os.path.join(rel_path, outputfile)
            else:    
                outfile = os.path.join(config.output_dir, outputfile)
        else:
            outfile = os.path.join(outdir, outputfile)
    else:
        _output_format = os.path.splitext(outfile)[1].lower()[1:]
        if _output_format not in ('mobi', 'azw3', 'epub'):
            config.log.critical(u'Неизвестный формат конечного файла: {0}'.format(_output_format))
            return -1
        else:
            if not config.mhl:
                config.output_format = _output_format
            outfile = '{0}.{1}'.format(os.path.splitext(outfile)[0], config.output_format)
    
    if config.output_format.lower() == 'epub':
        # Для epub всегда разбиваем по главам
        config.current_profile['chapterOnNewPage'] = True

    debug_dir = os.path.abspath(os.path.splitext(infile)[0])
    if os.path.splitext(debug_dir)[1].lower() == '.fb2':
        debug_dir = os.path.splitext(debug_dir)[0]

    if os.path.splitext(infile)[1].lower() == '.zip':
        config.log.info(u'Разархивируем...')
        try:
            infile = unzip(infile, temp_dir)
        except:
            config.log.critical(u'Произошла ошибка при разархивации файла "{0}". Проверьте архив, попробуйте перепаковать файл с помощью 7-zip.'.format(infile))
            return -1

        if not infile:
            config.log.critical(u'Произошла ошибка при разархивации файла "{0}".'.format(infile))
            return -1
              
    # Конвертируем в html
    config.log.info(u'Конвертируем в html...')
    fb2parser = Fb2XHTML(infile, outfile, temp_dir, config)  
    fb2parser.generate()

    config.log.info(u'Конвертация в html закончена за {0} сек.'.format(round(time.clock() - start_time, 2)))

    if config.output_format.lower() in ('mobi', 'azw3'):
        # Запускаем kindlegen
        application_path = get_executable_path()
        if sys.platform == 'win32':
            if os.path.exists(os.path.join(application_path, 'kindlegen.exe')):
                kindlegen_cmd = os.path.join(application_path, 'kindlegen.exe')
            else:
                kindlegen_cmd = 'kindlegen.exe'
        else:
            if os.path.exists(os.path.join(application_path, 'kindlegen')):
                kindlegen_cmd = os.path.join(application_path, 'kindlegen')
            else:
                kindlegen_cmd = 'kindlegen'

        try:
            config.log.info(u'Запускаем kindlegen...')  
            kindlegen_cmd_pars = '-c{0}'.format(config.kindle_compression_level)
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.Popen([kindlegen_cmd, os.path.join(temp_dir, 'OEBPS','content.opf'), kindlegen_cmd_pars, '-locale', 'en'], 
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            
            res = result.stdout.read()
            try:
                config.log.debug(unicode(res, 'utf-8'))
            except:
                config.log.debug(u'Не могу отобразить вывод kindlegen: ошибка преобразования в Unicode')
                
            result.communicate()
            
        except OSError as e:
            if e.errno == os.errno.ENOENT:
                config.log.critical(u'{0} не найден'.format(kindlegen_cmd))
                critical_error = True
            else:
                config.log.critical(e.winerror)
                config.log.critical(e.strerror)
                raise e
    elif config.output_format.lower() == 'epub':
        # Собираем epub
        outfile = os.path.splitext(outfile)[0] + '.epub'
        config.log.info(u'Создаем epub...')
        create_epub(temp_dir, outfile)

    if config.debug:
        # В режиме отладки копируем получившиеся файлы в выходной каталог
        config.log.info(u'Копируем промежуточные файлы в каталог {0}...'.format(debug_dir))
        if os.path.exists(debug_dir):
            rm_tmp_files(debug_dir)
        shutil.copytree(temp_dir, debug_dir)

    # Копируем mobi(azw3) из временного в выходной каталог
    if not critical_error:
        if config.output_format.lower() in ('mobi', 'azw3'):  
            result_book = os.path.join(temp_dir, 'OEBPS', 'content.mobi')
            if not os.path.isfile(result_book):
                config.log.critical(u'При запуске kindlegen произошла ошибка, конвертация прервана.')
                critical_error = True
            else:
                if config.output_format.lower() == 'mobi':        
                    shutil.copyfile(result_book, outfile)
            
                elif config.output_format.lower() == 'azw3':
                    config.log.info(u'Извлекаем azw3 из mobi...')
                    try:
                        splitter = mobi_split(result_book, config.current_profile['kindleRemovePersonalLabel'])
                        open(os.path.splitext(outfile)[0] + '.azw3', 'wb').write(splitter.getResult8())
                    except:
                        config.log.critical(u'Произошла ошибка при распаковке формата azw3, конвертация прервана.')
                        critical_error = True
    else:
        return -1

    if not critical_error:
        config.log.info(u'Конвертация книги закончена за {0} сек.\n'.format(round(time.clock() - start_time, 2)))

    if config.send_to_kindle['send'] and not critical_error:
        if config.output_format.lower() != 'mobi':
            config.log.warning(u'Отправлять книги по почте можно только в формате mobi.')
        else:
            config.log.info(u'Отправляем книгу по почте...')
            try:
                kindle = SendKindle()
                kindle.smtp_server = config.send_to_kindle['smtpServer']
                kindle.smtp_port = config.send_to_kindle['smtpPort'] 
                kindle.smtp_login = config.send_to_kindle['smtpLogin']
                kindle.smtp_password = config.send_to_kindle['smtpPassword']
                kindle.user_email = config.send_to_kindle['fromUserEmail']
                kindle.kindle_email = config.send_to_kindle['toKindleEmail']        
                kindle.convert = False
                
                kindle.files.append(outfile.encode(sys.getfilesystemencoding()))
                kindle.send_mail()
                config.log.info(u'Книга отправлена на адрес {0}'.format(config.send_to_kindle['toKindleEmail']))
                if config.send_to_kindle['deleteSendedBook']:
                    try:
                        os.remove(outfile)
                    except:
                        config.log.error(u'Ошибка удаления файла {0} после отправки.'.format(outfile))
                        return -1
                    
            except KeyboardInterrupt:
                config.log.info(u'Отправка прервана.')

            except:
                # Чистим временные файлы  
                rm_tmp_files(temp_dir)
                type, value, tb = sys.exc_info()
                raise Exception(value.message)

    # Чистим временные файлы            
    rm_tmp_files(temp_dir)

    return 0
   
def process_folder(config, inputdir, outputdir=None):
    ''' Обработка каталога со вложенными подкаталогами.
    Обрабатываются все файлы *.fb2, *.fb2.zip.
    Если передан параметр --outputdir, сконвертированные файлы помещаются в этот каталог    
    '''
    
    if isinstance(inputdir, str):
        inputdir = inputdir.decode(sys.getfilesystemencoding())
    
    if outputdir:
        if isinstance(outputdir, str):
            outputdir = outputdir.decode(sys.getfilesystemencoding())
        
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        
    if os.path.isdir(inputdir):
        for root, dirs, files in os.walk(inputdir):
            for file in files:
                try:
                    if file.lower().endswith(('.fb2', '.fb2.zip', '.zip')):
                        inputfile = os.path.join(root, file)
                        # Обработка каталога. Смотрим признак рекурсии по подкаталогам
                        if (not config.recursive and inputdir == root) or config.recursive:
                            process_file(config, inputfile, None)
                            if config.delete_source_file:
                                try:
                                    os.remove(inputfile)
                                except:
                                    log.error(u'Невозможно удалить файл "{0}"'.format(inputfile))

                            continue
                except KeyboardInterrupt, e:
                    print u'Прервано пользователем. Выходим...'
                    sys.exit(-1)
                    
                except IOError, e:
                    log.error(u'(Ош. ввода/вывода {0}) {1} - {2}'.format(e.errno, e.strerror, e.filename))
                except:
                    type, value, tb = sys.exc_info()
                    log.error(u'({0}) {1}'.format(type.__name__, value.message))
    else:
        log.critical(u'Каталог "{0}" не найден'.format(inputdir))
        sys.exit(-1)
    
 
def get_log_level(log_level):

    if log_level.lower() == 'info':
        return logging.INFO
    elif log_level.lower() == 'error':
        return logging.ERROR
    elif log_level.lower() == 'critical':
        return logging.CRITICAL
    elif log_level.lower() == 'debug':
        return logging.DEBUG
    else:
        return logging.INFO

def process(args):
    result = 0

    infile = args.infile
    outfile = args.outfile

    config_file_name = 'fb2conv.config'

    application_path = get_executable_path()

    if os.path.exists(os.path.join(application_path, config_file_name)):
        config_file = os.path.join(application_path, config_file_name)
    else:
        if sys.platform == 'win32':
            config_file = os.path.join(os.path.expanduser('~'), 'fb2conv', config_file_name)
        else:    
            config_file = os.path.join(os.path.expanduser('~'), '.fb2conv', config_file_name)

    config = ConverterConfig(config_file)

    if args.profilelist:
        print u'Список профилей в {0}:'.format(config.config_file)
        for p in config.profiles:
            print u'\t{0}: {1}'.format(p, config.profiles[p]['description'])
        exit(0) 

    # Если указаны параметры в командной строке, переопределяем дефолтные параметры 1
    if args:
        if args.debug:
            config.debug = args.debug
        if args.log:
            config.log_file = args.log
        if args.loglevel:
            config.log_level = args.loglevel
        if args.recursive:
            config.recursive = True
        if args.nc:
            config.mhl = True


    log = logging.getLogger('fb2conv')
    log.setLevel(get_log_level(config.log_level))

    if config.log_file:
        log_handler = logging.FileHandler(filename=config.log_file, mode='a', encoding='utf-8')
        log_handler.setLevel(get_log_level(config.log_level))
        log_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    else:
        log_handler = logging.StreamHandler()
        log_handler.setLevel(get_log_level(config.log_level))
        log_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    if len(log.handlers) == 0:
        log.addHandler(log_handler)
    
    config.log = log

    if args.profile:
        config.setCurrentProfile(args.profile)
    else:
        config.setCurrentProfile(config.default_profile)

    # Если указаны параметры в командной строке, переопределяем дефолтные параметры 2
    if args:            
        if args.outputformat:
            config.output_format = args.outputformat            
        if args.hyphenate is not None:
            config.current_profile['hyphens'] = args.hyphenate
        if args.transliterate is not None:
            config.transliterate = args.transliterate
        if args.kindlecompressionlevel:
            config.kindle_compression_level = args.kindlecompressionlevel
        if args.css:
            config.current_profile['css'] = args.css
        if args.dropcaps is not None:
            config.current_profile['dropcaps'] = args.dropcaps
        if args.tocmaxlevel:
            config.current_profile['tocMaxLevel'] = args.tocmaxlevel
        if args.tocbeforebody is not None:
            config.current_profile['tocBeforeBody'] = args.tocbeforebody
        if args.notesmode:
            config.current_profile['notesMode'] = args.notesmode
        if args.notesbodies:
            config.current_profile['notesBodies'] = args.notesbodies
        if args.annotationtitle:
            config.current_profile['annotationTitle'] = args.annotationtitle
        if args.toctitle:
            config.current_profile['tocTitle'] = args.toctitle
        if args.chapteronnewpage is not None:
            config.current_profile['chapterOnNewPage'] = args.chapteronnewpage
        if args.sendtokindle is not None:
            config.send_to_kindle['send'] = args.sendtokindle

        if args.inputdir:
            config.input_dir = args.inputdir
        if args.outputdir:
            config.output_dir = args.outputdir
        if args.deletesourcefile:
            config.delete_source_file = args.deletesourcefile
        if args.savestructure:
            config.save_structure = args.savestructure

        if args.transliterateauthorandtitle is not None:
            config.transliterate_author_and_title = args.transliterateauthorandtitle

    if args.inputdir:
        process_folder(config, args.inputdir, args.outputdir)
        if args.deleteinputdir:
            try:
                rm_tmp_files(args.inputdir, False)
            except:
                log.error(u'Невозможно удалить каталог "{0}"'.format(args.inputdir))

    elif infile:
        result = process_file(config, infile, outfile)
        if args.deletesourcefile:
            try:
                os.remove(infile)
            except:
                log.error(u'Невозможно удалить файл "{0}"'.format(infile))
    else:
        print argparser.description
        argparser.print_usage()

    return result

if __name__ == '__main__':
    # Настройка парсера аргументов
    argparser = argparse.ArgumentParser(description=u'Конвертер книг в формате fb2 в форматы mobi, azw3 и epub. Версия {0}'.format(version.VERSION))

    input_args_group = argparser.add_mutually_exclusive_group()
    input_args_group.add_argument('infile', type=str, nargs='?', default=None, help=u'Имя исходного файла в формате fb2, fb2.zip или zip')
    input_args_group.add_argument('-i', '--input-dir', dest='inputdir', type=str, default=None, help=u'Имя исходного каталога для пакетной рекурсивной конвертации файлов fb2, fb2.zip или zip')
    
    output_args_group = argparser.add_mutually_exclusive_group()
    output_args_group.add_argument('outfile', type=str, nargs='?', default=None, help=u'Имя конечного файла в формате mobi, azw3 или epub')
    output_args_group.add_argument('-o', '--output-dir', dest='outputdir', type=str, default=None, help=u'Имя конченого каталога для помещения сконвертированных файлов')
    
    argparser.add_argument('-f', '--output-format', dest='outputformat', type=str, default=None, help=u'Формат для конвертации: mobi, azw3 или epub')
    argparser.add_argument('-r', dest='recursive', action='store_true', default=False, help=u'Обрабатывать рекурсивно файлы в исходном каталоге')    
    argparser.add_argument('-s','--save-structure', dest='savestructure', action='store_true', default=False, help=u'Сохранить структуру подкаталогов при пакетной обработке каталога')
    argparser.add_argument('--delete-source-file', dest='deletesourcefile', action='store_true', default=False, help=u'Удалить после успешной конвертации исходный файл')
    argparser.add_argument('--delete-input-dir', dest='deleteinputdir', action='store_true', default=False, help=u'Удалить исходный каталог с файлами')

    argparser.add_argument('-d', '--debug', action='store_true', default=None, help=u'Сохранить промежуточные файлы конвертации (html, xml и т.п.) в каталоге конечного файла')
    argparser.add_argument('--log', type=str, default=None, help=u'Имя лог-файла')
    argparser.add_argument('--log-level', dest='loglevel', type=str, default=None, help=u'Уровень вывода информации на экран или в лог-файл: INFO, ERROR, CRITICAL, DEBUG')
    hyphenate_group = argparser.add_mutually_exclusive_group()
    hyphenate_group.add_argument('--hyphenate', dest='hyphenate', action='store_true', default=None, help=u'Включить режим расстановки переносов в тексте книги')
    hyphenate_group.add_argument('--no-hyphenate', dest='hyphenate', action='store_false', default=None, help=u'Отключить режим расстановки переносов в тексте книги')
    transliterate_group = argparser.add_mutually_exclusive_group()
    transliterate_group.add_argument('--transliterate', dest='transliterate', action='store_true', default=None, help=u'Включить транслитерацию имени выходного файла')
    transliterate_group.add_argument('--no-transliterate', dest='transliterate', action='store_false', default=None, help=u'Отключить транслитерацию имени выходного файла')

    transliterate_author_group = argparser.add_mutually_exclusive_group()
    transliterate_author_group.add_argument('--transliterate-author-and-title', dest='transliterateauthorandtitle', action='store_true', default=None, help=u'Включить транслитерацию автора и названия книги')
    transliterate_author_group.add_argument('--no-transliterate-author-and-title', dest='transliterateauthorandtitle', action='store_false', default=None, help=u'Отключить транслитерацию автора и названия книги')

    argparser.add_argument('--kindle-compression-level', dest='kindlecompressionlevel', type=int, default=None, help=u'Уровень сжатия конечного файла mobi kindlegen - 0, 1 или 2')

    argparser.add_argument('-p', '--profile', type=str, default=None, help=u'Имя профиля для переопределения профиля по умолчанию')
    argparser.add_argument('--css', type=str, default=None, help=u'Файл css стилей')
    dropcaps_group = argparser.add_mutually_exclusive_group()
    dropcaps_group.add_argument('--dropcaps', dest='dropcaps', action='store_true', default=None, help=u'Включить использование буквицы в книге')
    dropcaps_group.add_argument('--no-dropcaps', dest='dropcaps', action='store_false', default=None, help=u'Отключить использование буквицы в книге')
    argparser.add_argument('-l', '--profile-list', dest='profilelist', action='store_true', default=False, help=u'Вывести список профилей, настроенных в файле конфигурации')

    argparser.add_argument('--toc-max-level', dest='tocmaxlevel', type=int, default=None, help=u'Максимальный уровень вложенности заголовка для включения в раздел "Содержание"')
    argparser.add_argument('--notes-mode', dest='notesmode', type=str, default=None, help=u'Режим отображения сносок в книге:  default, inline или block')
    argparser.add_argument('--notes-bodies', dest='notesbodies', type=str, default=None, help=u'Список имен разделов (body) формата fb2, содержащих сноски (через запятую)')
    argparser.add_argument('--annotation-title', dest='annotationtitle', type=str, default=None, help=u'Заголовок для раздела "Аннотация"')
    argparser.add_argument('--toc-title', dest='toctitle', type=str, default=None, help=u'Заголовок для раздела "Содержание"')
    chapter_group = argparser.add_mutually_exclusive_group()
    chapter_group.add_argument('--chapter-on-new-page', dest='chapteronnewpage', action='store_true', default=None, help=u'Начинать главу книги с новой страницы')
    chapter_group.add_argument('--no-chapter-on-new-page', dest='chapteronnewpage', action='store_false', default=None, help=u'Не начинать главу книги с новой страницы')

    tocplace_group = argparser.add_mutually_exclusive_group()
    tocplace_group.add_argument('--toc-before-body', dest='tocbeforebody', action='store_true', default=None, help=u'Разместить оглавление в начале книги')
    tocplace_group.add_argument('--toc-after-body', dest='tocbeforebody', action='store_false', default=None, help=u'Разместить оглавление в конце книги')
 
    sendtokindle_group = argparser.add_mutually_exclusive_group()
    sendtokindle_group.add_argument('--send-to-kindle', dest='sendtokindle', action='store_true', default=None, help=u'Отправить книгу по почте на устройство Kindle (в файле конфигурации должны быть настроены параметры отправки)')
    sendtokindle_group.add_argument('--no-send-to-kindle', dest='sendtokindle', action='store_false', default=None, help=u'Не отправлять книгу по почте на устройство Kindle')

    # Для совместимости с MyHomeLib добавляем аргументы, которые передает MHL в fb2mobi.exe
    # Работает только в бинарной версии для Windows
    argparser.add_argument('-nc', action='store_true', default=False, help=u'Добавлен для совместимости с MyHomeLib')
    argparser.add_argument('-cl', action='store_true', help=u'Добавлен для совместимости с MyHomeLib')
    argparser.add_argument('-us', action='store_true', help=u'Добавлен для совместимости с MyHomeLib')
    argparser.add_argument('-nt', action='store_true', help=u'Добавлен для совместимости с MyHomeLib')


    # Парсим аргументы командной строки
    args = argparser.parse_args()

    process(args)

  