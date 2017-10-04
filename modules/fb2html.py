# -*- coding: utf-8 -*-

import os, sys
import re
import shutil
import io
import codecs
import uuid
import cssutils
import base64
import hashlib
import html
import imghdr

from copy import deepcopy
from lxml import etree, objectify
from PIL import Image

from modules.utils import transliterate
from modules.myhyphen import MyHyphen

HTMLHEAD = ('<html xmlns="http://www.w3.org/1999/xhtml">'
            '<head>'
            '<title>fb2mobi.py</title>'
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>'
            '<link rel="stylesheet" type="text/css" href="stylesheet.css"/>'
            '</head>'
            '<body>')

HTMLFOOT = ('</body>'
            '</html>')


def ns_tag(tag):
    if tag is not etree.Comment:
        if tag[0] == '{':
            tag = tag.split('}', 1)[1]
    return tag


def save_html(string):
    if string:
        return html.escape(string, quote=False)
    else:
        return ''


def sanitize_id(string):
    if string:
        return string.replace('\r', '').replace('\n', '').replace(' ', '')
    else:
        return ''

def make_dir(filename):
    d = os.path.dirname(filename)
    if not os.path.exists(d):
        os.makedirs(d)

def write_file(buff, filename):
    make_dir(filename)
    with codecs.open(filename, 'w', 'utf-8') as f:
        f.write(buff)


def write_file_bin(buff, filename):
    make_dir(filename)
    with open(filename, 'wb') as f:
        f.write(buff)


def copy_file(src, dest):
    make_dir(dest)
    shutil.copyfile(src, dest)


def format_title(s, seq):
    def replace_keyword(pict, k, v):
        if pict.count(k) > 0:
            return pict.replace(k, v), True if v else False
        return pict, False

    def replace_keywords(pict, seq):
        expanded = False
        for (k, v) in seq:
            pict, ok = replace_keyword(pict, k, v)
            expanded = expanded or ok
        if not expanded:
            return ''
        return pict

    p_o = -1
    p_c = -1

    # Hack - I do not want to write real parser
    pps = s.replace('\{', chr(1)).replace('\}', chr(2))

    for i in range(len(pps)):
        if pps[i] == '{':
            p_o = i
        elif pps[i] == '}':
            p_c = i
            break

    if p_o >= 0 and p_c > 0 and p_o < p_c:
        pps = format_title(pps[0:p_o] + replace_keywords(pps[p_o + 1:p_c], seq) + pps[p_c + 1:], seq)
    else:
        pps = replace_keywords(pps, seq)

    return pps.replace(chr(1), '{').replace(chr(2), '}')


