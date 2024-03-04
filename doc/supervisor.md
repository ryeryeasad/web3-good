# 安装进程管理工具 supervisor

## RedHat/CentOS
   1. yum install epel-release
   2. yum install -y supervisor
   3. systemctl enable supervisord
   4. systemctl start supervisord
   5. systemctl status supervisord
   6. ps -ef|grep supervisord