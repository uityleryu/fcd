#!/usr/bin/expect --

spawn ./scp2.sh /tftpboot/helper_ARxxxx ubnt@192.168.1.215:/tmp
expect "password:"
send "ubnt\n"
expect eof
