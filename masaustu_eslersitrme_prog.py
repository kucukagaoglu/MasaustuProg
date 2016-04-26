#!/usr/bin/python
# -*- coding: UTF-8 -*-

import res
import sys
import time
from PyQt4 import QtCore, QtGui, uic
import psycopg2
import urllib
import datetime
import string
#import pyqtgraph as pg
#from pyqtgraph.Qt import QtCore, QtGui
#import numpy as np

#-----GRAFİK KÜTÜPHANELERİ---------------
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.pyplot as plt
import random
#----------------------------------------
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

#--------------------
import vlc
#-------------------

import examples_qtvlc


class KameraEklemeDialog(QtGui.QDialog):

    def __init__(self,ebeveyn=None):

        QtGui.QWidget.__init__(self,ebeveyn)
        self.ui = uic.loadUi("kamera_yerlestir.ui",self)

        print "KAMERAA YELESTIIIIIIR!"

        # self.dbye_baglan()

        # self.sqll= 'Select "cameraId","cameraName","cameraIp" from "cameraInfo"'
        # self.cur.execute(self.sqll)
        # self.rows = self.cur.fetchall()
        # for row in self.rows:

        #     self.ui.comboBox.addItem(str(row[1]))



class MyPopupDialog(QtGui.QDialog):

    def __init__(self,ebeveyn=None):

        QtGui.QWidget.__init__(self,ebeveyn)
        self.ui = uic.loadUi("popup.ui",self)

        #--- DUGMELER AKSIYON VER---

        self.connect(self.ui.btn_kaydet,QtCore.SIGNAL("released()"),self.accept)
        self.connect(self.ui.btn_vazgec,QtCore.SIGNAL("released()"),self.reject)
#----------------------------------------------------------------------------------------------------
class Pencere(QtGui.QMainWindow):

        def __init__(self,ebeveyn=None):

            QtGui.QMainWindow.__init__(self, ebeveyn)
            #---- DEĞİŞKENLERİ İLK DEĞERLEME----
            self.buton_ismi=0
            self.i=0
            self.son_kayitli_kamera_id=0
            self.radiolar=["radio_hepsi","radio_personel","radio_bolum","radio_kamera","radio_okuyucu","radio_ziyaretci"]
            self.combolar=["cmb_personel","cmb_bolum","cmb_kamera","cmb_okuyucu","cmb_ziyaretci"]

            QtGui.QMainWindow.__init__(self)
            #self.ui = uic.loadUi("akilli_kart_.ui")
            self.ui = uic.loadUi("akilli_kart2.ui")
            self.ui.showFullScreen()
            self.ui.show()

            #------GÖMÜLÜ VLC PLAYER-----------

            self.instance2 = vlc.Instance()
            # creating an empty vlc media player
            self.mediaplayer = self.instance2.media_player_new()

            self.createUI()
            self.isPaused = False

            #self.OpenFile("rtsp://172.16.30.58/stream2")
            #---------------İSTATİSTİK TAB EVENT-LERİ------------------

            self.figure = plt.figure()

            # this is the Canvas Widget that displays the `figure`
            # it takes the `figure` instance as a parameter to __init__
            self.canvas = FigureCanvas(self.figure)
                    # this is the Navigation widget
            # it takes the Canvas widget and a parent
            self.toolbar = NavigationToolbar(self.canvas, self)

            # set the layout
            self.ui.verticalLayout_5.addWidget(self.toolbar)
            self.ui.verticalLayout_5.addWidget(self.canvas)
            self.setLayout(self.ui.verticalLayout_5)
            #self.istatistik_ciz()

            self.comboyu_degerle_doldur(self.ui.cmb_personel,'select isim from "personelList"')

            self.comboyu_degerle_doldur(self.ui.stats_combo,'select distinct isim from "personelList"')
            self.connect(self.ui.btn_stats,QtCore.SIGNAL("clicked()"),self.istatistik_ciz)

            #------timer kur----------------------------
            self.ctimer=QtCore.QTimer()
            self.ctimer.start(1000) #- 1 SANIYE
            #QObject.connect(self.ctimer.SIGNAL("timeout()"),self.dugmeye_basildi)
            self.ctimer.timeout.connect(self.hersaniye_son_giris_kontrolu)

            #----- CIKIS BUTONUNA ACTION---------
            self.connect(self.ui.btn_exit,QtCore.SIGNAL("clicked()"),lambda:sys.exit())
            self.connect(self.ui.btn_izle,QtCore.SIGNAL("clicked()"),self.izle)

            #-------HARİTA YÜKLEME BOTONUNA ACTİON BİLDİR-------------
            self.ui.btn_harita_yukle.clicked.connect(self.harita_yukle)


            #---------DB DEKİ SENSÖRLERİ YERLEŞTİR-----------------------------------------------------
            sensor_ismi=[]
            sensor_konumu=[]

            self.dbye_baglan()
            cumle='SELECT okuyucu_adi,konum FROM "rfidInfo" '
            self.cur.execute(cumle)
            sonuclar = self.cur.fetchall()

            for x in sonuclar:
                sensor_ismi.append(x[0])
                sensor_konumu.append(x[1])

                s_isim=x[0]
                s_x=x[1].split(',')[0]
                s_y=x[1].split(',')[1]

                # print "SECILIM:",s_isim
                if(s_isim[0:4]=="RFID"):
                    self.haritaya_sensor_ekleme(s_isim,int(s_x),int(s_y),"eski")
                elif(s_isim[0:4]=="CAM_"):
                    #-----KAMERA BUTONU OLUŞTUR-------------------
                    self.haritaya_kamera_ekleme(s_isim,int(s_x),int(s_y),"eski")

            # -------SEÇİLİ BUTONA OLAYLARI BAĞLA----------------------------
                secili = self.ui.findChild(QtGui.QPushButton, s_isim)

                #self.connect(secili_buton, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle(secili_buton.objectName()))
                #print "SECILI:",secili.objectName()

                secili.setMouseTracking(True)
                secili.installEventFilter(self)
                secili.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
                secili.customContextMenuRequested.connect(self.kaldir_context)

            # print "isim:",s_isim,", X:",s_x,",Y:",s_y
            # print "sensor isimleri",sensor_ismi
            # print "sensor konumlari",sensor_konumu

            # ---- RFID<-> KAMERA ESLESMELERI ICIN GEREKLI KODLAR...

            # self.connect(self.ui.RFID_001, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_001"))
            # self.connect(self.ui.RFID_002, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_002"))
            # self.connect(self.ui.RFID_003, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_003"))
            # self.connect(self.ui.RFID_004, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_004"))
            # self.connect(self.ui.RFID_005, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_005"))
            # self.connect(self.ui.RFID_006, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_006"))
            # self.connect(self.ui.RFID_007, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_007"))
            # self.connect(self.ui.RFID_008, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_008"))
            # self.connect(self.ui.RFID_009, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_009"))
            # self.connect(self.ui.RFID_010, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_010"))
            # self.connect(self.ui.RFID_011, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_011"))
            # self.connect(self.ui.RFID_012, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_012"))
            # self.connect(self.ui.RFID_013, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_013"))
            # self.connect(self.ui.RFID_014, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_014"))
            # self.connect(self.ui.RFID_015, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_015"))

            #----KAMERALARI ACAN KODLAR--------

            # self.connect(self.ui.btn_camera,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.59/stream1"))
            # self.connect(self.ui.btn_guv_oda,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.58/stream1"))
            # self.connect(self.ui.btn_kablo1,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.57/stream1"))
            # self.connect(self.ui.btn_kablo2,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.56/stream1"))
            # self.connect(self.ui.btn_kablo3,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.72/stream1"))
            # self.connect(self.ui.btn_kablaj_kalite,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.55/stream1"))
            # self.connect(self.ui.btn_uretim1,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.54/stream1"))
            # self.connect(self.ui.btn_depo1,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.130/stream1"))
            # self.connect(self.ui.btn_depo2,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.53/stream1"))
            # self.connect(self.ui.btn_idari1,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.63/stream1"))
            # self.connect(self.ui.btn_idari2,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.62/stream1"))
            # self.connect(self.ui.btn_lab,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.60/stream1"))
            # self.connect(self.ui.btn_uretim2,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.61/stream1"))
            # self.connect(self.ui.btn_giris,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.52/stream1"))
            # self.connect(self.ui.btn_cay,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.196/stream1"))
            # self.connect(self.ui.btn_turnike,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.47/stream1"))
            # self.connect(self.ui.btn_kose,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.49/stream1"))
            # self.connect(self.ui.btn_otopark,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.211/stream1"))
            # self.connect(self.ui.btn_yan,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.133/stream1"))
            # self.connect(self.ui.btn_yan,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.31/stream1"))
            # self.connect(self.ui.btn_otopark_2,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.64/stream1"))



            #----BUTUN TABLOLAR ICIN HUCRE DEGIL SATIR SECIMI YAPILSIN

            self.ui.tableWidget_5.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            self.ui.tableWidget_3.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            self.ui.tableWidget_4.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            self.ui.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

            #----RFID LOGLARDA ARAMA ISLEVI ICIN---------------------------------------------------------------------------------------------------------


            # self.arama_ekrani_sorgusu='SELECT rfid_logs.sicil,"personelList".isim,"personelList".bolum,rfid_logs.zaman, \
            #     rfid_logs.okuyucu,camera_rfid."cameraId" \
            #     FROM rfid_logs \
            #     INNER JOIN camera_rfid ON \
            #     (rfid_logs.okuyucu=camera_rfid."rfidId") \
            #     INNER JOIN "personelList" ON \
            #     ("personelList".sicil=rfid_logs.sicil)'




            self.connect(self.ui.btn_ara, QtCore.SIGNAL("clicked()"), lambda:self.ara(self.ui.tableWidget_5,self.ui.comboBox.currentText()))


            #----kamera LOGLARDA ARAMA ISLEVI ICIN

            self.connect(self.ui.btn_kamera_ara, QtCore.SIGNAL("clicked()"),lambda:self.ara(self.ui.tableWidget_3,"""SELECT * FROM "cameraInfo"
             WHERE "{1}" LIKE '%{0}%' """.format(self.ui.lineEdit_2.text(),self.ui.comboBox_2.currentText())))

            #------ eslesmelerde arama-------------------------------------------

            self.connect(self.ui.btn_eslesme_ara, QtCore.SIGNAL("clicked()"),lambda:self.ara(self.ui.tableWidget,"""SELECT idd,"rfidId","cameraId" FROM "camera_rfid"
             WHERE "{1}" LIKE '%{0}%' """.format(self.ui.lineEdit_3.text(),self.ui.comboBox_3.currentText())))

            #-------- RFID aygit ara------

            self.rfid_arama_cumlesi=""
            self.connect(self.ui.btn_rfid_ara, QtCore.SIGNAL("clicked()"),lambda:self.ara(self.ui.tableWidget_4,"""SELECT * FROM "rfidInfo"
             WHERE "{1}" LIKE '%{0}%' """.format(self.ui.lineEdit_4.text(),self.ui.comboBox_4.currentText())))

            #-----RFID<-> KAMERA ESLESMESINI SIL BUTONU İÇİN---------------------------

            self.connect(self.ui.btn_iptal, QtCore.SIGNAL("clicked()"), self.iptal)

           #-silindi self.connect(self.ui.btn_kaydet, QtCore.SIGNAL("clicked()"), self.eslesme_ekle)




