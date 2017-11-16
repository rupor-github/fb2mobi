# -*- coding: utf-8 -*-

import os
import html
import uuid

from lxml import etree
from modules.utils import transliterate
from modules.myhyphen import MyHyphen


def save_html(string):
    if string:
        return html.escape(string, quote=False)
    else:
        return ''


class EpubProc:
    def __init__(self, opffile, config):
        self.buff = []

        self.book_title = ''  # Название книги
        self.book_author = ''  # Автор
        self.book_series = ''  # Книжная серия
        self.book_series_num = ''  # Номер в книжной серии

        self.book_lang = 'ru'

        self.hyphenate = config.current_profile['hyphens']
        if self.hyphenate:
            self.replaceNBSP = config.current_profile['hyphensReplaceNBSP']
            self.hyphenator = MyHyphen(self.book_lang)

        self.opffile = opffile
        self.path = os.path.dirname(opffile)

        self.log = config.log
        self.bookseriestitle = config.current_profile['bookTitleFormat']
        self.transliterate_author_and_title = config.transliterate_author_and_title

        self.book_uuid = uuid.uuid4()

        self.tree = etree.parse(opffile, parser=etree.XMLParser(recover=True))
        self.root = self.tree.getroot()

    def insert_hyphenation(self, s):
        if not s:
            return ''
        return html.unescape(s) if not self.hyphenator or not self.hyphenate else self.hyphenator.hyphenate_text(html.unescape(s), self.replaceNBSP)

    def process(self):

        # get uuid if any
        for node in self.root.iter('{*}identifier'):
            try:
                self.book_uuid = uuid.UUID(node.text)
            except:
                pass
            break
        # Lookup series/sequences data if any
        for node in self.root.iter('{*}meta'):
            attributes = node.attrib
            if 'name' in attributes:
                if attributes['name'].endswith('series_index'):
                    self.book_series_num = attributes['content']
                elif attributes['name'].endswith('series'):
                    self.book_series = attributes['content']

        # And reformat book title accordingly
        if self.book_series != '':
            for node in self.root.iter('{*}title'):
                self.book_title = node.text
                abbr = ''.join(word[0] for word in self.book_series.split())
                title = self.bookseriestitle
                title = title.replace('#series', '' if not self.book_series else self.book_series.strip())
                title = title.replace('#number', '' if not self.book_series_num else self.book_series_num.strip())
                title = title.replace('#padnumber', '' if not self.book_series_num else self.book_series_num.strip().zfill(2))
                title = title.replace('#title', '' if not self.book_title else self.book_title.strip())
                title = title.replace('#abbrseries', '' if not abbr else abbr.lower())
                if self.transliterate_author_and_title:
                    title = transliterate(title)
                node.text = title

        for node in self.root.iter('{*}language'):
            self.book_lang = node.text if len(node.text) > 2 else node.text.lower()

        if self.book_lang in ('rus'):
            self.book_lang = 'ru'

        if self.hyphenate and self.hyphenator:
            try:
                self.hyphenator.set_language(self.book_lang.replace("-", "_"))
            except:
                self.log.warning('Unable to set hyphenation dictionary for language code "{}" - turning hyphenation off'.format(self.book_lang))
                self.hyphenate = False

        self.tree.write(self.opffile, encoding='utf-8', method='xml', xml_declaration=True, pretty_print=True)

        # See if we have items to correct and process
        for node in self.root.iter('{*}item'):
            attributes = node.attrib
            if 'href' in attributes and 'media-type' in attributes:
                if attributes['media-type'] == 'application/xhtml+xml':
                    filename = os.path.join(self.path, attributes['href'])
                    self.log.debug('Processing {}'.format(filename))
                    # Proper XML encoding needed by kndlegen
                    xhtml = etree.parse(filename, parser=etree.XMLParser(recover=True))
                    if self.hyphenate:
                        # Do hyphenation if desiried
                        for body in xhtml.getroot().iter('{*}body'):
                            for elem in body.iter('{*}p', '{*}div'):
                                if elem.text:
                                    elem.text = save_html(self.insert_hyphenation(elem.text))
                                if elem.tail:
                                    elem.tail = save_html(self.insert_hyphenation(elem.tail))
                                for child in elem.iterchildren(tag=etree.Element):
                                    if not child.tag.endswith('pre'):
                                        if child.text:
                                            child.text = save_html(self.insert_hyphenation(child.text))
                                        if child.tail:
                                            child.tail = save_html(self.insert_hyphenation(child.tail))
                    xhtml.write(filename, encoding='utf-8', method='xml', xml_declaration=True)

                    # TODO: Do we need profile per file extension?
                    # TODO: Replace stylesheets?
                    # TODO: book_author = transliterate(book_author)

