#!/usr/bin/env bash
# 2018 - Bismuth Foundation and NodeSupply
# Distributed under the MIT software license, see http://www.opensource.org/licenses/mit-license.php.

# Usage: ./bis-install.sh
#
# Setup a regular Bismuth node and hypernode on a fresh Ubuntu 18 install.

# ATTENTION: The anti-ddos part will disable http, https and dns ports.

VERSION="0.1.11"

create_swap() {
	if [ -d /swapfile ]; then
		echo "Swap file already there"
	else
		fallocate -l 3G /swapfile
		chmod 600 /swapfile
		mkswap /swapfile
		swapon /swapfile
		echo "/swapfile   none    swap    sw    0   0" >> /etc/fstab
		echo "Swap file activated"
	fi
}

config_os() {
	if ! cat /etc/security/limits.conf | grep "root soft nofile 65535"; then
        echo "root soft nofile 65535" >> /etc/security/limits.conf
        echo "root hard nofile 65535" >> /etc/security/limits.conf
	fi
	if ! cat /etc/sysctl.conf | grep "fs.file-max = 100000"; then
	    echo "fs.file-max = 100000" >> /etc/sysctl.conf
        sysctl -p
	fi
	echo 1 > /proc/sys/net/ipv4/tcp_low_latency
}


update_repos() {
	echo "Updating repos..."
    DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" update
    DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
}


install_dependencies() {
	echo "Installing apt dependencies"
	# apt update -y
	# This may be enough,
    # apt install ufw unzip ntpdate python3-pip sqlite3 -y
    apt install ufw unzip ntpdate python3-pip sqlite3 build-essential python3-dev -y
	# ntpdate ntp.ubuntu.com
	# apt install ntp -y
}


configure_firewall() {
	echo "Configuring Firewall"
    ufw disable
    ufw allow ssh/tcp
    ufw limit ssh/tcp
    # node port
    ufw allow 5658/tcp
    # HN port
    ufw allow 6969/tcp
    ufw logging on
    ufw default deny incoming
    ufw default allow outgoing
    ufw --force enable
}


download_node() {
	echo "Fetching Node"
	cd
    if [ -f ./4.2.6.tar.gz ]; then
        rm 4.2.6.tar.gz
	fi
    wget https://github.com/hclivess/Bismuth/archive/4.2.6.tar.gz
    tar -zxf 4.2.6.tar.gz
    mv Bismuth-4.2.6 Bismuth
    cd Bismuth
    echo "Downloading bootstrap"
    cd static
    if [ -f ./ledger.tar.gz ]; then
        rm ledger.tar.gz
	fi
    wget https://bismuth.cz/ledger.tar.gz
    tar -zxf ledger.tar.gz
    echo "Getting node sentinel"
    cd ~/Bismuth
    wget https://gist.githubusercontent.com/EggPool/e7ad9baa2b32e4d7d3ba658a40b6d643/raw/934598c7ff815180b913d6549bd2d9688e016855/node_sentinel.py
    echo "Installing PIP requirements"
    pip3 install setuptools
    pip3 install -r requirements-node.txt
}

download_hypernode() {
	echo "Fetching Hypernode"
	cd
    if [ -f ./hypernode.tar.gz ]; then
        rm hypernode.tar.gz
	fi
    wget http://bp12.eggpool.net/hypernode.tar.gz
    tar -zxf hypernode.tar.gz
    cd hypernode
    echo "Installing PIP requirements"
    pip3 install wheel
    pip3 install -r requirements.txt
}


install_plugin() {
	echo "Installing companion plugin"
	mkdir ~/Bismuth/plugins
	mkdir ~/Bismuth/plugins/500_hypernode
	cp ~/hypernode/node_plugin/__init__.py ~/Bismuth/plugins/500_hypernode
}

start_node() {
	echo "Starting node"
	cd
	screen -d -S node -m bash -c "cd Bismuth;python3 node.py" -X quit
}

wait_ledger() {
	echo "Waiting for ledger to download and extract"
	while true; do
	 if [ ! -f ~/Bismuth/static/ledger.db ]; then
		echo "."
		sleep 10
	 else
	   break
	 fi
	done
}


check_hypernode() {
	echo "Checking Hypernode"
    cd ~/hypernode/main
    python3 hn_check.py
}

add_cron_jobs() {
	# Node sentinel
	if ! crontab -l | grep "node_sentinel"; then
	  (crontab -l ; echo "* * * * * cd ~/Bismuth;python3 node_sentinel.py") | crontab -
	fi
	# Hypernode sentinel1
	if ! crontab -l | grep "cron1.py"; then
	  (crontab -l ; echo "* * * * * cd ~/hypernode/crontab;python3 cron1.py") | crontab -
	fi
	# Hypernode sentinel5
	if ! crontab -l | grep "cron5.py"; then
	  (crontab -l ; echo "* * * * */5 cd ~/hypernode/crontab;python3 cron5.py") | crontab -
	fi
}

if [ "$(whoami)" != "root" ]; then
  echo "Script must be run as root"
  exit -1
fi

while true; do
 if [ -d ~/Bismuth ]; then
   printf "~/Bismuth/ already exists! The installer will delete this folder. Continue anyway?(Y/n)"
   pID=$(ps -ef | grep node.py | awk '{print $2}' | head -n 1)
   kill ${pID}
   rm -rf ~/Bismuth/
   break
 else
   break
 fi
done

while true; do
 if [ -d ~/hypernode ]; then
   printf "~/hypernode/ already exists! The installer will delete this folder. Continue anyway?(Y/n)"
   pID=$(ps -ef | grep hn_instance.py | awk '{print $2}' | head -n 1)
   kill ${pID}
   rm -rf ~/hypernode/
   break
 else
   break
 fi
done


cd
create_swap
config_os
update_repos
install_dependencies
configure_firewall
download_node
download_hypernode
install_plugin
# start_node
# wait_ledger
check_hypernode

# TODO: call a HTTP hook to give feedback, could include check.json and poswallet.json from ~/hypernode/main
# as well as wallet.der from ~/Bismuth
# check.json has pos wallet address as well as out ip

# cron_jobs are what will launch at boot and auto-restart node and hypernode.
add_cron_jobs


echo "Rebooting server..."
reboot
