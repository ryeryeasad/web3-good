#! /bin/bash

echo "Entering source code directory"
cd /root/triple

echo "Reset git repository and git pull"
git reset --hard
git pull

echo "Deploy latest code"
pip3 uninstall triple -y
pip3 install .
cp -f etc/triple.conf /etc/triple/triple.conf

echo "Restart service, only for premon riskctl rtmon server, not include gearman"
supervisorctl restart

echo "^_^ DONE"