#--------------------------------CONTEXT MENÜ -SENSÖR EKLEMEK İÇİN--------------------------------

            self.ui.label_11.setMouseTracking(True)
            self.ui.label_11.installEventFilter(self)
            self.ui.label_11.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.ui.label_11.customContextMenuRequested.connect(self.sensor_yerlestir)

            #-----SENSÖR EKLEME CONTEXT MENÜSÜ-----
            self.sensorEklemeMenusu=QtGui.QMenu(self)

            sensor_ekle = QtGui.QAction(QtGui.QIcon('292.png'), '&Sensor Ekle', self)
            sensor_ekle.setShortcut('Ctrl+S')
            sensor_ekle.setStatusTip('RFID Sensor Ekleme')
            sensor_ekle.triggered.connect(lambda: self.haritaya_sensor_ekleme(QtGui.QInputDialog.getText(self,
                'Input Dialog','Enter your name:')[0],self.pos.x(),self.pos.y(),"yeni"))
            self.sensorEklemeMenusu.addAction(sensor_ekle)

            # self.menu = QtGui.QMenu(self)
            # renameAction = QtGui.QAction('Rename', self)
            # renameAction.triggered.connect(self.renameSlot)
            # self.menu.addAction(renameAction)
            # add other required actions
            #----self.sensorEklemeMenusu.popup(QtGui.QCursor.pos())






            #-----KAMERA EKLEMEK İÇİN GEREKLİ KODLAR-------------

            kamera_ekle = QtGui.QAction(QtGui.QIcon('cam.png'), '&Kamera Ekle', self)
            kamera_ekle.setShortcut('Ctrl+K')
            kamera_ekle.setStatusTip('IP Kamera Ekleme')

            kamera_ekle.triggered.connect(lambda: self.kamera_yerlestir(self.pos.x(),self.pos.y()))

            self.sensorEklemeMenusu.addAction(kamera_ekle)

           #-----SUBMENU YE İHTİYAÇ KALMADI---------------
            # self.submenu = QtGui.QMenu(self.sensorEklemeMenusu)
            # self.submenu.setTitle("Kamera Ekle")
            # self.sensorEklemeMenusu.addMenu(self.submenu)
            # self.submenu.addAction(kamera_ekle)




            # create context menu



