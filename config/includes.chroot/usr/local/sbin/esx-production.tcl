#!/usr/bin/expect --
set dev [lindex $argv 0]
set manuf [lindex $argv 1]
set idx [lindex $argv 2]
set model_string [lindex $argv 3]
set passphrase [lindex $argv 4]
set dev_bom [lindex $argv 5]
set device_type [lindex $argv 6]
set keydir [lindex $argv 7]
set mac_addr [lindex $argv 8]
set tftpserver [lindex $argv 9]
set tty_sid 0
set progress 0

set uboot_promt "RTL838x#"
set linux_promt " #"
set helper_file "helper_RTL838x_release"

#
# procedures
#
proc error_critical {msg} {
	log_error $msg
	exit 2
}

proc log_error { msg } {
	set d [clock format [clock seconds] -format {%H:%M:%S}]
	send_user "\r\n * ERROR: $d $msg * * *\r\n"
}

proc log_warn { msg } {
	set d [clock format [clock seconds] -format {%H:%M:%S}]
	send_user "\r\n * WARN: $d $msg *\r\n"
}

proc log_progress { p msg } {
	set d [clock format [clock seconds] -format {%H:%M:%S}]
	send_user "\r\n=== $p $d $msg ===\r\n"
}

proc log_progress_step { step msg } {
	global progress
	set progress [expr {$progress + $step}]

	set d [clock format [clock seconds] -format {%H:%M:%S}]
	send_user "\r\n=== $progress $d $msg ===\r\n"
}

proc log_debug { msg } {
	set d [clock format [clock seconds] -format {%H:%M:%S}]
	send_user "\r\nDEBUG: $d $msg\r\n"
}

proc wait_for_promt { sid } {
	global linux_promt
	set timeout 120
	expect -i $sid timeout {
		error_critical "Command promt not found"
	} $linux_promt
}

proc exec_cmd { sid cmd} {
	send -i $sid $cmd
	wait_for_promt $sid
}

proc wait_for_promt_uboot { sid } {
	global uboot_promt
	set timeout 15
	expect -i $sid timeout {
		error_critical "Command promt not found"
	} $uboot_promt
}

proc exec_cmd_uboot { sid cmd} {
	send -i $sid $cmd
	wait_for_promt_uboot $sid
}

log_debug "
launched with params:
	\[dev         \] = $dev
	\[manuf       \] = $manuf
	\[idx         \] = $idx
	\[model_string\] = $model_string
	\[passphrase  \] = $passphrase
	\[bom         \] = $dev_bom
	\[device_type \] = $device_type
	\[keydir      \] = $keydir
	\[mac_addr    \] = $mac_addr
	\[tftpserver  \] = $tftpserver"

log_debug "Device BOM: $dev_bom"

if { $tftpserver == "" } {
	set tftpserver "192.168.1.254"
}

if {![regexp {(\d+)} $idx]} {
        send_user "Invalid index! Defaulting to 0...\r\n"
        set idx 0
}
set ip_end [expr 20 + $idx]
set ip "192.168.1.$ip_end"

#
# PROCEDURES
#

proc stop_uboot {sid} {

	log_debug "Stoping U-boot"
	#send "any key"

	set timeout 30
	expect  -i $sid "Hit Esc key to stop autoboot:" { send \x1b } \
	timeout { error_critical "Device not found!" }
	wait_for_promt_uboot $sid
}

proc run_client { idx eeprom_txt eeprom_bin passphrase keydir} {
	log_debug "Connecting to server:"

	set outfile [open "/tmp/client$idx.sh" w]
	puts $outfile "#!/bin/sh\n"
	puts $outfile "/usr/local/sbin/client_x86_release -h devreg.ubnt.com -i field=product_class_id,value=basic \$(cat /tftpboot/$eeprom_txt  | sed -r -e \"s~^field=(.*)\$~-i field=\\1 ~g\" | grep -v \"eeprom\" | tr '\\n' ' ') -i field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_bin -o field=flash_eeprom,format=binary,pathname=/tftpboot/eeprom_out$idx -k $passphrase -o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message -x $keydir/ca.pem -y $keydir/key.pem -z $keydir/crt.pem "
	close $outfile

	if { [catch "spawn sh /tmp/client$idx.sh" reason] } {
		error_critical "Failed to spawn client: $reason\n"
	}
	set sid $spawn_id
	log_debug "sid $sid"

	set timeout 15

	expect {
		-i $sid eof { log_debug "Done." }
		-i $sid timeout {
			log_debug "Closing client session $sid."
			close -i $sid
			error_critical "Registration failure : timeout"
		}
	}
	catch wait result
	set res [lindex $result 3]
	log_debug "Client result $res"
	if { $res != 0 } {
		error_critical "Registration failure : $res\n"
	}
}

