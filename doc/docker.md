# TEST ENV SETUP

## Install docker if necessary
1. Support RedHat/CentOS 8
    - [root@iZbp1f0xu750v7gccn5vbhZ ~]# cat /etc/system-release
      > CentOS Linux release 8.3.2011
    - Install dependency
      > https://download.docker.com/linux/centos/8/x86_64/stable/Packages/containerd.io-1.4.4-3.1.el8.x86_64.rpm
    - Install docker
      > yum install docker-ce
      > systemctl start docker && systemctl status docker
      > systemctl restart docker
2. Install Mysql
    - Pull image from docker hub
      > docker pull docker.io/mysql
    - Run mysql instance
      > docker run -d -p 3306:3306 --name mysql-dev -e MYSQL_ROOT_PASSWORD=triple_dev  docker.io/mysql:latest
      > docker ps
    - Remote access configuration
      > docker exec -it mysql-dev /bin/sh
      > mysql -uroot -p
      > alter user 'root'@'%' identified with mysql_native_password by 'root';
    - Test will client
3. Install mongodb
    - Pull image
    > docker pull mongo:latest