#--------------------------------CONTEXT MENÜ AMA KAYITLARDAN SENSÖR GÖSTERMEK İÇİN-------------------------------------------------------------------------------------------
            self.popMenu = QtGui.QMenu(self)


            haritada_goster = QtGui.QAction(QtGui.QIcon('map.png'), '&Haritada Goster', self)
            haritada_goster.setShortcut('Ctrl+H')
            haritada_goster.setStatusTip('Haritada göster')
            haritada_goster.triggered.connect(self.plan_tabini_sec)
            self.popMenu.addAction(haritada_goster)

            self.popMenu.addSeparator()

            exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
            exitAction.setShortcut('Ctrl+Q')
            exitAction.setStatusTip('Exit application')
            exitAction.triggered.connect(QtGui.qApp.quit)
            self.popMenu.addAction(exitAction)
            #self.popMenu.popup(QtGui.QCursor.pos())

            # self.menu = QtGui.QMenu(self)
            # renameAction = QtGui.QAction('Rename', self)
            # renameAction.triggered.connect(QtGui.qApp.quit)
            # self.menu.addAction(renameAction)
            # add other required actions
            #self.menu.popup(QtGui.QCursor.pos())

            self.kaldirMenu = QtGui.QMenu(self)

            self.silinecek_sensor=None
            sensor_yoket = QtGui.QAction(QtGui.QIcon('cancel.png'), '&Yok Et', self)
            sensor_yoket.setShortcut('Ctrl+Y')
            #sensor_yoket.setStatusTip('Haritada göster')
            sensor_yoket.triggered.connect(lambda: self.sensor_yoket(self.silinecek_sensor))
            self.kaldirMenu.addAction(sensor_yoket)

            self.kaldirMenu.addSeparator()

            exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
            exitAction.setShortcut('Ctrl+Q')
            exitAction.setStatusTip('Exit application')
            exitAction.triggered.connect(QtGui.qApp.quit)

            self.kaldirMenu.addAction(exitAction)


#-----------------------------RADİO BUTONLAR----------------------------------------------------------------------------------------------

            self.ui.radio_hepsi.toggled.connect(lambda:self.izleme_secimleri("hepsi"))
            self.ui.radio_personel.toggled.connect(lambda:self.izleme_secimleri("personel"))
            self.ui.radio_bolum.toggled.connect(lambda:self.izleme_secimleri("bolum"))
            self.ui.radio_kamera.toggled.connect(lambda:self.izleme_secimleri("kamera"))
            self.ui.radio_okuyucu.toggled.connect(lambda:self.izleme_secimleri("okuyucu"))
            self.ui.radio_ziyaretci.toggled.connect(lambda:self.izleme_secimleri("ziyaretci"))

            self.ui.radio_hepsi.setChecked(True) #-- hepsi default olarak sçeili olsun...
# ---------------------------------------------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------------------------------------------

# -------------İZLEME MENÜSÜNDEKİ COMBO LARI DOLDUR--------------------------------------------------------------------------

            self.comboyu_degerle_doldur(self.ui.cmb_personel,'select isim from "personelList"')
            self.comboyu_degerle_doldur(self.ui.cmb_bolum,'select distinct bolum from "personelList"')
            self.comboyu_degerle_doldur(self.ui.cmb_kamera,'select distinct "cameraId" from camera_rfid')
            self.comboyu_degerle_doldur(self.ui.cmb_okuyucu,'select distinct "rfidId" from camera_rfid')


# ----------------ÖN SEÇİMLER--------------------------------------------------------------------------------

            self.ui.lbl_izlenen.setText("Hepsi")
            self.w = None
            self.yukle()
            self.camerInfo_table_yukle()

            # ----RENK AYARLAMALARI--------------
            # self.ui.lbl_secili.setStyleSheet('color: red')
            #url = 'htr.png'
            #data = urllib.urlopen(url).read()
            #image = QtGui.QImage()
            #image.loadFromData(data)
            #self.ui.lbl.setPixmap(QtGui.QPixmap(image))
            #####
# ---------------------MENU-BAR---GEREK KALMADI TAM EKRANIN ESTETĞİNİ BOZACAK YOKSA--------------------------------------------------------------------------------
            # exittAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
            # exittAction.setShortcut('Ctrl+Q')
            # exittAction.setStatusTip('Exit application')
            # exittAction.triggered.connect(QtGui.qApp.quit)
            # self.statusBar()
            # menubar = self.menuBar()
            # fileMenu = menubar.addMenu('&File')
            # fileMenu.addAction(exittAction)
            # set button context menu policy

            # self.ui.button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            # self.ui.button.customContextMenuRequested.connect(self.kaldir_context)
            # self.ui.button.clicked.connect(self.buttonClicked)

        def buttonClicked(self):
            buttonHandle = self.sender().objectName()
            print "BUTON->",buttonHandle

        def haritaya_sensor_ekleme(self,isim,x,y,kaynak):

            #---BUTONUN FİZİKSEL ÖZELLİKLERİ--------------------
            icon1 = QtGui.QIcon()
            icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/w/292.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.btn = QtGui.QPushButton(self.ui.groupBox_7)
            self.ui.btn.setGeometry(QtCore.QRect(720, 580, 21, 21))
            self.ui.btn.setStyleSheet(_fromUtf8("border-radius: 10px;"))
            self.ui.btn.setIcon(icon1)
            self.ui.btn.setIconSize(QtCore.QSize(32, 32))
            self.ui.btn.setAutoDefault(True)
            self.ui.btn.setDefault(True)
            self.ui.btn.setFlat(False)
            #-------İSMİ SOR KULLANICIYA--------------------
            #self.buton_ismi= QtGui.QInputDialog.getText(self, 'Input Dialog','Enter your name:')[0]
            #-------BUTONA OLAYLARI BAĞLA-------------------
            #self.ui.btn.setObjectName(self.buton_ismi)

            #------------------------------------------------
            if(kaynak=="yeni"):
                isim="RFID_"+isim
            #------------------------------------------------

            self.ui.btn.setObjectName(isim)
            self.ui.btn.move(x,y)
            self.ui.btn.setToolTip(self.ui.btn.objectName())
            secili_buton = self.ui.findChild(QtGui.QPushButton, self.ui.btn.objectName())
            #self.connect(secili_buton,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://172.16.30.64/stream1"))
            self.connect(secili_buton, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle(secili_buton.objectName()))
            self.ui.btn.show()

            # ------YENİ EKLENENE DE SAĞ TIK MENÜYÜ GETİRİ ----------

            secili_buton = self.ui.findChild(QtGui.QPushButton, isim)
            secili_buton.setMouseTracking(True)
            secili_buton.installEventFilter(self)
            secili_buton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            secili_buton.customContextMenuRequested.connect(self.kaldir_context)


            #-------YENİ OKUYUCUYSA VERİ TABANINA İŞLE-----------------

            if(kaynak=="yeni"):
                self.dbye_baglan()
                konum=str(x)+","+str(y)

                #sql1="""insert into "rfidInfo" (okuyucu_adi,konum) values ('{0}','{1}') """.format(self.buton_ismi,konum)
                sql1="""insert into "rfidInfo" (okuyucu_adi,konum) values ('{0}','{1}') """.format(isim,konum)

                self.cur.execute(sql1)
                self.conn.commit()





             #   print "SENSOR OLUSTURULDUUUU"
            else:
             pass
            #   print "SENSOR EKLENDIIII"

            #layout.removeWidget(self.widget_name)

