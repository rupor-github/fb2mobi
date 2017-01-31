#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import subprocess
import webbrowser
import logging

from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTreeWidgetItem, QMessageBox, QDialog, QWidget
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, QEvent, Qt

from ui.MainWindow import Ui_MainWindow
from ui.AboutDialog import Ui_AboutDialog
from ui.gui_config import GuiConfig
import ui.images_rc
import ui.ui_version

from modules.config import ConverterConfig
import fb2mobi
import version


SUPPORT_URL = u'http://www.the-ebook.org/forum/viewtopic.php?t=30380'


class ConvertThread(QThread):
    convertBegin = pyqtSignal(object)
    convertDone = pyqtSignal(object, bool)
    convertAllDone = pyqtSignal()

    def __init__(self, files, config):
        super(ConvertThread, self).__init__()
        self.files = files
        self.config = config    
        self.cancel = False


    def run(self):
        for file in self.files:
            result = True
            if not self.cancel:
                self.convertBegin.emit(file)
                fb2mobi.process_file(self.config, file, None)
                if not os.path.exists(self.getDestFileName(file)):
                    result = False

                self.convertDone.emit(file, result)
            else:
                break

        self.convertAllDone.emit()

    def getDestFileName(self, file):
        if self.config.output_dir is None:
            output_dir = os.path.abspath(os.path.split(file)[0])
        else:
            output_dir = os.path.abspath(self.config.output_dir)
        file_name = os.path.join(output_dir, os.path.splitext(os.path.split(file)[1])[0])
        return '{0}.{1}'.format(file_name, self.config.output_format)


    def stop(self):
        self.cancel = True


