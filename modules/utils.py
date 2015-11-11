# -*- coding: utf-8 -*-

import os
import sys
import re
import io
import codecs

def transliterate(string):
    '''Транслитерация строки'''

    transtable =  {
        'а' : 'a',
        'б' : 'b',
        'в' : 'v',
        'г' : 'g',
        'д' : 'd',
        'е' : 'e',
        'ё' : 'e',
        'ж' : 'zh',
        'з' : 'z',
        'и' : 'i',
        'й' : 'i',
        'к' : 'k',
        'л' : 'l',
        'м' : 'm',
        'н' : 'n',
        'о' : 'o',
        'п' : 'p',
        'р' : 'r',
        'с' : 's',
        'т' : 't',
        'у' : 'u',
        'ф' : 'f',
        'х' : 'h',
        'ц' : 'c',
        'ч' : 'ch',
        'ш' : 'sh',
        'щ' : 'csh',
        'ъ' : "'",
        'ы' : 'i',
        'ь' : "'",
        'э' : 'e',
        'ю' : '',
        'я' : 'ya',

        'А' : 'A',
        'Б' : 'B',
        'В' : 'V',
        'Г' : 'G',
        'Д' : 'D',
        'Е' : 'E',
        'Ё' : 'E',
        'Ж' : 'Zh',
        'З' : 'Z',
        'И' : 'I',
        'Й' : 'I',
        'К' : 'K',
        'Л' : 'L',
        'М' : 'M',
        'Н' : 'N',
        'О' : 'O',
        'П' : 'P',
        'Р' : 'R',
        'С' : 'S',
        'Т' : 'T',
        'У' : 'U',
        'Ф' : 'F',
        'Х' : 'H',
        'Ц' : 'C',
        'Ч' : 'Ch',
        'Ш' : 'Sh',
        'Щ' : 'Csh',
        'Ъ' : "'",
        'Ы' : 'I',
        'Ь' : "'",
        'Э' : 'E',
        'Ю' : 'U',
        'Я' : 'YA'
    }

    translatedstring = []
    for c in string:
        translatedstring.append(transtable.setdefault(c, c))

    return ''.join(translatedstring)

def indent(elem, level=0):
    '''Функция для улучшения вида xml/html.
    Вставляет символы табуляции согласно уровню вложенности тэга
    '''

    i = '\n' + level*'\t'
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '\t'
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