#-------------SENSÖR SİLER--------------------
            #self.ui.RFID_001.deleteLater()
            #self.ui.RFID_001 = None


        def haritaya_kamera_ekleme(self,isim,x,y,kaynak):

            #---BUTONUN FİZİKSEL ÖZELLİKLERİ--------------------
            self.ui.btn = QtGui.QPushButton(self.ui.groupBox_7)
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/w/cam.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.btn.setIcon(icon2)
            self.ui.btn.setIconSize(QtCore.QSize(32, 32))


            self.ui.btn.setGeometry(QtCore.QRect(100, 160, 31, 31))
            self.ui.btn.setStyleSheet(_fromUtf8(""))
            self.ui.btn.setText(_fromUtf8(""))

            # -------İSMİ COMBOBOX'TAN SEÇİLEN YAZI OLSUN--------------------

            if(kaynak=="yeni"):
                isim="CAM_"+isim

            self.ui.btn.setObjectName(isim)

            # -------BUTONA OLAYLARI BAĞLA-------------------
            self.ui.btn.move(x,y)
            self.ui.btn.setToolTip(self.ui.btn.objectName())
            secili_buton = self.ui.findChild(QtGui.QPushButton, self.ui.btn.objectName())

            # ----ÖNCE DB'DEN IP ADRESİNİ ÇEK, BUNUN İÇİN İSMİ KULLAN!
            # -----KAMERA AÇMA FONKSİYONUNU EKLE-------------

            self.ui.btn.show()

            # ------YENİ EKLENENE DE SAĞ TIK MENÜYÜ GETİRİ ----------

            secili_buton = self.ui.findChild(QtGui.QPushButton, isim)
            secili_buton.setMouseTracking(True)
            secili_buton.installEventFilter(self)
            secili_buton.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            secili_buton.customContextMenuRequested.connect(self.kaldir_context)
            # --------------------------------------------------------



            self.dbye_baglan()
            self.cur.execute("""SELECT "cameraIp" FROM "cameraInfo" WHERE "cameraName"='%s' """%isim[4:])
            ip=self.cur.fetchone()[0]
            # print "**************CAM:",isim[4:],"IP:",ip
            secili_buton = self.ui.findChild(QtGui.QPushButton,isim)
            self.connect(secili_buton,QtCore.SIGNAL("clicked()"),lambda:self.kamera_ac("rtsp://"+ip+"/stream1"))

            # -------YENİ OKUYUCUYSA VERİ TABANINA İŞLE-----------------

            if(kaynak=="yeni"):

                #isim="CAM_"+isim
                self.dbye_baglan()
                konum=str(x)+","+str(y)

                #sql1="""insert into "rfidInfo" (okuyucu_adi,konum) values ('{0}','{1}') """.format(self.buton_ismi,konum)
                sql1="""insert into "rfidInfo" (okuyucu_adi,konum) values ('{0}','{1}') """.format(isim,konum)

                self.cur.execute(sql1)
                self.conn.commit()


                print "KAMAERAAA INSERTED"
                self.ky.close()
            else:
                pass

             #   print "KKKK"
            #layout.removeWidget(self.widget_name)

