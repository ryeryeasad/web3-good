# 安装redis教程

1. root用户导航到安装目录
    - cd /home/software
2. 下载redis源文件，解压并编译
    - wget http://download.redis.io/releases/redis-5.0.0.tar.gz
    - tar xzf redis-5.0.0.tar.gz
    - cd redis-5.0.0
    - make
    - ll -h 查看编译后的文件目录结构(和编译前的目录结构一样)
    - make install  将Redis安装到/usr/local/bin目录中
    - ll -h /usr/local/bin/   查看/usr/local/bin目录中的文件

##启动/关闭redis
   启动Redis有两种方式，直接启动（开发环境）和通过脚本启动(生产环境)
   1. 直接启动Redis
       - redis-server 使用make install后可以这样启动Redis,因为 /usr/local/bin目录下有该执行程序
       - 可以通过 redis-server --port 6380 指定端口
   2. 使用脚本启动redis
       - 在/redis/utils 工具箱目录中，有一个redis_init_script脚本文件,它是Redis启动脚本的模板
       - 可以通过 redis-server --port 6380 指定端口
       - 修改配置文件，放在/etc/redis文件夹下
           - mkdir /etc/redis
           - cp redis.conf /etc/redis/6379.conf
           - vim /etc/redis/6379.conf 
           ######修改部分配置文件
               bind 127.0.0.1  # 设置访问ip，这里是只允许本机访问，如果要让其他机器访问，可使用bind 0.0.0.0
               daemonize yes     # 开启守护进程（后台运行）
               # pidfile文件（与启停脚本要一致）
               pidfile /var/run/redis_6379.pid
               # 数据库文件的地址(需要手动创建该目录)
               # mkdir -p /var/redis/6379
               dir /var/redis/6379
       - 将启动脚本放在 /etc/init.d/redis_6379
           - cp utils/redis_init_script /etc/init.d/redie_6379
           
       ####设置开机启动
            # 将init.d目录中的redis_6379脚本设备开机启动
            chkconfig redis_6379 on
            # 检查是否为开机启动
            chkconfig --list | grep redis
            # redis_6379     0:关闭   1:关闭    2:启用    3:启用    4:启用    5:启用    6:关闭
            
       ####脚本启动
            # 启动
            $ /etc/init.d/redis_6379 start
            
            # 用脚本停止redis
            $ /etc/init.d/redis_6379 stop
            # 用户客户端停止redis
            $ redis-cli shutdown
