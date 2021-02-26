#!/bin/bash
# 2019 - Bismuth Foundation and NodeSupply
# Distributed under the MIT software license, see http://www.opensource.org/licenses/mit-license.php.

# Usage: bash ./bis-install.sh
# or one liner : curl https://raw.githubusercontent.com/bismuthfoundation/hypernode/beta99/auto-install/bis-install.sh|bash
# Setup a regular Bismuth node and hypernode on a fresh Ubuntu 18 install.

# BEWARE: The anti-ddos part will disable http, https and dns ports.

# This installs latest node 4.4.0.3 and latest 0.0.99 hn version

VERSION="0.1.26"

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
	fi
	if ! cat /etc/sysctl.conf | grep "vm.swappiness = 10"; then
	    echo "vm.swappiness = 10" >> /etc/sysctl.conf
	fi
	if ! cat /etc/sysctl.conf | grep "vm.vfs_cache_pressure = 50"; then
	    echo "vm.vfs_cache_pressure = 50" >> /etc/sysctl.conf
    fi	    
    sysctl -p
	echo 1 > /proc/sys/net/ipv4/tcp_low_latency
}


update_repos() {
    echo "Updating repos..."
    DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" update
    DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
}


install_dependencies() {
    echo "Installing apt dependencies"
    apt update -y
    # This may be enough,
    # apt install ufw unzip ntpdate python3-pip sqlite3 -y
    apt install screen htop ufw unzip ntpdate sqlite3 build-essential python3.7-dev python3-pip -y
    # Install optional packages that may be needed on some setups only
    apt install autoconf autogen pkg-config -y
    apt install libtool-bin -y
    apt install libsecp256k1-dev -y
    apt install libgmp3-dev -y
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
    # Wallet server
    ufw allow 8150/tcp
    # Websocket server
    ufw allow 8155/tcp
    ufw logging on
    ufw default deny incoming
    ufw default allow outgoing
    ufw --force enable
}


download_node() {
    echo "Fetching Node"
    cd
    if [ -f ./master.zip ]; then
        rm master.zip
    fi
    wget https://github.com/bismuthfoundation/Bismuth/archive/master.zip
    unzip master.zip
    mv Bismuth-master Bismuth
    cd Bismuth
    echo "Configuring node"    
    echo "ram=False" >> config_custom.txt
    echo "full_ledger=True" >> config_custom.txt
    echo "mempool_ram=False" >> config_custom.txt
    echo "Downloading bootstrap"
    cd static
    if [ -f ./ledger-verified.tar.gz ]; then
        rm ledger-verified.tar.gz
    fi
    wget http://212.47.253.89/ledger-verified.tar.gz
    tar -zxf ledger-verified.tar.gz
    # Make some room
    rm ledger-verified.tar.gz
    echo "Getting companions"
    cd /root/Bismuth
    mkdir plugins
    mkdir plugins/035_socket_client
    mkdir plugins/500_hypernode
    cd plugins/035_socket_client
    rm __init__.py
    wget https://github.com/bismuthfoundation/BismuthPlugins/raw/master/plugins/035_socket_client/__init__.py
    cd ../500_hypernode
    rm __init__.py
    wget https://github.com/bismuthfoundation/hypernode/raw/beta99/node_plugin/__init__.py
    cd /root/Bismuth
    rm ledger_queries.py
    wget https://github.com/bismuthfoundation/hypernode/raw/beta99/node_plugin/ledger_queries.py       
    echo "Getting node sentinel"
    cd /root/Bismuth
    wget https://gist.githubusercontent.com/EggPool/63f146c6c6b7de8e0929a09dc190c62e/raw/322437b7ec2dea4f2b5f99e0582f2a97f42e420a/node_sentinel.py
    echo "Installing PIP requirements"
    python3.7 -m pip install setuptools ipwhois
    python3.7 -m pip install -r requirements-node.txt
    # make sure in case of remainings of oldies.
    rm -rd polysign
}

download_hypernode() {
    echo "Fetching Hypernode"
    cd
    if [ -f ./beta99.zip ]; then
        rm beta99.zip
    fi
    wget https://github.com/bismuthfoundation/hypernode/archive/beta99.zip
    unzip beta99.zip
    mv hypernode-beta99 hypernode
    cd hypernode
    echo "Installing PIP requirements"
    python3.7 -m pip install wheel
    python3.7 -m pip install fastecdsa
    python3.7 -m pip install -r requirements.txt
    echo "Adjusting cron1.py for python3.7"
    sed -i -e "s/python3'/python3.7'/g" ./crontab/cron1.py
}


install_plugin() {
    echo "Installing companion plugin"
    mkdir /root/Bismuth/plugins
    mkdir /root/Bismuth/plugins/500_hypernode
    cp /root/hypernode/node_plugin/__init__.py /root/Bismuth/plugins/500_hypernode
}

start_node() {
    echo "Starting node"
    cd
    screen -d -S node -m bash -c "cd Bismuth;python3.7 node.py" -X quit
}

wait_ledger() {
	echo "Waiting for ledger to download and extract"
	while true; do
    if [ ! -f /root/Bismuth/static/ledger.db ]; then
        echo "."
        sleep 10
    else
	    break
    fi
    done
}


check_hypernode() {
    echo "Checking Hypernode"
    cd /root/hypernode/main
    python3.7 hn_check.py
}

add_cron_jobs() {
	# Node sentinel
	if ! crontab -l | grep "node_sentinel"; then
	  (crontab -l ; echo "* * * * * cd /root/Bismuth;python3.7 node_sentinel.py") | crontab -
	fi
	# Hypernode sentinel1
	if ! crontab -l | grep "cron1.py"; then
	  (crontab -l ; echo "* * * * * cd /root/hypernode/crontab;python3.7 cron1.py") | crontab -
	fi
	# Hypernode sentinel5
	if ! crontab -l | grep "cron5.py"; then
	  (crontab -l ; echo "*/5 * * * * cd /root/hypernode/crontab;python3.7 cron5.py") | crontab -
	fi
}

if [ "$(whoami)" != "root" ]; then
    echo "Script must be run as root"
    exit -1
fi

while true; do
    if [ -d /root/Bismuth ]; then
        printf "/root/Bismuth/ already exists! The installer will delete this folder. Continue anyway?(Y/n)"
        pID=$(ps -ef | grep node.py | awk '{print $2}' | head -n 1)
        kill ${pID}
        rm -rf /root/Bismuth/
        break
    else
        break
    fi
done

while true; do
    if [ -d /root/hypernode ]; then
        printf "/root/hypernode/ already exists! The installer will delete this folder. Continue anyway? (Y/n)"
        pID=$(ps -ef | grep hn_instance.py | awk '{print $2}' | head -n 1)
        kill ${pID}
        rm -rf /root/hypernode/
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
# install_plugin
# start_node
# wait_ledger
check_hypernode

# TODO: call a HTTP hook to give feedback, could include check.json and poswallet.json from /root/hypernode/main
# as well as wallet.der from /root/Bismuth
# check.json has pos wallet address as well as out ip

# cron_jobs are what will launch at boot and auto-restart node and hypernode.
add_cron_jobs


echo "Rebooting server."
reboot