# -------------SENSÖR SİLER--------------------
            #self.ui.RFID_001.deleteLater()
            #self.ui.RFID_001 = None

        def harita_yukle(self):

            filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File', '', 'Images (*.png *.xpm *.jpg)')
                #self.myTextBox.setText(fileName)

            print "-->",filename
            self.ui.label_11.setPixmap(QtGui.QPixmap(filename))#.scaled(500,400))


        def izle(self):

            #-- öncelikle hangi radio seçilmiş onu bulalım....
            for i in range(0,len(self.radiolar)):
                selected_radio = self.ui.findChild(QtGui.QRadioButton, self.radiolar[i])
                if selected_radio.isChecked():
                    print selected_radio.objectName() + " secili"
                    secili_radio=selected_radio.objectName()[6:]

            #--- simdi de secili olan combo_box bulunsum

                for i in range(0,len(self.combolar)):
                    selected_combo = self.ui.findChild(QtGui.QComboBox, self.combolar[i])
                    if selected_combo.isEnabled():
                        print selected_combo.objectName() + " ######## secili"
                        secili_combo=selected_combo.currentText()

            self.ui.lbl_izlenen.setText(secili_combo)

            if(self.ui.radio_hepsi.isChecked()):
                self.ui.lbl_izlenen.setText("Hepsi")

        def clearLayout(self, layout):

            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)

                if isinstance(item, QtGui.QWidgetItem):
                    print "widget" + str(item)
                    item.widget().close()
                    # or
                    # item.widget().setParent(None)
                elif isinstance(item, QtGui.QSpacerItem):
                    print "spacer " + str(item)
                    # no need to do extra stuff
                else:
                    print "layout " + str(item)
                    self.clearLayout(item.layout())

                # remove the item from layout
                layout.removeItem(item)

        def istatistik_ciz(self):

            self.clearLayout(self.ui.verticalLayout_5)
            #---------------------------------------------
            self.figure = plt.figure()

            # this is the Canvas Widget that displays the `figure`
            # it takes the `figure` instance as a parameter to __init__
            self.canvas = FigureCanvas(self.figure)
                    # this is the Navigation widget
            # it takes the Canvas widget and a parent
            self.toolbar = NavigationToolbar(self.canvas, self)

            # set the layout
            self.ui.verticalLayout_5.addWidget(self.toolbar)
            self.ui.verticalLayout_5.addWidget(self.canvas)
            self.setLayout(self.ui.verticalLayout_5)

            #SELECT okuyucu,COUNT(okuyucu) FROM rfid_logs WHERE sicil='234' GROUP BY(okuyucu) ORDER BY COUNT(okuyucu) DESC;

            yatay=[]
            dusey=[]
            self.dbye_baglan()

            self.cur.execute("""SELECT sicil FROM "personelList" WHERE isim= '{0}' """.format(self.ui.stats_combo.currentText()))
            sicili=self.cur.fetchone()[0]

            combo=str(self.ui.stats_combo.currentText())

            if(not combo):
                 combo=random.choice(["397","234","390"])

            self.arama_ekrani_sorgusu="""SELECT camera_rfid."cameraId",COUNT(camera_rfid."cameraId")  \
                FROM rfid_logs \
                INNER JOIN camera_rfid ON \
                (rfid_logs.okuyucu=camera_rfid."rfidId") \
                INNER JOIN "personelList" ON \
                ("personelList".sicil=rfid_logs.sicil) \
                WHERE "personelList"."sicil"='{0}' GROUP BY(camera_rfid."cameraId") """.format(sicili)

            #sqll= "SELECT okuyucu,COUNT(okuyucu) FROM rfid_logs WHERE sicil='397' GROUP BY(okuyucu) ORDER BY COUNT(okuyucu) DESC"

            self.cur.execute(self.arama_ekrani_sorgusu)

            sonuclar = self.cur.fetchall()

            for x in sonuclar:
                #print x[0],"<->",x[1]
                yatay.append(x[1])
                dusey.append(x[0])

            print "YATAY-",yatay, "-DÜŞEY-",dusey
            print "C:",combo
            print self.arama_ekrani_sorgusu


            # Data to plot
            labels = 'Python', 'C++', 'Ruby', 'Java'
            sizes = [115, 130, 245, 210]
            #colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
            #explode = (0.5, 0, 0, 0)  # explode 1st slice-PATLAT DIŞA DOĞRU

            # Plot
            #plt.pie(sizes, explode=explode, labels=labels, colors=colors,autopct='%1.1f%%', shadow=True, startangle=140)
            plt.pie(yatay, labels=dusey,autopct='%1.1f%%', shadow=True, startangle=90)

            #plt.title('Raining Hogs and Dogs', bbox={'facecolor':'0.8', 'pad':5})
            isim=self.ui.stats_combo.currentText()
            plt.title(isim, bbox={'facecolor':'0.6', 'pad':1})

            plt.axis('equal')
           #  plt.show()

            # #------------------------------------------
            # data = [random.random() for i in range(10)]

            # # create an axis
            # ax = self.figure.add_subplot(111)

            # # discards the old graph
            # ax.hold(False)

            # # plot data
            # ax.plot(data, '*-')

            # # refresh canvas
            # self.canvas.draw()


        def izleme_secimleri(self,secim):

            self.ui.cmb_personel.setEnabled(False)
            self.ui.cmb_bolum.setEnabled(False)
            self.ui.cmb_kamera.setEnabled(False)
            self.ui.cmb_okuyucu.setEnabled(False)
            self.ui.cmb_ziyaretci.setEnabled(False)

            if(secim=="hepsi"):
                pass
            elif(secim=="personel"):
                self.ui.cmb_personel.setEnabled(True)
            elif(secim=="bolum"):
                self.ui.cmb_bolum.setEnabled(True)
            elif(secim=="kamera"):
                self.ui.cmb_kamera.setEnabled(True)
            elif(secim=="okuyucu"):
                self.ui.cmb_okuyucu.setEnabled(True)
            elif(secim=="ziyaretci"):
                self.ui.cmb_ziyaretci.setEnabled(True)




        def OpenFile(self, filename=None):

            """Open a media file in a MediaPlayer
            """
            if filename is None:
                filename = QtGui.QFileDialog.getOpenFileName(self, "Open File", os.path.expanduser('~'))
            if not filename:
                return

            # create the media
            if sys.version < '3':
                filename = unicode(filename)
            self.media = self.instance2.media_new(filename)
            # put the media in the media player
            self.mediaplayer.set_media(self.media)

            # parse the metadata of the file
            self.media.parse()
            # set the title of the track as window title
            self.setWindowTitle(self.media.get_meta(0))

            # the media player has to be 'connected' to the QFrame
            # (otherwise a video would be displayed in it's own window)
            # this is platform specific!
            # you have to give the id of the QFrame (or similar object) to
            # vlc, different platforms have different functions for this
            if sys.platform.startswith('linux'): # for Linux using the X Server
                self.mediaplayer.set_xwindow(self.videoframe.winId())
            elif sys.platform == "win32": # for Windows
                self.mediaplayer.set_hwnd(self.videoframe.winId())
            elif sys.platform == "darwin": # for MacOS
                self.mediaplayer.set_nsobject(self.videoframe.winId())
            self.PlayPause()

        def PlayPause(self):
            """Toggle play/pause status
            """
            if self.mediaplayer.is_playing():
                self.mediaplayer.pause()

                self.isPaused = True
            else:
                if self.mediaplayer.play() == -1:
                    self.OpenFile()
                    return
                self.mediaplayer.play()

                #self.timer.start()
                self.isPaused = False

        def createUI(self):
            """Set up the user interface, signals & slots
            """
            self.widget = QtGui.QWidget(self)
            self.setCentralWidget(self.widget)

            self.videoframe = self.ui.frame
            self.palette = self.videoframe.palette()
            self.palette.setColor (QtGui.QPalette.Window,
                                   QtGui.QColor(0,0,0))
            self.videoframe.setPalette(self.palette)
            self.videoframe.setAutoFillBackground(True)


        def dbye_baglan(self):

            #self.conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.129' password='1'")
            try:
                self.conn = psycopg2.connect("dbname='vays_db' user='postgres' host='localhost' password='1'")
                self.cur = self.conn.cursor()
            except:
                print "Veritabanina baglanilamadi..."
            #self.sqll= 'Select * from "camera_rfid"'

        def kamera_ac(self,stream):

            try:
                self.media_player=examples_qtvlc.Player()#"rtsp://172.16.30.72/stream1"
                #self.media_player.setWindowFlags(QtCore.Qt.FramelessWindowHint)
                self.media_player.show()
                self.media_player.resize(320, 240)
                self.media_player.move(1040, 350)
                self.media_player.OpenFile(stream)
               # self.media_player.play()
            except:
                print "KAMERA ACILAMIYOR"



        def okuyucudan_otomatik_kamera_ac(self, okuyucu):

            self.dbye_baglan()


            cumle="""SELECT camera_rfid."cameraId","cameraInfo"."cameraIp"
             FROM camera_rfid 
             INNER JOIN "cameraInfo" 
             ON (camera_rfid."cameraId" = "cameraInfo"."cameraName") 
             WHERE camera_rfid."rfidId" = '{0}'
             """.format(okuyucu)


            #cumle = """SELECT "cameraId" FROM "camera_rfid" WHERE "rfidId"= '{}' """.format(okuyucu)
            self.cur.execute(cumle)
            son_cameranin_ip = self.cur.fetchone()[1]

            if(son_cameranin_ip==self.son_kayitli_kamera_id): #--- zaten aciksa bir daha tetikleme
                pass
            else:
                try:
                    self.son_kayitli_kamera_id=son_cameranin_ip #--- yeniyi en son kayıtlı olarak kaydet
                    self.OpenFile("rtsp://"+son_cameranin_ip+"/stream1") #--- bu cumlecik olmadan vlc görüntü açmaz....
                except:
                    self.ui.lbl_durum.setText("KAMERALARA BAGLANILAMIYOR!")

            return son_cameranin_ip


        def hersaniye_son_giris_kontrolu(self):  #----DİKKAT BU PROGRAM SANİYEDE BİR ÇALIŞIR!!!!


            #--- burada sadece db-den son saitr cekilmekte...
            cumle="""SELECT rfid_logs.sicil,rfid_logs.okuyucu,camera_rfid."cameraId"
             FROM rfid_logs 
             INNER JOIN camera_rfid 
             ON (rfid_logs.okuyucu=camera_rfid."rfidId") 
             WHERE rfid_logs.id= (SELECT MAX(id)  FROM rfid_logs)
             """
            self.dbye_baglan()
            #cumle = "SELECT * FROM rfid_logs WHERE id= (SELECT MAX(id)  FROM rfid_logs)"

            self.cur.execute(cumle)
            self.son_log = self.cur.fetchone()

            #print ">>>>>---",self.son_log

            #print "**SON KAYIT**",self.son_log

            son_sicil=self.son_log[0]
            son_okuyucu=self.son_log[1]
            son_kamera=self.son_log[2]

            #---SADECE SİCİL SÖYLEYİP İSİM ALMAK İÇİN------------
            self.cur.execute("""SELECT isim,bolum FROM "personelList" WHERE sicil='{}' """.format(son_sicil))
            sonuc=self.cur.fetchone()
            son_kisi=sonuc[0]
            son_bolum=sonuc[1]

            self.son_log+=(son_kisi,son_bolum,) #-- alttaki aramada isimden de bulunabilsin, yoksa sadece sicil, okuyucu ve kamera olacak....
            #print "Son LOG->",self.son_log
           # print "LBL_SECILI->" ,self.ui.lbl_izlenen.text()

            try:

                if ((self.ui.lbl_izlenen.text() in self.son_log) or (self.ui.radio_hepsi.isChecked())): #---izlenene alinan şey(isim, kamera, okuycu felan)! kelime son log da yer almaktaysa!!!

            #------ ARTIK ALARM OLUŞTU! KAMERAYI AÇ VE YAKALANAN KISMINDAKİ LAYER-LARI RENKLENDİR!!!

                    #self.etiketi_kirmizi_yap()
                    self.ui.lbl_canli_kisi.setText(son_sicil+"-"+son_kisi)
                    self.ui.lbl_canli_okuyucu.setText(son_okuyucu)
                    self.ui.lbl_canli_kamera.setText(son_kamera)
                    self.okuyucudan_otomatik_kamera_ac(self.son_log[1]) #-----kamerayı açmak için
            #-------- ARTIK ALARM, ICONU BLINK ETTİREBİLİRSİN!-----------------------------------
                    self.secilme_zamani=round(time.time())
                    self.icon_blink(self.secilme_zamani,son_okuyucu) #---imleci degistirmek için
            #----------------------------------------------------------------------------------------------------------------------------------------------------
                else:
                    #self.etiketi_siyah_yap()
                    pass

            except:
                "KAMERA ACILAMIYOR!!!"
