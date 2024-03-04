# 更新系统python版本到3.8

## 升级依赖
   1. sudo yum update
   2. sudo yum upgrade
   3. yum install libffi-devel openssl-devel -y
   5. yum install zlib-devel bzip2-devel ncurses-devel 
   6. yum install sqlite-devel readline-devel tk-devel
   7. yum install gcc

## 下载安装包
   1. mkdir -p /root/Downloads/python_install && cd /root/Downloads/python_install
   2. wget https://www.python.org/ftp/python/3.8.15/Python-3.8.15.tgz
      1. tar -zxvf Python-3.8.15.tgz
      2. cd Python-3.8.15/
      
## 安装
   1. mkdir /usr/local/python3
   2. ./configure --prefix=/usr/local/python3 --with-ssl --enable-loadable-sqlite-extensions
   3. make && make install
   4. ln -s /usr/local/python3/bin/python3 /usr/bin/python3
   5. ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3