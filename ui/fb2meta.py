#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import os
import zipfile
import codecs

from io import StringIO, BytesIO
from lxml import etree
from lxml.etree import QName


def indent(elem, level=0):
    '''Функция для улучшения вида xml/html.
    Вставляет символы пробела согласно уровню вложенности тэга
    '''

    i = '\n' + level * '  '
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

class Author():
    def __init__(self):
        self.first_name = ''
        self.middle_name = ''
        self.last_name = ''


class Sequence():
    def __init__(self):
        self.name = ''
        self.number = None


class Fb2Meta():
    def __init__(self, file):
        self.file = file

        self.genre = []
        self.author = []
        self.book_title = ''
        self.annotation = None
        self.keywords = None
        self.date = None
        self.coverpage = ''
        self.lang = 'ru'
        self.src_lang = ''
        self.translator = []
        self.sequence = []
        
        self.coverdata = None
        self.coverpage_href = ''
        self.is_zip = False

        if os.path.splitext(self.file)[1].lower() == '.zip':
            self.is_zip = True

        if self.is_zip:
            zip_file = zipfile.ZipFile(self.file, 'r')
            content = None

            if len(zip_file.namelist()) == 1:
                f = zip_file.open(zip_file.namelist()[0])
                content = f.read()
                f.close()

                self.tree = etree.parse(BytesIO(content), parser=etree.XMLParser(recover=True))
            else:
                # TODO: архиве несколько файлов. Ошибка
                pass
        else:
            self.tree = etree.parse(self.file, parser=etree.XMLParser(recover=True))

    def get_first_series(self):
        series_name = ''
        series_num = ''
        for series in self.sequence:
            series_name = series.name
            series_num = series.number

        return (series_name, series_num)


    def set_series(self, series_name, series_num):
        self.sequence = []
        if series_name:
            cur_series = Sequence()
            cur_series.name = series_name
            cur_series.number = series_num
            self.sequence.append(cur_series)


    def set_authors(self, author_str):
        self.author = []
        if author_str:
            for cur_author_str in author_str.split(','):
                author_elements = cur_author_str.strip().split()
                cur_author = Author()
                if len(author_elements) == 3:
                    cur_author.first_name = author_elements[0]
                    cur_author.middle_name = author_elements[1]
                    cur_author.last_name = author_elements[2]
                elif len(author_elements) == 2:
                    cur_author.first_name = author_elements[0]
                    cur_author.last_name = author_elements[1]
                else:
                    cur_author.last_name = cur_author_str.strip()

                self.author.append(cur_author)


    def get_autors(self):
        author_str = ''
        
        for author in self.author:
            if len(author_str) > 0:
                author_str += ', '

            if author.first_name:
            	author_str += author.first_name 
            if author.middle_name:
                author_str += ' ' + author.middle_name
            if author.last_name:
                author_str += ' ' + author.last_name

        return author_str.replace('  ', ' ').strip()


    def get(self):
        ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        for title_info in self.tree.xpath('//fb:description/fb:title-info', namespaces=ns):
            for elem in title_info:                
                if QName(elem).localname == 'genre':
                    self.genre.append(elem.text)
                elif QName(elem).localname == 'author':
                    author = Author()
                    for e in elem:
                        if QName(e).localname == 'first-name':
                            author.first_name = e.text
                        elif QName(e).localname == 'middle-name':
                            author.middle_name = e.text
                        elif QName(e).localname == 'last-name':
                            author.last_name = e.text
                    self.author.append(author)
                elif QName(elem).localname == 'book-title':
                    self.book_title = elem.text
                elif QName(elem).localname == 'annotation':
                    self.annotation = elem
                elif QName(elem).localname == 'keywords':
                    self.keywords = elem
                elif QName(elem).localname == 'date':
                    self.date = elem
                elif QName(elem).localname == 'coverpage':
                    for e in elem:
                        if QName(e).localname == 'image':
                            for attrib in e.attrib:                                
                                if QName(attrib).localname == 'href':
                                    self.coverpage = e.attrib[attrib][1:]
                                    self.coverpage_href = attrib
                elif QName(elem).localname == 'lang':
                    self.lang = elem.text
                elif QName(elem).localname == 'src-lang':
                    self.src_lang = elem.text
                elif QName(elem).localname == 'translator':
                    self.translator.append(elem)                    
                elif QName(elem).localname == 'sequence':
                    seq = Sequence()
                    for a in elem.attrib:
                        if a == 'name':
                            seq.name = elem.attrib[a]
                        elif a == 'number':
                            seq.number = elem.attrib[a]
                    self.sequence.append(seq)

        if self.coverpage:
            for tag in self.tree.xpath('//fb:binary[@id="{0}"]'.format(self.coverpage), namespaces=ns):
                self.coverdata = base64.b64decode(tag.text.encode('ascii'))
        

    def _create_title_info(self):
        ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

        title_info = etree.Element('title-info')
        
        for genre in self.genre:
            etree.SubElement(title_info, 'genre').text = genre
        
        for author in self.author:
            author_elem = etree.Element('author')
            if author.first_name:
                elem = etree.Element('first-name')
                elem.text = author.first_name
                author_elem.append(elem)
            if author.middle_name:
                elem = etree.Element('middle-name')
                elem.text = author.middle_name
                author_elem.append(elem)
            if author.last_name:
                elem = etree.Element('last-name')
                elem.text = author.last_name
                author_elem.append(elem)
            title_info.append(author_elem)
        
        etree.SubElement(title_info, 'book-title').text = self.book_title
        if self.annotation is not None:
            title_info.append(self.annotation)
        if self.keywords is not None:
            title_info.append(self.keywords)
        if self.date is not None:
            title_info.append(self.date)
        if self.coverpage:
            elem = etree.SubElement(title_info, 'coverpage')
            etree.SubElement(elem, 'image').attrib[self.coverpage_href] = '#{0}'.format(self.coverpage)
        etree.SubElement(title_info, 'lang').text = self.lang
        if self.src_lang:
            etree.SubElement(title_info, 'src-lang').text = self.src_lang
        for translator in self.translator:
            title_info.append(translator)
        for sequence in self.sequence:
            elem = etree.SubElement(title_info, 'sequence')
            if sequence.name:
                elem.attrib['name'] = sequence.name
            if sequence.number:
                elem.attrib['number'] = sequence.number

        for elem in self.tree.xpath('//fb:description/fb:title-info', namespaces=ns):
            elem.getparent().replace(elem, title_info)

        if self.coverpage and self.coverdata is not None:
            image_elem = None
            for elem in self.tree.xpath('//fb:binary[@id="{0}"]'.format(self.coverpage), namespaces=ns):
                image_elem = elem
                break

            if image_elem is None:
                image_elem = etree.SubElement(self.tree.getroot(), 'binary')
                image_elem.attrib['id'] = self.coverpage
                image_elem.attrib['content-type']='image/jpeg'

            image_elem.text = base64.encodebytes(self.coverdata)


    def write(self):
        ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

        self._create_title_info()
        indent(self.tree.getroot())

        if self.is_zip:
            zip_file = zipfile.ZipFile(self.file, 'w', zipfile.ZIP_DEFLATED)
            zip_file.writestr(os.path.splitext(self.file)[0], etree.tostring(self.tree, encoding='utf-8', 
            																 method='xml', xml_declaration=True))
            zip_file.close()
        else:
            self.tree.write(self.file, encoding='utf-8', method='xml', xml_declaration=True, pretty_print=False)

if __name__ == '__main__':
    # meta = Fb2Meta('Судья Ди 01. Золото Будды.fb2.zip')
    # meta = Fb2Meta('_test.fb2')
    # meta = Fb2Meta('Судья Ди 09. Убийство среди лотосов.fb2')
    # meta = Fb2Meta('Судья Ди 09. Убийство среди лотосов.fb2.zip')
    # meta.get()
    # meta.write()

    meta = Fb2Meta('Судья Ди 01. Золото Будды.fb2.zip')
    meta.set_authors('Роберт ван Гулик, Гулик Ван Роберт')