class Fb2XHTML:
    def __init__(self, fb2file, mobifile, tempdir, config):

        self.log = config.log

        self.kindle = config.output_format.lower() in ('mobi', 'azw3')

        self.buff = []
        self.current_header_level = 0  # Уровень текущего заголовка
        self.header = False  # Признак формирования заголовка
        self.subheader = False  # Признак формирования подзаголовка
        self.first_chapter_line = False  # Признак первой строки в главе (секции) - для расстановки dropcaps
        self.inline_image_mode = False  # Индикатор режима вставки картинок (inline)
        self.body_name = ''  # Имя текущего раздела body, например notes
        self.no_paragraph = False  # Индикатор, что последующий парагаф находится в эпиграфе, аннотации и т.п.
        self.first_header_in_body = True  # Признак первого заголовка в секции body

        # Make sure book title is never empty
        temp_book_name = os.path.basename(fb2file)
        if not temp_book_name:
            temp_book_name = fb2file
        if os.path.splitext(temp_book_name)[1].lower() == '.fb2':
            temp_book_name = os.path.splitext(temp_book_name)[0]

        self.orig_file_name = fb2file

        self.book_title = temp_book_name  # Название книги
        self.book_author = ''  # Автор
        self.book_lang = 'ru'  # Язык книги, по-умолчанию 'ru'
        self.book_series = ''  # Книжная серия
        self.book_series_num = ''  # Номер в книжной серии
        self.book_cover = ''  # Ссылка на файл изображения обложки книги
        self.book_date = ''

        self.dropcaps = config.current_profile['dropcaps'].lower()  # Признак вставки стилей буквицы (dropcaps)
        self.nodropcaps = config.no_dropcaps_symbols  # Строка символов, для исключения буквицы

        # Максимальный уровень заголовка (секции) для помещения в содержание (toc.xhtml)
        # В toc.ncx помещаются все уровни
        self.toc_max_level = config.current_profile['tocMaxLevel'] if config.current_profile['tocMaxLevel'] else 1000
        # How to split toc.ncx for Kindle (eInk devices only show 2 levels)
        self.toc_kindle_level = config.current_profile['tocKindleLevel'] if config.current_profile['tocKindleLevel'] else 2

        self.authorformat = config.current_profile['authorFormat']
        self.booktitleformat = config.current_profile['bookTitleFormat']

        self.css_file = config.current_profile['css']
        self.parse_css = config.current_profile['parse_css']

        self.open_book_from_cover = config.current_profile['openBookFromCover']

        self.annotation = None

        self.generate_toc_page = config.current_profile['generateTOCPage']
        self.generate_annotation_page = config.current_profile['generateAnnotationPage']
        self.generate_opf_guide = config.current_profile['generateOPFGuide']

        self.vignettes = config.current_profile['vignettes']
        self.vignette_files = []

        self.removepngtransparency = config.current_profile['removePngTransparency']  # Remove transparency in PNG images

        self.annotation_title = config.current_profile['annotationTitle']  # Заголовок для раздела аннотации
        self.toc_title = config.current_profile['tocTitle']  # Заголовок для раздела содержания

        self.chaptersplit = config.current_profile['chapterOnNewPage']  # Разделять на отдельные файлы по главам
        self.chapterlevel = config.current_profile['chapterLevel']

        self.seriespositions = config.current_profile['seriesPositions']

        self.tocbeforebody = config.current_profile['tocBeforeBody']  # Положение содержания - в начале либо в конце книги
        self.transliterate_author_and_title = config.transliterate_author_and_title

        self.screen_width = config.screen_width
        self.screen_height = config.screen_height

        self.toc_type = config.current_profile['tocType']

        self.toc = {}  # Содрержание, формируется по мере парсинга
        self.toc_index = 1  # Текущий номер раздела содержания
        # Имя текущего файла для записи текста книги в xhtml.
        self.current_file = 'index.xhtml'
        self.current_file_index = 0

        # Для включения сносок и комментариев в текст книги
        self.notes_dict = {}  # Словарь со сносками и комментариями
        self.notes_order = []  # Notes in order of discovery
        self.notes_titles = {} # Dictionary of note body titles
        self.notes_mode = config.current_profile['notesMode']  # Режим отображения сносок: inline, block
        self.notes_bodies = config.current_profile['notesBodies']
        self.current_notes = []  # Переменная для хранения текущей сноски

        self.temp_dir = tempdir  # Временный каталог для записи промежуточных файлов
        self.temp_content_dir = os.path.join(self.temp_dir, 'OEBPS')
        self.temp_inf_dir = os.path.join(self.temp_dir, 'META-INF')

        self.html_file_list = []  # Массив для хранения списка сгенерированных xhtml файлов
        self.image_file_list = []  # Массив для хранения списка картинок
        self.image_count = 0

        self.pages_list = {}  # Additional pages per file
        self.page_length = 0

        self.characters_per_page = config.characters_per_page

        self.genres = []

        self.mobi_file = mobifile

        self.tree = etree.parse(fb2file, parser=etree.XMLParser(recover=True))
        if 'xslt' in config.current_profile:

            # rupor - this allows for smaller xsl, quicker replacement and allows handling of tags in the paragraphs
            class MyExtElement(etree.XSLTExtension):
                def execute(self, context, self_node, input_node, output_parent):
                    child = deepcopy(input_node)
                    found = False
                    for elem in child.getiterator():
                        if not found and elem.text is not None:
                            found = True
                            old_text = elem.text
                            elem.text = self_node.text
                            if len(old_text) > 1:
                                i = 1
                                for c in old_text[1:]:
                                    if c.isspace():
                                        i += 1
                                    else:
                                        break
                                elem.text = elem.text + old_text[i:]
                        if not hasattr(elem.tag, 'find'):
                            continue
                        i = elem.tag.find('}')
                        if i >= 0:
                            elem.tag = elem.tag[i + 1:]
                    objectify.deannotate(child, cleanup_namespaces=True)
                    output_parent.append(child)

            config.log.info('Applying XSLT transformations "{0}"'.format(config.current_profile['xslt']))
            self.transform = etree.XSLT(etree.parse(config.current_profile['xslt']),
                                        extensions={('fb2mobi_ns', 'katz_tr'): MyExtElement()})
            self.tree = self.transform(self.tree)
            for entry in self.transform.error_log:
                self.log.warning(entry)

        self.root = self.tree.getroot()

        self.hyphenate = config.current_profile['hyphens']
        if self.hyphenate:
            self.replaceNBSP = config.current_profile['hyphensReplaceNBSP']
            self.hyphenator = MyHyphen(self.book_lang)

        self.first_body = True  # Признак первого body
        self.font_list = []
        self.book_uuid = uuid.uuid4()
        self.links_location = {}

    def generate(self):

        self.get_notes_dict()

        for child in self.root:
            if ns_tag(child.tag) == 'binary':
                self.parse_binary(child)

        for child in self.root:
            if ns_tag(child.tag) == 'description':
                self.parse_description(child)
            elif ns_tag(child.tag) == 'body':
                self.parse_body(child)

        self.correct_links()

        if self.generate_toc_page:
            self.generate_toc()
        self.generate_cover()
        self.generate_ncx()

        if self.css_file:
            self.copy_css()

        for v in self.vignette_files:
            try:
                copy_file(v, os.path.join(os.path.join(self.temp_content_dir, 'vignettes'), os.path.split(v)[1]))
            except:
                self.log.warning('File {} not found.'.format(v))

        self.generate_pagemap()
        self.generate_opf()
        self.generate_container()
        self.generate_mimetype()

    def copy_css(self):
        base_dir = os.path.abspath(os.path.dirname(self.css_file))
        self.font_list = []

        def replace_url(url):
            source_file = os.path.abspath(os.path.join(base_dir, url))

            if os.path.splitext(url)[1].lower() in ('.ttf', '.otf'):
                dest_file = os.path.abspath(os.path.join(self.temp_content_dir, 'fonts', os.path.basename(source_file)))
                new_url = 'fonts/' + os.path.basename(url)
                self.font_list.append(new_url)
            else:
                dest_file = os.path.abspath(
                    os.path.join(self.temp_content_dir, 'images', 'css_' + os.path.basename(source_file)))
                new_url = 'images/css_' + os.path.basename(url)

            try:
                copy_file(source_file, dest_file)
            except:
                self.log.error('File {0}, referred by css, not found.'.format(url))

            return new_url

        if self.parse_css:

            # Note, macros are temporary, until CSS3 module is fixed and starts to recognize "rem" units
            cssutils.profile.addProfile('CSS extentions',
                                        {'-webkit-hyphens': 'none',
                                         'adobe-hyphenate': 'none',
                                         '-moz-hyphens': 'none',
                                         '-ms-hyphens': 'none',
                                         'hyphens': 'none|manual|auto'},
                                        {'length': r'0|{num}(em|ex|px|in|cm|mm|pt|pc|q|ch|rem|vw|vh|vmin|vmax)',
                                         'positivelength': r'0|{positivenum}(em|ex|px|in|cm|mm|pt|pc|q|ch|rem|vw|vh|vmin|vmax)',
                                         'angle': r'0|{num}(deg|grad|rad|turn)'})

            stylesheet = cssutils.parseFile(self.css_file)
            cssutils.replaceUrls(stylesheet, replace_url)
            write_file(str(stylesheet.cssText, 'utf-8'), os.path.join(self.temp_content_dir, 'stylesheet.css'))
        else:
            copy_file(self.css_file, os.path.join(self.temp_content_dir, 'stylesheet.css'))

    def correct_links(self):
        for fl in self.html_file_list:
            parser = etree.XMLParser(encoding='utf-8')
            root = etree.parse(os.path.join(self.temp_content_dir, fl), parser).getroot()

            for elem in root.xpath('//xhtml:a', namespaces={'xhtml': 'http://www.w3.org/1999/xhtml'}):
                link = elem.get('href', '')
                if len(link) > 0 and link.startswith('#'):
                    try:
                        elem.set('href', self.links_location[link[1:]] + link)
                    except:
                        pass

            self.buff = str.replace(str(etree.tostring(root, encoding='utf-8', method='xml', xml_declaration=True), 'utf-8'),' encoding=\'utf-8\'', '', 1)

            self.current_file = fl
            self.write_buff()

    def write_buff(self, dname='', fname=''):
        if len(fname) == 0:
            dirname = self.temp_content_dir
            filename = os.path.join(self.temp_content_dir, self.current_file)
        else:
            dirname = dname
            filename = os.path.join(dname, fname)

        if not os.path.exists(dirname):
            os.makedirs(dirname)

        parser = etree.XMLParser(encoding='utf-8', remove_blank_text=True)
        xhtml = etree.parse(io.StringIO(self.get_buff()), parser)
        xhtml.write(filename, encoding='utf-8', method='xml', xml_declaration=True, pretty_print=True)

    def write_buff_debug(self, dname='', fname=''):
        if len(fname) == 0:
            dirname = self.temp_content_dir
            filename = os.path.join(self.temp_content_dir, self.current_file)
        else:
            dirname = dname
            filename = os.path.join(dname, fname)
        write_file(self.get_buff(), filename)

    def write_debug(self, dname):
        self.tree.write(os.path.join(dname, os.path.split(self.orig_file_name)[1]), encoding='utf-8', method='xml', xml_declaration=True, pretty_print=False)

    def parse_note_elem(self, elem, body_name):
        note_title = ''

        if ns_tag(elem.tag) == 'title':

            # this is essetially a hack to preserve notes title (if any) for floating notes

            toc_title = etree.tostring(elem, method='text', encoding='utf-8').decode('utf-8').strip()
            toc_title = re.compile('[\[{].*[\]}]').sub('', toc_title) # Удалим остатки ссылок
            if toc_title:
                # Do real title parsing (notes file is not in pages_list anyways)
                save_buff = self.buff
                self.buff = []
                self.header = True
                self.parse_format(elem, 'div', 'h0')
                self.header = False
                self.notes_titles[body_name] = (toc_title, self.buff[:])
                self.buff = save_buff

        elif ns_tag(elem.tag) == 'section' and 'id' in elem.attrib:
            id = elem.attrib['id']
            notetext = []
            self.buff = []

            for e in elem:
                if ns_tag(e.tag) == 'title':
                    note_title = etree.tostring(e, method='text', encoding='utf-8').decode('utf-8').strip()
                else:
                    notetext.append(etree.tostring(e, method='text', encoding='utf-8').decode('utf-8').strip())

            self.notes_dict[id] = (note_title, ' '.join(notetext))
            self.notes_order.append((id, body_name))
        else:
            for e in elem:
                self.parse_note_elem(e, body_name)

    def get_notes_dict(self):
        self.notes_dict = {}

        notes_bodies = self.notes_bodies.replace(' ', '').split(',')

        for item in self.root:
            if ns_tag(item.tag) == 'body':
                if 'name' in item.attrib:
                    if item.attrib['name'] in notes_bodies:
                        for section in item:
                            self.parse_note_elem(section, item.attrib['name'])

    def get_vignette(self, level, vignette_type):
        vignette = None
        try:
            vignette = self.vignettes[level][vignette_type]
        except:
            try:
                vignette = self.vignettes['default'][vignette_type]
            except:
                pass

        found = False

        if vignette:
            for v in self.vignette_files:
                if v == vignette:
                    found = True
                    break

            if not found:
                self.vignette_files.append(vignette)

        if vignette:
            vignette = os.path.split(vignette)[1]

        return vignette

    def parse_description(self, elem):
        lastname = ''
        middlename = ''
        firstname = ''

        self.log.debug('Parsing description')

        for e in elem:
            if ns_tag(e.tag) == 'document-info':
                for t in e:
                    if ns_tag(t.tag) == 'id':
                        if t.text:
                            try:
                                self.book_uuid = uuid.UUID(t.text)
                            except:
                                pass
                            break
            elif ns_tag(e.tag) == 'title-info':
                for t in e:
                    if ns_tag(t.tag) == 'book-title':
                        if t.text:
                            self.book_title = t.text
                    elif ns_tag(t.tag) == 'lang':
                        if t.text:
                            self.book_lang = t.text if len(t.text) > 2 else t.text.lower()
                        else:
                            self.book_lang = 'ru'
                        if self.book_lang in ('rus'):
                            self.book_lang = 'ru'
                        if self.hyphenate and self.hyphenator:
                            try:
                                self.hyphenator.set_language(self.book_lang)
                            except:
                                self.log.warning('Unable to set hyphenation dictionary for language code "{}" - turning hyphenation off'.format(self.book_lang))
                                self.hyphenate = False

                    elif ns_tag(t.tag) == 'coverpage':
                        for c in t:
                            if ns_tag(c.tag) == 'image':
                                for a in c.attrib:
                                    if ns_tag(a) == 'href':
                                        self.book_cover = c.attrib[a][1:]
                                        break
                                    elif ':href' in a:
                                        self.book_cover = c.attrib[a][1:]
                                        self.log.warning('Wrong namespace is used for href attribute for cover page: {0}. Will attempt to recover...'.format(c.attrib))
                                        break

                    elif ns_tag(t.tag) == 'genre':
                        self.genres.append(t.text)

                    elif ns_tag(t.tag) == 'author':
                        if self.book_author == '':
                            for a in t:
                                if ns_tag(a.tag) == 'first-name':
                                    firstname = a.text
                                elif ns_tag(a.tag) == 'middle-name':
                                    middlename = a.text
                                elif ns_tag(a.tag) == 'last-name':
                                    lastname = a.text

                            self.book_author = format_title(self.authorformat,
                                                            [('#fi', '' if not firstname else firstname[0] + '.'),
                                                             ('#mi', '' if not middlename else middlename[0] + '.'),
                                                             ('#f', '' if not firstname else firstname.strip()),
                                                             ('#m', '' if not middlename else middlename.strip()),
                                                             ('#l', '' if not lastname else lastname.strip())])

                            self.book_author = self.book_author.strip()

                    elif ns_tag(t.tag) == 'sequence':
                        if 'name' in t.attrib:
                            self.book_series = t.attrib['name']
                        if 'number' in t.attrib:
                            self.book_series_num = t.attrib['number']

                    elif ns_tag(t.tag) == 'annotation':
                        self.annotation = etree.tostring(t, method='text', encoding='utf-8').decode('utf-8').strip()

                        if self.generate_annotation_page:
                            self.buff = []
                            self.current_file = 'annotation.xhtml'
                            self.html_file_list.append(self.current_file)

                            self.buff.append(HTMLHEAD)
                            self.buff.append('<div class="annotation"><div class="h1">{0}</div>'.format(self.annotation_title))
                            self.parse_format(t, 'div')
                            self.buff.append('</div>')
                            self.buff.append(HTMLFOOT)

                            self.write_buff()

                    elif ns_tag(t.tag) == 'date':
                        self.book_date = etree.tostring(t, method='text', encoding='utf-8').decode('utf-8').strip()

    def parse_binary(self, elem):
        if elem.attrib['id'] and elem.attrib['content-type']:
            have_file = False
            self.log.debug('Parsing binary {0}'.format(elem.attrib))
            id = elem.attrib['id']
            decl_type = elem.attrib['content-type'].lower()
            buff = base64.b64decode(elem.text.encode('ascii'))
            try:
                img = Image.open(io.BytesIO(buff))
                real_type = Image.MIME[img.format]
                format = img.format.lower()
                filename = "bin{0:08}.{1}".format(self.image_count,format.lower().replace('jpeg','jpg'))
                full_name = os.path.join(os.path.join(self.temp_content_dir, 'images'), filename)
                make_dir(full_name)

                if self.kindle and not format in ('gif', 'jpeg', 'png', 'bmp'):
                    self.log.warning('Image type "{0}" for ref-id "{1} is not supported by your device. Ignoring...'.format(real_type, id))
                    return

                if real_type != decl_type:
                    self.log.warning('Declared and detected image types for ref-id "{0}" do not match: "{1}" is not "{2}". Using detected type...'.format(id, decl_type, real_type))

                if self.removepngtransparency and format == 'png' and (img.mode in ('RGBA', 'LA') or (img.mode in ('RGB', 'L', 'P') and 'transparency' in img.info)):
                    try:
                        self.log.debug('Removing image transparency for ref-id "{0}" in file "{1}"'.format(id, filename))
                        if img.mode == "P" and type(img.info.get("transparency")) is bytes:
                            img = img.convert("RGBA")
                        if img.mode in ("L", "LA"):
                            bg = Image.new("L", img.size, 255)
                        else:
                            bg = Image.new("RGB", img.size, (255, 255, 255))
                        alpha = img.convert("RGBA").split()[-1]
                        bg.paste(img, mask=alpha)
                        bg.save(full_name, dpi=img.info.get("dpi"))
                        have_file = True
                    except:
                        self.log.warning('Unable to remove transparency for ref-id "{0}" in file "{1}"'.format(id, filename))
                        self.log.debug('Getting details:', exc_info=True)

                self.image_count += 1

            except:
                # Pillow does not recognize SVG files
                if decl_type.split('/')[1].lower() == 'svg':
                    real_type = 'image/svg+xml'
                    filename = "bin{0:08}.svg".format(self.image_count)
                    full_name = os.path.join(os.path.join(self.temp_content_dir, 'images'), filename)
                    self.image_count += 1
                else:
                    self.log.error('Unable to process binary for ref-id "{0}". Skipping...'.format(id))
                    # self.log.debug('Getting details:', exc_info=True)
                    return

            if not have_file:
                write_file_bin(buff, full_name)

            self.image_file_list.append((id, real_type, filename))

    def parse_span(self, span, elem):
        self.parse_format(elem, 'span', span)

    def parse_emphasis(self, elem):
        self.parse_span('emphasis', elem)

    def parse_strong(self, elem):
        self.parse_span('strong', elem)

    def parse_strikethrough(self, elem):
        self.parse_span('strike', elem)

    def parse_style(self, elem):
        self.parse_format(elem, 'span')

    def parse_emptyline(self):
        self.buff.append('<div class="emptyline" />')

    def parse_title(self, elem):
        toc_ref_id = 'tocref{0}'.format(self.toc_index)
        toc_title = etree.tostring(elem, method='text', encoding='utf-8').decode('utf-8').strip()
        toc_title = re.compile('[\[{].*[\]}]').sub('', toc_title) # Удалим остатки ссылок

        if not self.body_name or self.first_header_in_body:
            self.header = True
            self.first_chapter_line = True

            if self.current_header_level < self.chapterlevel:
                self.buff.append('<div class="titleblock" id="{0}">'.format(toc_ref_id))
            else:
                self.buff.append('<div class="titleblock_nobreak" id="{0}">'.format(toc_ref_id))

            if not self.body_name and self.first_header_in_body:
                vignette = self.get_vignette('h0', 'beforeTitle')
                if vignette:
                    self.buff.append('<div class="vignette_title_before"><img src="vignettes/{0}" /></div>'.format(vignette))

                self.parse_format(elem, 'div', 'h0')

                vignette = self.get_vignette('h0', 'afterTitle')
                if vignette:
                    self.buff.append('<div class="vignette_title_after"><img src="vignettes/{0}" /></div>'.format(vignette))

            else:
                level = 'h{0}'.format(self.current_header_level if self.current_header_level <= 6 else 6)

                vignette = self.get_vignette(level, 'beforeTitle')
                if vignette:
                    self.buff.append('<div class="vignette_title_before"><img src="vignettes/{0}" /></div>'.format(vignette))

                self.parse_format(elem, 'div', level)

                vignette = self.get_vignette(level, 'afterTitle')
                if vignette:
                    self.buff.append('<div class="vignette_title_after"><img src="vignettes/{0}" /></div>'.format(vignette))

            self.toc[self.toc_index] = ['{0}#{1}'.format(self.current_file, toc_ref_id), toc_title, self.current_header_level, self.body_name]
        else:
            self.buff.append('<div class="titlenotes" id="{0}">'.format(toc_ref_id))
            self.parse_format(elem, 'div')

        self.buff.append('</div>')
        self.first_header_in_body = False
        self.toc_index += 1
        self.header = False

    def parse_subtitle(self, elem):
        self.subheader = True
        self.parse_format(elem, 'p', 'subtitle')
        self.subheader = False

    def parse_image(self, elem):
        img_id = None
        int_id = None
        alt = None

        for a in elem.attrib:
            if ns_tag(a) == 'href':
                int_id = elem.attrib[a][1:]
            elif ':href' in a:
                self.log.warning('Wrong namespace is used for href attribute in <image>: {0}. Will attempt to recover...'.format(elem.attrib))
                int_id = elem.attrib[a][1:]
            elif ns_tag(a) == 'id':
                img_id = elem.attrib[a]
            elif ns_tag(a) == 'alt':
                alt = elem.attrib[a]

        if not int_id:
            self.log.error('Unable to find image ref-id in "{0}" "{1}.'.format(elem.tag, elem.attrib))
            return

        filename = None
        for id, type, file in self.image_file_list:
            if id == int_id:
                filename = file
                break
        if not filename:
            self.log.error('Unable to find image for ref-id "{0}" in "{1}" "{2}.'.format(int_id, elem.tag, elem.attrib))
            filename = "nonexistent.gif"
            alt = int_id

        if not alt:
            alt = filename

        if self.inline_image_mode:
            if img_id:
                self.buff.append('<img id="{0}" class="inlineimage" src="images/{1}" alt="{2}"/>'.format(img_id, filename, alt))
            else:
                self.buff.append('<img class="inlineimage" src="images/{0}" alt="{1}"/>'.format(filename, alt))
        else:
            if img_id:
                self.buff.append('<div id="{0}" class="image">'.format(img_id))
            else:
                self.buff.append('<div class="image">')
            self.buff.append('<img src="images/{0}" alt="{1}"/>'.format(filename, alt))
            self.buff.append('</div>')

        self.parse_format(elem)

    def parse_a(self, elem):
        href = None
        for name in elem.attrib:
            if ns_tag(name) == 'href':
                href = elem.attrib[name]
                break
            elif ':href' in name:
                self.log.warning('Wrong namespace is used for href attribute in <a>: {0}. Will attempt to recover...'.format(elem.attrib))
                href = elem.attrib[name]
                break
        if not href:
            self.log.error('Unable to find href attribute in <a>: {0}.'.format(elem.attrib))

        self.parse_format(elem, 'a', 'anchor', href=href)

    def parse_p(self, elem):
        ptag = 'p'
        pcss = None

        if self.header:
            pcss = 'title'

        self.parse_format(elem, ptag, pcss)

    def parse_poem(self, elem):
        self.no_paragraph = True
        self.parse_format(elem, 'div', 'poem')
        self.no_paragraph = False

    def parse_stanza(self, elem):
        self.parse_format(elem, 'div', 'stanza')

    def parse_v(self, elem):
        self.parse_format(elem, 'p')

    def parse_cite(self, elem):
        self.parse_format(elem, 'div', 'cite')

    def parse_textauthor(self, elem):
        self.no_paragraph = True
        self.parse_format(elem, 'div', 'text-author')
        self.no_paragraph = False

    def parse_annotation(self, elem):
        self.no_paragraph = True
        self.parse_format(elem, 'div', 'annotation')
        self.no_paragraph = False

    def parse_table(self, elem):
        self.buff.append('<table class="table"')
        for attr in elem.attrib:
            self.buff.append(' {0}="{1}"'.format(attr, elem.attrib[attr]))
        self.buff.append('>')
        self.parse_format(elem)
        self.buff.append('</table>')

    def parse_epigraph(self, elem):
        self.no_paragraph = True
        self.parse_format(elem, 'div', 'epigraph')
        self.no_paragraph = False

    def parse_code(self, elem):
        self.parse_format(elem, 'code')

    def parse_other(self, elem):
        self.parse_format(elem, ns_tag(elem.tag))

    def parse_section(self, elem):

        if not self.body_name and self.current_header_level == 0 and self.first_header_in_body:

            # We encountered main body without a title - need to add it forcefully, otherwise toc and books structure would be wrong

            toc_ref_id = 'tocref{0}'.format(self.toc_index)
            toc_title = self.book_author + self.book_title

            if self.current_header_level < self.chapterlevel:
                self.buff.append('<div class="titleblock" id="{0}">'.format(toc_ref_id))
            else:
                self.buff.append('<div class="titleblock_nobreak" id="{0}">'.format(toc_ref_id))

            vignette = self.get_vignette('h0', 'beforeTitle')
            if vignette:
                self.buff.append('<div class="vignette_title_before"><img src="vignettes/{0}" /></div>'.format(vignette))

            self.buff.append('<div class ="h0">')
            if self.book_author:
                self.buff.append('<p class="title">{0}</p>'.format(self.book_author))
            self.buff.append('<p class="title">{0}</p>'.format(self.book_title))
            self.buff.append('</div>')

            vignette = self.get_vignette('h0', 'afterTitle')
            if vignette:
                self.buff.append('<div class="vignette_title_after"><img src="vignettes/{0}" /></div>'.format(vignette))

            self.toc[self.toc_index] = ['{0}#{1}'.format(self.current_file, toc_ref_id), toc_title, self.current_header_level, '']

            self.buff.append('</div>')
            self.first_header_in_body = False
            self.toc_index += 1

        self.current_header_level = self.current_header_level + 1

        if not self.body_name:
            if self.chaptersplit and self.current_header_level < self.chapterlevel:
                self.buff.append(HTMLFOOT)
                self.write_buff()

                self.buff = []
                self.current_file_index += 1
                self.current_file = 'index{0}.xhtml'.format(self.current_file_index)
                self.html_file_list.append(self.current_file)
                self.buff.append(HTMLHEAD)

                self.pages_list[self.current_file] = 0
                self.page_length = 0

        self.parse_format(elem, tag='div', css='section')

        if not self.body_name:
            level = 'h{0}'.format(self.current_header_level if self.current_header_level <= 6 else 6)
            vignette = self.get_vignette(level, 'chapterEnd')
            if vignette:
                self.buff.append('<p class="vignette_chapter_end"><img src="vignettes/{0}" /></p>'.format(vignette))
            self.buff.append('<span class="chapter_end"/>')

        self.current_header_level = max(0, self.current_header_level - 1)

    def parse_date(self, elem):
        self.parse_format(elem, 'time')

    def parse_format(self, elem, tag=None, css=None, href=None):
        dodropcaps = 0

        if elem.text:
            # Обработка dropcaps
            if self.first_chapter_line and not (self.header or self.subheader or self.body_name or self.no_paragraph):
                if tag == 'p':
                    if self.dropcaps == 'simple':
                        if elem.text[0] not in self.nodropcaps:
                            dodropcaps = 1
                            css = 'dropcaps'
                    elif self.dropcaps == 'smart':
                        for i, c in enumerate(elem.text):
                            if c not in self.nodropcaps and not c.isspace():
                                dodropcaps = i + 1
                                css = 'dropcaps'
                                break
                self.first_chapter_line = False

        if self.notes_mode in ('inline', 'block') and tag == 'a':
            note_id = href[1:]
            try:
                note = self.notes_dict[note_id]
                self.current_notes.append(note)
                tag = 'span'
                css = '{0}anchor'.format(self.notes_mode)
                href = None
            except KeyError:
                pass
        elif self.notes_mode in ('default', 'float') and tag == 'a':
            if href[1:] in self.notes_dict:
                elem.set('id', 'back_' + href[1:])
            else:
                css = 'linkanchor'

        if tag:
            self.buff.append('<{0}'.format(tag))
            if css:
                self.buff.append(' class="{0}"'.format(css))
            if 'id' in elem.attrib:
                new_id = save_html(sanitize_id(elem.attrib['id']))
                if new_id != elem.attrib['id']:
                    self.log.warning('id "{}" for tag "{}" was sanitized. This may create problems with links (TOC, notes) - it is better to fix original file.'.format(new_id, tag))
                self.buff.append(' id="{}"'.format(new_id))
                self.links_location[new_id] = self.current_file
            if href:
                self.buff.append(' href="{}"'.format(save_html(href)))
            if css == 'section':
                self.buff.append(' />')
            else:
                self.buff.append('>')
            # Для inline-картинок
            if tag == 'p':
                self.inline_image_mode = True

        if elem.text:
            if self.current_file in self.pages_list and self.page_length + len(elem.text) >= self.characters_per_page:
                page = self.pages_list[self.current_file]
                text = ''

                for w in elem.text.split(' '):
                    if not text:
                        text = ' ' if not w else w
                    else:
                        text = ' '.join([text, w])
                    if self.page_length + len(text) >= self.characters_per_page:
                        hs = self.insert_hyphenation(text)
                        if dodropcaps > 0:
                            self.buff.append('<span class="dropcaps">{}</span>{}'.format(hs[0:dodropcaps], save_html(hs[dodropcaps:])))
                            dodropcaps = 0
                        else:
                            self.buff.append(save_html(hs))
                        self.buff.append('<a class="pagemarker" id="page_{0:d}"/> '.format(page))
                        page += 1
                        text = ''
                        self.page_length = 0

                self.page_length = len(text)
                if len(text) > 0:
                    hs = self.insert_hyphenation(text)
                    if dodropcaps > 0:
                        self.buff.append('<span class="dropcaps">{}</span>{}'.format(hs[0:dodropcaps], save_html(hs[dodropcaps:])))
                    else:
                        self.buff.append(save_html(hs))
                self.pages_list[self.current_file] = page
            else:
                self.page_length += len(elem.text)
                hs = self.insert_hyphenation(elem.text)
                if dodropcaps > 0:
                    self.buff.append('<span class="dropcaps">{}</span>{}'.format(hs[0:dodropcaps], save_html(hs[dodropcaps:])))
                else:
                    self.buff.append(save_html(hs))

        for e in elem:
            if e.tag == etree.Comment:
                continue
            if ns_tag(e.tag) == 'title':
                self.parse_title(e)
            elif ns_tag(e.tag) == 'subtitle':
                self.parse_subtitle(e)
            elif ns_tag(e.tag) == 'epigraph':
                self.parse_epigraph(e)
            elif ns_tag(e.tag) == 'annotation':
                self.parse_annotation(e)
            elif ns_tag(e.tag) == 'section':
                self.parse_section(e)
            elif ns_tag(e.tag) == 'strong':
                self.parse_strong(e)
            elif ns_tag(e.tag) == 'emphasis':
                self.parse_emphasis(e)
            elif ns_tag(e.tag) == 'strikethrough':
                self.parse_strikethrough(e)
            elif ns_tag(e.tag) == 'style':
                self.parse_style(e)
            elif ns_tag(e.tag) == 'a':
                self.parse_a(e)
            elif ns_tag(e.tag) == 'image':
                self.parse_image(e)
            elif ns_tag(e.tag) == 'p':
                self.parse_p(e)
            elif ns_tag(e.tag) == 'poem':
                self.parse_poem(e)
            elif ns_tag(e.tag) == 'stanza':
                self.parse_stanza(e)
            elif ns_tag(e.tag) == 'v':
                self.parse_v(e)
            elif ns_tag(e.tag) == 'cite':
                self.parse_cite(e)
            elif ns_tag(e.tag) == 'empty-line':
                self.parse_emptyline()
            elif ns_tag(e.tag) == 'text-author':
                self.parse_textauthor(e)
            elif ns_tag(e.tag) == 'table':
                self.parse_table(e)
            elif ns_tag(e.tag) == 'code':
                self.parse_code(e)
            elif ns_tag(e.tag) == 'date':
                self.parse_date(e)
            elif ns_tag(e.tag) == 'tr':
                self.parse_table_element(e)
            elif ns_tag(e.tag) == 'td':
                self.parse_table_element(e)
            elif ns_tag(e.tag) == 'th':
                self.parse_table_element(e)
            else:
                self.parse_other(e)

        if tag:
            if css == 'section':
                pass
            else:
                self.buff.append('</{0}>'.format(tag))
            # Для inline-картинок
            if tag == 'p':
                self.inline_image_mode = False

            if self.current_notes:
                if self.notes_mode == 'inline' and tag == 'span':
                    self.buff.append('<span class="inlinenote">{0}</span>'.format(save_html(self.insert_hyphenation(''.join(self.current_notes[0][1])))))
                    self.current_notes = []
                elif self.notes_mode == 'block' and tag == 'p':
                    self.buff.append('<div class="blocknote">')
                    for note in self.current_notes:
                        if note[1]:
                            self.buff.append('<p><span class="notenum">{0}) </span>{1}</p>'.format(save_html(note[0]), save_html(self.insert_hyphenation(''.join(note[1])))))
                    self.buff.append('</div>')
                    self.current_notes = []

        if elem.tail:
            self.page_length += len(elem.tail)
            self.buff.append(save_html(self.insert_hyphenation(elem.tail)))

    def parse_table_element(self, elem):
        self.buff.append('<{0}'.format(ns_tag(elem.tag)))

        for attr in elem.attrib:
            self.buff.append(' {0}="{1}"'.format(attr, elem.attrib[attr]))

        self.buff.append('>')
        self.parse_format(elem)
        self.buff.append('</{0}>'.format(ns_tag(elem.tag)))

    def insert_hyphenation(self, s):
        if not s:
            return ''
        return html.unescape(s) if not self.hyphenate or not self.hyphenator or self.header or self.subheader else self.hyphenator.hyphenate_text(html.unescape(s), self.replaceNBSP)

    def parse_body(self, elem):

        self.log.debug('Parsing body: {0}'.format(elem.attrib))

        self.body_name = elem.attrib['name'] if 'name' in elem.attrib else ''
        self.current_header_level = 0
        self.first_header_in_body = True

        if self.first_body:
            self.first_body = False
            self.body_name = ''

        self.buff = []
        self.buff.append(HTMLHEAD)

        if not self.body_name:
            self.current_file_index += 1
            self.current_file = 'index{0}.xhtml'.format(self.current_file_index)
            self.html_file_list.append(self.current_file)
        else:
            self.current_file = '{0}.xhtml'.format(hashlib.md5(bytes(self.body_name, 'utf-8')).hexdigest())
            self.html_file_list.append(self.current_file)

        self.pages_list[self.current_file] = 0
        self.page_length = 0

        if self.notes_mode in ('inline', 'block', 'float'):
            notes_bodies = self.notes_bodies.replace(' ', '').split(',')
            if self.body_name not in notes_bodies:
                self.parse_format(elem)
            elif self.notes_mode == 'float':

                # To satisfy Amazon's requirements for floating notes I have to create notes body on the fly here, removing most of the formatting

                if len(self.notes_order) > 0:
                    if self.body_name in self.notes_titles:
                        toc_title = self.notes_titles[self.body_name][0]
                        title = ''.join(self.notes_titles[self.body_name][1])
                    else:
                        toc_title = self.body_name[0].upper() + self.body_name[1:]
                        title = '<div class="h0"><p class="title">{0}</p></div>'.format(toc_title)

                    toc_ref_id = 'tocref{0}'.format(self.toc_index)
                    self.buff.append('<div class="titleblock" id="{0}">'.format(toc_ref_id))

                    vignette = self.get_vignette('h0', 'beforeTitle')
                    if vignette:
                        self.buff.append(
                            '<div class="vignette_title_before"><img src="vignettes/{0}" /></div>'.format(vignette))

                    self.buff.append(title)

                    vignette = self.get_vignette('h0', 'afterTitle')
                    if vignette:
                        self.buff.append('<div class="vignette_title_after"><img src="vignettes/{0}" /></div>'.format(vignette))

                    self.toc[self.toc_index] = ['{0}#{1}'.format(self.current_file, toc_ref_id), toc_title, 0, self.body_name]

                    self.buff.append('</div>')
                    self.toc_index += 1

                for id, body_name in self.notes_order:
                    if body_name == self.body_name:
                        note = self.notes_dict[id]
                        id_b = 'back_' + id
                        self.links_location[id] = self.current_file
                        # Sometimes due to an error document does not have a reference to note and numbers are all messed up
                        back_ref = 'nowhere'
                        try:
                            back_ref = self.links_location[id_b]
                        except:
                            pass
                        self.buff.append('<p class="floatnote"><a href="{0}#{1}" id="{2}">{3}).</a>&#160;{4}</p>'.format(back_ref, id_b, id, save_html(note[0]) if len(note[0]) > 0 else '***', save_html(note[1])))
                    else:
                        continue
        else:
            self.parse_format(elem)

        self.buff.append(HTMLFOOT)
        self.write_buff()

    def generate_toc(self):
        self.buff = []
        self.buff.append(HTMLHEAD)
        self.current_file = 'toc.xhtml'

        self.buff.append('<div class="toc">')
        self.buff.append('<div class="h1" id="toc">{0}</div>'.format(self.toc_title))
        for (idx, item) in self.toc.items():

            if item[2] <= self.toc_max_level:  # Ограничение уровня вложенности секций для TOC
                if item[3] == '':
                    ind = item[2] if item[2] <= 6 else 6
                    if ind == 0:
                        lines = item[1].splitlines()
                        self.buff.append('<div class="indent0"><a href="{0}">'.format(item[0]))
                        for line in lines:
                            if line.strip():
                                self.buff.append(save_html(line.strip()) + '<br/>')
                        self.buff.append('</a></div>')
                    else:
                        self.buff.append('<div class="indent{0}"><a href="{1}">{2}</a></div>'.format(ind, item[0], save_html(' '.join(item[1].split()))))
                else:
                    self.buff.append('<div class="indent0"><a href="{0}">{1}</a></div>'.format(item[0], save_html(' '.join(item[1].split()))))

        self.buff.append('</div>')
        self.buff.append(HTMLFOOT)

        self.write_buff()
        self.html_file_list.append(self.current_file)

    def ncx_navp_beg(self, index, title, link):
        self.buff.append('<navPoint id="navpoint{0}" playOrder="{1}">'.format(index, index))
        self.buff.append('<navLabel><text>{0}</text></navLabel>'.format(title))
        self.buff.append('<content src="{0}" />'.format(link))

    def ncx_navp_end(self):
        self.buff.append('</navPoint>')

    def generate_ncx(self):
        self.buff = []
        self.buff.append('<?xml version="1.0"?>'
                         '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="en-US">'
                         '<head>')
        self.buff.append('<meta name="dtb:uid" content="urn:uuid:{0}"/>'.format(self.book_uuid))
        self.buff.append('</head>'
                         '<docTitle>'
                         '<text>fb2mobi.py</text>'
                         '</docTitle>'
                         '<navMap>')
        i = 1

        # Включим содержание в навигацию, если содержание помещается в начале книги
        if self.tocbeforebody and len(self.toc.items()) > 0 and self.generate_toc_page:
            self.ncx_navp_beg(i, self.toc_title, 'toc.xhtml')
            self.ncx_navp_end()
            i += 1

        # First (book title) on the same level as the rest, if you want everything be under it do ncx_level = -1
        ncx_level = 2
        ncx_barrier = sys.maxsize

        if self.toc_type in 'flat':
            ncx_level = sys.maxsize
            ncx_barrier = 1

        if self.toc_type in 'kindle':
            ncx_level = self.toc_kindle_level
            ncx_barrier = 1

        history = []
        prev_item = None
        for (idx, item) in self.toc.items():
            if prev_item is None:  # first time
                self.ncx_navp_beg(i, save_html(' '.join(item[1].split())), item[0])
                history.append(item[2])
                i += 1
            elif prev_item[2] < item[2]:
                if item[2] < ncx_level or len(history) > ncx_barrier:
                    self.ncx_navp_end()
                    history.pop()
                self.ncx_navp_beg(i, save_html(' '.join(item[1].split())), item[0])
                history.append(item[2])
                i += 1
            elif prev_item[2] == item[2]:  # Same level
                self.ncx_navp_end()
                self.ncx_navp_beg(i, save_html(' '.join(item[1].split())), item[0])
            elif prev_item[2] > item[2]:  # Going out
                while history != [] and history[len(history) - 1] >= item[2]:
                    self.ncx_navp_end()
                    history.pop()
                self.ncx_navp_beg(i, save_html(' '.join(item[1].split())), item[0])
                history.append(item[2])
                i += 1
            else:
                assert False
            prev_item = item

        # Whatever levels are open - close them
        while history != []:
            self.ncx_navp_end()
            history.pop()

        # Включим содержание в навигацию, если содержание помещается в конце книги
        if not self.tocbeforebody and len(self.toc.items()) > 0 and self.generate_toc_page:
            self.ncx_navp_beg(i, self.toc_title, 'toc.xhtml')
            self.ncx_navp_end()

        self.buff.append('</navMap></ncx>')
        self.write_buff(self.temp_content_dir, 'toc.ncx')

    def generate_mimetype(self):
        mimetype = 'application/epub+zip'
        write_file(mimetype, os.path.join(self.temp_dir, 'mimetype'))

    def generate_container(self):
        self.buff = []
        self.buff.append('<?xml version="1.0"?>'
                         '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                         '<rootfiles>'
                         '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                         '</rootfiles>'
                         '</container>')
        self.write_buff(self.temp_inf_dir, 'container.xml')

    def generate_cover(self):
        filename = None
        if self.book_cover:
            for id, type, file in self.image_file_list:
                if id == self.book_cover:
                    filename = file
                    break
            if not filename:
                self.log.error('Unable to find book cover image for ref-id "{0}". Disabling book cover...'.format(self.book_cover))
                self.book_cover = ''
                return

            # make sure kindlegen does not complain on cover size and make sure that epub cover takes whole screen
            full_name = os.path.join(self.temp_content_dir, 'images', filename)
            im = Image.open(full_name)
            if im.height < self.screen_height:
                im.resize((int(self.screen_height * im.width / im.height), self.screen_height), Image.LANCZOS).save(full_name)

            self.buff = []
            self.buff.append(HTMLHEAD)
            self.buff.append('<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100%" height="100%" viewBox="0 0 {0} {1}" preserveAspectRatio="xMidYMid meet">'.format(self.screen_width, self.screen_height))
            self.buff.append('<image width="{0}" height="{1}" xlink:href="images/{2}" />'.format(self.screen_width, self.screen_height, filename))
            self.buff.append('</svg>')
            self.buff.append(HTMLFOOT)
            self.current_file = 'cover.xhtml'

            self.write_buff()

    def generate_pagemap(self):
        page = 1
        self.buff = []
        self.buff.append('<?xml version = "1.0" ?>'
                         '<page-map xmlns = "http://www.idpf.org/2007/opf">')

        if self.book_cover:
            self.buff.append('<page name="{0}" href="cover.xhtml"/>'.format(page))
            page += 1
        if self.tocbeforebody and self.generate_toc_page:
            self.buff.append('<page name="{0}" href="toc.xhtml"/>'.format(page))
            page += 1

        for item in self.html_file_list:
            if item != 'toc.xhtml':
                self.buff.append('<page name="{0}" href="{1}"/>'.format(page, item))
                page += 1
                if item in self.pages_list:
                    for p in range(0, self.pages_list[item]):
                        self.buff.append('<page name="{0:d}" href="{1:s}#page_{2:d}"/>'.format(page, item, p))
                        page += 1

        if not self.tocbeforebody and self.generate_toc_page:
            self.buff.append('<page name="{0}" href="toc.xhtml"/>'.format(page))
            page += 1

        self.buff.append('</page-map>')
        self.write_buff(self.temp_content_dir, 'page-map.xml')

    def generate_opf(self):
        self.buff = []
        self.buff.append('<?xml version="1.0" ?>'
                         '<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">'
                         '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">')

        title = self.book_title

        if self.booktitleformat:
            title = format_title(self.booktitleformat,
                                 [('#title', '' if not self.book_title else self.book_title.strip()),
                                  ('#series', '' if not self.book_series else self.book_series.strip()),
                                  ('#abbrseries', ''.join(word[0] for word in self.book_series.split()).lower() if self.book_series else ''),
                                  ('#number', '' if not self.book_series_num else self.book_series_num.strip()),
                                  ('#padnumber', '' if not self.book_series_num else self.book_series_num.strip().zfill(self.seriespositions)),
                                  ('#date', '' if not self.book_date else self.book_date.strip())])
            if not title:
                title = self.book_title

        title = title.strip()

        book_author = self.book_author

        if self.transliterate_author_and_title:
            title = transliterate(title)
            book_author = transliterate(book_author)

        self.buff.append('<dc:title>{0}</dc:title>'.format(save_html(title)))
        self.buff.append('<dc:language>{0}</dc:language>'.format(self.book_lang))
        self.buff.append('<dc:identifier id="BookId" opf:scheme="uuid">urn:uuid:{0}</dc:identifier>'.format(self.book_uuid))
        self.buff.append('<dc:creator opf:role="aut">{0}</dc:creator>'.format(save_html(book_author)))
        self.buff.append('<dc:publisher />')

        for genre in self.genres:
            self.buff.append('<dc:subject>{0}</dc:subject>'.format(genre))

        if self.annotation:
            self.buff.append('<dc:description>{0}</dc:description>'.format(save_html(self.annotation)))

        if self.book_cover:
            self.buff.append('<meta name="cover" content="cover-image" />')

        self.buff.append('</metadata>')
        self.buff.append('<manifest>'
                         '<item id="ncx" media-type="application/x-dtbncx+xml" href="toc.ncx"/>'
                         '<item id = "map" media-type="application/oebps-page-map+xml" href="page-map.xml"/>')

        for item in self.html_file_list:
            self.buff.append('<item id="{0}" media-type="application/xhtml+xml" href="{1}"/>'.format(item.split('.')[0], item))

        item_id = 0
        for id, type, filename in self.image_file_list:
            if id == self.book_cover:
                self.buff.append('<item id="cover-image" media-type="{0}" href="images/{1}"/>'.format(type, filename))
                self.buff.append('<item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml"/>')
            else:
                self.buff.append('<item id="image{0}" media-type="{1}" href="images/{2}"/>'.format(item_id, type, filename))

            item_id += 1

        for item in self.vignette_files:
            item_file = os.path.split(item)[1]
            item_type = os.path.splitext(item_file)[1]
            item_type = item_type[1:]

            if item_type == 'jpg':
                item_type = 'jpeg'

            self.buff.append('<item id="image{0}" media-type="image/{1}" href="vignettes/{2}"/>'.format(item_id, item_type, item_file))
            item_id += 1

        self.buff.append('<item id="style" href="stylesheet.css" media-type="text/css"/>')

        font_id = 0
        for f in self.font_list:
            if f.lower().endswith('.otf'):
                self.buff.append('<item id="font{0}" href="{1}" media-type="application/opentype"/>'.format(font_id, f))
            else:
                self.buff.append('<item id="font{0}" href="{1}" media-type="application/x-font-ttf"/>'.format(font_id, f))
            font_id += 1

        self.buff.append('</manifest>'
                         '<spine page-map="map" toc="ncx">')

        if self.book_cover:
            self.buff.append('<itemref idref="cover-page" linear="no"/>')
        if self.tocbeforebody and self.generate_toc_page:
            self.buff.append('<itemref idref="toc"/>')

        for item in self.html_file_list:
            if item != 'toc.xhtml':
                self.buff.append('<itemref idref="{0}"/>'.format(item.split('.')[0]))

        if not self.tocbeforebody and self.generate_toc_page:
            self.buff.append('<itemref idref="toc"/>')

        self.buff.append('</spine>')

        if self.generate_opf_guide:
            self.buff.append('<guide>')
            if self.book_cover:
                self.buff.append('<reference type="cover-page" href="cover.xhtml"/>')

            if self.open_book_from_cover and self.book_cover:
                self.buff.append('<reference type="text" title="book" href="cover.xhtml"/>')
            else:
                for item in self.html_file_list:
                    if item.split('.')[0].startswith('index'):
                        self.buff.append('<reference type="text" title="Starts here" href="{0}"/>'.format(item))
                        break

            self.buff.append('<reference type="toc" title="Table of Contents" href="toc.xhtml"/>')
            self.buff.append('</guide>')

        self.buff.append('</package>')

        self.write_buff(self.temp_content_dir, 'content.opf')

    def get_buff(self):
        return ''.join(self.buff)