proc to_tftp_srv { sid src_file ip} {
	log_debug "Uplading file $src_file:"
	if { [ catch { exec rm -f /tftpboot/$src_file } msg ] } {
		puts "$::errorInfo"
	}
	if { [ catch { exec touch /tftpboot/$src_file } msg ] } {
		puts "$::errorInfo"
	}
	if { [ catch { exec chmod a+w /tftpboot/$src_file } msg ] } {
		puts "$::errorInfo"
	}

	exec_cmd $sid "tftp -p -l $src_file $ip\r"
}

proc from_tftp_srv { sid rem_file ip} {
	exec_cmd $sid "tftp -g -r $rem_file $ip\r"
}

proc is_alive { {ip} {count} } {
	send_user  "PING to $ip "

	set status 0
	for { set i 1 } { $i <= $count } { incr i } {

		if {[catch {exec ping $ip -c 2} ping]} { set ping 0 }
		if {[lindex $ping 0] == "0"} { send_user "." }
		if {[lindex $ping 0] != "0"} {
			if {[regexp {time=(.*) ms} $ping -> time]} {
				send_user "\nGot response\n"
				return 0
			}
		}
	}
	send_user "\nNot responding\n"
	return 1
}

proc download_helper { sid } {
	global ip
	global tftpserver
	global tty_sid
	global helper_file

	set timeout 120

	exec_cmd $sid "ifconfig eth0 $ip\r"

	log_debug "Sending helpers..."
	exec_cmd $sid "cd /tmp\r"

	set ping_res [is_alive $ip 30]
	if { $ping_res == 0 } {
		log_debug "Detected with ping..."
	} else {
		error_critical "Network failure"
	}

	set timeout 10
	from_tftp_srv $sid $helper_file $tftpserver

	exec_cmd $sid "chmod +x $helper_file\r"
}

proc remove_on_host { file } {
	if { [ catch { exec rm -f $file } msg ] } {
		puts "$::errorInfo"
	}
}

proc copy_on_host { src dest } {
	if { [ catch { exec cp $src $dest } msg ] } {
		puts "$::errorInfo"
	}
}

proc do_security { sid } {
	global ip
	global tftpserver
	global idx
	global passphrase
	global keydir
	global tty_sid
	global user
	global helper_file

	set timeout 120

	set eeprom_bin e.b$idx
	set eeprom_txt e.t$idx

	remove_on_host /tmp/$eeprom_bin
	remove_on_host /tmp/$eeprom_txt

	exec_cmd $sid "cd /tmp\r"

	log_debug "Launching helper..."

	exec_cmd $sid "rm -f /tmp/$eeprom_bin\r"
	exec_cmd $sid "rm -f /tmp/$eeprom_txt\r"
	exec_cmd $sid "rm -f /tmp/check_eeprom$idx\r"

	exec_cmd $sid "./$helper_file -q -c product_class=basic -o field=flash_eeprom,format=binary,pathname=$eeprom_bin > $eeprom_txt\r"

	log_debug "Uploading files..."

	to_tftp_srv $sid $eeprom_bin $tftpserver
	to_tftp_srv $sid $eeprom_txt $tftpserver

	copy_on_host /tftpboot/$eeprom_bin /tmp/$eeprom_bin
	copy_on_host /tftpboot/$eeprom_txt /tmp/$eeprom_txt

	set file_size [file size  "/tmp/$eeprom_bin"]
	if { $file_size == 0 } then { ; # check for file exist
		error_critical "EEPROM (bin) download failure"
	}

	set file_size [file size  "/tmp/$eeprom_txt"]
	if { $file_size == 0 } then { ; # check for file exist
		error_critical "EEPROM (txt) download failure"
	}

	remove_on_host /tmp/check_eeprom$idx
	remove_on_host /tmp/eeprom_out$idx

	log_debug "Connecting to server:"
	run_client $idx $eeprom_txt $eeprom_bin $passphrase $keydir

	sleep 1
	log_debug "Downloading eeprom..."
	from_tftp_srv $sid "eeprom_out$idx" $tftpserver
	log_debug "File received."

	log_debug "Writing eeprom..."
	exec_cmd $sid "./$helper_file -q -i field=flash_eeprom,format=binary,pathname=/tmp/eeprom_out$idx\r"

	exec_cmd $sid "cp /dev/mtdblock5 /tmp/check_eeprom$idx\r"

	log_debug "Checking EEPROM..."

	exec_cmd $sid "cd /tmp\r"
	to_tftp_srv $sid check_eeprom$idx $tftpserver

	if {[catch { exec cmp /tftpboot/check_eeprom$idx /tftpboot/eeprom_out$idx } results]} {
		set details [dict get $results -errorcode]

		if {[lindex $details 0] eq "CHILDSTATUS"} {
			set status [lindex $details 2]
			error_critical "EEPROM check failed"
		} else {
		}
	}
	log_debug $results
	log_debug "EEPROM check OK..."

	log_debug "Rebooting device..."
	send -i $sid  "reboot\r"
}

