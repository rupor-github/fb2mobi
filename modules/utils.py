# -*- coding: utf-8 -*-

import os
import sys
import shutil


def make_dir(filename):
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        os.makedirs(d)


def copy_file(src, dest):
    make_dir(dest)
    shutil.copyfile(src, dest)


def get_executable_path():
    if getattr(sys, 'frozen', False):
        executable_path = os.path.abspath(os.path.dirname(sys.executable))
    else:
        executable_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    return executable_path


def get_executable_name():
    if getattr(sys, 'frozen', False):
        name, _ = os.path.splitext(os.path.basename((sys.executable)))
    else:
        name, _ = os.path.splitext(os.path.basename((sys.argv[0])))

    return name


def transliterate(string):
    '''Транслитерация строки'''

    transtable = {
        'а': 'a',
        'б': 'b',
        'в': 'v',
        'г': 'g',
        'д': 'd',
        'е': 'e',
        'ё': 'e',
        'ж': 'zh',
        'з': 'z',
        'и': 'i',
        'й': 'i',
        'к': 'k',
        'л': 'l',
        'м': 'm',
        'н': 'n',
        'о': 'o',
        'п': 'p',
        'р': 'r',
        'с': 's',
        'т': 't',
        'у': 'u',
        'ф': 'f',
        'х': 'h',
        'ц': 'c',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'csh',
        'ъ': "'",
        'ы': 'i',
        'ь': "'",
        'э': 'e',
        'ю': '',
        'я': 'ya',
        'А': 'A',
        'Б': 'B',
        'В': 'V',
        'Г': 'G',
        'Д': 'D',
        'Е': 'E',
        'Ё': 'E',
        'Ж': 'Zh',
        'З': 'Z',
        'И': 'I',
        'Й': 'I',
        'К': 'K',
        'Л': 'L',
        'М': 'M',
        'Н': 'N',
        'О': 'O',
        'П': 'P',
        'Р': 'R',
        'С': 'S',
        'Т': 'T',
        'У': 'U',
        'Ф': 'F',
        'Х': 'H',
        'Ц': 'C',
        'Ч': 'Ch',
        'Ш': 'Sh',
        'Щ': 'Csh',
        'Ъ': "'",
        'Ы': 'I',
        'Ь': "'",
        'Э': 'E',
        'Ю': 'U',
        'Я': 'YA'
    }

    translatedstring = []
    for c in string:
        translatedstring.append(transtable.setdefault(c, c))

    return ''.join(translatedstring)
