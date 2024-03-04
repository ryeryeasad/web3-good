# 安装mysql教程
http://t.zoukankan.com/yecao8888-p-6370990.html

rpm -qa | grep mysql　　// 这个命令就会查看该操作系统上是否已经安装了mysql数据库

有的话，我们就通过 rpm -e 命令 或者 rpm -e --nodeps 命令来卸载掉
rpm -e mysql　　// 普通删除模式
rpm -e --nodeps mysql　　// 强力删除模式，如果使用上面命令删除时，提示有依赖的其它文件，则用该命令可以对其进行强力删除

## 安装
   1. yum install -y mysql-server mysql mysql-devel
   2. rpm -qi mysql-server
   
## 启动
   1. service mysqld start
   2. service mysqld restart 重启

## 设置开机自启动
   1. 通过  chkconfig --list | grep mysqld 命令来查看mysql服务是不是开机自动启动
   2. chkconfig mysqld on
   
## 设置管理员账号
   1. mysqladmin -u root password 'root'
   
## 创建账户
   1. Create database web3;
   1. CREATE USER 'web3'@'%' IDENTIFIED BY 'web3';
   2. 使用GRANT创建用户并授权 triple 库的所有操作
        grant all privileges on web3.* to 'web3'@'%' ;