#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import cssutils
import codecs
import time
import subprocess
import webbrowser
import logging
import shutil

from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTreeWidgetItem, QMessageBox, QDialog, QWidget, 
                            QLabel, QAbstractItemView, QSizePolicy, QAction, QMenu)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QFontMetrics
from PyQt5.QtCore import (QObject, QThread, pyqtSignal, QEvent, Qt, QTranslator, QLocale, QCoreApplication, QTimer, 
                          QSize, QRectF, QByteArray, QBuffer, QPoint)

from ui.MainWindow import Ui_MainWindow
from ui.AboutDialog import Ui_AboutDialog
from ui.SettingsDialog import Ui_SettingsDialog

from ui.gui_config import GuiConfig
import ui.images_rc
import ui.ui_version
from ui.fb2meta import Fb2Meta
from ui.fontdb import FontDb

from modules.config import ConverterConfig
import modules.default_css
import fb2mobi
import synccovers
import version


TREE_LIST_CSS_ACTIVE = "selection-color: white; selection-background-color: #386CDA; alternate-background-color: #F3F6FA;"
TREE_LIST_CSS_UNACTIVE = "selection-color: black; selection-background-color: #D4D4D4; alternate-background-color: #F3F6FA;"

SUPPORT_URL = u'http://www.the-ebook.org/forum/viewtopic.php?t=30380'

_translate = QCoreApplication.translate


class CopyThread(QThread):
    copyBegin = pyqtSignal(object)
    copyDone = pyqtSignal()
    copyAllDone = pyqtSignal()

    def __init__(self, files, dest_path, synccovers):
        super(CopyThread, self).__init__()
        self.files = files
        self.dest_path = dest_path
        self.thumbnail_path = ''
        self.synccovers = synccovers

        # Определим и проверим путь до иниатюр обложек на Kindle
        if self.dest_path:
            self.thumbnail_path = os.path.join(os.path.dirname(os.path.abspath(dest_path)), 'system', 'thumbnails')
            if not os.path.isdir(self.thumbnail_path):
                self.thumbnail_path = ''


    def run(self):
        for file in self.files:
            self.copyBegin.emit(file)
            try:
                if os.path.exists(self.dest_path):                    
                    shutil.copy2(file, self.dest_path)
                    src_sdr_dir = '{0}.{1}'.format(os.path.splitext(file)[0], 'sdr')
                    dest_sdr_dir = os.path.join(self.dest_path, os.path.split(src_sdr_dir)[1])

                    # Обработка apnx-файла, он находится в каталоге <имя файла книги>.sdr
                    if os.path.isdir(src_sdr_dir):
                        if os.path.isdir(dest_sdr_dir):
                           shutil.rmtree(dest_sdr_dir)

                        shutil.copytree(src_sdr_dir, dest_sdr_dir)

                    # Создадим миниатюру обложки, если оперделили путь и установлен признак
                    if self.thumbnail_path and self.synccovers:
                        dest_file = os.path.join(self.dest_path, os.path.split(file)[1])
                        if os.path.exists(dest_file):
                            synccovers.process_file(dest_file, self.thumbnail_path, 330, 470, False, False)
            except:
                pass
            self.copyDone.emit()

        self.copyAllDone.emit()


class ConvertThread(QThread):
    convertBegin = pyqtSignal(object)
    convertDone = pyqtSignal(object, bool, object)
    convertAllDone = pyqtSignal()

    def __init__(self, files, gui_config):
        super(ConvertThread, self).__init__()
        self.files = files
        self.config = gui_config.converterConfig
        self.cancel = False

        self.config.setCurrentProfile(gui_config.currentProfile)
        self.config.output_format = gui_config.currentFormat
        if gui_config.embedFontFamily:
            css_file = os.path.join(os.path.dirname(gui_config.config_file), 'profiles', '_font.css')
            if os.path.exists(css_file):
                self.config.current_profile['css'] = css_file

        if not gui_config.convertToSourceDirectory:
            self.config.output_dir = gui_config.outputFolder
        else:
            self.config.output_dir = None

        if gui_config.hyphens.lower() == 'yes':
            self.config.current_profile['hyphens']= True
        elif gui_config.hyphens.lower()  == 'no':
            self.config.current_profile['hyphens'] = False


    def run(self):
        dest_file = None

        for file in self.files:
            result = True
            dest_file = None
            if not self.cancel:
                self.convertBegin.emit(file)
                dest_file = self.getDestFileName(file)
                # Перед конвертацией удалим старый файл
                if os.path.exists(dest_file):
                    os.remove(dest_file)

                self.config.log.info(' ')
                fb2mobi.process_file(self.config, file, None)

                if not os.path.exists(dest_file):
                    dest_file = None
                    result = False
                else:
                    dest_file = self.getDestFileName(file)

                self.convertDone.emit(file, result, dest_file)
            else:
                break

        self.convertAllDone.emit()


    def getDestFileName(self, file):
        if self.config.output_dir is None:
            output_dir = os.path.abspath(os.path.split(file)[0])
        else:
            output_dir = os.path.abspath(self.config.output_dir)
        file_name = os.path.join(output_dir, os.path.splitext(os.path.split(file)[1])[0])
        if os.path.splitext(file_name)[1].lower() == '.fb2':
            file_name = os.path.splitext(file_name)[0]

        return '{0}.{1}'.format(file_name, self.config.output_format)


    def stop(self):
        self.cancel = True


