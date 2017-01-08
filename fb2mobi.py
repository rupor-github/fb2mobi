#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

import tempfile
import subprocess
import argparse
import zipfile
import time
import shutil
import uuid

import version

from modules.utils import transliterate
from modules.fb2html import Fb2XHTML
from modules.epub import EpubProc
from modules.config import ConverterConfig
from modules.sendtokindle import SendToKindle
from modules.mobi_split import mobi_split, mobi_read
from modules.mobi_pagemap import PageMapProcessor


def get_executable_path():
    if getattr(sys, 'frozen', False):
        executable_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        executable_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    return executable_path


def get_executable_name():
    if getattr(sys, 'frozen', False):
        name, ext = os.path.splitext(os.path.basename((sys.executable)))
    else:
        name, ext = os.path.splitext(os.path.basename((sys.argv[0])))

    return name


def create_epub(rootdir, epubname):
    epub = zipfile.ZipFile(epubname, "w")
    epub.write(os.path.join(rootdir, 'mimetype'), 'mimetype', zipfile.ZIP_STORED)

    for root, dirs, files in os.walk(rootdir):
        relpath = os.path.relpath(root, rootdir)
        if relpath != '.':
            epub.write(root, relpath)

        for filename in files:
            if filename != 'mimetype' and filename != '_unzipped.fb2':
                epub.write(os.path.join(root, filename), os.path.join(relpath, filename), zipfile.ZIP_DEFLATED)

    epub.close()


def get_mobi_filename(filename, translit=False):
    out_file = os.path.splitext(filename)[0]

    if os.path.splitext(out_file)[1].lower() == '.fb2':
        out_file = os.path.splitext(out_file)[0]

    if translit:
        out_file = transliterate(out_file)

    return '{0}.mobi'.format(out_file)


def unzip(filename, tempdir):
    unzipped_file = None

    zfile = zipfile.ZipFile(filename)
    zname = zfile.namelist()[0]
    zdirname, zfilename = os.path.split(zname)
    if zfilename:
        unzipped_file = os.path.join(tempdir, '_unzipped.fb2')
        with open(unzipped_file, 'wb') as f:
            f.write(zfile.read(zname))

    zfile.close()

    return unzipped_file


def unzip_epub(filename, tempdir):
    unzipped_file = None

    zfile = zipfile.ZipFile(filename)
    zname = next((x for x in zfile.namelist() if x.lower().endswith('.opf')), None)
    if zname:
        zfile.extractall(tempdir)
        unzipped_file = os.path.normpath(os.path.join(tempdir, zname))

    zfile.close()

    return unzipped_file


