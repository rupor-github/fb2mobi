# -*- coding: utf-8 -*-

from lxml import etree
from lxml.builder import E
from importlib import import_module

import os, codecs


class ConverterConfig:
    def __init__(self, config_file):
        self.config_file = config_file

        self.debug = False
        self.log_file = None
        self.original_log_file = None
        self.log_level = 'Info'
        self.output_format = 'epub'
        self.kindle_compression_level = 1
        self.no_dropcaps_symbols = '\'"-.…0123456789‒–—«»'
        self.transliterate = False
        self.transliterate_author_and_title = False
        self.default_profile = 'default'

        self.input_dir = None
        self.output_dir = None
        self.save_structure = None
        self.delete_source_file = None

        self.log = None

        self.profiles = {}
        self.profiles['default'] = {}
        self.profiles['default']['name'] = 'default'
        self.profiles['default']['description'] = 'Default profile'
        self.profiles['default']['outputFormat'] = None
        self.profiles['default']['transliterate'] = None
        self.profiles['default']['transliterateAuthorAndTitle'] = None
        self.profiles['default']['hyphens'] = True
        self.profiles['default']['dropcaps'] = 'None'
        self.profiles['default']['tocMaxLevel'] = 1000
        self.profiles['default']['tocBeforeBody'] = False
        self.profiles['default']['flatTOC'] = True
        self.profiles['default']['originalcss'] = 'default.css'
        self.profiles['default']['css'] = 'default.css'
        self.profiles['default']['parse_css'] = True
        self.profiles['default']['chapterOnNewPage'] = True
        self.profiles['default']['authorFormat'] = '#l #f #m'
        self.profiles['default']['bookTitleFormat'] = '(#abbrseries #number) #title'
        self.profiles['default']['annotationTitle'] = 'Annotation'
        self.profiles['default']['tocTitle'] = 'Content'
        self.profiles['default']['notesMode'] = 'default'
        self.profiles['default']['notesBodies'] = 'notes'
        self.profiles['default']['vignettes'] = {}
        self.profiles['default']['vignettes_save'] = {}
        self.profiles['default']['generateTOCPage'] = True
        self.profiles['default']['generateAnnotationPage'] = True
        self.profiles['default']['generateOPFGuide'] = True
        self.profiles['default']['kindleRemovePersonalLabel'] = True

        self.current_profile = {}
        self.mhl = False
        self.recursive = False

        if not os.path.exists(self.config_file):
            # Если файл настроек отсутствует, созданим файл по-умолчанию
            self.write()
            # Создадим умолчательный css
            default_css = import_module('default_css')
            with codecs.open(os.path.join(os.path.split(self.config_file)[0], 'default.css'), "w", 'utf-8') as f:
                f.write(default_css.default_css)
                f.close()

        self._load()

    def _load(self):
        config = etree.parse(self.config_file)
        for e in config.getroot():
            if e.tag == 'debug':
                self.debug = e.text.lower() == 'true'

            elif e.tag == 'logFile':
                if e.text:
                    self.original_log_file = e.text
                    self.log_file = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(self.config_file)), e.text))

            elif e.tag == 'logLevel':
                self.log_level = e.text

            elif e.tag == 'outputFormat':
                self.output_format = e.text

            elif e.tag == 'kindleCompressionLevel':
                self.kindle_compression_level = int(e.text)

            elif e.tag == 'noDropcapsSymbols':
                self.no_dropcaps_symbols = e.text

            elif e.tag == 'transliterate':
                self.transliterate = e.text.lower() == 'true'

            elif e.tag == 'defaultProfile':
                self.default_profile = e.text

            elif e.tag == 'profiles':
                self.profiles = {}
                for prof in e:
                    prof_name = prof.attrib['name']
                    self.profiles[prof_name] = {}
                    self.profiles[prof_name]['name'] = prof.attrib['name']
                    self.profiles[prof_name]['description'] = prof.attrib['description']
                    self.profiles[prof_name]['vignettes'] = {}

                    self.profiles[prof_name]['generateTOCPage'] = True
                    self.profiles[prof_name]['generateAnnotationPage'] = True
                    self.profiles[prof_name]['generateOPFGuide'] = True
                    self.profiles[prof_name]['flatTOC'] = True
                    self.profiles[prof_name]['kindleRemovePersonalLabel'] = True

                    for p in prof:
                        if p.tag == 'hyphens':
                            self.profiles[prof_name]['hyphens'] = p.text.lower() == 'true'

                        elif p.tag == 'dropcaps':
                            self.profiles[prof_name]['dropcaps'] = p.text

                        elif p.tag == 'outputFormat':
                            self.profiles[prof_name]['outputFormat'] = p.text

                        elif p.tag == 'transliterate':
                            self.profiles[prof_name]['transliterate'] = p.text.lower() == 'true'

                        elif p.tag == 'transliterateAuthorAndTitle':
                            self.profiles[prof_name]['transliterateAuthorAndTitle'] = p.text.lower() == 'true'

                        elif p.tag == 'tocMaxLevel':
                            self.profiles[prof_name]['tocMaxLevel'] = int(p.text)

                        elif p.tag == 'generateTOCPage':
                            self.profiles[prof_name]['generateTOCPage'] = p.text.lower() == 'true'

                        elif p.tag == 'flatTOC':
                            self.profiles[prof_name]['flatTOC'] = p.text.lower() == 'true'

                        elif p.tag == 'kindleRemovePersonalLabel':
                            self.profiles[prof_name]['kindleRemovePersonalLabel'] = p.text.lower() == 'true'

                        elif p.tag == 'generateAnnotationPage':
                            self.profiles[prof_name]['generateAnnotationPage'] = p.text.lower() == 'true'

                        elif p.tag == 'generateOPFGuide':
                            self.profiles[prof_name]['generateOPFGuide'] = p.text.lower() == 'true'

                        elif p.tag == 'tocBeforeBody':
                            self.profiles[prof_name]['tocBeforeBody'] = p.text.lower() == 'true'

                        elif p.tag == 'css':
                            self.profiles[prof_name]['originalcss'] = p.text
                            self.profiles[prof_name]['css'] = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(self.config_file)), p.text))
                            if 'parse' in p.attrib:
                                self.profiles[prof_name]['parse_css'] = p.attrib['parse'].lower() == 'true'
                            else:
                                self.profiles[prof_name]['parse_css'] = True

                        elif p.tag == 'xslt':
                            self.profiles[prof_name]['xslt'] = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(self.config_file)), p.text))

                        elif p.tag == 'chapterOnNewPage':
                            self.profiles[prof_name]['chapterOnNewPage'] = p.text.lower() == 'true'

                        elif p.tag == 'authorFormat':
                            self.profiles[prof_name]['authorFormat'] = p.text

                        elif p.tag == 'bookTitleFormat':
                            self.profiles[prof_name]['bookTitleFormat'] = p.text

                        elif p.tag == 'annotationTitle':
                            self.profiles[prof_name]['annotationTitle'] = p.text

                        elif p.tag == 'tocTitle':
                            self.profiles[prof_name]['tocTitle'] = p.text

                        elif p.tag == 'notesMode':
                            self.profiles[prof_name]['notesMode'] = p.text

                        elif p.tag == 'notesBodies':
                            self.profiles[prof_name]['notesBodies'] = p.text

                        elif p.tag == 'vignettes':
                            self.profiles[prof_name]['vignettes'] = {}
                            self.profiles[prof_name]['vignettes_save'] = {}

                            for vignettes in p:
                                vignettes_level = vignettes.attrib['level']
                                vign_arr = {}
                                vign_arr_save = {}

                                for v in vignettes:
                                    vign_arr[v.tag] = None if v.text.lower() == 'none' else os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(self.config_file)), v.text))
                                    vign_arr_save[v.tag] = None if v.text.lower() == 'none' else v.text

                                self.profiles[prof_name]['vignettes'][vignettes_level] = vign_arr
                                self.profiles[prof_name]['vignettes_save'][vignettes_level] = vign_arr_save

    def _getVignette(self, vignette_arr):
        for v in vignette_arr:
            print(v)

    def _getVignettes(self, profile):
        result = []

        try:
            for v in self.profiles[profile]['vignettes_save']:
                result.append(E('vignette',
                                E('beforeTitle', self.profiles[profile]['vignettes_save'][v]['beforeTitle'] if self.profiles[profile]['vignettes_save'][v]['beforeTitle'] else 'None'),
                                E('afterTitle', self.profiles[profile]['vignettes_save'][v]['afterTitle'] if self.profiles[profile]['vignettes_save'][v]['afterTitle'] else 'None'),
                                E('chapterEnd', self.profiles[profile]['vignettes_save'][v]['chapterEnd'] if self.profiles[profile]['vignettes_save'][v]['chapterEnd'] else 'None'),
                                level=v
                                ))

        except:
            pass

        return result

    def _getProfiles(self):
        result = []
        for p in self.profiles:
            result.append(E('profile',
                            E('hyphens', str(self.profiles[p]['hyphens'])),
                            E('dropcaps', str(self.profiles[p]['dropcaps'])),
                            E('tocMaxLevel', str(self.profiles[p]['tocMaxLevel'])),
                            E('tocBeforeBody', str(self.profiles[p]['tocBeforeBody'])),
                            E('flatTOC', str(self.profiles[p]['flatTOC'])),
                            E('css', self.profiles[p]['originalcss'], parse=str(self.profiles[p]['parse_css'])),
                            E('chapterOnNewPage', str(self.profiles[p]['chapterOnNewPage'])),
                            E('authorFormat', self.profiles[p]['authorFormat']),
                            E('bookTitleFormat', self.profiles[p]['bookTitleFormat']),
                            E('annotationTitle', self.profiles[p]['annotationTitle']),
                            E('tocTitle', self.profiles[p]['tocTitle']),
                            E('notesMode', self.profiles[p]['notesMode']),
                            E('notesBodies', self.profiles[p]['notesBodies']),
                            E('generateTOCPage', str(self.profiles[p]['generateTOCPage'])),
                            E('generateAnnotationPage', str(self.profiles[p]['generateAnnotationPage'])),
                            E('generateOPFGuide', str(self.profiles[p]['generateOPFGuide'])),
                            E('kindleRemovePersonalLabel', str(self.profiles[p]['kindleRemovePersonalLabel'])),
                            E('vignettes',
                              *self._getVignettes(p)
                              ),
                            name=p, description=self.profiles[p]['description']))

        return result

    def setCurrentProfile(self, profile_name):
        try:
            self.current_profile = self.profiles[profile_name]
        except:
            self.log.warning('Unable to locate profile "{0}". Using default one.'.format(profile_name))
            self.current_profile = self.profiles[self.default_profile]

        if 'outputFormat' in self.current_profile:
            self.output_format = self.current_profile['outputFormat']

        if 'transliterate' in self.current_profile:
            self.transliterate = self.current_profile['transliterate']

        if 'transliterateAuthorAndTitle' in self.current_profile:
            self.transliterate_author_and_title = self.current_profile['transliterateAuthorAndTitle']

    def write(self):
        config = E('settings',
                   E('debug', str(self.debug)),
                   E('logFile', self.original_log_file) if self.original_log_file else E('logFile'),
                   E('logLevel', self.log_level),
                   E('outputFormat', self.output_format),
                   E('kindleCompressionLevel', str(self.kindle_compression_level)),
                   E('noDropcapsSymbols', self.no_dropcaps_symbols),
                   E('transliterate', str(self.transliterate)),
                   E('defaultProfile', self.default_profile),
                   E('profiles',
                     *self._getProfiles()
                     ),
                   )

        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        with codecs.open(self.config_file, "w", 'utf-8') as f:
            f.write(str(etree.tostring(config, encoding="utf-8", pretty_print=True, xml_declaration=True), 'utf-8'))
            f.close()
