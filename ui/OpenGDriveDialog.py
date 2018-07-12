# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\OpenGDriveDialog.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GDriveDialog(object):
    def setupUi(self, GDriveDialog):
        GDriveDialog.setObjectName("GDriveDialog")
        GDriveDialog.resize(528, 348)
        self.gridLayout = QtWidgets.QGridLayout(GDriveDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.tree = QtWidgets.QTreeView(GDriveDialog)
        self.tree.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree.setObjectName("tree")
        self.tree.header().setVisible(False)
        self.verticalLayout.addWidget(self.tree)
        self.buttonBox = QtWidgets.QDialogButtonBox(GDriveDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Open)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        self.retranslateUi(GDriveDialog)
        self.buttonBox.accepted.connect(GDriveDialog.accept)
        self.buttonBox.rejected.connect(GDriveDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(GDriveDialog)

    def retranslateUi(self, GDriveDialog):
        _translate = QtCore.QCoreApplication.translate
        GDriveDialog.setWindowTitle(_translate("GDriveDialog", "Open from Google Drive"))

