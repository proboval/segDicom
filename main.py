import json
import random

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QImage
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5 import QtCore, QtWidgets, QtGui
import asyncio
from razmetka import Ui_MainWindow
import pydicom
import copy
import numpy as np
import sys
import os
import shutil
from PIL import Image


def generate_color():
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)

    return red, green, blue


class mywindow(QMainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.color = []
        self.markSet = []
        self.comment = []
        self.tempfile = ''
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
        self.inf_patient = {}
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
        self.ui.create_new_mark.clicked.connect(lambda: self.create_new_mark_())
        self.ui.save_marker_list.triggered.connect(self.save_markers_)
        self.ui.open_marker_list.triggered.connect(self.open_markers_)

    def open_markers_(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Открыть файл, содержащий маркеры", "", "JSON-файл (*.json);;Все файлы (*)",
                                                   options=options)
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    keys = data.keys()
                    self.color.clear()
                    self.markSet.clear()
                    self.ui.marker_set.clear()
                    for key in keys:
                        self.markSet.append(key)
                        self.color.append(QColor(data[key]['red'], data[key]['green'], data[key]['blue']))
                        self.ui.marker_set.addItem(key)
                except json.JSONDecodeError:
                    print('Ошибка декодирования JSON файла.')


    def save_markers_(self):
        markers_dict = {}
        for i in range(len(self.markSet)):
            markers_dict[self.markSet[i]] = {}
            markers_dict[self.markSet[i]]['red'] = QColor(self.color[i]).red()
            markers_dict[self.markSet[i]]['green'] = QColor(self.color[i]).green()
            markers_dict[self.markSet[i]]['blue'] = QColor(self.color[i]).blue()

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(None, "Сохранить файл", "", "JSON-файл (*.json);;Все файлы (*)",
                                                   options=options)
        if file_name:
            with open(f'{file_name}', 'w', encoding="utf-8") as file:
                json.dump(markers_dict, file, ensure_ascii=False)

    def create_new_mark_(self):
        self.markSet.append(self.ui.new_mark_line.text())
        r, g, b = generate_color()
        self.color.append(QtGui.QColor(r, g, b))
        self.ui.marker_set.addItem(self.ui.new_mark_line.text())
        self.ui.new_mark_line.setText('')

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
            row = self.ui.tableWidget.currentRow()
            self.colorArr[self.count].pop(row)
            self.arrPoint[self.count].pop(row)
            if row > -1:
                self.ui.tableWidget.removeRow(row)
                self.ui.tableWidget.selectionModel().clearCurrentIndex()
            geometry = self.ui.tableWidget.geometry()
            geometry.setHeight(geometry.height() - 41)
            self.ui.tableWidget.setGeometry(geometry)
            self.update()
        except:
            pass

    def select_area(self):
        try:
            self.colorArr[self.count].append(self.ui.marker_set.currentIndex())
            self.tempArrPoint = []
            self.rClick = True
            self.countClick = 0
        except:
            pass

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
            row = self.ui.tableWidget.rowCount()
            row += 1
            self.ui.tableWidget.setRowCount(row)
            geometry = self.ui.tableWidget.geometry()
            geometry.setHeight(geometry.height() + 41)
            self.ui.tableWidget.setGeometry(geometry)
            row_ = self.ui.tableWidget.rowCount()
            item = QtWidgets.QTableWidgetItem()
            item.setText(self.markSet[self.colorArr[self.count][-1]])
            self.ui.tableWidget.setItem(row_-1,0,item)
            item = QtWidgets.QTableWidgetItem()
            brush = QtGui.QBrush(self.color[self.colorArr[self.count][-1]])
            brush.setStyle(QtCore.Qt.SolidPattern)
            item.setBackground(brush)
            self.ui.tableWidget.setItem(row_-1,1,item)
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(QtCore.Qt.NoBrush)

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
        for i in range(len(self.arrPoint)):
            self.inf_patient[i] = {}
            self.inf_patient[i]['arrPathology'] = {}
            self.inf_patient[i]['flagArr'] = self.flagArr[i]
            for j in range(len(self.arrPoint[i])):
                self.inf_patient[i]['arrPathology'][f'pathologyPoint{j}'] = [{'x': point.x(), 'y': point.y()} for point in self.arrPoint[i][j]]
                self.inf_patient[i]['arrPathology'][f'pathologyName{j}'] = self.markSet[self.colorArr[i][j]]

        with open(self.dirlist+'\\segRez.json', 'w', encoding="utf-8") as file:
            json.dump(self.inf_patient, file, ensure_ascii=False)

        shutil.rmtree(self.newDirList)
        self.inf_patient.clear()
        self.count = 0
        self.countMRT = 0
        self.dirlist = ''
        self.newDirList = ''
        self.arrPoint = []
        self.tempArrPoint = []
        self.invFlag()
        self.ui.tableWidget.setRowCount(0)
        geometry = self.ui.tableWidget.geometry()
        geometry.setHeight(41)
        self.ui.tableWidget.setGeometry(geometry)
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
        if self.countMRT > 0 and self.drawMRT:
            if event.key() == QtCore.Qt.Key_D:
                self.next()
            elif event.key() == QtCore.Qt.Key_A:
                self.back()
            elif event.key() == QtCore.Qt.Key_E:
                self.select_area()
            elif event.key() == QtCore.Qt.Key_Delete:
                self.del_area()

    def next(self):
        if self.countMRT > 0:
            size = self.size()
            rect = QRect(size.width() // 2 - (512 // 2), (size.height() - 61) // 2 - (512 // 2), 512, 512)
            pix = QPixmap(self.size())
            self.render(pix)
            newPix = pix.copy(rect)
            newPix.save(f'{self.segRez}\\{self.tempfile[:-4]}.png', 'png')
            self.rClick = False
            self.tempArrPoint = []
            if self.count + 1 != self.countMRT:
                self.count += 1
                name = self.dirlist.split('/')[-2]
                self.ui.countMRT_.setText(f"{name}, Снимок {self.count + 1} из {self.countMRT}")
                self.ui.tableWidget.setRowCount(0)
                geometry = self.ui.tableWidget.geometry()
                geometry.setHeight(41 * (len(self.arrPoint[self.count]) + 1))
                self.ui.tableWidget.setGeometry(geometry)
                self.ui.tableWidget.setRowCount(len(self.arrPoint[self.count]))
                for i in range(len(self.arrPoint[self.count])):
                    item = QtWidgets.QTableWidgetItem()
                    item.setText(self.markSet[self.colorArr[self.count][i]])
                    self.ui.tableWidget.setItem(i, 0, item)
                    item = QtWidgets.QTableWidgetItem()
                    brush = QtGui.QBrush(self.color[self.colorArr[self.count][i]])
                    brush.setStyle(QtCore.Qt.SolidPattern)
                    item.setBackground(brush)
                    self.ui.tableWidget.setItem(i, 1, item)
                    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
                    brush.setStyle(QtCore.Qt.NoBrush)
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
                self.ui.tableWidget.setRowCount(0)
                geometry = self.ui.tableWidget.geometry()
                geometry.setHeight(41 * (len(self.arrPoint[self.count]) + 1))
                self.ui.tableWidget.setGeometry(geometry)
                self.ui.tableWidget.setRowCount(len(self.arrPoint[self.count]))
                for i in range(len(self.arrPoint[self.count])):
                    item = QtWidgets.QTableWidgetItem()
                    item.setText(self.markSet[self.colorArr[self.count][i]])
                    self.ui.tableWidget.setItem(i, 0, item)
                    item = QtWidgets.QTableWidgetItem()
                    brush = QtGui.QBrush(self.color[self.colorArr[self.count][i]])
                    brush.setStyle(QtCore.Qt.SolidPattern)
                    item.setBackground(brush)
                    self.ui.tableWidget.setItem(i, 1, item)
                    brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
                    brush.setStyle(QtCore.Qt.NoBrush)
                self.invFlag()
                self.setFlag()
                self.update()

    async def tryOpenFile(self):
        try:
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
        except:
            pass

    async def tryCountFile(self):
        count = 0
        self.ui.countMRT_.setText(f"Загрузилось {count} снимков")
        await asyncio.sleep(1)
        while count != self.countMRT:
            self.ui.countMRT_.setText(f"Загрузилось {count} снимков")
            count = self.countMRT
            await asyncio.sleep(1)

    def open_(self):
        self.dirlist = QFileDialog.getExistingDirectory(self, "Выбрать папку", ".")
        with open("История.txt", 'a', encoding="utf-8") as file:
            print(str(self.dirlist), file=file, sep='\n')
        if self.dirlist != '':

            open_ = [
                asyncio.ensure_future(self.tryCountFile()),
                asyncio.ensure_future(self.tryOpenFile())
                ]
            event_loop = asyncio.get_event_loop()
            event_loop.run_until_complete(asyncio.gather(*open_))
            try:
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

        qp.drawRect(size.width() // 2 - (512 // 2) - 10, (size.height() - 61) // 2 - (512 // 2) - 10, 532, 532)
        if self.drawMRT:
            k = 0
            self.tempfile = ''
            for fileName in os.listdir(self.newDirList):
                if k == self.count:
                    self.image = QImage(self.newDirList + '\\' + fileName)
                    rect = QRect(size.width() // 2 - (512 // 2), (size.height() - 61) // 2 - (512 // 2), 512, 512)
                    pixmap = QImage(self.newDirList + '\\' + fileName)
                    qp.drawImage(rect, pixmap)
                    self.tempfile = fileName
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
        qp.end()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    application = mywindow()

    sys.exit(app.exec())