def rm_tmp_files(dir, deleteroot=True):
    for root, dirs, files in os.walk(dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    if deleteroot:
        os.rmdir(dir)


def process_file(config, infile, outfile=None):
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
        if not infile.lower().endswith(('.fb2', '.fb2.zip', '.zip', '.epub')):
            config.log.critical('"{0}" not *.fb2, *.fb2.zip, *.zip or *.epub'.format(infile))
            return

    if not config.current_profile['css'] and not infile.lower().endswith(('.epub')):
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

    input_epub = False

    if os.path.splitext(infile)[1].lower() == '.zip':
        config.log.info('Unpacking...')
        tmp_infile = infile
        try:
            infile = unzip(infile, temp_dir)
        except:
            config.log.critical('Error unpacking file "{0}".'.format(tmp_infile))
            return

        if not infile:
            config.log.critical('Error unpacking file "{0}".'.format(tmp_infile))
            return

    elif os.path.splitext(infile)[1].lower() == '.epub':
        config.log.info('Unpacking epub...')
        tmp_infile = infile
        try:
            infile = unzip_epub(infile, temp_dir)
        except:
            config.log.critical('Error unpacking file "{0}".'.format(tmp_infile))
            return

        if not infile:
            config.log.critical('Error unpacking file "{0}".'.format(tmp_infile))
            return

        input_epub = True

    if input_epub:
        # Let's see what we could do
        config.log.info('Processing epub...')
        epubparser = EpubProc(infile, config)
        epubparser.process()
        document_id = epubparser.book_uuid
    else:
        # Конвертируем в html
        config.log.info('Converting fb2 to html...')
        try:
            fb2parser = Fb2XHTML(infile, outfile, temp_dir, config)
            fb2parser.generate()
            document_id = fb2parser.book_uuid
            infile = os.path.join(temp_dir, 'OEBPS', 'content.opf')
        except:
            config.log.critical('Error while converting file "{0}"'.format(infile))
            config.log.debug('Getting details', exc_info=True)
            return

    config.log.info('Processing took {0} sec.'.format(round(time.clock() - start_time, 2)))

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

            with subprocess.Popen([kindlegen_cmd, infile, kindlegen_cmd_pars, '-locale', 'en'], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, startupinfo=startupinfo) as result:
                config.log.debug(str(result.stdout.read(), 'utf-8', errors='replace'))

        except OSError as e:
            if e.errno == os.errno.ENOENT:
                config.log.critical('{0} not found'.format(kindlegen_cmd))
                critical_error = True
            else:
                config.log.critical(e.winerror)
                config.log.critical(e.strerror)
                config.log.debug('Getting details', exc_info=True, stack_info=True)
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
        ext = config.output_format.lower()
        if ext in ('mobi', 'azw3'):
            result_book = infile.replace('.opf', '.mobi')
            if not os.path.isfile(result_book):
                config.log.critical('kindlegen error, conversion interrupted.')
                critical_error = True
            else:
                remove_personal = False
                try:
                    if ext not in 'mobi' or not config.send_to_kindle['send']:
                        remove_personal = config.current_profile['kindleRemovePersonalLabel']
                    if ext in ('mobi') and config.noMOBIoptimization:
                        config.log.info('Copying resulting file...')
                        shutil.copyfile(result_book, outfile)
                    else:
                        config.log.info('Optimizing resulting file...')
                        splitter = mobi_split(result_book, document_id, remove_personal, ext)
                        open(os.path.splitext(outfile)[0] + '.' + ext, 'wb').write(splitter.getResult() if ext == 'mobi' else splitter.getResult8())
                except:
                    config.log.critical('Error optimizing file, conversion interrupted.')
                    config.log.debug('Getting details', exc_info=True, stack_info=True)
                    critical_error = True

                if config.apnx and remove_personal:
                    # only for non-personal books we will have ASIN and could associate PageMap with book file
                    try:
                        base = os.path.splitext(outfile)[0]
                        reader = mobi_read(base + '.' + ext)
                        pagedata = reader.getPageData()
                        if len(pagedata) > 0:
                            config.log.info('Generating page index (APNX)...')
                            pages = PageMapProcessor(pagedata, config.log)
                            apnx = pages.generateAPNX(
                                {'contentGuid': str(uuid.uuid4()).replace('-', '')[:8],
                                 'asin': reader.getASIN(),
                                 'cdeType': 'EBOK',
                                 'format': 'MOBI_8' if ext in 'azw3' else 'MOBI_7',
                                 'pageMap': pages.getPageMap(),
                                 'acr': reader.getACR()})
                            if config.apnx == 'eink':
                                basename = os.path.basename(base)
                                sdr = base + '.sdr'
                                if not os.path.exists(sdr):
                                    os.makedirs(sdr)
                                apnxfile = os.path.join(sdr, basename + '.apnx')
                            else:
                                apnxfile = base + '.apnx'
                            open(apnxfile, 'wb').write(apnx)
                        else:
                            config.log.warning('No information to generate page index')
                    except:
                        config.log.warning('Unable to generate page index (APNX)')
                        config.log.debug('Getting details', exc_info=True, stack_info=True)

    if not critical_error:
        config.log.info('Book conversion completed in {0} sec.\n'.format(round(time.clock() - start_time, 2)))

        if config.send_to_kindle['send']:
            if config.output_format.lower() != 'mobi':
                config.log.warning('Kindle Personal Documents Service only accepts personal mobi files')
            else:
                config.log.info('Sending book...')
                try:
                    kindle = SendToKindle()
                    kindle.smtp_server = config.send_to_kindle['smtpServer']
                    kindle.smtp_port = config.send_to_kindle['smtpPort']
                    kindle.smtp_login = config.send_to_kindle['smtpLogin']
                    kindle.smtp_password = config.send_to_kindle['smtpPassword']
                    kindle.user_email = config.send_to_kindle['fromUserEmail']
                    kindle.kindle_email = config.send_to_kindle['toKindleEmail']
                    kindle.convert = False
                    kindle.send_mail([outfile])

                    config.log.info('Book has been sent to "{0}"'.format(config.send_to_kindle['toKindleEmail']))

                    if config.send_to_kindle['deleteSendedBook']:
                        try:
                            os.remove(outfile)
                        except:
                            config.log.error('Unable to remove file "{0}".'.format(outfile))
                            return -1

                except KeyboardInterrupt:
                    print('User interrupt. Exiting...')
                    sys.exit(-1)

                except:
                    config.log.error('Error sending file')
                    config.log.debug('Getting details', exc_info=True, stack_info=True)

    # Чистим временные файлы
    rm_tmp_files(temp_dir)


def process_folder(config, inputdir, outputdir=None):
    if outputdir:
        if not os.path.exists(outputdir):
            os.makedirs(outputdir)

    if os.path.isdir(inputdir):
        for root, dirs, files in os.walk(inputdir):
            for file in files:
                try:
                    if file.lower().endswith(('.fb2', '.fb2.zip', '.zip', '.epub')):
                        inputfile = os.path.join(root, file)
                        # Обработка каталога. Смотрим признак рекурсии по подкаталогам
                        if (not config.recursive and inputdir == root) or config.recursive:
                            process_file(config, inputfile, None)
                            if config.delete_source_file:
                                try:
                                    os.remove(inputfile)
                                except:
                                    config.log.error('Unable to remove file "{0}"'.format(inputfile))

                            continue
                except KeyboardInterrupt as e:
                    print('User interrupt. Exiting...')
                    sys.exit(-1)

                except IOError as e:
                    config.log.error('(I/O error {0}) {1} - {2}'.format(e.errno, e.strerror, e.filename))
                except:
                    config.log.error('Error processing folder')
                    config.log.debug('Getting details', exc_info=True, stack_info=True)

    else:
        config.log.critical('Unable to find directory "{0}"'.format(inputdir))
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
    infile = args.infile
    outfile = args.outfile
    config_file_name = "{0}.config".format(get_executable_name())
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
        if args.consolelevel:
            config.console_level = args.consolelevel
        if args.recursive:
            config.recursive = True
        if args.nc:
            config.mhl = True

    log = logging.getLogger('fb2mobi')
    log.setLevel("DEBUG")

    log_stream_handler = logging.StreamHandler()
    log_stream_handler.setLevel(get_log_level(config.console_level))
    log_stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    log.addHandler(log_stream_handler)

    if config.log_file:
        log_file_handler = logging.FileHandler(filename=config.log_file, mode='a', encoding='utf-8')
        log_file_handler.setLevel(get_log_level(config.log_level))
        log_file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
        log.addHandler(log_file_handler)

    config.log = log

    if args.profile:
        config.setCurrentProfile(args.profile)
    else:
        config.setCurrentProfile(config.default_profile)

    # Если указаны параметры в командной строке, переопределяем дефолтные параметры 2
    if args:
        if args.apnx:
            config.apnx = args.apnx.lower()
        if args.outputformat:
            config.output_format = args.outputformat
        if args.hyphenate is not None:
            config.current_profile['hyphens'] = args.hyphenate
        if args.transliterate is not None:
            config.transliterate = args.transliterate
        if args.screen_width is not None:
            config.screen_width = args.screen_width
        if args.screen_height is not None:
            config.screen_height = args.screen_height
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
        if args.removepngtransparency is not None:
            config.current_profile['removePngTransparency'] = args.removepngtransparency
        if args.noMOBIoptimization:
            config.noMOBIoptimization = args.noMOBIoptimization
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
                log.error('Unable to remove directory "{0}"'.format(args.inputdir))

    elif infile:
        process_file(config, infile, outfile)
        if args.deletesourcefile:
            try:
                os.remove(infile)
            except:
                log.error('Unable to remove file "{0}"'.format(infile))
    else:
        print(argparser.description)
        argparser.print_usage()


if __name__ == '__main__':

    # Настройка парсера аргументов
    argparser = argparse.ArgumentParser(
        description='Converter of fb2 and epub ebooks to mobi, azw3 and epub formats. Version {0}'.format(
            version.VERSION))

    input_args_group = argparser.add_mutually_exclusive_group()
    input_args_group.add_argument('infile', type=str, nargs='?', default=None, help='Source file name (fb2, fb2.zip, zip or epub)')
    input_args_group.add_argument('-i', '--input-dir', dest='inputdir', type=str, default=None, help='Source directory for batch conversion.')

    output_args_group = argparser.add_mutually_exclusive_group()
    output_args_group.add_argument('outfile', type=str, nargs='?', default=None, help='Destination file name (mobi, azw3 or epub)')
    output_args_group.add_argument('-o', '--output-dir', dest='outputdir', type=str, default=None, help='Destination directory name for batch conversion')

    argparser.add_argument('-f', '--output-format', dest='outputformat', type=str, default=None, help='Output format: mobi, azw3 or epub')
    argparser.add_argument('-r', dest='recursive', action='store_true', default=False, help='Perform recursive processing of files in source directory')
    argparser.add_argument('-s', '--save-structure', dest='savestructure', action='store_true', default=False,
                           help='Keep directory structure during batch processing')
    argparser.add_argument('--delete-source-file', dest='deletesourcefile', action='store_true', default=False, help='In case of success remove source file')
    argparser.add_argument('--delete-input-dir', dest='deleteinputdir', action='store_true', default=False, help='Remove source directory')

    argparser.add_argument('-d', '--debug', action='store_true', default=None, help='Keep imtermediate files in desctination directory')
    argparser.add_argument('--log', type=str, default=None, help='Log file name')
    argparser.add_argument('--log-level', dest='loglevel', type=str, default=None, help='Log level: INFO, ERROR, CRITICAL, DEBUG')
    argparser.add_argument('--console-level', dest='consolelevel', type=str, default=None, help='Log level: INFO, ERROR, CRITICAL, DEBUG')

    argparser.add_argument('--apnx', dest='apnx', type=str, default=None, choices=['eInk', 'PC'], help='Genrate page index file (APNX): eInk, PC')

    hyphenate_group = argparser.add_mutually_exclusive_group()
    hyphenate_group.add_argument('--hyphenate', dest='hyphenate', action='store_true', default=None, help='Turn on hyphenation')
    hyphenate_group.add_argument('--no-hyphenate', dest='hyphenate', action='store_false', default=None, help='Turn off hyphenation')

    transliterate_group = argparser.add_mutually_exclusive_group()
    transliterate_group.add_argument('--transliterate', dest='transliterate', action='store_true', default=None, help='Transliterate destination file name')
    transliterate_group.add_argument('--no-transliterate', dest='transliterate', action='store_false', default=None,
                                     help='Do not transliterate destination file name')

    transliterate_author_group = argparser.add_mutually_exclusive_group()
    transliterate_author_group.add_argument('--transliterate-author-and-title', dest='transliterateauthorandtitle', action='store_true', default=None,
                                            help='Transliterate book title and author(s)')
    transliterate_author_group.add_argument('--no-transliterate-author-and-title', dest='transliterateauthorandtitle', action='store_false', default=None,
                                            help='Do not transliterate book title and author(s)')

    screen_group = argparser.add_argument_group('Target device screen dimensions', 'default 800x573')
    screen_group.add_argument('--screen-width', dest='screen_width', type=int, default=None, help='Target screen width')
    screen_group.add_argument('--screen-height', dest='screen_height', type=int, default=None, help='Target screen height')

    argparser.add_argument('--kindle-compression-level', dest='kindlecompressionlevel', type=int, default=None, help='Kindlegen compression level - 0, 1, 2')
    argparser.add_argument('-p', '--profile', type=str, default=None, help='Profile name from configuration')
    argparser.add_argument('--no-MOBI-optimization', dest='noMOBIoptimization', action='store_true', default=False,
                           help='Do not do anything with resulting mobi file (Old behavior)')
    argparser.add_argument('--css', type=str, default=None, help='css file name')
    argparser.add_argument('--xslt', type=str, default=None, help='xslt file name')
    argparser.add_argument('--dropcaps', dest='dropcaps', type=str, default=None, choices=['Simple', 'Smart', 'None'],
                           help='Control dropcaps processing (Simple, Smart, None)')
    argparser.add_argument('-l', '--profile-list', dest='profilelist', action='store_true', default=False, help='Show list of available profiles')

    argparser.add_argument('--toc-max-level', dest='tocmaxlevel', type=int, default=None, help='Maximum level of titles in the TOC')
    argparser.add_argument('--notes-mode', dest='notesmode', type=str, default=None, choices=['default', 'inline', 'block', 'float'],
                           help='How to show footnotes: default, inline, block or float')
    argparser.add_argument('--notes-bodies', dest='notesbodies', type=str, default=None, help='List of fb2 part names (body) with footnotes (comma separated)')
    argparser.add_argument('--annotation-title', dest='annotationtitle', type=str, default=None, help='Annotations title')
    argparser.add_argument('--toc-title', dest='toctitle', type=str, default=None, help='TOC title')

    chapter_group = argparser.add_mutually_exclusive_group()
    chapter_group.add_argument('--chapter-on-new-page', dest='chapteronnewpage', action='store_true', default=None, help='Start chapter from the new page')
    chapter_group.add_argument('--no-chapter-on-new-page', dest='chapteronnewpage', action='store_false', default=None,
                               help='Do not start chapter from the new page')

    sendtokindle_group = argparser.add_mutually_exclusive_group()
    sendtokindle_group.add_argument('--send-to-kindle', dest='sendtokindle', action='store_true', default=None,
                                    help='Use Kindle Personal Documents Service to send book to device (<sendToKindle> in configuration file must have proper values!)')
    sendtokindle_group.add_argument('--no-send-to-kindle', dest='sendtokindle', action='store_false', default=None,
                                    help='Do not use Kindle Personal Documents Service to send book to device')

    tocplace_group = argparser.add_mutually_exclusive_group()
    tocplace_group.add_argument('--toc-before-body', dest='tocbeforebody', action='store_true', default=None, help='Put TOC at the book beginning')
    tocplace_group.add_argument('--toc-after-body', dest='tocbeforebody', action='store_false', default=None, help='Put TOC at the book end')

    pngtransparency_group = argparser.add_mutually_exclusive_group()
    pngtransparency_group.add_argument('--remove-png-transparency', dest='removepngtransparency', action='store_true', default=None,
                                       help='Remove transparency in PNG images')
    pngtransparency_group.add_argument('--no-remove-png-transparency', dest='removepngtransparency', action='store_false', default=None,
                                       help='Do not remove transparency in PNG images')

    # Для совместимости с MyHomeLib добавляем аргументы, которые передает MHL в fb2mobi.exe
    argparser.add_argument('-nc', action='store_true', default=False, help='For MyHomeLib compatibility')
    argparser.add_argument('-cl', action='store_true', help='For MyHomeLib compatibility')
    argparser.add_argument('-us', action='store_true', help='For MyHomeLib compatibility')
    argparser.add_argument('-nt', action='store_true', help='For MyHomeLib compatibility')

    # Парсим аргументы командной строки
    args = argparser.parse_args()

    process(args)
