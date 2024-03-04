# 服务配置及运行环境

## 基础配置（软硬件）
   1. 硬件
      - CPU 2核 （没太大要求）
      - RAM 内存不低于 8G （服务器端缓存比较多）
      - 网络 （内网IP没太大要求， 外网要考虑到gearman server的处理量增加带宽）
   2: 系统以及依赖软件
      - OS， Limux （RedHat/CentOS 7）
      - 主要依赖软件
          - 进程管理， superviosrd
          - Python, Python3.8
              - 异步任务分发， gear
              - 数据库中间件， sqlalchemy
              - redis
              - elasticsearch 

## 服务配置
   1. Supervisord
       - 详见 superviosr.md
   2: Python
       - 详见 ugrade_python38.md
   3: gearman
       - 详见 gearman.md
   4. mysql
       - 详见 mysql.md
   4. redis
       - 详见 mysql.md
   4： 服务配置文件  triple.conf
       - 样例参照  ../etc/triple.conf
           - [gearman_server], gearman server 启动配置参数
           - [gearman], 为 gearman client/worker 提供所要连接的 gearman server地址，包括
               - listener 命令客户端
               - 事前监控 client/worker
               - 事前风控 client/worker
               - 事中监控 client/worker
           - [triple] triple 主服务启动参数，以及日志配置
           - [rtsummary] 实时汇总参数
           - [transaction] 交易配置
           - [elasticsearch] ES配置
           - [redis] redis配置
           - [database] mysql配置
           - [taos] 实时行情接口配置
           - [webapp] 预留，web服务耦合到架构服务中

## 服务启动
   1. 源代码clone目录
       - /root/triple
   2: 配置文件默认目录 (triple.conf以及各日志配置文件)
       - /etc/triple/
   3: 创建supervisor进程配置文件 (/etc/supervisord.d/)
       - triple-server.ini
           ```
            [program:triple-server]
            directory = /root/triple/
            command = triple-server -d
            user=root
            autostart=true
            autorestart=true
           ``` 
   4：安装模块
      - python3 /root/triple/setup.py install
      
   5: 重启supervisord服务，配置进程会自动启动
       - systemctl status supervisord && systemctl restart supervisord
       - supervisord服务日志 （/etc/supervisord.conf）
           - [supervisord], logfile=/var/log/supervisor/supervisord.log 
   5: 检查进程状态
       - supervisorctl status
       - 重启进程 supervisorctl restart <进程名>
       - 停止进程 supervisorctl stop <进程名>
   6: 进程运行信息
       - 查看各进程日志配置
       
       
## 排查僵死问题
    https://juejin.cn/post/6850418112203128845
    https://zhuanlan.zhihu.com/p/358987957?ivk_sa=1024320u
   1. 查看所有线程 top -H -p {pid} 或者 打印某个进程的线程数 pstree -p {pid}
   2. 排查原因 strace -p 16634  (跟踪进程执行时的系统调用和所接收的信号（即它跟踪到一个进程产生的系统调用，包括参数、返回值、执行消耗的时间)
   3. strace -T -tt -e trace=all -p {pid} 
   4. cd /proc/1/fd   
   5. ls -l
   6. netstat -ent|grep 51457776
   