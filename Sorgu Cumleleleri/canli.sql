SELECT rfid_logs.sicil,rfid_logs.okuyucu,camera_rfid."cameraId"
             FROM rfid_logs 
             INNER JOIN camera_rfid 
             ON (rfid_logs.okuyucu=camera_rfid."rfidId") 
             WHERE rfid_logs.id= (SELECT MAX(id)  FROM rfid_logs);
