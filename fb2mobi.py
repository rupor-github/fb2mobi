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
#import traceback

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'modules'))
from fb2html import Fb2XHTML, transliterate
from config import ConverterConfig

from mobi_split import mobi_split

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

    return '{0}.mobi'.format(out_file)

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
        config.log.critical('File {0} not found'.format(infile))
        return

    config.log.info('Converting "{0}"...'.format(os.path.split(infile)[1]))
    config.log.info('Using profile "{0}".'.format(config.current_profile['name']))

    # Проверка корректности параметров
    if infile:
        if not infile.lower().endswith(('.fb2', '.fb2.zip', '.zip')):
            config.log.critical('"{0}" not *.fb2, *.fb2.zip or *.zip'.format(infile))
            return -1
    if not config.current_profile['css']:
        config.log.warning('Profile does not have link to css file.')

    if 'xslt' in config.current_profile and not os.path.exists(config.current_profile['xslt']):
        config.log.critical('Transformation file {0} not found'.format(config.current_profile['xslt']))
        return

    if config.kindle_compression_level < 0 or config.kindle_compression_level > 2:
        config.log.warning('Parameter kindleCompressionLevel should be between 0 and 2, using default value (1).')
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
            config.log.critical('Unknown output format: {0}'.format(_output_format))
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
        config.log.info('Unpacking...')
        try:
            infile = unzip(infile, temp_dir)
        except:
            config.log.critical('Error unpacking file "{0}".'.format(infile))
            return -1

        if not infile:
            config.log.critical('Error unpacking file "{0}".'.format(infile))
            return -1

    # Конвертируем в html
    config.log.info('Converting to html...')
    fb2parser = Fb2XHTML(infile, outfile, temp_dir, config)
    fb2parser.generate()

    config.log.info('Converting to html took {0} sec.'.format(round(time.clock() - start_time, 2)))

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
            config.log.info('Running kindlegen...')
            kindlegen_cmd_pars = '-c{0}'.format(config.kindle_compression_level)

            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.Popen( [kindlegen_cmd, os.path.join(temp_dir, 'OEBPS','content.opf'), kindlegen_cmd_pars, '-locale', 'en'],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupinfo)

            res = result.stdout.read()
            config.log.debug(str(res, 'utf-8', errors='replace' ))

        except OSError as e:
            if e.errno == os.errno.ENOENT:
                config.log.critical('{0} not found'.format(kindlegen_cmd))
                critical_error = True
            else:
                config.log.critical(e.winerror)
                config.log.critical(e.strerror)
                raise e
    elif config.output_format.lower() == 'epub':
        # Собираем epub
        outfile = os.path.splitext(outfile)[0] + '.epub'
        config.log.info('Creating epub...')
        create_epub(temp_dir, outfile)

    if config.debug:
        # В режиме отладки копируем получившиеся файлы в выходной каталог
        config.log.info('Copying intermediate files to {0}...'.format(debug_dir))
        if os.path.exists(debug_dir):
            rm_tmp_files(debug_dir)
        shutil.copytree(temp_dir, debug_dir)

    # Копируем mobi(azw3) из временного в выходной каталог
    if not critical_error:
        if config.output_format.lower() in ('mobi', 'azw3'):
            result_book = os.path.join(temp_dir, 'OEBPS', 'content.mobi')
            if not os.path.isfile(result_book):
                config.log.critical('kindlegen error, convertion interrupted.')
                critical_error = True
            else:
                if config.output_format.lower() == 'mobi':
                    shutil.copyfile(result_book, outfile)

                elif config.output_format.lower() == 'azw3':
                    config.log.info('Extracting azw3 from mobi...')
                    try:
                        splitter = mobi_split(result_book, config.current_profile['kindleRemovePersonalLabel'])
                        open(os.path.splitext(outfile)[0] + '.azw3', 'wb').write(splitter.getResult8())
                    except:
                        config.log.critical('Error processing azw3, convertion interrupted.')
                        critical_error = True
    else:
        return -1

    if not critical_error:
        config.log.info('Book convertion completed in {0} sec.\n'.format(round(time.clock() - start_time, 2)))

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
                                    log.error('Unable to remove file "{0}"'.format(inputfile))

                            continue
                except KeyboardInterrupt as e:
                    print('User interrupt. Exiting...')
                    sys.exit(-1)

                except IOError as e:
                    log.error('(I/O error {0}) {1} - {2}'.format(e.errno, e.strerror, e.filename))
                except:
                    type, value, tb = sys.exc_info()
                    log.error('({0}) {1}'.format(type.__name__, value.message))
    else:
        log.critical('Unable to find directory "{0}"'.format(inputdir))
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

    config_file_name = 'fb2mobi.config'

    application_path = get_executable_path()

    if os.path.exists(os.path.join(application_path, config_file_name)):
        config_file = os.path.join(application_path, config_file_name)
    else:
        if sys.platform == 'win32':
            config_file = os.path.join(os.path.expanduser('~'), 'fb2mobi', config_file_name)
        else:
            config_file = os.path.join(os.path.expanduser('~'), '.fb2mobi', config_file_name)

    config = ConverterConfig(config_file)

    if args.profilelist:

        print('Profile list in {0}:'.format(config.config_file))
        for p in config.profiles:
            print('\t{0}: {1}'.format(p, config.profiles[p]['description']))
        sys.exit(0)

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


    log = logging.getLogger('fb2mobi')
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
        if args.xslt:
            config.current_profile['xslt'] = args.xslt
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
                log.error('Unable to remove directory "{0}"'.format(args.inputdir))

    elif infile:
        result = process_file(config, infile, outfile)
        if args.deletesourcefile:
            try:
                os.remove(infile)
            except:
                log.error('Unable to remove file "{0}"'.format(infile))
    else:
        print(argparser.description)
        argparser.print_usage()

    return result

