#!/bin/sh
path="/usr/local/listen/src"
install_cm="/usr/local/listen/src/pyinstaller-2.0.zip"
path="/usr/local/listen/src/pyinstaller-2.0"
rm -rf listen.spec
rm -rf dist/listen
rm -rf ../bin/*
[ ! -s ${install_cm} ] && echo "Error: no found pyinstaller-2.0.zip" && exit 1
rpm -q unzip || yum -y unzip &>/dev/null
[ $? -ne 0 ] && echo "Error: yum not use " && exit 1
unzip ${install_cm}
install_path="pyinstaller-2.0"
src_path="/usr/local/listen/src"
server="/usr/local/listen/sbin/listend"
python ${install_path}/pyinstaller.py listen.py
python ${install_path}/pyinstaller.py listen.spec
cp pubutil.pyc ../bin/
cp dist/listen/* ../bin/
cp -R cgi-bin /usr/local/listen/www
rm -rf build
rm -rf logdict2.6.6.final.0-1.log
chmod +x ../www/cgi-bin/*
ln -s ../www/cgi-bin ../bin/cgi-bin
cp ../sbin/listend /etc/init.d/
chmod +x /etc/init.d/listend