proc write_hw_info { {sid} {mac} {device_type} {bom}} {

	scan $device_type %x device_type_dec

	set device_type1 [format %02x [expr { $device_type_dec & 0xFF }]]
	set device_type2 [format %02x [expr { ( $device_type_dec >> 8 ) & 0xFF  }] ]

	set ssid_str "$device_type2$device_type1"

	set macs [split $mac ":"]

	set str_dec [expr 0x[lindex $macs 0]]
	set localy_adm [expr $str_dec | 0x02]
	set hex_str [format "%02x" $localy_adm]

	set mac_addr0 "[lindex $macs 0]:[lindex $macs 1]:[lindex $macs 2]:[lindex $macs 3]:[lindex $macs 4]:[lindex $macs 5]"
	set mac_addr1 "$hex_str:[lindex $macs 1]:[lindex $macs 2]:[lindex $macs 3]:[lindex $macs 4]:[lindex $macs 5]"

	send_user "MAC0: $mac_addr0\nMAC1: $mac_addr1\r"

	exec_cmd_uboot $sid "setenv ethaddr $mac_addr0\r"
	exec_cmd_uboot $sid "setenv eth1addr $mac_addr1\r"
	exec_cmd_uboot $sid "setenv sysid $ssid_str\r"
	exec_cmd_uboot $sid "setenv bom $bom\r"

	exec_cmd_uboot $sid "setubinfo\r"
	exec_cmd_uboot $sid "printubinfo\r"

	#clean production variables
	exec_cmd_uboot $sid "setenv eth1addr\r"
	exec_cmd_uboot $sid "setenv sysid\r"
	exec_cmd_uboot $sid "setenv bom\r"
}

proc linux_login { sid user password} {
	global linux_promt
	set timeout 10
	set login_found 0
	set retry_count 12

	for {set x 0} { $x<$retry_count } {incr x} {
		expect  {
			-i $sid timeout { continue }
			-i $sid "Generating a SSHv2" { log_progress_step 10 "Booting in progress..." }
			-i $sid "Press any key to continue" {
				send -i $sid "\r"
				set login_found 1
				set x $retry_count
			}
		}
	}

	if {$login_found < 1} {
        error_critical "Failed to login"
    }

	set timeout 10

	expect  {
		-i $sid "Username: " {
			send -i $sid "$user\r"
			expect  {
				-i $sid timeout { error_critical "Failed to login" }
				-i $sid "Password: " { send -i $sid "$password\r"}
			}
		}
		-i $sid timeout { "Failed to login" }
	}

	expect -i $sid timeout {
		error_critical "Login promt not found"
	} "EdgeSwitch X#"

	set timeout 5
	#send ctrl+t
	send \x14

	expect  {
		-i $sid "Diagnostics:" { send -i $sid "rtk2379"; sleep 1; send -i $sid "\r" }
		-i $sid timeout { error_critical "Login promt not found" }
	}

	expect  {
		-i $sid "Press ENTER to continue" { send -i $sid "\r" }
		-i $sid timeout { error_critical "Login promt not found" }
	}

	expect  {
		-i $sid "Enter Selection:" { send -i $sid "s"; sleep 1;	send -i $sid "\r"}
		-i $sid timeout { error_critical "Login promt not found" }
	}

	expect  -i $sid $linux_promt { } \
	timeout { error_critical "Login promt not found" }

}

