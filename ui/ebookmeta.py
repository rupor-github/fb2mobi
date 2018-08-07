#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import os

from modules.myzipfile import ZipFile, ZipInfo

from io import BytesIO
from lxml import etree
from lxml.etree import QName
from ui.genres import genres
from modules.utils import format_pattern


class Author():
    def __init__(self):
        self.first_name = ''
        self.middle_name = ''
        self.last_name = ''


class Sequence():
    def __init__(self):
        self.name = ''
        self.number = None


class EbookMeta():
    def __init__(self, file):
        self.file = file
        self.book_type = ''

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
        self.encoding = ''
        self.zip_info = ZipInfo()

        if self.file.lower().endswith(('.fb2', '.fb2.zip', '.zip')):
            self.book_type = 'fb2'
        elif self.file.lower().endswith('.epub'):
            self.book_type = 'epub'

        if os.path.splitext(self.file)[1].lower() == '.zip':
            self.is_zip = True

        try:
            if self.book_type == 'fb2':
                if self.is_zip:
                    with ZipFile(self.file) as myzip:
                        # TODO - warn here if len(myzip.infolist) > 1?
                        self.zip_info = myzip.infolist()[0]
                        with myzip.open(self.zip_info, 'r') as myfile:
                            self.tree = etree.parse(BytesIO(myfile.read()), parser=etree.XMLParser(recover=True))
                            self.encoding = self.tree.docinfo.encoding
                else:
                    self.tree = etree.parse(self.file, parser=etree.XMLParser(recover=True))
                    self.encoding = self.tree.docinfo.encoding
            elif self.book_type == 'epub':
                pass
        except:
            self.book_type = ''

    def get_first_genre_name(self):
        genre_name = ''
        genre = self.get_first_genre()
        if genre in genres.keys():
            genre_name = genres[genre]

        return genre_name

    def get_first_genre(self):
        genre_name = ''
        for g in self.genre:
            genre_name = g
            break

        return genre_name

    def get_first_series(self):
        series_name = ''
        series_num = ''

        if self.book_type == 'fb2':
            for series in self.sequence:
                series_name = series.name
                series_num = series.number
                break

        return (series_name, series_num)

    def get_first_series_str(self):
        series = ''
        (name, num) = self.get_first_series()
        if name:
            series = name
        if num and series:
            series = series + ' [{}]'.format(num)

        return series

    def set_series(self, series_name, series_num):
        if self.book_type == 'fb2':
            self.sequence = []
            if series_name:
                cur_series = Sequence()
                cur_series.name = series_name
                cur_series.number = series_num
                self.sequence.append(cur_series)

    def set_authors(self, author_str):
        if self.book_type == 'fb2':
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

    def set_translators(self, translator_str):
        if self.book_type == 'fb2':
            self.translator = []
            if translator_str:
                for cur_tr_str in translator_str.split(','):
                    tr_elements = cur_tr_str.strip().split()
                    cur_tr = Author()
                    if len(tr_elements) == 3:
                        cur_tr.first_name = tr_elements[0]
                        cur_tr.middle_name = tr_elements[1]
                        cur_tr.last_name = tr_elements[2]
                    elif len(tr_elements) == 2:
                        cur_tr.first_name = tr_elements[0]
                        cur_tr.last_name = tr_elements[1]
                    else:
                        cur_tr.last_name = cur_tr_str.strip()

                    self.translator.append(cur_tr)

    def set_genre(self, genre):
        self.genre = []
        if genre and genre != 'empty':
            self.genre.append(genre)
        
    def get_translators(self):
        author_str = ''

        if self.book_type == 'fb2':
            for author in self.translator:
                if len(author_str) > 0:
                    author_str += ', '

                if author.first_name:
                    author_str += author.first_name
                if author.middle_name:
                    author_str += ' ' + author.middle_name
                if author.last_name:
                    author_str += ' ' + author.last_name

        return author_str.replace('  ', ' ').strip()

    def get_first_translator_lastname(self):
        translator = ''
        for t in self.translator:
            translator = t.last_name
            break
        return translator

    def get_autors(self):
        author_str = ''

        if self.book_type == 'fb2':
            for author in self.author:
                if len(author_str) > 0:
                    author_str += ', '

                if author.first_name:
                    author_str += author.first_name
                if author.middle_name:
                    author_str += ' ' + author.middle_name
                if author.last_name:
                    author_str += ' ' + author.last_name
        elif self.book_type == 'epub':
            author_str = ', '.join(self.author)

        return author_str.replace('  ', ' ').strip()


    def get(self):
        try:
            if self.book_type == 'fb2':
                self._get_fb2_metadata()
            elif self.book_type == 'epub':
                self._get_epub_metadata()
        except:
            self.book_type = ''


    def _get_epub_metadata(self):
        ns = {
            'n':'urn:oasis:names:tc:opendocument:xmlns:container',
            'pkg':'http://www.idpf.org/2007/opf',
            'dc':'http://purl.org/dc/elements/1.1/'
        }

        # prepare to read from the .epub file
        zip = ZipFile(self.file)

        # find the contents metafile
        txt = zip.read('META-INF/container.xml')
        tree = etree.fromstring(txt)
        cfname = tree.xpath('n:rootfiles/n:rootfile/@full-path',namespaces=ns)[0]

        # grab the metadata block from the contents metafile
        cf = zip.read(cfname)
        tree = etree.fromstring(cf)
        p = tree.xpath('/pkg:package/pkg:metadata',namespaces=ns)[0]

        self.author = []

        for e in p:
            if QName(e).localname == 'title':
                self.book_title = e.text
            elif QName(e).localname == 'creator':
                self.author.append(e.text)
            elif QName(e).localname == 'language':
                self.lang = e.text

        # get cover image
        p = tree.xpath('/pkg:package/pkg:manifest',namespaces=ns)[0]
        for e in p:
            if QName(e).localname == 'item':
                if 'id' in e.attrib:
                    if e.attrib['id'] in ['cover.jpg', 'cover-image', 'coverimage']:
                        if 'href' in e.attrib:
                            cover_file = e.attrib['href']
                            try:
                                self.coverdata = zip.read(os.path.join(os.path.split(cfname)[0], cover_file))
                            except:
                                null
                            break


    def _get_fb2_metadata(self):
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
                    translator = Author()
                    for e in elem:
                        if QName(e).localname == 'first-name':
                            translator.first_name = e.text
                        elif QName(e).localname == 'middle-name':
                            translator.middle_name = e.text
                        elif QName(e).localname == 'last-name':
                            translator.last_name = e.text
                    self.translator.append(translator)                    
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
            tr_elem = etree.Element('translator')
            if translator.first_name:
                elem = etree.Element('first-name')
                elem.text = translator.first_name
                tr_elem.append(elem)
            if translator.middle_name:
                elem = etree.Element('middle-name')
                elem.text = translator.middle_name
                tr_elem.append(elem)
            if translator.last_name:
                elem = etree.Element('last-name')
                elem.text = translator.last_name
                tr_elem.append(elem)
            title_info.append(tr_elem)
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
                image_elem.attrib['content-type'] = 'image/jpeg'

            image_elem.text = base64.encodebytes(self.coverdata)

    def write(self):
        if self.book_type == 'fb2':
            self._write_fb2_metadata()

    def _write_fb2_metadata(self):
        self._create_title_info()
        if self.is_zip:
            with ZipFile(self.file, 'w') as myzip:
                myzip.writestr(self.zip_info, etree.tostring(self.tree, encoding=self.encoding, method='xml', xml_declaration=True, pretty_print=True))
        else:
            self.tree.write(self.file, encoding=self.encoding, method='xml', xml_declaration=True, pretty_print=True)

    def get_formatted_authors(self, format_str, short=False):
        authors = []
        if len(self.author) > 0:
            for a in self.author:
                author = format_pattern(format_str, [
                        ('#fi', '' if not a.first_name else a.first_name[0] + '.'),
                        ('#mi', '' if not a.middle_name else a.middle_name[0] + '.'),
                        ('#f', '' if not a.first_name else a.first_name.strip()),
                        ('#m', '' if not a.middle_name else a.middle_name.strip()),
                        ('#l', '' if not a.last_name else a.last_name.strip())                    
                    ])
                authors.append(author)
                if short:
                    break

            if short and len(self.author) > 1:
                return authors[0] + ' и др' if self.lang.lower() == 'ru' else ', et al'
            else:
                return ', '.join(authors)
        else:
            return ''

    def get_file_ext(self):
        if self.file.lower().endswith('.fb2.zip'):
            return 'fb2.zip'
        elif self.file.lower().endswith('.zip'):
            return 'zip'
        elif self.file.lower().endswith('.fb2'):
            return 'fb2'
        return ''

    def meta_to_filename(self, author_format, filename_format, dest_path=None):
        if author_format and filename_format and self.book_type == 'fb2':
            (series_name, series_num) = self.get_first_series()

            name = format_pattern(filename_format, 
                [
                    ('#title', '' if not self.book_title else self.book_title.strip()),
                    ('#series', series_name.strip()),
                    ('#abbrseries', ''.join(word[0] for word in series_name.split()).lower() if series_name else ''),
                    ('#number', str(series_num).strip()),
                    ('#authors', self.get_formatted_authors(author_format, short=False)),
                    ('#author', self.get_formatted_authors(author_format, short=True)),
                    ('#translator', self.get_first_translator_lastname()),
                ])
            ext = self.get_file_ext()
            if not dest_path:
                dest_path = os.path.split(self.file)[0]
            return os.path.normpath(os.path.join(dest_path, '{0}.{1}'.format(name, ext)))
        else:
            return ''