class SettingsDialog(QDialog, Ui_SettingsDialog):
    def __init__(self, parent, config):
        super(SettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self.config = config

        for p in self.config.converterConfig.profiles:
            self.comboProfile.addItem('{0} ({1})'.format(p, self.config.converterConfig.profiles[p]['description']), p)

        for f in ['mobi', 'azw3', 'epub']:
            self.comboFormat.addItem(f, f)

        self.comboProfile.setCurrentIndex(self.comboProfile.findData(self.config.currentProfile))
        self.comboFormat.setCurrentIndex(self.comboFormat.findData(self.config.currentFormat))        
        self.lineDestPath.setText(self.config.outputFolder)
        self.checkConvertToSrc.setChecked(self.config.convertToSourceDirectory)
        self.checkWriteLog.setChecked(self.config.writeLog)
        self.checkClearLogAfterExit.setChecked(self.config.clearLogAfterExit)

        if self.config.hyphens.lower() == 'yes':
            self.radioHypYes.setChecked(True)
            self.radioHypNo.setChecked(False)
            self.radioHypProfile.setChecked(False)

        elif self.config.hyphens.lower() == 'no':
            self.radioHypYes.setChecked(False)
            self.radioHypNo.setChecked(True)
            self.radioHypProfile.setChecked(False)

        elif self.config.hyphens.lower() == 'profile':
            self.radioHypYes.setChecked(False)
            self.radioHypNo.setChecked(False)
            self.radioHypProfile.setChecked(True)

        # Строим выбор шрифта
        # для начала обновим список доступных шрифтов
        self.config.fontDb.update_db()
        self.comboFont.addItem(_translate('fb2mobi-gui', 'None'), 'None')
        for font in self.config.fontDb.families:
            self.comboFont.addItem(font, font)

        if self.config.embedFontFamily is None:
            self.comboFont.setCurrentIndex(self.comboFont.findData('None'))
        else:
            self.comboFont.setCurrentIndex(self.comboFont.findData(self.config.embedFontFamily))

        self.comboLogLevel.setCurrentIndex(self.comboLogLevel.findText(self.config.logLevel))

        self.lineKindlePath.setText(self.config.kindlePath)
        self.checkCopyAfterConvert.setChecked(self.config.kindleCopyToDevice)
        self.checkSyncCovers.setChecked(self.config.kindleSyncCovers)
        self.enableCheckSyncCovers(self.config.kindleCopyToDevice)


    def selectDestPath(self):
        self.lineDestPath.setText(self.selectPath(self.lineDestPath.text()))

    def selectKindlePath(self):
        self.lineKindlePath.setText(self.selectPath(self.lineKindlePath.text()))

    def selectPath(self, path):
        if not path:
            path = os.path.expanduser('~')

        dlgPath = QFileDialog(self, _translate('fb2mobi-gui', 'Select folder'), path)
        dlgPath.setFileMode(QFileDialog.Directory)
        dlgPath.setOption(QFileDialog.ShowDirsOnly, True)

        if dlgPath.exec_():
            for d in dlgPath.selectedFiles():
                path = os.path.normpath(d)

        return path


    def checkConvertToSrcClicked(self, state):
        enabled = False
        if state == 0:
            enabled = True

        self.lineDestPath.setEnabled(enabled)
        self.btnSelectDestPath.setEnabled(enabled)

    def checkCopyAfterConvertClicked(self, state):
        checked = False
        if state == 2:
            checked = True

        self.enableCheckSyncCovers(checked)

    def enableCheckSyncCovers(self, enabled):
        if enabled:
            self.checkSyncCovers.setEnabled(True)
        else:
            self.checkSyncCovers.setEnabled(False)
            self.checkSyncCovers.setChecked(False)


    def closeAccept(self):
        self.config.currentProfile = self.comboProfile.currentData()
        self.config.currentFormat = self.comboFormat.currentData()
        self.config.outputFolder = os.path.normpath(self.lineDestPath.text())
        self.config.convertToSourceDirectory = self.checkConvertToSrc.isChecked()
        if self.radioHypYes.isChecked():
           self.config.hyphens = 'Yes'
        elif self.radioHypNo.isChecked():
            self.config.hyphens = 'No'
        else:
            self.config.hyphens = 'Profile'

        if self.lineKindlePath.text():
            self.config.kindlePath = os.path.normpath(self.lineKindlePath.text())
        self.config.kindleCopyToDevice = self.checkCopyAfterConvert.isChecked()
        self.config.kindleSyncCovers = self.checkSyncCovers.isChecked()
        self.config.writeLog = self.checkWriteLog.isChecked()
        self.config.clearLogAfterExit = self.checkClearLogAfterExit.isChecked()
        self.config.logLevel = self.comboLogLevel.currentText()

        if self.comboFont.currentData() == 'None':
            self.config.embedFontFamily = None
        else:
            self.config.embedFontFamily = self.comboFont.currentData()


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        image  = QPixmap(':/Images/icon128.png')
        self.labelImage.setPixmap(image)
        self.labelVersion.setText(version.VERSION)
        self.labelUIVersion.setText(ui.ui_version.VERSION)

        self.setFixedSize(self.size())
       

class MainAppWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainAppWindow, self).__init__()
        self.setupUi(self)

        self.savedPath = ''
        self.convertRun = False
        self.convertedCount = 0
        self.copyCount = 0
        self.convertedFiles = []

        # self.setAcceptDrops(True)
        self.treeFileList.setAcceptDrops(True)
        self.treeFileList.installEventFilter(self)

        self.imgBookCover.setAcceptDrops(True)
        self.imgBookCover.installEventFilter(self)

        self.book_cover = None

        self.config_file = None
        self.log_file = None
        self.log = None
        self.config = {}

        self.convert_worker = None
        self.copy_worker = None
        self.is_convert_cancel = False

        self.rootFileList = self.treeFileList.invisibleRootItem()
        self.iconWhite = QIcon(':/Images/bullet_white.png')
        self.iconRed = QIcon(':/Images/bullet_red.png')
        self.iconGreen = QIcon(':/Images/bullet_green.png')
        self.iconGo = QIcon(':/Images/bullet_go.png')

        self.pixmapConnected = QPixmap(':/Images/bullet_green.png')
        self.pixmapNotConnected = QPixmap(':/Images/bullet_red.png')

        config_file_name = "fb2mobi.config"
        log_file_name = "fb2mobi.log"
        gui_config_file = 'fb2mobi-gui.config'

        # Определяем, где находится файл конфигурации. 
        # Если есть в домашнем каталоге пользователя (для windows ~/2bmobi, для остальных ~/.fb2mobi),
        # то используется он.
        # Иначе - из каталога программы
        application_path = os.path.normpath(fb2mobi.get_executable_path())
        config_path = None
        if sys.platform == 'win32':
            config_path = os.path.normpath(os.path.join(os.path.expanduser('~'), 'fb2mobi'))
        else:
            config_path = os.path.normpath(os.path.join(os.path.expanduser('~'), '.fb2mobi'))

        if not os.path.exists(os.path.join(config_path, config_file_name)):
            config_path = application_path

        self.config_file = os.path.normpath(os.path.join(config_path, config_file_name))
        self.log_file = os.path.normpath(os.path.join(config_path, log_file_name))
        self.gui_config_file = os.path.normpath(os.path.join(config_path, gui_config_file))
        
        self.gui_config = GuiConfig(self.gui_config_file)
        self.gui_config.converterConfig = ConverterConfig(self.config_file)

        self.log = logging.getLogger('fb2mobi')
        self.log.setLevel(self.gui_config.logLevel)

        self.log_stream_handler = logging.StreamHandler()
        self.log_stream_handler.setLevel(fb2mobi.get_log_level(self.gui_config.converterConfig.console_level))
        self.log_stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.log.addHandler(self.log_stream_handler)

        self.log_file_handler = logging.FileHandler(filename=self.log_file, mode='a', encoding='utf-8')
        self.log_file_handler.setLevel(fb2mobi.get_log_level(self.gui_config.converterConfig.log_level))
        self.log_file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))        
        if self.gui_config.writeLog:            
            self.log.addHandler(self.log_file_handler)

        self.gui_config.converterConfig.log = self.log
        # Строим базу доступных шрифтов
        self.font_path = os.path.normpath(os.path.join(config_path, 'profiles/fonts'))
        if os.path.exists(self.font_path):
            self.gui_config.fontDb = FontDb(self.font_path)

        if not self.gui_config.outputFolder:
            self.gui_config.outputFolder = os.path.abspath(os.path.expanduser("~/Desktop"))

        if not self.gui_config.currentFormat:
            self.gui_config.currentFormat = 'mobi'

        if not self.gui_config.currentProfile:
            for p in self.gui_config.converterConfig.profiles:
                self.gui_config.currentProfile = p
                break

        if not self.gui_config.convertToSourceDirectory:
            self.gui_config.convertToSourceDirectory = False

        if not self.gui_config.hyphens:
            self.gui_config.hyphens = 'profile'

        if self.gui_config.geometry['x'] and self.gui_config.geometry['y']:
            self.move(self.gui_config.geometry['x'], self.gui_config.geometry['y'])
            self.resize(self.gui_config.geometry['width'], self.gui_config.geometry['height'])

        # self.progressBar.setRange(0, 100)
        # self.progressBar.setValue(0)
        # self.progressBar.setVisible(False)        

        self.setWindowIcon(QIcon(':/Images/icon32.png'))
        self.treeFileList.installEventFilter(self)
        self.bookInfoSplitter.installEventFilter(self)

        self.labelKindleStatus = QLabel()
        self.labelKindleStatusIcon = QLabel()
        self.labelStatus = QLabel()

        self.imgBookCover.setContextMenuPolicy(Qt.CustomContextMenu)
        self.imgBookCover.customContextMenuRequested[QPoint].connect(self.contextCoverMenu)

        self.toolBar.setIconSize(QSize(26, 26))

        self.toolAdd.setIcon(QIcon(':/toolbar/add.png'))
        self.toolStart.setIcon(QIcon(':/toolbar/start.png'))
        self.toolSettings.setIcon(QIcon(':/toolbar/settings.png'))
        self.toolInfo.setIcon(QIcon(':/toolbar/info_on.png'))        

        # Немного подстраиваем стили UI для более нативного отображения
        if sys.platform == 'darwin':
            # Для Mac OS X
            font = self.labelKindleStatus.font()
            font.setPointSize(11)
            self.labelKindleStatus.setFont(font)
            self.labelStatus.setFont(font)
            self.treeFileList.setFont(font)
            self.labelAuthor.setFont(font)
            self.labelBookTitle.setFont(font)
            self.labelSeries.setFont(font)
            self.labelSeriesNumber.setFont(font)
            self.labelBookLanguage.setFont(font)
            self.treeFileList.setAttribute(Qt.WA_MacShowFocusRect, 0)
            self.treeFileList.setStyleSheet(TREE_LIST_CSS_ACTIVE)
            self.labelStatus.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

            self.toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.setUnifiedTitleAndToolBarOnMac(True)
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.toolBar.addWidget(spacer)
            self.toolBar.addAction(self.toolAdd)
            self.toolBar.addAction(self.toolStart)
            self.toolBar.addAction(self.toolSettings)
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.toolBar.addWidget(spacer)            
            self.toolBar.addAction(self.toolInfo)
        else:
            # Для Windows, Linux
            self.toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.toolBar.setStyleSheet('QToolButton { padding: 4px; }')

            spacer = QWidget()

            self.toolBar.addAction(self.toolAdd)
            self.toolBar.addAction(self.toolStart)
            self.toolBar.addAction(self.toolSettings)
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.toolBar.addWidget(spacer)            
            self.toolBar.addAction(self.toolInfo)
            self.toolInfo.setPriority(QAction.LowPriority)

        self.setBookInfoPanelVisible()
        self.scrollBookInfo.setVisible(self.gui_config.bookInfoVisible)
        if self.gui_config.bookInfoSplitterState:
            splitter_sizes = self.gui_config.bookInfoSplitterState.split(',')
            self.bookInfoSplitter.setSizes([int(i) for i in splitter_sizes])

        self.statusBar().addWidget(self.labelStatus, 1) 
        self.statusBar().addWidget(self.labelKindleStatusIcon)        
        self.statusBar().addWidget(self.labelKindleStatus)

        if self.gui_config.columns['0']:
            self.treeFileList.setColumnWidth(0, self.gui_config.columns['0']) 
            self.treeFileList.setColumnWidth(1, self.gui_config.columns['1']) 
            self.treeFileList.setColumnWidth(2, self.gui_config.columns['2']) 


        self.timerKindleStatus = QTimer()
        self.timerKindleStatus.timeout.connect(self.checkKindleStatus)
        self.timerKindleStatus.start(1500)


    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            if sys.platform == 'darwin':
               self.treeFileList.setStyleSheet(TREE_LIST_CSS_ACTIVE) 
        elif event.type() == QEvent.WindowDeactivate:
            if sys.platform == 'darwin':
               self.treeFileList.setStyleSheet(TREE_LIST_CSS_UNACTIVE) 

        return super(MainAppWindow, self).event(event)


    def checkKindleStatus(self):
        if self.gui_config.kindleCopyToDevice:
            if os.path.isdir(self.gui_config.kindlePath):
                self.labelKindleStatusIcon.setPixmap(self.pixmapConnected)
                self.labelKindleStatus.setText(_translate('fb2mobi-gui', 'Device connected'))
            else:
                self.labelKindleStatusIcon.setPixmap(self.pixmapNotConnected)
                self.labelKindleStatus.setText(_translate('fb2mobi-gui', 'Device not connected'))

        else:
            self.labelKindleStatus.setText('')
            self.labelKindleStatusIcon.clear()

    def setBookInfoPanelVisible(self):
        if self.gui_config.bookInfoVisible:
            self.toolInfo.setIcon(QIcon(':/toolbar/info_on.png'))
        else:
            self.toolInfo.setIcon(QIcon(':/toolbar/info_off.png'))

        self.scrollBookInfo.setVisible(self.gui_config.bookInfoVisible)


    def switchInfoPanel(self):
        self.gui_config.bookInfoVisible = not self.gui_config.bookInfoVisible
        self.setBookInfoPanelVisible()


    def eventFilter(self, source, event):
        if source is self.treeFileList:
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    event.accept()
                    return True
                else:
                    event.ignore()

            elif event.type() == QEvent.Drop:
                file_list = [u.toLocalFile() for u in event.mimeData().urls()]        
                self.addFiles(file_list)
                event.accept()
                return True

        elif source is self.imgBookCover:
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    if len(self.treeFileList.selectedItems()) == 1:
                        event.accept()
                        return True
                    else:
                        event.ignore()
                else:
                    event.ignore()

            elif event.type() == QEvent.Drop:
                file_list = [u.toLocalFile() for u in event.mimeData().urls()] 
                for f in file_list:
                    self.loadNewCoverFormFile(f)                    
                    break
                event.accept()
                return True

        elif source is self.bookInfoSplitter:
            if event.type() == QEvent.Paint:
                splitter_sizes = self.bookInfoSplitter.sizes()
                if splitter_sizes[1] > 0:
                    self.gui_config.bookInfoSplitterState = ', '.join(str(e) for e in splitter_sizes)

        if event.type() == QEvent.KeyPress:
            if (event.key() == Qt.Key_Delete or (event.key() == Qt.Key_Backspace 
                and event.modifiers() == Qt.ControlModifier)):
                self.deleteRecAction()
                return True
                
        return QWidget.eventFilter(self, source, event)


    def contextCoverMenu(self, point):
        if len(self.treeFileList.selectedItems()) == 1:
            menu = QMenu()

            actionLoad = menu.addAction(_translate('fb2mobi-gui', 'Load from file...'))
            actionSave = menu.addAction(_translate('fb2mobi-gui', 'Save to file...'))
            actionClear = menu.addAction(_translate('fb2mobi-gui', 'Clear'))

            action = menu.exec_(self.imgBookCover.mapToGlobal(point))

            if action == actionLoad:
                fileDialog = QFileDialog(self, _translate('fb2mobi-gui', 'Select book cover'))
                fileDialog.setFileMode(QFileDialog.ExistingFile)
                fileDialog.setNameFilters([_translate('fb2mobi-gui', 'Image files (*.png *.jpg *.bmp)')])

                if fileDialog.exec_():
                    file_list = fileDialog.selectedFiles()
                    self.loadNewCoverFormFile(file_list[0])
            elif action == actionSave:
                fileDialog = QFileDialog(self, _translate('fb2mobi-gui', 'Save cover as'))
                fileDialog.setAcceptMode(QFileDialog.AcceptSave)
                fileDialog.setFileMode(QFileDialog.AnyFile)
                fileDialog.setNameFilters([_translate('fb2mobi-gui', 'Image files (*.png *.jpg *.bmp)')])

                if fileDialog.exec_():
                    file_list = fileDialog.selectedFiles()  
                    self.book_cover.save(file_list[0], os.path.splitext(file_list[0])[1][1:].upper());

            elif action == actionClear:
                self.book_cover = None
                self.imgBookCover.clear()


    def selectAllAction(self):
        self.treeFileList.selectAll()


    def deleteRecAction(self):
        for item in self.treeFileList.selectedItems():
            self.rootFileList.removeChild(item)
     

    def openLog(self):
        self.openFile(self.log_file)


    def checkDestDir(self):
        filename = os.path.normpath(self.gui_config.outputFolder)
        if not os.path.exists(filename):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText(_translate('fb2mobi-gui', 'Folder does not exist.'))
            msg.setWindowTitle(_translate('fb2mobi-gui', 'Error'))
            msg.exec_()

            return False
        else:
            return True


    def showMessage(self, message):
        self.labelStatus.setText(message)


    def clearMessage(self):
        self.labelStatus.setText('')


    def startConvert(self):
        if self.rootFileList.childCount() > 0:
            if not self.checkDestDir():
                return

            if not self.convertRun:
                # self.btnStart.setText(_translate('fb2mobi-gui', 'Cancel'))
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.toolStart.setText(_translate('fb2mobi-gui', 'Cancel'))
                self.toolStart.setIcon(QIcon(':/toolbar/stop.png'))
                self.actionConvert.setText(_translate('fb2mobi-gui', 'Cancel conversion'))
                self.convertRun = True
                self.is_convert_cancel = False
                self.allControlsEnabled(False)

                files = []
                for i in range(self.rootFileList.childCount()):
                    files.append(self.rootFileList.child(i).text(2))

                # self.progressBar.setRange(0, len(files))
                # self.progressBar.setValue(0)
                # self.progressBar.setVisible(True)
                self.convertedCount = 0
                self.convertedFiles = []
                
                self.gui_config.converterConfig = ConverterConfig(self.config_file)
                self.gui_config.converterConfig.log = self.log


                self.convert_worker = ConvertThread(files, self.gui_config)
                self.convert_worker.convertBegin.connect(self.convertBegin)
                self.convert_worker.convertDone.connect(self.convertDone)
                self.convert_worker.convertAllDone.connect(self.convertAllDone)

                if self.gui_config.embedFontFamily:
                    self.generateFontCSS()

                self.convert_worker.start()
            else:
                self.is_convert_cancel = True
                self.convert_worker.stop() 
                # self.btnStart.setEnabled(False)
                self.toolStart.setEnabled(False)
                self.actionConvert.setEnabled(False)


    def generateFontCSS(self):
        # Список стилей для встраивания шрифтов
        style_rules = ['.titleblock', '.text-author', 'p', 'p.title', '.cite', '.poem', 
               '.table th', '.table td', '.annotation', 'body']


        css_string = modules.default_css.default_css
        css = cssutils.parseString(css_string)

        font_regular = ''
        font_italic = ''
        font_bold = ''
        font_bolditalic = ''

        if 'Regular' in self.gui_config.fontDb.families[self.gui_config.embedFontFamily]:
            font_regular = self.gui_config.fontDb.families[self.gui_config.embedFontFamily]['Regular']

        if 'Italic' in self.gui_config.fontDb.families[self.gui_config.embedFontFamily]:
            font_italic = self.gui_config.fontDb.families[self.gui_config.embedFontFamily]['Italic']
        else:
            font_italic = font_regular

        if 'Bold' in self.gui_config.fontDb.families[self.gui_config.embedFontFamily]:
            font_bold = self.gui_config.fontDb.families[self.gui_config.embedFontFamily]['Bold']
        else:
            font_bold = font_regular

        if 'Bold Italic' in self.gui_config.fontDb.families[self.gui_config.embedFontFamily]:
            font_bolditalic = self.gui_config.fontDb.families[self.gui_config.embedFontFamily]['Bold Italic']
        else:
            font_bolditalic = font_italic

        css.add('@font-face {{ font-family: "para"; src: url("fonts/{0}"); }}'.format(font_regular))
        css.add('@font-face {{ font-family: "para"; src: url("fonts/{0}"); font-style: italic; }}'.format(font_italic))
        css.add('@font-face {{ font-family: "para"; src: url("fonts/{0}"); font-weight: bold; }}'.format(font_bold))
        css.add('@font-face {{ font-family: "para"; src: url("fonts/{0}"); font-style: italic; font-weight: bold; }}'.format(font_bolditalic))

        found_body = False

        for rule in css:
            if rule.type == rule.STYLE_RULE:
                if rule.selectorText in style_rules:
                    rule.style['font-family'] = '"para"'
                if rule.selectorText == 'body':
                    found_body = True

        # Добавим стиль для 
        if not found_body:
            css.add('body {font-family: "para"; line-height: 100%; }')

        css_path = os.path.join(os.path.dirname(self.config_file), 'profiles')
        if not os.path.exists(css_path):
            os.makedirs(css_path)

        with codecs.open(os.path.join(css_path, '_font.css'), 'w', 'utf-8') as f:
            f.write(str(css.cssText, 'utf-8'))


    def convertAllDone(self):
        self.convertRun = False        
        # self.btnStart.setText(_translate('fb2mobi-gui', 'Start'))
        QApplication.restoreOverrideCursor()
        self.toolStart.setText(_translate('fb2mobi-gui', 'Start'))
        self.toolStart.setIcon(QIcon(':/toolbar/start.png'))
        self.actionConvert.setText(_translate('fb2mobi-gui', 'Start conversion'))
        self.allControlsEnabled(True)
        self.clearMessage()

        time.sleep(0.5)    
        # self.progressBar.setVisible(False)
        
        if self.gui_config.kindleCopyToDevice and not self.is_convert_cancel:
            if self.gui_config.kindlePath and os.path.exists(self.gui_config.kindlePath):
                self.copy_worker = CopyThread(self.convertedFiles, self.gui_config.kindlePath, 
                                              self.gui_config.kindleSyncCovers)
                self.copy_worker.copyBegin.connect(self.copyBegin)
                self.copy_worker.copyDone.connect(self.copyDone)
                self.copy_worker.copyAllDone.connect(self.copyAllDone)

                # self.progressBar.setRange(0, len(self.convertedFiles))
                # self.progressBar.setValue(0)
                self.copyCount = 0

                # self.progressBar.setVisible(True)
                self.allControlsEnabled(False, True)
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.copy_worker.start()
            else:
                msg = QMessageBox(QMessageBox.Critical, _translate('fb2mobi-gui', 'Error'), 
                                  _translate('fb2mobi-gui', 'Error when copying files - device not found.'), 
                                  QMessageBox.Ok, self)
                msg.exec_()


    def copyBegin(self, file):
        self.showMessage(_translate('fb2mobi-gui', 'Copying file to device: {0}').format(os.path.split(file)[1]))


    def copyDone(self):
        self.copyCount += 1
        # self.progressBar.setValue(self.copyCount)


    def copyAllDone(self):
        time.sleep(0.5)    
        # self.progressBar.setVisible(False)
        QApplication.restoreOverrideCursor()
        self.allControlsEnabled(True)
        self.clearMessage()


    def convertBegin(self, file):
        found = False
        item = None

        self.showMessage(_translate('fb2mobi-gui', 'Converting file: {0}').format(os.path.split(file)[1]))

        for i in range(self.rootFileList.childCount()):
            if file == self.rootFileList.child(i).text(2):
                found = True
                item = self.rootFileList.child(i)
                self.treeFileList.scrollToItem(item, QAbstractItemView.EnsureVisible)
                break

        if found:
            item.setIcon(0, self.iconGo)


    def convertDone(self, file, result, dest_file):
        found = False
        item = None

        if result:
            self.convertedFiles.append(dest_file)

        for i in range(self.rootFileList.childCount()):
            if file == self.rootFileList.child(i).text(2):
                found = True
                item = self.rootFileList.child(i)
                break

        if found:
            if result:
                item.setIcon(0, self.iconGreen)
            else:
                item.setIcon(0, self.iconRed)

        self.convertedCount += 1
        # self.progressBar.setValue(self.convertedCount)


    def allControlsEnabled(self, enable, disable_all=False):
        # self.btnSettings.setEnabled(enable)
        self.toolSettings.setEnabled(enable)
        self.toolAdd.setEnabled(enable)
        self.toolInfo.setEnabled(enable)
        self.actionAddFile.setEnabled(enable)
        self.actionSettings.setEnabled(enable)
        self.actionViewLog.setEnabled(enable)
        self.actionDelete.setEnabled(enable)
        if disable_all and not enable:
            self.actionConvert.setEnabled(enable)
            # self.btnStart.setEnabled(enable)
            self.toolStart.setEnabled(enable)
        elif enable:
            self.actionConvert.setEnabled(enable)
            # self.btnStart.setEnabled(enable)
            self.toolStart.setEnabled(enable)


    def loadNewCoverFormFile(self, img_file):
        self.book_cover = QPixmap(img_file)
        self.displayCoverThumbmail(self.book_cover)


    def clearBookInfo(self):        
        self.book_cover = None
        self.imgBookCover.clear()
        self.editAuthor.clear()
        self.editTitle.clear()
        self.editSeries.clear()
        self.editSeriesNumber.clear()
        self.editBookLanguage.clear()


    def saveBookInfo(self):
        selected_items = self.treeFileList.selectedItems()
        if len(selected_items) == 1:
            QApplication.setOverrideCursor(Qt.BusyCursor)

            item = selected_items[0]
            meta = Fb2Meta(item.text(2))
            meta.get()

            if self.book_cover:
                data = QByteArray()
                buf = QBuffer(data)
                self.book_cover.save(buf, 'JPG')
                meta.coverdata = bytes(buf.buffer())
                if not meta.coverpage:
                    meta.coverpage = 'cover.jpg'
                    meta.coverpage_href = '{http://www.w3.org/1999/xlink}href'
            else:
                meta.coverpage = ''
                meta.coverdata = None

            meta.set_authors(self.editAuthor.text())
            meta.book_title = self.editTitle.text()
            meta.set_series(self.editSeries.text(), self.editSeriesNumber.text())
            meta.lang = self.editBookLanguage.text()
            meta.write()

            item.setText(0, meta.book_title)
            item.setText(1, meta.get_autors())

            QApplication.restoreOverrideCursor()
        elif len(selected_items) > 1:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle(_translate('fb2mobi', 'Save'))
            msg.setText(_translate('fb2mobi', 'Save changes in selected files?'))
            msg.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
            if msg.exec_() == QMessageBox.Save:
                QApplication.setOverrideCursor(Qt.BusyCursor)
                
                for item in selected_items:
                    meta = Fb2Meta(item.text(2))
                    meta.get()
                    (series, series_number) = meta.get_first_series()
                    authors = meta.get_autors()
                    if self.editAuthor.text():
                        authors = self.editAuthor.text()
                    if self.editSeries.text():
                        series = self.editSeries.text()

                    meta.set_authors(authors)
                    meta.set_series(series, series_number)
                    if self.editBookLanguage.text():
                        meta.lang = self.editBookLanguage.text()
                    meta.write()

                    item.setText(0, meta.book_title)
                    item.setText(1, meta.get_autors())

                QApplication.restoreOverrideCursor()


    def displayCoverThumbmail(self, img):
        scaled_img = img.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter = QPainter(scaled_img)
        painter.setBackgroundMode(Qt.OpaqueMode)
        cur_font = painter.font()
        cur_font.setWeight(QFont.Bold)
        painter.setFont(cur_font)                
        img_size = '{0}x{1}'.format(img.width(), img.height())
        metrics = QFontMetrics(cur_font)
        painter.drawText(2, metrics.boundingRect(img_size).height(), img_size)
        painter.end()

        self.imgBookCover.setPixmap(scaled_img)


    def changeBook(self):
        self.clearBookInfo()

        selected_items = self.treeFileList.selectedItems()
        if len(selected_items) == 1:
            self.editTitle.setEnabled(True)
            self.editSeriesNumber.setEnabled(True)

            meta = Fb2Meta(selected_items[0].text(2))
            meta.get()

            self.editAuthor.setText(meta.get_autors())
            self.editTitle.setText(meta.book_title)
            (series_name, series_num) = meta.get_first_series()
            self.editSeries.setText(series_name)
            self.editSeriesNumber.setText(series_num)
            self.editBookLanguage.setText(meta.lang)
            
            if meta.coverdata:
                self.book_cover = QPixmap()
                self.book_cover.loadFromData(meta.coverdata)
                self.displayCoverThumbmail(self.book_cover)
        elif len(selected_items) > 1:
            self.editTitle.setEnabled(False)
            self.editSeriesNumber.setEnabled(False)
                
       

    def addFile(self, file):
        if not file.lower().endswith((".fb2", ".fb2.zip", ".zip")):
            return

        found = False

        file = os.path.normpath(file)
        
        for i in range(self.rootFileList.childCount()):
            if file == self.rootFileList.child(i).text(2):
                found = True
                break

        if not found:
            meta = Fb2Meta(file)
            meta.get()

            item = QTreeWidgetItem(0)
            item.setIcon(0, self.iconWhite)
            item.setText(0, meta.book_title)
            item.setText(1, meta.get_autors())
            item.setText(2, file)
            # Установим подсказки
            item.setToolTip(0, meta.book_title)
            item.setToolTip(1, meta.get_autors())
            item.setToolTip(2, file)
            
            self.treeFileList.addTopLevelItem(item)


    def addFiles(self, file_list):
        QApplication.setOverrideCursor(Qt.BusyCursor)
        for item in file_list:
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    for f in files:
                        self.addFile(os.path.join(root, f))
            else:
                self.addFile(item)
        QApplication.restoreOverrideCursor()


    def addFilesAction(self):
        if not self.gui_config.lastUsedPath:
            self.gui_config.lastUsedPath = os.path.expanduser('~')

        fileDialog = QFileDialog(self, _translate('fb2mobi-gui', 'Select files'), self.gui_config.lastUsedPath)
        fileDialog.setFileMode(QFileDialog.ExistingFiles)
        fileDialog.setNameFilters([_translate('fb2mobi-gui', 'Fb2 files (*.fb2 *.fb2.zip *.zip)'), 
                                  _translate('fb2mobi-gui', 'All files (*.*)')])

        if fileDialog.exec_():
            self.gui_config.lastUsedPath = os.path.normpath(fileDialog.directory().absolutePath())
            file_list = fileDialog.selectedFiles()
            self.addFiles(file_list)


    def closeApp(self):
        # Очистим лог-файл на выходе, если указано в настройках
        if self.gui_config.clearLogAfterExit:
            if self.log_file:
                with open(self.log_file, 'w'):
                    pass

        win_x = self.pos().x()
        win_y = self.pos().y()
        win_width = self.size().width()
        win_height = self.size().height()

        self.gui_config.geometry['x'] = win_x
        self.gui_config.geometry['y'] = win_y
        self.gui_config.geometry['width'] = win_width
        self.gui_config.geometry['height'] = win_height 

        self.gui_config.columns['0'] = self.treeFileList.columnWidth(0)   
        self.gui_config.columns['1'] = self.treeFileList.columnWidth(1)   
        self.gui_config.columns['2'] = self.treeFileList.columnWidth(2)   

        # # self.gui_config.bookInfoVisible = self.toolInfo.isChecked()
        # splitter_sizes = self.bookInfoSplitter.sizes()
        # print(splitter_sizes[1])
        # self.gui_config.bookInfoSplitterState = ', '.join(str(e) for e in splitter_sizes)

        self.gui_config.write()

        self.close()


    def openSupportURL(self):
        webbrowser.open(url=SUPPORT_URL)


    def openFile(self, filename):
        if sys.platform == 'win32':
            os.startfile(filename)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', filename])
        else:
            try:
                subprocess.Popen(['xdg-open', filename])
            except:
                pass


    def settings(self):
        prev_writeLog = self.gui_config.writeLog

        settingsDlg = SettingsDialog(self, self.gui_config)
        if settingsDlg.exec_():
            self.gui_config = settingsDlg.config
            self.gui_config.write()
            self.log.setLevel(self.gui_config.logLevel)

            if prev_writeLog != self.gui_config.writeLog:
                if self.gui_config.writeLog:
                    self.gui_config.converterConfig.log.addHandler(self.log_file_handler)
                else:
                    self.gui_config.converterConfig.log.removeHandler(self.log_file_handler)


    def about(self):
        aboutDlg = AboutDialog(self)
        aboutDlg.exec_()


    def closeEvent(self, event):
        self.closeApp()


class AppEventFilter(QObject):
    def __init__(self, app_win):
        super(AppEventFilter, self).__init__()
        self.app_win = app_win

    def eventFilter(self, receiver, event):
        if event.type() == QEvent.FileOpen:
            self.app_win.addFiles([event.file()])
            return True
        else:
            return super(AppEventFilter, self).eventFilter(receiver, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    app_path = os.path.normpath(fb2mobi.get_executable_path())
    locale_path = os.path.join(app_path, 'ui/locale')
    locale = QLocale.system().name()[:2]

    qt_translator = QTranslator()
    qt_translator.load(os.path.join(locale_path, 'qtbase_' + locale + '.qm'))
    app.installTranslator(qt_translator)

    app_translator = QTranslator()
    app_translator.load(os.path.join(locale_path, 'fb2mobi_' + locale + '.qm'))
    app.installTranslator(app_translator)

    app.setStyleSheet('QStatusBar::item { border: 0px }');

    mainAppWindow = MainAppWindow()
    mainAppWindow.show()

    appEventFilter = AppEventFilter(mainAppWindow)
    app.installEventFilter(appEventFilter)

    sys.exit(app.exec_())