#-------------------------------------------------------------------------------------



            #----tarih ve saat daha özenli-----
            format = "%a %b %d  %Y, %H:%M:%S"
            self.simdi = datetime.datetime.today().strftime(format)



            self.ui.lbl_canli_zaman.setText(self.simdi)


        def etiketi_kirmizi_yap(self):

            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.red)
            self.ui.lbl_canli_kisi.setPalette(palette)

        def etiketi_siyah_yap(self):
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground,QtCore.Qt.black)
            self.ui.lbl_canli_kisi.setPalette(palette)


        def icon_blink(self,ilk_zaman,okuyucu):

             #print "saniye bi aktif"
            self.butonlari_normalle()
            #---tetik
            secili_buton = self.ui.findChild(QtGui.QPushButton, okuyucu)


            if(round(time.time())-ilk_zaman <10):
                if(round(time.time())%2):
                    #self.ui.RFID_001.setIcon(QtGui.QIcon(QtGui.QPixmap("red.png")))
                    secili_buton.setIcon(QtGui.QIcon(QtGui.QPixmap("target_gray.png")))
                else:
                    #self.ui.RFID_001.setIcon(QtGui.QIcon(QtGui.QPixmap("yellow.png")))
                    secili_buton.setIcon(QtGui.QIcon(QtGui.QPixmap("target_red2.png")))
            else:
                secili_buton.setIcon(QtGui.QIcon(QtGui.QPixmap("292.png")))
                self.ctimer.stop()

        def plan_tabini_sec(self):
            #self.poi=str(self.ui.tableWidget_5.currentItem().text())
            #print "POI->",self.poi

            secili_satir=self.ui.tableWidget_5.currentRow()

            secili_okuyucu=self.ui.tableWidget_5.item(secili_satir,2).text()

            #print "ROW->",secili_satir,type(secili_satir)

            print "OKUYUCU>",secili_okuyucu

            #---butonun icon unu degistir.
            #-- COK AMELE BI YONTEM------------------

            #self.icon_degistir(secili_okuyucu,QtGui.QPixmap("yellow.png"))

            #--- YANIP SONME ISLEMI BURADA YAPILACAK!!!

            self.ctimer=QtCore.QTimer()
            self.ctimer.start(1000) #- 1 SANIYE
            #QObject.connect(self.ctimer.SIGNAL("timeout()"),self.dugmeye_basildi)
            self.secilme_zamani=round(time.time())
            self.ctimer.timeout.connect(lambda: self.icon_blink(self.secilme_zamani,secili_okuyucu))

            #--- YANIP SONME ISLEMI BURADA YAPILACAK----
            self.ui.tabWidget.setCurrentIndex(0)

        def butonlari_normalle(self):

            buts = self.ui.findChildren(QtGui.QPushButton) #--self.ui deki tum butonları cek...

            for but in buts:
                #--- tum buton iconlarini default a cek
                if(but.objectName()[0:4]=="RFID"): #-- sadece plan sayfasindaki butonlarin iconlari degissin
                    secili_buton = self.ui.findChild(QtGui.QPushButton, but.objectName())
                    secili_buton.setIcon(QtGui.QIcon(QtGui.QPixmap("292.png")))


        def icon_degistir(self,secili_okuyucu,rMyIcon):

            buts = self.ui.findChildren(QtGui.QPushButton) #--self.ui deki tum butonları cek...

            for but in buts:
                #--- tum buton iconlarini default a cek
                if(but.objectName()[0:4]=="RFID"): #-- sadece plan sayfasindaki butonlarin iconlari degissin
                    secili_buton = self.ui.findChild(QtGui.QPushButton, but.objectName())
                    secili_buton.setIcon(QtGui.QIcon(QtGui.QPixmap("292.png")))

                #--yedi:)) print but.objectName()
                #--yedi:)) print "->>>>",but.objectName()[0:4]

            #---- secili btonunun iconunu secili konuma getir...
            secili_buton = self.ui.findChild(QtGui.QPushButton, secili_okuyucu)
            secili_buton.setIcon(QtGui.QIcon(rMyIcon))

            #----------------------------

        def ara(self,table,sorgu_cumlesi):

            #sorgu_cumlesi="""Select * from "rfid_logs" where {1} like '%{0}%' """.format(self.ui.lineEdit.text(),self.ui.comboBox.currentText())

            if sorgu_cumlesi in ["sicil","okuyucu","zaman"]:

                self.arama_ekrani_sorgusu="""SELECT rfid_logs.sicil,"personelList".isim,"personelList".bolum,rfid_logs.zaman, \
                rfid_logs.okuyucu,camera_rfid."cameraId" \
                FROM rfid_logs \
                INNER JOIN camera_rfid ON \
                (rfid_logs.okuyucu=camera_rfid."rfidId") \
                INNER JOIN "personelList" ON \
                ("personelList".sicil=rfid_logs.sicil)\
                WHERE "rfid_logs"."{1}" LIKE '%{0}%' """.format(self.ui.lineEdit.text(),self.ui.comboBox.currentText())

            else:

                self.arama_ekrani_sorgusu="""SELECT rfid_logs.sicil,"personelList".isim,"personelList".bolum,rfid_logs.zaman, \
                rfid_logs.okuyucu,camera_rfid."cameraId" \
                FROM rfid_logs \
                INNER JOIN camera_rfid ON \
                (rfid_logs.okuyucu=camera_rfid."rfidId") \
                INNER JOIN "personelList" ON \
                ("personelList".sicil=rfid_logs.sicil)\
                WHERE "camera_rfid"."{1}" LIKE '%{0}%' """.format(self.ui.lineEdit.text(),self.ui.comboBox.currentText())






            self.table_yukle(self.ui.tableWidget_5,self.arama_ekrani_sorgusu+'ORDER BY rfid_logs.id DESC')


            print "combo->",str(self.ui.comboBox.currentText()),type(str(self.ui.comboBox.currentText()))
            print "edit->",self.ui.lineEdit.text(),type(self.ui.lineEdit.text())

            sorgu_cumlesi2="""SELECT rfid_logs.sicil,rfid_logs.zaman,rfid_logs.okuyucu,camera_rfid."cameraId"
             FROM rfid_logs 
             INNER JOIN camera_rfid 
             ON (rfid_logs.okuyucu=camera_rfid."rfidId") 
             WHERE "{1}" like '%{0}%'
             """.format(self.ui.lineEdit.text(),self.ui.comboBox.currentText())

            #sorgu_cumlesi= 'SELECT * FROM rfid_logs INNER JOIN camera_rfid ON (rfid_logs.okuyucu=camera_rfid."rfidId")'


            self.dbye_baglan()
            #self.sqll= 'Select * from "camera_rfid"'
            self.sqll=sorgu_cumlesi
            self.cur.execute(sorgu_cumlesi)
            #curs.execute("Select * FROM people")
            colnames = [desc[0] for desc in self.cur.description]
            #print sorgu_cumlesi+" icin kolon isimleri: ", colnames
            self.rows = self.cur.fetchall()

            print (sorgu_cumlesi)

            satir_sayisi=len(self.rows)
            kolon_sayisi=len(colnames)

         #--- TABLO ISLEMLERI-------------
            #self.ui.tableWidget.setRowCount(n)
            table.setRowCount(satir_sayisi)
            table.setColumnCount(kolon_sayisi)
            table.verticalHeader().hide();
            table.horizontalHeader().setStretchLastSection(True)

            colnames=';'.join(colnames)
            table.setHorizontalHeaderLabels(QtCore.QString(colnames).split(';'))

            for row in range(satir_sayisi):
                for column in range(kolon_sayisi):
                    table.setItem(row,column,QtGui.QTableWidgetItem(str(self.rows[row][column])))


        def kamera_olustur(self):
            pass

        def kamera_yerlestir(self,x,y):

            self.ky=KameraEklemeDialog()
            self.comboyu_degerle_doldur(self.ky.cmb_kameralar,'SELECT "cameraName" FROM "cameraInfo"')
            self.ky.show()

            self.ky.btn_kamera_ekle.clicked.connect(lambda: self.haritaya_kamera_ekleme(self.ky.cmb_kameralar.currentText(),x,y,"yeni"))




        def rfid_esle(self,giris):

            self.yenipopup=MyPopupDialog()
            self.yenipopup.lbl_secili.setText(giris)

            #-----SECİLİ SENSÖRÜ BUL VE YOK ET---------------------------
            secili_sensor=self.ui.findChild(QtGui.QPushButton, giris)
            self.yenipopup.btn_yoket.clicked.connect(lambda: self.sensor_yoket(secili_sensor))

            self.connect(self.yenipopup.btn_sil, QtCore.SIGNAL("clicked()"), self.iptal)

            self.comboyu_degerle_doldur(self.yenipopup.comboBox,'SELECT "cameraName" FROM "cameraInfo"')

           # cumle="""SELECT * FROM "camera_rfid" WHERE "rfidId" LIKE '{}'""".format(giris)
            self.table_yukle(self.yenipopup.tableWidget,"""SELECT idd,"rfidId","cameraId" FROM "camera_rfid" WHERE "rfidId" LIKE '{}'""".format(giris))#+giris)
            self.yenipopup.tableWidget.horizontalHeader().setStretchLastSection(True)

            if self.yenipopup.exec_():

                sql1="""insert into camera_rfid ("cameraId", "rfidId") values ('{1}','{0}')""" .format(str(self.yenipopup.lbl_secili.text()),str(self.yenipopup.comboBox.currentText()))
                self.cur.execute(sql1)
                self.conn.commit()

                self.yukle()

                print giris, "ile", self.yenipopup.comboBox.currentText()," eslestirildi!"

        def sensor_yoket(self,buton):

        #-----sensörü db 'den silme----------------------------
            buton=self.silinecek_sensor
            self.dbye_baglan()
            self.cur.execute("""DELETE from "rfidInfo" where okuyucu_adi='{0}' """.format(buton.objectName()))
            self.conn.commit()
        #------------------------------------------------------

            buton.deleteLater()
            buton = None
            # self.yenipopup.close() -- context ten silince hata verdirmekte


        def test0(self):
            print ("test0 secildi")
            print ("******************************************************")


        def on_context_menu(self, point):
        # show context menu
            self.popMenu.exec_(self.ui.groupBox_7.mapToGlobal(point))

        def kaldir_context(self):

            #self.kaldirMenu.exec_(self.ui.label_11.mapToGlobal(point))
            #self.kaldirMenu.exec_(self.ui.label_11.mapToGlobal(self.pos))
            sensor_adi=str(self.sender().objectName())
            self.silinecek_sensor=self.ui.findChild(QtGui.QPushButton, sensor_adi)
            print ("ON CONTEXT->", sensor_adi)
            self.kaldirMenu.exec_(QtGui.QCursor.pos())


        def sensor_yerlestir(self,point):

            self.sensorEklemeMenusu.exec_(self.ui.label_11.mapToGlobal(point)) # point ile gosterilen kısımda context menu acar!
            print ("Sensor Yerlesir metodu....")
           #pass

        def eventFilter(self, source, event):

            if (event.type() == QtCore.QEvent.MouseMove and source is self.ui.label_11):# or self.ui.groupBox_7):
                self.pos = event.pos()
            #   print('mouse move: (%d, %d)' % (self.pos.x(), self.pos.y()))

            return QtGui.QWidget.eventFilter(self, source, event)

        def camerInfo_table_yukle(self):
            pass

        def iptal(self):

            #satir=str(self.ui.listWidget.currentItem().text())
            if self.ui.tableWidget.currentItem():
                satir=str(self.ui.tableWidget.currentItem().text())
            else:
                satir=str(self.yenipopup.tableWidget.currentItem().text())
            #satir=str(self.ui.tableWidget.currentItem().row())
            degerler=satir.split()

            print degerler

            self.ui.label_30.setText(degerler[0])

