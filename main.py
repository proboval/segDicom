from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5 import QtCore
from razmetka import Ui_MainWindow
import pydicom
import copy
import numpy as np
import sys
import os
import shutil
from PIL import Image


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.color = [Qt.yellow, Qt.blue, Qt.red, Qt.green, Qt.magenta, Qt.cyan, QColor(175, 80, 95),
                      QColor(99, 70, 185), QColor(216, 140, 39)]
        self.markSet = ['кровоизлияние (в вещество мозга, в оболочки, субарахноидальное)',
                        'хроническая ишемия (глиоз, очаги ДЭП)',
                        'кистозно-глиозные изменения (рубец)',
                        'киста', 'опухоль', 'острая ишемия (инсульт)',
                        'лейкоареоз', 'демиелинезация', 'перифокальный отек']
        self.comment = []
        self.segRez = ''
        self.image = None
        self.countClick = 0
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.count = 0
        self.countMRT = 0
        self.dirlist = ''
        self.newDirList = ''
        self.drawMRT = False
        self.arrPoint = []
        self.tempArrPoint = []
        self.flagArr = []
        self.colorArr = []
        self.rClick = False
        self.initUI()
        self.ui.open_.clicked.connect(lambda: self.open_())
        self.ui.next.clicked.connect(lambda: self.next())
        self.ui.back_.clicked.connect(lambda: self.back())
        self.ui.select_area.clicked.connect(lambda: self.select_area())
        self.ui.save_.clicked.connect(lambda: self.save_())
        self.ui.del_area.clicked.connect(lambda: self.del_area())
        self.ui.MRT.stateChanged.connect(self.state_changed_MRT)
        self.ui.KT.stateChanged.connect(self.state_changed_KT)
        self.ui.PET_KT.stateChanged.connect(self.state_changed_PRT_KT)
        self.ui.contrasting.stateChanged.connect(self.state_changed_contrasting)
        self.ui.no_contrasting.stateChanged.connect(self.state_changed_no_contrasting)

    def state_changed_contrasting(self, int):
        if self.ui.contrasting.isChecked():
            self.ui.no_contrasting.setChecked(False)
            if self.flagArr != []:
                self.flagArr[self.count][1] = 'С контрастированием'

    def state_changed_no_contrasting(self, int):
        if self.ui.no_contrasting.isChecked():
            self.ui.contrasting.setChecked(False)
            if self.flagArr != []:
                self.flagArr[self.count][1] = 'Без контрастирования'

    def state_changed_MRT(self, int):
        if self.ui.MRT.isChecked():
            self.ui.KT.setChecked(False)
            self.ui.PET_KT.setChecked(False)
            if self.flagArr != []:
                self.flagArr[self.count][0] = 'МРТ'

    def state_changed_KT(self, int):
        if self.ui.KT.isChecked():
            self.ui.MRT.setChecked(False)
            self.ui.PET_KT.setChecked(False)
            if self.flagArr != []:
                self.flagArr[self.count][0] = 'КТ'

    def state_changed_PRT_KT(self, int):
        if self.ui.PET_KT.isChecked():
            self.ui.MRT.setChecked(False)
            self.ui.KT.setChecked(False)
            if self.flagArr != []:
                self.flagArr[self.count][0] = 'ПЭТ КТ'

    def del_area(self):
        try:
            count = self.ui.count_area.value()
            self.colorArr[self.count].pop(count - 1)
            self.arrPoint[self.count].pop(count - 1)
            self.ui.area_label.setText('')
            txt = ''
            for i in range(len(self.arrPoint[self.count])):
                txt += f'{i+1}) {self.markSet[self.colorArr[self.count][i]]} \n'
            self.ui.area_label.setText(txt)
            lg = self.ui.area_label.geometry()
            lg.setHeight(lg.height() - 21)
            self.ui.area_label.setGeometry(lg)
            self.update()
        except:
            pass

    def select_area(self):
        self.colorArr[self.count].append(self.ui.marker_set.currentIndex())
        self.tempArrPoint = []
        self.rClick = True
        self.countClick = 0

    def mousePressEvent(self, event):
        if self.rClick and self.countClick < 4:
            pos = event.pos()
            self.tempArrPoint.append(pos)
            self.countClick += 1
            self.update()
        if self.countClick == 4:
            self.rClick = False
            self.countClick = 0
            self.arrPoint[self.count].append(self.tempArrPoint)
            self.tempArrPoint = []
            txt = ''
            for i in range(len(self.arrPoint[self.count])):
                txt += f'{i + 1}) {self.markSet[self.colorArr[self.count][i]]}\n'
            self.ui.area_label.setText(txt)
            lg = self.ui.area_label.geometry()
            lg.setHeight(lg.height() + 21)
            self.ui.area_label.setGeometry(lg)

    def initUI(self):
        self.setWindowTitle("Разметка")
        self.show()

    def save_(self):
        size = self.size()
        for i in range(len(self.arrPoint)):
            for j in range(len(self.arrPoint[i])):
                for k in range(len(self.arrPoint[i][j])):
                    self.arrPoint[i][j][k].setX(self.arrPoint[i][j][k].x() - (size.width() // 2 - (512 // 2)))
                    self.arrPoint[i][j][k].setY(self.arrPoint[i][j][k].y() - ((size.height() - 61) // 2 - (512 // 2)))
        with open(self.dirlist+'\\segRez.txt', 'w', encoding="utf-8") as file:
            for i in range(len(self.arrPoint)):
                print(f'Снимок {i + 1}', file=file, end = '\n')
                for j in range(len(self.arrPoint[i])):
                    print(str(self.arrPoint[i][j]).replace("PyQt5.QtCore.QPoint", '') + ' - '
                          + str(self.markSet[self.colorArr[i][j]]), file=file, end = '\n')
                print('(' + self.flagArr[i][0] + ' ' + self.flagArr[i][1] + ')', file=file, end='\n')
                if len(self.arrPoint[i]) == 0:
                    print('Патологии не обнаружены', file=file, end='\n')
                print('\n', file=file, end = '\n')
        shutil.rmtree(self.newDirList)
        self.count = 0
        self.countMRT = 0
        self.dirlist = ''
        self.newDirList = ''
        self.arrPoint = []
        self.tempArrPoint = []
        self.invFlag()
        self.ui.area_label.setText('')
        lg = self.ui.area_label.geometry()
        lg.setHeight(21)
        self.ui.area_label.setGeometry(lg)
        self.drawMRT = False
        self.ui.countMRT_.setText('Сохранение прошло успешно')

    def invFlag(self):
        self.ui.KT.setChecked(False)
        self.ui.MRT.setChecked(False)
        self.ui.PET_KT.setChecked(False)
        self.ui.contrasting.setChecked(False)
        self.ui.no_contrasting.setChecked(False)

    def setFlag(self):
        if self.flagArr[self.count][0] == 'МРТ':
            self.ui.MRT.setChecked(True)
        elif self.flagArr[self.count][0] == 'КТ':
            self.ui.KT.setChecked(True)
        elif self.flagArr[self.count][0] == 'ПЭТ КТ':
            self.ui.PET_KT.setChecked(True)
        if self.flagArr[self.count][1] == 'С контрастированием':
            self.ui.contrasting.setChecked(True)
        elif self.flagArr[self.count][1] == 'Без контрастирования':
            self.ui.no_contrasting.setChecked(True)

    def keyPressEvent(self, event):
        if self.countMRT > 0:
            if event.key() == QtCore.Qt.Key_D:
                self.next()
            elif event.key() == QtCore.Qt.Key_A:
                self.back()
            elif event.key() == QtCore.Qt.Key_E:
                self.select_area()

    def next(self):
        if self.countMRT > 0:
            self.rClick = False
            self.tempArrPoint = []
            if self.count + 1 != self.countMRT:
                self.count += 1
                name = self.dirlist.split('/')[-2]
                self.ui.countMRT_.setText(f"{name}, Снимок {self.count + 1} из {self.countMRT}")
                txt = ''
                for i in range(len(self.arrPoint[self.count])):
                    txt += f'{i + 1}) {self.markSet[self.colorArr[self.count][i]]} \n'
                self.ui.area_label.setText(txt)
                lg = self.ui.area_label.geometry()
                n = 21 * len(self.colorArr[self.count])
                lg.setHeight(n)
                self.ui.area_label.setGeometry(lg)
                self.invFlag()
                self.setFlag()
                tempArr = copy.deepcopy(self.arrPoint)
                size = self.size()
                for i in range(len(tempArr)):
                    for j in range(len(tempArr[i])):
                        for k in range(len(tempArr[i][j])):
                            tempArr[i][j][k].setX(
                                tempArr[i][j][k].x() - (size.width() // 2 - (512 // 2)))
                            tempArr[i][j][k].setY(
                                tempArr[i][j][k].y() - ((size.height() - 61) // 2 - (512 // 2)))
                with open(self.dirlist + '\\segRez.txt', 'w', encoding="utf-8") as file:
                    print(f'{self.count}', file=file, end='\n')
                    for i in range(len(tempArr)):
                        print(f'Снимок {i + 1}', file=file, end='\n')
                        for j in range(len(tempArr[i])):
                            print(str(tempArr[i][j]).replace("PyQt5.QtCore.QPoint", '') + ' - '
                                    + str(self.markSet[self.colorArr[i][j]]), file=file, end='\n')
                        print('(' + self.flagArr[i][0] + ' ' + self.flagArr[i][1] + ')', file=file, end='\n')
                        if len(tempArr[i]) == 0:
                            print('Патологии не обнаружены', file=file, end='\n')
                        print('\n', file=file, end='\n')
                self.update()

    def back(self):
        if self.countMRT > 0:
            self.rClick = False
            self.tempArrPoint = []
            if self.count != 0:
                self.count -= 1
                name = self.dirlist.split('/')[-2]
                self.ui.countMRT_.setText(f"{name}, Снимок {self.count + 1} из {self.countMRT}")
                txt = ''
                for i in range(len(self.arrPoint[self.count])):
                    txt += f'{i + 1}) {self.markSet[self.colorArr[self.count][i]]} \n'
                self.ui.area_label.setText(txt)
                lg = self.ui.area_label.geometry()
                n = 21 * len(self.colorArr[self.count])
                lg.setHeight(n)
                self.ui.area_label.setGeometry(lg)
                self.invFlag()
                self.setFlag()
                self.update()

    def open_(self):
        try:
            self.dirlist = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
            with open("История.txt", 'a', encoding="utf-8") as file:
                print(str(self.dirlist), file=file, sep='\n')
            self.count = 0
            self.tempArrPoint = []
            self.newDirList = self.dirlist + 'new'
            os.mkdir(self.newDirList)
            self.countMRT = 0
            try:
                for dirName in os.listdir(self.dirlist):
                    self.countMRT += 1
                    newName = self.dirlist + '\\' + dirName
                    ds = pydicom.dcmread(newName)
                    new_image = ds.pixel_array.astype(float)
                    scaled_image = (np.maximum(new_image, 0) / new_image.max()) * 255.0
                    scaled_image = np.uint8(scaled_image)
                    final_image = Image.fromarray(scaled_image)
                    final_image.save(self.newDirList + '\\' + dirName[:-4] + 'new.png')
            except:
                pass
            self.drawMRT = True
            name = self.dirlist.split('/')[-2]
            self.ui.countMRT_.setText(f"{name}, Снимок 1 из {self.countMRT}")
            self.arrPoint = [[] for i in range(self.countMRT)]
            self.colorArr = [[] for i in range(self.countMRT)]
            self.flagArr = [['', ''] for i in range(self.countMRT)]
            os.mkdir(self.dirlist + '\\segRez')
            self.segRez = self.dirlist + '\\segRez'
        except:
            self.ui.countMRT_.setText(f"Ошибка")

    def paintEvent(self, e):
        qp = QPainter()
        size = self.size()
        qp.begin(self)
        if self.drawMRT:
            k = 0
            tempfile = ''
            for fileName in os.listdir(self.newDirList):
                if k == self.count:
                    self.image = QImage(self.newDirList + '\\' + fileName)
                    rect = QRect(size.width() // 2 - (512 // 2), (size.height() - 61) // 2 - (512 // 2), 512, 512)
                    pixmap = QImage(self.newDirList + '\\' + fileName)
                    qp.drawImage(rect, pixmap)
                    tempfile = fileName
                    break
                k += 1
            if self.tempArrPoint != []:
                qp.setPen(self.color[self.colorArr[self.count][-1]])
                qp.drawPolygon(self.tempArrPoint)
                for i in range(len(self.tempArrPoint)):
                    qp.drawPoint(self.tempArrPoint[i])
            for i in range(len(self.arrPoint[self.count])):
                qp.setPen(self.color[self.colorArr[self.count][i]])
                qp.drawPolygon(self.arrPoint[self.count][i])
            rect = QRect(size.width() // 2 - (512 // 2), (size.height() - 61) // 2 - (512 // 2), 512, 512)
            pix = QPixmap(self.size())
            self.render(pix)
            newPix = pix.copy(rect)
            newPix.save(f'{self.segRez}\\{tempfile[:-4]}.png', 'png')

        qp.end()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    application = mywindow()

    sys.exit(app.exec())
