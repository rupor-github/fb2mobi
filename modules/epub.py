# -*- coding: utf-8 -*-

import os
import sys
from lxml import etree, html, objectify
import re
import shutil
import io
import codecs
import uuid
import cssutils
import base64
import hashlib
import html

from utils import transliterate, indent

class EpubProc:
    def __init__(self, opffile, config):
        self.buff = []

        self.book_title = ''    # Название книги
        self.book_author = ''   # Автор
        self.book_series = ''   # Книжная серия
        self.book_series_num = ''   # Номер в книжной серии

        self.opffile = opffile

        self.log = config.log
        self.bookseriestitle = config.current_profile['bookTitleFormat']
        self.transliterate_author_and_title = config.transliterate_author_and_title

        self.tree = etree.parse(opffile, parser=etree.XMLParser(recover=True))
        self.root = self.tree.getroot()

    def process(self):

#        stdout = sys.stdout
#        sys.stdout = codecs.open('stdout.txt', 'w', 'utf-8')

        # Lookup series/sequences data if any
        for node in self.root.iter('{*}meta'):
            attributes = node.attrib
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
                title = title.replace('#series',     '' if not self.book_series else self.book_series.strip())
                title = title.replace('#number',     '' if not self.book_series_num else self.book_series_num.strip())
                title = title.replace('#padnumber',  '' if not self.book_series_num else self.book_series_num.strip().zfill(2))
                title = title.replace('#title',      '' if not self.book_title else self.book_title.strip())
                title = title.replace('#abbrseries', '' if not abbr else abbr.lower())
                if self.transliterate_author_and_title:
                    title = transliterate(title)
                node.text = title

        # TODO: Do we need profile per file extension?
        # TODO: Hyphenator?
        # TODO: Replace stylesheets?
        # TODO: book_author = transliterate(book_author)

        indent(self.root)
        self.tree.write(self.opffile, encoding='utf-8', method='xml', xml_declaration=True)

#        sys.stdout = stdout
