#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import subprocess
import webbrowser
import logging
import shutil

from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QTreeWidgetItem, QMessageBox, QDialog, QWidget, 
                            QLabel, QAbstractItemView)
from PyQt5.QtGui import QIcon, QPixmap 
from PyQt5.QtCore import QThread, pyqtSignal, QEvent, Qt

from ui.MainWindow import Ui_MainWindow
from ui.AboutDialog import Ui_AboutDialog
from ui.SettingsDialog import Ui_SettingsDialog

from ui.gui_config import GuiConfig
import ui.images_rc
import ui.ui_version

from modules.config import ConverterConfig
import fb2mobi
import synccovers
import version


SUPPORT_URL = u'http://www.the-ebook.org/forum/viewtopic.php?t=30380'


class CopyThread(QThread):
    copyBegin = pyqtSignal(object)
    copyDone = pyqtSignal()
    copyAllDone = pyqtSignal()

    def __init__(self, files, dest_path):
        super(CopyThread, self).__init__()
        self.files = files
        self.dest_path = dest_path

    def run(self):
        for file in self.files:
            self.copyBegin.emit(file)
            # try:
            if os.path.exists(self.dest_path):                    
                shutil.copy2(file, self.dest_path)
                src_sdr_dir = '{0}.{1}'.format(os.path.splitext(file)[0], 'sdr')
                dest_sdr_dir = os.path.join(self.dest_path, os.path.split(src_sdr_dir)[1])

                # Обработка apnx-файла, он находится в каталоге <имя файла книги>.sdr
                if os.path.isdir(src_sdr_dir):
                	if os.path.isdir(dest_sdr_dir):
                		shutil.rmtree(dest_sdr_dir)
                		shutil.copytree(src_sdr_dir, dest_sdr_dir)
            # except:
            #     pass
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

                fb2mobi.process_file(self.config, file, None)
                if not os.path.exists(self.getDestFileName(file)):
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

        self.buttonBox.button(self.buttonBox.Cancel).setText('Отмена')

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

        self.lineKindlePath.setText(self.config.kindlePath)
        self.checkCopyAfterConvert.setChecked(self.config.kindleCopyToDevice)
        self.checkSyncCovers.setChecked(self.config.kindleSyncCovers)


    def selectDestPath(self):
        self.lineDestPath.setText(self.selectPath(self.lineDestPath.text()))

    def selectKindlePath(self):
        self.lineKindlePath.setText(self.selectPath(self.lineKindlePath.text()))

    def selectPath(self, path):
        if not path:
            path = os.path.expanduser('~')

        dlgPath = QFileDialog(self, 'Выберите папку', path)
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


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)
        self.setupUi(self)

        image  = QPixmap(':/Images/128.png')
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

        self.setAcceptDrops(True)

        self.config_file = None
        self.log_file = None
        self.log = None
        self.config = {}

        self.convert_worker = None
        self.copy_worker = None

        self.rootFileList = self.treeFileList.invisibleRootItem()
        self.iconWhite = QIcon(':/Images/bullet_white.png')
        self.iconRed = QIcon(':/Images/bullet_red.png')
        self.iconGreen = QIcon(':/Images/bullet_green.png')
        self.iconGo = QIcon(':/Images/bullet_go.png')

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

        log = logging.getLogger('fb2mobi')
        log.setLevel("DEBUG")

        log_stream_handler = logging.StreamHandler()
        log_stream_handler.setLevel(fb2mobi.get_log_level(self.gui_config.converterConfig.console_level))
        log_stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        log.addHandler(log_stream_handler)

        if self.log_file:
            log_file_handler = logging.FileHandler(filename=self.log_file, mode='a', encoding='utf-8')
            log_file_handler.setLevel(fb2mobi.get_log_level(self.gui_config.converterConfig.log_level))
            log_file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
            log.addHandler(log_file_handler)


        self.gui_config.converterConfig.log = log


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

        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(False)        

        self.setWindowIcon(QIcon(':/Images/icon32.png'))
        self.treeFileList.installEventFilter(self)


    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if (event.key() == Qt.Key_Delete or (event.key() == Qt.Key_Backspace and event.modifiers() == Qt.ControlModifier)):
                self.deleteRecAction()
                return True
                
        return QWidget.eventFilter(self, source, event)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()


    def dropEvent(self, event):
        file_list = [u.toLocalFile() for u in event.mimeData().urls()]        
        self.addFiles(file_list)
        event.accept()


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
            msg.setText('Указанный каталог не существует')
            msg.setWindowTitle('Ошибка')
            msg.exec_()

            return False
        else:
            return True


    def startConvert(self):
        if self.rootFileList.childCount() > 0:
            if not self.checkDestDir():
                return

            if not self.convertRun:
                self.btnStart.setText('Стоп')
                self.actionConvert.setText('Прервать конвертацию')
                self.convertRun = True
                self.allControlsEnabled(False)

                files = []
                for i in range(self.rootFileList.childCount()):
                    files.append(self.rootFileList.child(i).text(0))

                self.progressBar.setRange(0, len(files))
                self.progressBar.setValue(0)
                self.progressBar.setVisible(True)
                self.convertedCount = 0
                self.convertedFiles = []
                
                self.convert_worker = ConvertThread(files, self.gui_config)
                self.convert_worker.convertBegin.connect(self.convertBegin)
                self.convert_worker.convertDone.connect(self.convertDone)
                self.convert_worker.convertAllDone.connect(self.convertAllDone)

                self.convert_worker.start()
            else:
                self.convert_worker.stop() 
                self.btnStart.setEnabled(False)
                self.actionConvert.setEnabled(False)


    def convertAllDone(self):
        self.convertRun = False        
        self.btnStart.setText('Старт')
        self.actionConvert.setText('Конвертировать')
        self.allControlsEnabled(True)
        self.statusBar().clearMessage()

        time.sleep(0.5)    
        self.progressBar.setVisible(False)
        
        if self.gui_config.kindleCopyToDevice:
            if self.gui_config.kindlePath and os.path.exists(self.gui_config.kindlePath):
                self.copy_worker = CopyThread(self.convertedFiles, self.gui_config.kindlePath)
                self.copy_worker.copyBegin.connect(self.copyBegin)
                self.copy_worker.copyDone.connect(self.copyDone)
                self.copy_worker.copyAllDone.connect(self.copyAllDone)

                self.progressBar.setRange(0, len(self.convertedFiles))
                self.progressBar.setValue(0)
                self.copyCount = 0

                self.progressBar.setVisible(True)
                self.allControlsEnabled(False, True)
                self.copy_worker.start()
            else:
                msg = QMessageBox(QMessageBox.Critical, 'Ошибка', 'Копирование невозможно - устройство недоступно.', QMessageBox.Ok, self)
                msg.exec_()


    def copyBegin(self, file):
        self.statusBar().showMessage('Копируется на устройство: {0}'.format(os.path.split(file)[1]))


    def copyDone(self):
        self.copyCount += 1
        self.progressBar.setValue(self.copyCount)


    def copyAllDone(self):
        if self.gui_config.kindleSyncCovers:
            if self.gui_config.kindlePath and os.path.exists(self.gui_config.kindlePath):
                self.statusBar().showMessage('Синхронизация обложек')
                self.progressBar.setMinimum(0)
                self.progressBar.setMaximum(0)
                try:                    
                    synccovers.process_folder(self.gui_config.kindlePath, 330, 470, False, False)
                except:
                    pass

        time.sleep(0.5)    
        self.progressBar.setVisible(False)
        self.allControlsEnabled(True)
        self.statusBar().clearMessage()


    def convertBegin(self, file):
        found = False
        item = None

        self.statusBar().showMessage('Обработка файла: {0}'.format(os.path.split(file)[1]))

        for i in range(self.rootFileList.childCount()):
            if file == self.rootFileList.child(i).text(0):
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
            if file == self.rootFileList.child(i).text(0):
                found = True
                item = self.rootFileList.child(i)
                break

        if found:
            if result:
                item.setIcon(0, self.iconGreen)
            else:
                item.setIcon(0, self.iconRed)

        self.convertedCount += 1
        self.progressBar.setValue(self.convertedCount)


    def allControlsEnabled(self, enable, disable_all=False):
        self.btnSettings.setEnabled(enable)
        self.actionAddFile.setEnabled(enable)
        self.actionSettings.setEnabled(enable)
        self.actionViewLog.setEnabled(enable)
        self.actionDelete.setEnabled(enable)
        if disable_all and not enable:
            self.actionConvert.setEnabled(enable)
            self.btnStart.setEnabled(enable)
        elif enable:
            self.actionConvert.setEnabled(enable)
            self.btnStart.setEnabled(enable)


    def addFile(self, file):
        if not file.lower().endswith((".fb2", ".fb2.zip", ".zip")):
            return

        found = False

        file = os.path.normpath(file)
        
        for i in range(self.rootFileList.childCount()):
            if file == self.rootFileList.child(i).text(0):
                found = True
                break

        if not found:
            item = QTreeWidgetItem(0)
            item.setText(0, file)
            item.setIcon(0, self.iconWhite)
            self.treeFileList.addTopLevelItem(item)


    def addFiles(self, file_list):
        for item in file_list:
            if os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    for f in files:
                        self.addFile(os.path.join(root, f))
            else:
                self.addFile(item)


    def addFilesAction(self):
        if not self.savedPath:
            self.savedPath = os.path.expanduser('~')

        fileDialog = QFileDialog(self, "Выберите файлы", self.savedPath)
        fileDialog.setFileMode(QFileDialog.ExistingFiles)
        fileDialog.setNameFilters(['Файлы fb2 (*.fb2 *.fb2.zip *.zip)', 'Все файлы (*.*)'])

        if fileDialog.exec_():
            self.savedPath = fileDialog.directory().absolutePath()
            file_list = fileDialog.selectedFiles()
            self.addFiles(file_list)


    def closeApp(self):
        win_x = self.pos().x()
        win_y = self.pos().y()
        win_width = self.size().width()
        win_height = self.size().height()

        self.gui_config.geometry['x'] = win_x
        self.gui_config.geometry['y'] = win_y
        self.gui_config.geometry['width'] = win_width
        self.gui_config.geometry['height'] = win_height    

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
        settingsDlg = SettingsDialog(self, self.gui_config)
        if settingsDlg.exec_():
            self.gui_config = settingsDlg.config
            self.gui_config.write()


    def about(self):
        aboutDlg = AboutDialog(self)
        aboutDlg.exec_()


    def closeEvent(self, event):
        self.closeApp()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainAppWindow = MainAppWindow()
    mainAppWindow.show()

    sys.exit(app.exec_())