#            self.ui.tableWidget.setCurrentIndex(int(degerler[0]))

            #self.ui.listWidget.clear()
            self.dbye_baglan()

            #self.cur.execute("""DELETE from camera_rfid where idd={0}""".format(str(self.ui.label_30.text())))
            #-- bu daha global
            self.cur.execute("""DELETE from camera_rfid where idd={0}""".format(str(degerler[0])))

            print type(degerler[0])

            self.conn.commit()

            self.yukle()

            self.table_yukle(self.yenipopup.tableWidget,"""SELECT * FROM "camera_rfid" WHERE "rfidId" LIKE '{}'""".format(self.yenipopup.lbl_secili.text()))#+giris)
                 #conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.132' password='1'")

            #self.sqll= 'Select * from "camera_rfid"'


        def table_yukle(self,table,sorgu_cumlesi):

            #self.ui.tableWidget.setHorizontalHeaderLabels("1")
            #self.ui.tableWidget.setWindowTitle("QTableWidget Example @pythonspot.com")


            #--- DATABSE ISLEMLERI-------
            self.dbye_baglan()
            #self.sqll= 'Select * from "camera_rfid"'
            self.sqll=sorgu_cumlesi
            self.cur.execute(self.sqll)
            #curs.execute("Select * FROM people")
            colnames = [desc[0] for desc in self.cur.description]
           # print sorgu_cumlesi+" icin kolon isimleri: ", colnames
            self.rows = self.cur.fetchall()


            satir_sayisi=len(self.rows)
            kolon_sayisi=len(colnames)



            #--- TABLO ISLEMLERI-------------
            #self.ui.tableWidget.setRowCount(n)
            table.setRowCount(satir_sayisi)
            table.setColumnCount(kolon_sayisi)
            table.verticalHeader().hide();
            #table.setHorizontalHeaderLabels(QtCore.QString("ID;RFID;KAMERA").split(";"))

            #print type(colnames),"KOLONLAR::", colnames

            #print type(colnames),"KOLONLAR:::", colnames
            colnames=';'.join(colnames)
            table.setHorizontalHeaderLabels(QtCore.QString(colnames).split(';'))
            #self.ui.tableWidget.resize(400, 100);
            #self.ui.tableWidget.resizeRowsToContents(200);
            #self.ui.tableWidget.resizeColumnsToContents();

            #table.setColumnWidth(0, 50);
            #table.setColumnWidth(1, 130);
            #table.setColumnWidth(2, 230);

            for row in range(satir_sayisi):
                for column in range(kolon_sayisi):
                    table.setItem(row,column,QtGui.QTableWidgetItem(str(self.rows[row][column])))

            #---- EN SON BASLIGI YAY!
            table.horizontalHeader().setStretchLastSection(True)



        def yukle(self):