proc setup_uboot_env { sid } {
	global model_string
	global mac_addr
	global ip
	global tftpserver
	exec_cmd_uboot $sid "setenv ethaddr $mac_addr\r"
	exec_cmd_uboot $sid "setenv ipaddr $ip\r"
	exec_cmd_uboot $sid "setenv serverip $tftpserver\r"
	exec_cmd_uboot $sid "setenv boardmodel $model_string\r"
	exec_cmd_uboot $sid "saveenv\r"
}

proc check_update_progress { sid progress_increment } {
	global progress

	set timeout 15
	while { 1 } {
		expect {
			-i $sid "success" { log_debug "Update sucedded"; return }
			-i $sid "Comparing file ......" {
				log_debug "Flashed. Checking.";
				if {$progress_increment != 0} {
					log_progress_step $progress_increment "Comparing..."
				}
				set timeout 60
			}
			-i $sid "%" {}
			-i $sid "#" {}
			-i $sid "Erasing"
			{
				if {$progress_increment != 0} {
					log_progress_step $progress_increment "Erasing..."
				}
			}
			-i $sid "Writting" {
				if {$progress_increment != 0} {
					log_progress_step $progress_increment "Writting..."
				}
			}
			timeout { error_critical "Firmware upgrade failed!" }
		  	eof {error_critical "Firmware upgrade failed!"}
		}
	}
}

proc update_bootloader { sid } {
	send -i $sid "upgrade loader esx-u-boot.bin\r"
	check_update_progress $sid 0
	wait_for_promt_uboot $sid
}

proc update_firmware { sid } {
	send -i $sid "upgrade runtime esx-vmlinux.bix\r"
	check_update_progress $sid 10
	wait_for_promt_uboot $sid
}

proc clean_up { sid } {
	exec_cmd_uboot $sid "setenv ipaddr 192.168.1.20\r"
	exec_cmd_uboot $sid "setenv serverip 192.168.1.254\r"
	exec_cmd_uboot $sid "saveenv\r"
	exec_cmd_uboot $sid "flerase name JFFS2_CFG\r"
	exec_cmd_uboot $sid "flerase name JFFS2_LOG\r"
}

proc handle_boot { } {
	global ip
	global tftpserver
	global device_type
	global tty_sid
	global dev
	global mac_addr
	global dev_id
	global dev_bom
	global progress

	set progress 0

	stop_uboot $tty_sid
	log_progress_step 0 "Got into U-Boot"
	set progress [expr {$progress + 0}]

	setup_uboot_env $tty_sid
	log_progress_step 5 "Updating bootloader..."
	update_bootloader $tty_sid

	log_debug "Reseting..."
	send -i $tty_sid "reset\r"
	stop_uboot $tty_sid
	setup_uboot_env $tty_sid

	log_progress_step 5 "Writing HW details..."
	write_hw_info $tty_sid $mac_addr $device_type $dev_bom

	log_progress_step 5 "Updating firmware..."
	update_firmware $tty_sid

	log_debug "Cleaning environment..."
	clean_up $tty_sid

	log_progress_step 5 "Booting..."

	send -i $tty_sid "boota\r"
	linux_login $tty_sid "ubnt" "ubnt"

	log_progress_step 20 "Downloading helper..."
	download_helper $tty_sid

	log_progress_step 20 "Signing..."
	do_security $tty_sid

	log_progress 100 "Completed with $mac_addr"
}

proc main_detector { } {
	set timeout 30
	global tty_sid
	sleep 1
	send -i $tty_sid \003
	send -i $tty_sid "\r"

	log_progress 1 "Waiting - PLUG in the device..."

	expect -i $tty_sid "Board: RTL838x" { handle_boot } \
		-i $tty_sid timeout { error_critical "Device not found!" }
}

#
# action starts here
#
set ver_file "/etc/skel/Desktop/version.txt"
if { [file exists $ver_file] == 1} {
	set file [open $ver_file r]
	while {[gets $file buf] != -1} {
		send_user "FCD version $buf\n\r"
	}
	close $file
} else {
	send_user "NO version found\r"
}

spawn -open [open /dev/$dev w+]
stty 115200 < /dev/$dev
stty raw -echo < /dev/$dev

set tty_sid $spawn_id
log_debug "tty_sid $tty_sid"

main_detector

