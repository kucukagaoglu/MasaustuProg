#!/usr/bin/python
# -*- coding: UTF-8 -*-

import res
import sys
import time
from PyQt4 import QtCore, QtGui, uic
import psycopg2
import urllib
import random




import examples_qtvlc

class Alarm_ureteci(QtGui.QMainWindow):

        def __init__(self,ebeveyn=None):

            self.i=0
            
            QtGui.QMainWindow.__init__(self)
            self.ui = uic.loadUi("yapay_alarm_ureteci.ui")
            self.ui.show()
            #----ON AYARLAMALAR

            self.ui.btn_elle.setChecked(True)   #-- elle ayarlama secili olsun
            self.ui.cmb_freq.setEnabled(False)  #-- frekans secimi pasifte kalsin...



            #---- LISTELER----------------

            # self.okuyucular_listesi = ["RFID_001","RFID_002","RFID_003","RFID_004","RFID_005","RFID_006",
            # "RFID_007","RFID_008","RFID_009","RFID_010","RFID_011","RFID_012","RFID_013","RFID_014","RFID_015"]
            # self.siciller_listesi=["381","397","390","234","365","201","699",
            # "399","500","750","403","180","433","345","187","485","497","450"]
            
            self.okuyucular_listesi=self.rfid_cihaz_listesi_doldur()
            self.siciller_listesi=self.personel_listesi_doldur()

            #-----CAM LERDE EKLİ OLDUĞUNDAN YALNIZCA RFID 'LERİ ÇEK!
            self.comboyu_degerle_doldur(self.ui.cmb_rfid,"""SELECT okuyucu_adi FROM "rfidInfo" WHERE okuyucu_adi LIKE 'RFID%' """)
            self.comboyu_degerle_doldur(self.ui.cmb_personel,'SELECT sicil FROM "personelList"')

           #---- sinyal ve slotlar

            self.simdi=round(time.time())
            self.connect(self.ui.btn_basla,QtCore.SIGNAL("released()"),lambda:self.alarm_ekle(str(self.ui.cmb_rfid.currentText()), \
                str(self.ui.cmb_personel.currentText()),str(self.ui.cmb_freq.currentText())))
            self.ui.btn_elle.toggled.connect(self.elle_secim)
            self.ui.btn_oto.toggled.connect(self.oto_secim)

           #self.connect(self.ui.RFID_001, QtCore.SIGNAL("clicked()"), lambda:self.rfid_esle("RFID_001"))



        def comboyu_degerle_doldur(self,combo_adi,sorgu):

            self.dbye_baglan()

            self.cur.execute(sorgu)

            sonuclar = self.cur.fetchall()
                
            combo_adi.clear()


            for eklenen in sonuclar:

                print eklenen
                combo_adi.addItem(eklenen[0])


        def rfid_cihaz_listesi_doldur(self):

            kayitli_okuyucular=[]

            self.dbye_baglan()
            self.cur.execute("""SELECT okuyucu_adi FROM "rfidInfo" WHERE okuyucu_adi LIKE 'RFID%' """)
            okuyucular=self.cur.fetchall()
                    
            for okuyucu in okuyucular:
                kayitli_okuyucular.append(okuyucu[0])
                        
            print kayitli_okuyucular
            return kayitli_okuyucular



        def personel_listesi_doldur(self):

                kayitli_personel=[]
                self.dbye_baglan()

                self.cur.execute("""SELECT sicil FROM "personelList" """)
                sonuclar=self.cur.fetchall()
                
                for sicil in sonuclar:
                     #print x[0],"<->",x[1]
                    kayitli_personel.append(sicil[0])
                #     dusey.append(x[0])

                print kayitli_personel

                return kayitli_personel



        def elle_secim(self):

            self.ui.cmb_freq.setEnabled(False)
            self.ui.cmb_personel.setEnabled(True)
            self.ui.cmb_rfid.setEnabled(True)
            self.ui.lbl_durum.setText("Manuel mode...")

        def oto_secim(self):

            self.ui.cmb_freq.setEnabled(True)
            self.ui.cmb_personel.setEnabled(False)
            self.ui.cmb_rfid.setEnabled(False)
            self.ui.cmb_io.setEnabled(False)
            self.ui.lbl_durum.setText("Random mode...")



        def dbye_baglan(self):

			self.conn = psycopg2.connect("dbname='vays_db' user='postgres' host='localhost' password='1'")
			self.cur = self.conn.cursor()


        def inmioutmu(self,sicil):

            self.dbye_baglan()

            cumle="SELECT MAX(id)  FROM rfid_logs WHERE sicil='{0}'".format(sicil) #--kisinin son hareketi
            self.cur.execute(cumle)
            self.son_hareket = self.cur.fetchone()[0]

            print self.son_hareket

            if (self.son_hareket is None):
                return "in" #--- kayıtta yoksa herhangi bir yere giriş
            else:

                cumle="SELECT okuyucu,inout FROM rfid_logs WHERE id={}".format(self.son_hareket)
                self.cur.execute(cumle)
                self.son_hareket=self.cur.fetchone()[1]
                try:
                    if(self.son_hareket=="in"): #---son hareket girmişse aynı okuyucudan çıkış olacak
                        return self.cur.fetchone()[0]
                    elif(self.son_hareket=="out"): #----son hareket çıkışsa herhangi bir yere giriş olacak
                        return "in"
                except:
                    print "HATA!"


        def alarm_ekle(self, okuyucu,sicil,sure):

            if (self.ui.btn_oto.isChecked()):

                self.ctimer=QtCore.QTimer()
                self.ctimer.start(int(sure)*1000) #- 1 SANIYE
                #QObject.connect(self.ctimer.SIGNAL("timeout()"),self.dugmeye_basildi)
                #self.secilme_zamani=round(time.time())

                eklenen_okuyucu=random.choice(self.okuyucular_listesi)
                eklenen_kisi=random.choice(self.siciller_listesi)
                eklenen_hareket=self.inmioutmu(eklenen_kisi)

                

                self.ctimer.timeout.connect(lambda: self.log_ekle(eklenen_okuyucu,eklenen_kisi,eklenen_hareket))

            else:
                try:
                    self.ctimer.stop()
                except:
                    pass
                self.log_ekle(str(self.ui.cmb_rfid.currentText()),str(self.ui.cmb_personel.currentText()),str(self.ui.cmb_io.currentText()))


        def log_ekle(self,okuyucu,sicil,io):


            self.dbye_baglan()

            
            #----ÖNCE RASTGELE KİŞİ BELİRLE-----------------------------------
            sicil=random.choice(self.siciller_listesi)


            #------SONRA BU KİŞİNİN SON HAREKET ID SİNİ------------
            cumle="SELECT MAX(id)  FROM rfid_logs WHERE sicil='{0}'".format(sicil) #--kisinin son hareketi
            self.cur.execute(cumle)
            son_hareket_id = self.cur.fetchone()[0]

            print "SON HAREKT ID:",son_hareket_id

            #----EĞER BU KİŞİNİN KAYDI YOKSA---HERHANGİ BİR YERE GİRİŞ YAPSIN!
            if (son_hareket_id is None):

                okuyucu=random.choice(self.okuyucular_listesi)
                io="in"

            #----EĞER SON HAREKET "NONE" DEĞİL İSE ...
            else:
                cumle="SELECT okuyucu,inout FROM rfid_logs WHERE id={}".format(son_hareket_id)
                self.cur.execute(cumle)
                son_hareket=self.cur.fetchone()

                inmioutmu=son_hareket[1]
            
            #----EĞER SON HAREKET "İN" İSE ORADAN ÇIKMASI LAZIM YANİ "OUT" OLACAK, OKUYUCU DEĞİŞMEZ....
            
                if(inmioutmu=="in"):
                    io="out"
                    okuyucu=son_hareket[0]

            #----EĞER SON HAREKET "OUT" İSE YENİ OKUYUCU LAZIM, VE HAREKET İN OLACAK....
                elif(inmioutmu=="out"):
                    io="in"
                    okuyucu=random.choice(self.okuyucular_listesi)


            print ">>>>>>>",sicil,"-",okuyucu,"-",io

            self.dbye_baglan()

            sql1="""insert into rfid_logs ("sicil", "okuyucu","zaman","inout") values ('{0}','{1}', now(),'{2}' )""".format(sicil,okuyucu,io)
            self.cur.execute(sql1)
            self.conn.commit()
       


            self.ui.lbl_durum.setText(okuyucu+"<-->"+sicil+">"+io)
            self.ui.lbl_eklenen_sicil.setText(sicil)
            self.ui.lbl_eklenen_reader.setText(okuyucu)


                

        #--- DUGMELER AKSIYON VER---
        
        #self.connect(self.ui.btn_kaydet,QtCore.SIGNAL("released()"),self.accept)
        #self.connect(self.ui.btn_vazgec,QtCore.SIGNAL("released()"),self.reject)

if __name__ == "__main__":
        app = QtGui.QApplication([])
        win = Alarm_ureteci()
        #win.show()
        sys.exit(app.exec_())