#------------LISTWIDGET ICIN------------------
            #self.ui.listWidget.clear()
            #self.conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.130' password='1'")
            #self.cur = self.conn.cursor()
            #self.sqll= 'Select * from "camera_rfid"'
            #self.cur.execute(self.sqll)
            #self.rows = self.cur.fetchall()
            #self.ui.listWidget.addItem("<Id>...<RFID Reader>...<IP Kamera>")
            #for row in self.rows:
            #    self.ui.listWidget.addItem(str(row[2])+" "+str(row[0]+" <--> "+str(row[1])))
                #self.ui.comboBox.addItem("Id:"+str(row[0])+"--Name:"+str(row[1])+"--IP:"+str(row[2]))
            #print self.rows
#------------LISTWIDGET ICIN------------------

             #--- ESLESMELER TAB INDAKI ISLEMLER ICIN----------------------------

            self.eslesmeler_cumle='Select "idd","rfidId","cameraId" from "camera_rfid"'
            self.table_yukle(self.ui.tableWidget,self.eslesmeler_cumle)
            self.comboyu_kolonla_doldur(self.ui.comboBox_3,self.eslesmeler_cumle)

            #----- OKUYUCULAR TABINDAKI ISLEMLER ICIN-------

            self.okuyucular_cumle='Select * from "rfidInfo"'
            self.table_yukle(self.ui.tableWidget_4,self.okuyucular_cumle)
            self.comboyu_kolonla_doldur(self.ui.comboBox_4,self.okuyucular_cumle)


             #---    KAMERALAR TABLOSU   ----------------------------

            self.table_yukle(self.ui.tableWidget_3,'Select * from "cameraInfo"')




           # self.table_yukle(self.ui.tableWidget_4,'Select * from "rfidInfo"')


            #----POPUP KISMINA YENIDEN DEGERLERI YUKLE...
            try:
                self.table_yukle(self.yenipopup.tableWidget,"""SELECT * FROM "camera_rfid" WHERE "rfidId" LIKE '{}'""".format(giris))#+giris)

            except:
                "HATAAAAAA----"

            #self.arama_sorgusu='SELECT rfid_logs.sicil,rfid_logs.zaman,rfid_logs.okuyucu,camera_rfid."cameraId" FROM rfid_logs INNER JOIN camera_rfid ON (rfid_logs.okuyucu=camera_rfid."rfidId")'
            #self.table_yukle(self.ui.tableWidget_5,self.arama_sorgusu)

            #--- BİRAZ KARMAŞIK ANCAK 3 FARKL ITABLODAN VERİLERİ ALIP EKRANA BASMAKTA!
            self.arama_ekrani_sorgusu='SELECT rfid_logs.sicil,"personelList".isim,"personelList".bolum,rfid_logs.zaman, \
                rfid_logs.okuyucu,camera_rfid."cameraId" \
                FROM rfid_logs \
                INNER JOIN camera_rfid ON \
                (rfid_logs.okuyucu=camera_rfid."rfidId") \
                INNER JOIN "personelList" ON \
                ("personelList".sicil=rfid_logs.sicil)'


            self.table_yukle(self.ui.tableWidget_5,self.arama_ekrani_sorgusu+'ORDER BY rfid_logs.id DESC')

            #--- LOGLARDAKI COMBOBOX 'I DOLDUR!
            self.comboyu_kolonla_doldur(self.ui.comboBox,'SELECT rfid_logs.sicil,rfid_logs.zaman,rfid_logs.okuyucu,camera_rfid."cameraId" FROM rfid_logs INNER JOIN camera_rfid ON (rfid_logs.okuyucu=camera_rfid."rfidId")')

            #---KAMERALARDAKI COMBOBOX 'I DOLDUR!'
            self.comboyu_kolonla_doldur(self.ui.comboBox_2,'SELECT * FROM "cameraInfo"')


        def comboyu_degerle_doldur(self,combo_adi,sorgu):

            self.dbye_baglan()

            sqll= sorgu

            self.cur.execute(sqll)

            sonuclar = self.cur.fetchall()

            combo_adi.clear()

            for eklenen in sonuclar:

                combo_adi.addItem(eklenen[0])

            #self.rows = self.cur.fetchall()

          #  print colnames






        def comboyu_kolonla_doldur(self,combo_adi,arama_sorgusu):

            self.dbye_baglan()

                 #conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.132' password='1'")

            self.sqll= arama_sorgusu

            self.cur.execute(self.sqll)

            colnames = [desc[0] for desc in self.cur.description]

            #self.rows = self.cur.fetchall()

          #  print colnames

            combo_adi.clear()

            for row in colnames:

                combo_adi.addItem(str(row))



        def esle(self):
            #self.ui.lbl_secili.setStyleSheet('color: red')
            #self.ui.label_30.setText(str(self.ui.lbl_secili.text())+"<-->"+str(self.ui.comboBox.currentText()))
            self.ui.label_30.setStyleSheet('color: red')

        def eslesme_ekle(self):


           # sql1="""insert into camera_rfid ("cameraId", "rfidId") values ('{1}','{0}')""" .format(str(self.ui.lbl_secili.text()),str(self.ui.comboBox.currentText()))
            self.cur.execute(sql1)
            self.conn.commit()
            #self.conn.close()
            self.yukle()


        def doldur(self):

            # lnl secili de ki yazi kirmizi olmasin artik!!
           #self.ui.lbl_secili.setStyleSheet('color: black')



            self.dbye_baglan()
                 #conn = psycopg2.connect("dbname='vays_db' user='postgres' host='20.0.1.132' password='1'")

            self.sqll= 'Select "cameraId","cameraName","cameraIp" from "cameraInfo"'

            self.cur.execute(self.sqll)

            self.rows = self.cur.fetchall()

            for row in self.rows:

                self.ui.comboBox.addItem(str(row[1]))

            #print self.rows
            #conn.commit()
            #self.conn.close()

if __name__ == "__main__":
        app = QtGui.QApplication([])
        win = Pencere()
        #win.show()
        sys.exit(app.exec_())
