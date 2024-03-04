# 启动 gearman server

## supervisor 管理
   1. vim /etc/supervisord.d/gearman.ini
      ```
      [program:gearman]
      directory = /home/server/triple/triple/dispatcher
      command = python3 gearmand.py
      user=root
      autostart=true
      autorestart=true
      ``` 
   2. supervisorctl status
      ```
      gearman                          RUNNING   pid 408245, uptime 0:00:07
      ```
      
   3. netstat -auntp
      ```
      tcp        0      0 0.0.0.0:4730            0.0.0.0:*               LISTEN      408247/python3
      ```
