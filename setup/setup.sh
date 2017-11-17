#!/bin/bash


# default login: debian:temppwd

sudo nano /etc/hostname
sudo nano /etc/hosts

sudo adduser nuc
sudo usermod -aG sudo nuc
sudo usermod -aG dialout nuc
sudo usermod -aG i2c nuc
sudo bash -c " echo \"nuc ALL=(ALL) NOPASSWD:ALL\" > /etc/sudoers.d/nuc"

# sudo reboot, login as nuc, then
sudo userdel -r -f debian
sudo userdel -r -f pi




# RSA keys
if [ ! -f ~/.ssh/id_rsa ]; then
	echo "Generating RSA keys..."
	ssh-keygen
	cat ~/.ssh/id_rsa.pub
else
# or if you have a key pair you'd like to use, copy into ~/.ssh then
	sudo chmod 700 ~/.ssh/id_rsa
fi


sudo apt update && sudo apt upgrade -y
sudo apt install ntp ntpdate git minicom autossh -y
#dpkg-reconfigure tzdata
sudo nano /etc/ntp.conf

# crontab...


cd
#git clone git@github.com:stanleylio/fishie.git ~/node
git clone https://github.com/stanleylio/fishie ~/node
cd ~/node
git config --global user.name "Stanley Lio"
git config --global user.email stanleylio@gmail.com
#git remote set-url origin git@github.com:stanleylio/fishie.git

cd
#git clone git@github.com:stanleylio/kmetlog.git ~/kmetlog
git clone https://github.com/stanleylio/kmetlog
cd ~/kmetlog
git config --global user.name "Stanley Lio"
git config --global user.email stanleylio@gmail.com
#git remote set-url origin git@github.com:stanleylio/kmetlog.git


# sampling
sudo apt install supervisor -y
sudo systemctl enable supervisor
sudo systemctl start supervisor
sudo chown nuc:nuc /etc/supervisor/conf.d
sudo apt install build-essential python-dev python-setuptools python-pip python-twisted python-zmq -y
sudo pip install pyserial requests pycrypto



# db
sudo apt install sqlite3 -y


sudo mkdir /var/uhcm
sudo chown nuc:nuc /var/uhcm
mkdir /var/uhcm/log


sudo echo "cape_enable=bone_capemgr.enable_partno=BB-UART1,BB-UART2,BB-UART4,BB-UART5,BB-I2C1,BB-I2C2" >> /boot/uEnv.txt
sudo echo "cape_disable=bone_capemgr.disable_partno=BB-HDMI" >> /boot/uEnv.txt
sudo pip install Adafruit_BBIO
sudo apt install i2c-tools python-smbus -y
source ~/node/setup/time/install_ds1307.sh

# expand partition to full disk
cd /opt/scripts/tools/
sudo git pull
sudo ./grow_partition.sh
#sudo bash update_kernel.sh
