# Form implementation generated from reading ui file 'game_ui.ui'
#
# Created by: PyQt6 UI code generator 6.8.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainGame(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(700, 800)
        MainWindow.setMinimumSize(QtCore.QSize(579, 384))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.pushButton = QtWidgets.QPushButton(parent=self.centralwidget)
        self.pushButton.setStyleSheet("background-color: rgb(255, 255, 127);")
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 5, 2, 1, 1)
        self.msg = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.msg.setMinimumSize(QtCore.QSize(142, 19))
        self.msg.setMaximumSize(QtCore.QSize(168, 19))
        self.msg.setObjectName("msg")
        self.gridLayout.addWidget(self.msg, 3, 2, 1, 1)
        self.send_btn = QtWidgets.QPushButton(parent=self.centralwidget)
        self.send_btn.setMaximumSize(QtCore.QSize(168, 17))
        self.send_btn.setStyleSheet("background-color: rgb(255, 85, 127);")
        self.send_btn.setObjectName("send_btn")
        self.gridLayout.addWidget(self.send_btn, 4, 2, 1, 1)
        self.game_field = QtWidgets.QGraphicsView(parent=self.centralwidget)
        self.game_field.setMinimumSize(QtCore.QSize(393, 334))
        self.game_field.setMouseTracking(True)
        self.game_field.setTabletTracking(True)
        self.game_field.setObjectName("game_field")
        self.gridLayout.addWidget(self.game_field, 1, 0, 4, 2)
        self.game_chat = QtWidgets.QTextEdit(parent=self.centralwidget)
        self.game_chat.setMaximumSize(QtCore.QSize(168, 16777215))
        self.game_chat.setReadOnly(True)
        self.game_chat.setObjectName("game_chat")
        self.gridLayout.addWidget(self.game_chat, 1, 2, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setMinimumSize(QtCore.QSize(168, 11))
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 3)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 579, 18))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "Exit game"))
        self.send_btn.setText(_translate("MainWindow", "Send"))
        self.label.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:9pt; font-weight:600;\">05:00</span></p></body></html>"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainGame()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