if __name__ == '__main__':
    # Настройка парсера аргументов
    argparser = argparse.ArgumentParser(description='Converter of fb2 ebooks to mobi, azw3 and epub formats. Version {0}'.format(version.VERSION))

    input_args_group = argparser.add_mutually_exclusive_group()
    input_args_group.add_argument('infile', type=str, nargs='?', default=None, help='Source file name (fb2, fb2.zip or zip)')
    input_args_group.add_argument('-i', '--input-dir', dest='inputdir', type=str, default=None, help='Source directory for batch conversion.')

    output_args_group = argparser.add_mutually_exclusive_group()
    output_args_group.add_argument('outfile', type=str, nargs='?', default=None, help='Destination file name (mobi, azw3 or epub)')
    output_args_group.add_argument('-o', '--output-dir', dest='outputdir', type=str, default=None, help='Destination directory name for batch conversion')

    argparser.add_argument('-f', '--output-format', dest='outputformat', type=str, default=None, help='Output format: mobi, azw3 or epub')
    argparser.add_argument('-r', dest='recursive', action='store_true', default=False, help='Perform recursive processing of files in source directory')
    argparser.add_argument('-s','--save-structure', dest='savestructure', action='store_true', default=False, help='Keep directory structure during batch processing')
    argparser.add_argument('--delete-source-file', dest='deletesourcefile', action='store_true', default=False, help='In case of success remove source file')
    argparser.add_argument('--delete-input-dir', dest='deleteinputdir', action='store_true', default=False, help='Remove source directory')

    argparser.add_argument('-d', '--debug', action='store_true', default=None, help='Keep imtermediate files in desctination directory')
    argparser.add_argument('--log', type=str, default=None, help='Log file name')
    argparser.add_argument('--log-level', dest='loglevel', type=str, default=None, help='Log level: INFO, ERROR, CRITICAL, DEBUG')
    hyphenate_group = argparser.add_mutually_exclusive_group()
    hyphenate_group.add_argument('--hyphenate', dest='hyphenate', action='store_true', default=None, help='Turn on hyphenation')
    hyphenate_group.add_argument('--no-hyphenate', dest='hyphenate', action='store_false', default=None, help='Turn off hyphenation')
    transliterate_group = argparser.add_mutually_exclusive_group()
    transliterate_group.add_argument('--transliterate', dest='transliterate', action='store_true', default=None, help='Transliterate destination file name')
    transliterate_group.add_argument('--no-transliterate', dest='transliterate', action='store_false', default=None, help='Do not transliterate destination file name')

    transliterate_author_group = argparser.add_mutually_exclusive_group()
    transliterate_author_group.add_argument('--transliterate-author-and-title', dest='transliterateauthorandtitle', action='store_true', default=None, help='Transliterate book title and author(s)')
    transliterate_author_group.add_argument('--no-transliterate-author-and-title', dest='transliterateauthorandtitle', action='store_false', default=None, help='Do not transliterate book title and author(s)')

    argparser.add_argument('--kindle-compression-level', dest='kindlecompressionlevel', type=int, default=None, help='Kindlegen compression level - 0, 1, 2')

    argparser.add_argument('-p', '--profile', type=str, default=None, help='Profile name from configuration')
    argparser.add_argument('--css', type=str, default=None, help='css file name')
    argparser.add_argument('--xslt', type=str, default=None, help='xslt file name')
    dropcaps_group = argparser.add_mutually_exclusive_group()
    dropcaps_group.add_argument('--dropcaps', dest='dropcaps', action='store_true', default=None, help='Use dropcaps')
    dropcaps_group.add_argument('--no-dropcaps', dest='dropcaps', action='store_false', default=None, help='Do not use dropcaps')
    argparser.add_argument('-l', '--profile-list', dest='profilelist', action='store_true', default=False, help='Show list of available profiles')

    argparser.add_argument('--toc-max-level', dest='tocmaxlevel', type=int, default=None, help='Maximum level of titles in the TOC')
    argparser.add_argument('--notes-mode', dest='notesmode', type=str, default=None, help='How to show footnotes: default, inline or block')
    argparser.add_argument('--notes-bodies', dest='notesbodies', type=str, default=None, help='List of fb2 part names (body) with footnotes (comma separated)')
    argparser.add_argument('--annotation-title', dest='annotationtitle', type=str, default=None, help='Annotations title')
    argparser.add_argument('--toc-title', dest='toctitle', type=str, default=None, help='TOC title')
    chapter_group = argparser.add_mutually_exclusive_group()
    chapter_group.add_argument('--chapter-on-new-page', dest='chapteronnewpage', action='store_true', default=None, help='Start chapter from the new page')
    chapter_group.add_argument('--no-chapter-on-new-page', dest='chapteronnewpage', action='store_false', default=None, help='Do not start chapter from the new page')

    tocplace_group = argparser.add_mutually_exclusive_group()
    tocplace_group.add_argument('--toc-before-body', dest='tocbeforebody', action='store_true', default=None, help='Put TOC at the book beginning')
    tocplace_group.add_argument('--toc-after-body', dest='tocbeforebody', action='store_false', default=None, help='Put TOC at the book end')

    # Для совместимости с MyHomeLib добавляем аргументы, которые передает MHL в fb2mobi.exe
    # Работает только в бинарной версии для Windows
    argparser.add_argument('-nc', action='store_true', default=False, help='For MyHomeLib compatibility')
    argparser.add_argument('-cl', action='store_true', help='For MyHomeLib compatibility')
    argparser.add_argument('-us', action='store_true', help='For MyHomeLib compatibility')
    argparser.add_argument('-nt', action='store_true', help='For MyHomeLib compatibility')


    # Парсим аргументы командной строки
    args = argparser.parse_args()

    process(args)