class AboutDialog(QDialog, Ui_AboutDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
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

        self.setAcceptDrops(True)

        self.config_file = None
        self.log_file = None
        self.log = None
        self.config = {}

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

        self.config = ConverterConfig(self.config_file)
        self.gui_config = GuiConfig(self.gui_config_file)


        log = logging.getLogger('fb2mobi')
        log.setLevel("DEBUG")

        log_stream_handler = logging.StreamHandler()
        log_stream_handler.setLevel(fb2mobi.get_log_level(self.config.console_level))
        log_stream_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        log.addHandler(log_stream_handler)

        if self.log_file:
            log_file_handler = logging.FileHandler(filename=self.log_file, mode='a', encoding='utf-8')
            log_file_handler.setLevel(fb2mobi.get_log_level(self.config.log_level))
            log_file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
            log.addHandler(log_file_handler)

        self.log = log


        for p in self.config.profiles:
            self.comboProfiles.addItem('{0} ({1})'.format(p, self.config.profiles[p]['description']), p)

        for f in ['mobi', 'azw3', 'epub']:
            self.comboOutputFormat.addItem(f, f)

        if self.gui_config.lastUsedProfile:
            self.comboProfiles.setCurrentIndex(self.comboProfiles.findData(self.gui_config.lastUsedProfile))
        
        if self.gui_config.lastUsedFormat:
            self.comboOutputFormat.setCurrentIndex(self.comboOutputFormat.findData(self.gui_config.lastUsedFormat))

        if self.gui_config.outputFolder:
            self.editDestPath.setText(self.gui_config.outputFolder)
        else:
            self.editDestPath.setText(os.path.abspath(os.path.expanduser("~/Desktop")))

        if self.gui_config.geometry['x'] and self.gui_config.geometry['y']:
            self.move(self.gui_config.geometry['x'], self.gui_config.geometry['y'])
            self.resize(self.gui_config.geometry['width'], self.gui_config.geometry['height'])

        self.checkConvertToSrcDir.setChecked(self.gui_config.convertToSourceDirectory)
        self.checkConvertToDestDirClicked(self.gui_config.convertToSourceDirectory)

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
     

    def checkConvertToDestDirClicked(self, state):
        enabled = False
        if state == 0:
            enabled = True

        self.editDestPath.setEnabled(enabled)
        self.btnSelectDestDir.setEnabled(enabled)
        self.btnOpenDestDir.setEnabled(enabled)


    def openDestDir(self):
        filename = os.path.normpath(self.editDestPath.text())
        self.openFile(filename)


    def openLog(self):
        self.openFile(self.log_file)

    def checkDestDir(self):
        filename = os.path.normpath(self.editDestPath.text())
        if not os.path.exists(filename):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText('Указанный каталог не существует')
            msg.setWindowTitle('Ошибка')
            msg.exec_()
            self.editDestPath.selectAll()
            self.editDestPath.setFocus()

            return False
        else:
            return True


    def selectDestDir(self):
        if self.editDestPath.text():
            dest_dir = self.editDestPath.text()
        else:
            dest_dir = os.path.expanduser('~')

        dirDialog = QFileDialog(self, 'Выберите каталог', dest_dir)
        dirDialog.setFileMode(QFileDialog.Directory)
        dirDialog.setOption(QFileDialog.ShowDirsOnly, True)

        if dirDialog.exec_():
            for d in dirDialog.selectedFiles():
                self.editDestPath.setText(os.path.normpath(d))


    def startConvert(self):
        if self.rootFileList.childCount() > 0:
            if not self.checkDestDir():
                return

            if not self.convertRun:
                self.btnStart.setText('Стоп')
                self.convertRun = True
                self.allControlsEnabled(False)
                files = []
                for i in range(self.rootFileList.childCount()):
                    files.append(self.rootFileList.child(i).text(0))

                self.progressBar.setRange(0, len(files))
                self.progressBar.setValue(0)
                self.progressBar.setVisible(True)
                self.convertedCount = 0

                self.config.setCurrentProfile(self.comboProfiles.currentData())
                self.config.log = self.log
                self.config.output_format = self.comboOutputFormat.currentData()
                if not self.checkConvertToSrcDir.isChecked():
                    self.config.output_dir = self.editDestPath.text()
                else:
                   self.config.output_dir = None 

                self.worker = ConvertThread(files, self.config)
                self.worker.convertBegin.connect(self.convertBegin)
                self.worker.convertDone.connect(self.convertDone)
                self.worker.convertAllDone.connect(self.convertAllDone)
                self.worker.start()
            else:
                self.worker.stop()            


    def convertAllDone(self):
        self.convertRun = False        
        self.btnStart.setText('Пуск')
        self.allControlsEnabled(True)
        time.sleep(0.5)
        self.progressBar.setVisible(False)

    def convertBegin(self, file):
        found = False
        item = None

        for i in range(self.rootFileList.childCount()):
            if file == self.rootFileList.child(i).text(0):
                found = True
                item = self.rootFileList.child(i)
                break

        if found:
            item.setIcon(0, self.iconGo)


    def convertDone(self, file, result):
        found = False
        item = None

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


    def allControlsEnabled(self, enable):
        self.comboProfiles.setEnabled(enable)
        self.comboOutputFormat.setEnabled(enable)
        self.btnSelectDestDir.setEnabled(enable)
        self.checkConvertToSrcDir.setEnabled(enable)
        self.editDestPath.setEnabled(enable)


    def addFile(self, file):
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
        profile = self.comboProfiles.currentData()
        output_format = self.comboOutputFormat.currentData()
        output_dir = self.editDestPath.text()
        convert_to_source_dir = self.checkConvertToSrcDir.isChecked()

        if profile:
            self.gui_config.lastUsedProfile = profile
        if output_format:
            self.gui_config.lastUsedFormat = output_format
        if output_dir:
            self.gui_config.outputFolder = os.path.normpath(output_dir)
        self.gui_config.convertToSourceDirectory = str(convert_to_source_dir)
    
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


    def about(self):
        aboutDlg = AboutDialog()
        aboutDlg.exec_()


    def closeEvent(self, event):
        self.closeApp()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainAppWindow = MainAppWindow()
    mainAppWindow.show()

    sys.exit(app.exec_())
