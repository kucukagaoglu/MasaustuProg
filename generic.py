#!/usr/bin/python
# -*- coding: UTF-8 -*-

import serial
import res
import sys
import time
from PyQt4 import QtCore, QtGui, uic
import psycopg2
import urllib



class Pencere(QtGui.QMainWindow):

        def __init__(self):

            super(Pencere, self).__init__()

            #self.initUI()

            self.i=0
    
            QtGui.QMainWindow.__init__(self)
            self.ui = uic.loadUi("generic.ui")
            self.ui.show()
            self.setMouseTracking(True)

           # self.connect(self.ui.pushButton_4, QtCore.SIGNAL("clicked()"), self.rfid01)
            #self.connect(self.ui.pushButton_5, QtCore.SIGNAL("clicked()"), self.rfid02)
            #self.connect(self.ui.pushButton_12, QtCore.SIGNAL("clicked()"), self.rfid02)
            #oself.connect(self.ui.label_26, QtCore.SIGNAL("clicked()"), self.rfid02)
           # self.connect(self.ui.btn_esle, QtCore.SIGNAL("clicked()"), self.eslesme_ekle)


            ###
            
            url = 'htr.png'
            data = urllib.urlopen(url).read()

            image = QtGui.QImage()
            image.loadFromData(data)

            self.ui.lbl.setPixmap(QtGui.QPixmap(image))


        def mousePressEvent(self, QMouseEvent):
            print QMouseEvent.pos()


        def mouseReleaseEvent(self, QMouseEvent):
            cursor =QtGui.QCursor()
            print cursor.pos()  


        def eslesme_ekle(self):


            sql1='insert into camera_rfid ("cameraId", "rfidId") values  ("DenemeCamera","DenemeRFID")' #("{0}","{1}")'.format(str(self.ui.lbl_secili.text),str(self.ui.comboBox.currentText()))
            self.cur.execute(sql1)
            self.conn.commit()
            #self.conn.close()
                    
        def rfid01(self):

            self.doldur()
            self.ui.lbl_secili.setText("RFID Reader-1")

        def rfid02(self):

            self.doldur()
            self.ui.lbl_secili.setText("RFID Reader-2")





        def doldur(self):

                                       
            self.conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.130' password='1'")
            self.cur = self.conn.cursor()

                 #conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.132' password='1'")
            
            self.sqll= 'Select "cameraId","cameraName","cameraIp" from "cameraInfo"'

            self.cur.execute(self.sqll)

            self.rows = self.cur.fetchall()

            for row in self.rows:
                
                self.ui.comboBox.addItem("Id:"+str(row[0])+"--Name:"+str(row[1])+"--IP:"+str(row[2]))

            print self.rows
            #conn.commit()
            #self.conn.close()






if __name__ == "__main__":
        app = QtGui.QApplication(sys.argv)
        win = Pencere()
        sys.exit(app.exec_())
