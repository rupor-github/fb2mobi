#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from lxml import etree
from lxml.builder import ElementMaker
import os
import codecs

class GuiConfig():
    def __init__(self, config_file):
        self.config_file = os.path.normpath(os.path.abspath(config_file))

        self.converterConfig = {}
        self.currentProfile = None
        self.currentFormat = None
        self.outputFolder = None
        self.lastUsedTargetPath = None
        self.hyphens = None
        self.kindlePath = None
        self.kindleSyncCovers = False
        self.kindleDocsSubfolder = None
        self.lastUsedPath = None
        self.GoogleMail = None
        self.GooglePassword = None
        self.KindleMail = None
        self.embedFontFamily = None
        self.fontDb = None
        self.writeLog = True
        self.logLevel = 'DEBUG'
        self.clearLogAfterExit = False
        self.bookInfoVisible = True
        self.bookInfoSplitterState = None

        self.columns = {}
        self.authorPattern = '#l, #f'
        self.filenamePattern = '#author. #title{ (пер. #translator)}'

        self.geometry = {}
        self.geometry['x'] = None
        self.geometry['y'] = None
        self.geometry['width'] = None
        self.geometry['height'] = None

        if not os.path.exists(self.config_file):
            self.write()

        self.load()


    def load(self):
        config = etree.parse(self.config_file)
        for e in config.getroot():
            if e.tag == 'currentProfile':
                self.currentProfile = e.text

            elif e.tag == 'currentFormat':
                self.currentFormat = e.text

            elif e.tag == 'outputFolder':
                self.outputFolder = e.text

            elif e.tag == 'lastUsedTargetPath':
                self.lastUsedTargetPath = e.text

            elif e.tag == 'embedFontFamily':
                self.embedFontFamily = e.text

            elif e.tag == 'hyphens':
                self.hyphens = e.text

            elif e.tag == 'lastUsedPath':
                self.lastUsedPath = e.text

            elif e.tag == 'kindlePath':
                self.kindlePath = e.text

            elif e.tag == 'kindleDocsSubfolder':
                self.kindleDocsSubfolder = e.text

            elif e.tag == 'writeLog':
                self.writeLog = e.text.lower() == 'true'

            elif e.tag == 'bookInfoVisible':
                self.bookInfoVisible = e.text.lower() == 'true'

            elif e.tag == 'bookInfoSplitterState':
                self.bookInfoSplitterState = e.text

            elif e.tag == 'clearLogAfterExit':
                self.clearLogAfterExit = e.text.lower() == 'true'

            elif e.tag == 'GoogleMail':
                self.GoogleMail = e.text

            elif e.tag == 'GooglePassword':
                self.GooglePassword = e.text

            elif e.tag == 'KindleMail':
                self.KindleMail = e.text

            elif e.tag == 'logLevel':
                self.logLevel = e.text    

            elif e.tag == 'kindleSyncCovers':
                self.kindleSyncCovers = e.text.lower() == 'true'

            elif e.tag == 'columns':
                for c in e:
                    if c.tag == 'column':
                        self.columns[c.attrib['number']] = int(c.text) if c.text else 100
                    
            elif e.tag == 'geometry':
                for g in e:
                    self.geometry[g.tag] = int(g.text) if g.text else None

            elif e.tag == 'authorPattern':
                self.authorPattern = e.text

            elif e.tag == 'filenamePattern':
                self.filenamePattern = e.text


    def write(self):
        def number(v):
            return {'number': str(v)}

        E = ElementMaker()

        config = E.settings(
                    E.currentProfile(self.currentProfile) if self.currentProfile else E.currentProfile(),
                    E.currentFormat(self.currentFormat) if self.currentFormat else E.currentFormat(),
                    E.embedFontFamily(self.embedFontFamily) if self.embedFontFamily else E.embedFontFamily(),
                    E.hyphens(self.hyphens) if self.hyphens else E.hyphens(),
                    E.outputFolder(self.outputFolder) if self.outputFolder else E.outputFolder(),
                    E.lastUsedTargetPath(self.lastUsedTargetPath) if self.lastUsedTargetPath else E.lastUsedTargetPath(),
                    E.lastUsedPath(self.lastUsedPath) if self.lastUsedPath else E.lastUsedPath(),
                    E.writeLog(str(self.writeLog)),
                    E.clearLogAfterExit(str(self.clearLogAfterExit)),
                    E.logLevel(self.logLevel) if self.logLevel else E.logLevel(),
                    E.kindlePath(self.kindlePath) if self.kindlePath else E.kindlePath(),
                    E.kindleSyncCovers(str(self.kindleSyncCovers)),
                    E.kindleDocsSubfolder(self.kindleDocsSubfolder) if self.kindleDocsSubfolder else E.kindleDocsSubfolder(),
                    E.GoogleMail(self.GoogleMail) if self.GoogleMail else E.GoogleMail(),
                    E.GooglePassword(self.GooglePassword) if self.GooglePassword else E.GooglePassword(),
                    E.KindleMail(self.KindleMail) if self.KindleMail else E.KindleMail(),
                    E.bookInfoVisible(str(self.bookInfoVisible)),
                    E.bookInfoSplitterState(self.bookInfoSplitterState) if self.bookInfoSplitterState else E.bookInfoSplitterState(),
                    E.authorPattern(self.authorPattern if self.authorPattern else E.authorPattern()),
                    E.filenamePattern(self.filenamePattern if self.filenamePattern else E.filenamePattern()),
                    E.columns(
                        *[E.column(str(self.columns[col]), number(col)) for col in self.columns.keys()]
                    ),
                    E.geometry(
                        E.x(str(self.geometry['x'])) if self.geometry['x'] else E.x(),
                        E.y(str(self.geometry['y'])) if self.geometry['y'] else E.y(),
                        E.width(str(self.geometry['width'])) if self.geometry['width'] else E.width(),
                        E.height(str(self.geometry['height'])) if self.geometry['height'] else E.height()
                    )

        )
        config_dir = os.path.dirname(self.config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        with codecs.open(self.config_file, "wb") as f:
            f.write(etree.tostring(config, encoding="utf-8", pretty_print=True, xml_declaration=True))
            f.close()


if __name__ == '__main__':
    gui_config = GuiConfig('fb2mobi-gui.config')
    gui_config.write()

