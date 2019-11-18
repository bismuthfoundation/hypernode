# Auto install script

- Tested on Ubuntu 18 Only
- Needs login as root
- will reboot the vps after install

- For bare VPS with nothing else. Does configure a firewall with only needed rules. May break other things running on the vps if you run many things on a single vps. In that case, check what the script does.

Usage:  
`curl https://raw.githubusercontent.com/bismuthfoundation/hypernode/beta99/auto-install/bis-install.sh|bash`

See https://github.com/bismuthfoundation/Bismuth-FAQ/blob/master/Hypernodes/00-Auto-Install-Script.md for more details.
