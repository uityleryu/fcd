#!/usr/bin/expect --
set dev [lindex $argv 0]
set idx [lindex $argv 1]
set boardid [lindex $argv 2]
set fwimg [lindex $argv 3]
set tftpserver [lindex $argv 4]
set brd_type "unknown"
set vxAE ""
set flash_size ""
set cmd_prefix ""

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

proc log_debug { msg } {
    set d [clock format [clock seconds] -format {%H:%M:%S}]
    send_user "\r\nDEBUG: $d $msg\r\n"
}



log_debug "launched with params: dev=$dev; idx=$idx; boardid=$boardid; fwimg=$fwimg; tftpserver=$tftpserver"


if { $tftpserver == "" } {
    set tftpserver "192.168.1.19"
}

if {![regexp {(\d+)} $idx]} {
        send_user "Invalid index! Defaulting to 0...\r\n"
        set idx 0
}
set ip_end [expr 21 + $idx]
set ip "192.168.1.$ip_end"


#
# PROCEDURES
#

proc handle_login { } {
    set timeout 20
    log_progress 2 "Detected device in login mode"
    send "ubnt\r"
    log_debug "Sent username..."
    expect "Password:"
    send "ubnt\r"
    log_debug "Sent password..."
    sleep 2
    send "reboot\r"

    expect "== Executing boot script in" { 
            handle_redboot 1 
            return
            } \
        timeout { error_critical "Device not found!" }
        send \003
        process_redboot
}

proc handle_logged_in { } {
    set timeout 20
    log_progress 2 "Detected device in logged in mode"
    send "reboot\r"
    expect "== Executing boot script in" { 
            handle_redboot 1
            return 
        } \
        timeout { error_critical "Device not found!" }
        send \003
        process_redboot
}

proc uboot_finish { } {

    log_progress 50 "Restarting..."
    send "\r"
    expect "ar7240>"
    send "re\r"
}


proc stop_uboot {} {

    log_debug "Stoping U-boot"
    #send "any key"
    
    set timeout 30
    expect  "Hit any key to stop autoboot" { send "\r"} \
    timeout { error_critical "Device not found!" }  
    
    set timeout 30
    expect timeout {
    error_critical "U-boot prompt not found !"
    } "ar7240>"
}

proc handle_uboot { {wait_prompt 0} } {
    global ip
    global tftpserver
    global fwimg
    global cmd_prefix

    if { $wait_prompt == 1 } {
        stop_uboot
    }

    log_progress 10 "Got INTO U-boot"
    
    send "\r" 

    set timeout 30
    expect timeout {
    error_critical "U-boot prompt not found !"
    } "ar7240>"

    if { $cmd_prefix != "" } {

      set timeout 30
      send "$cmd_prefix uappinit\r"
      expect timeout {
      error_critical "U-boot prompt not found !"
      } "ar7240>"

    }
    set send_slow {1 .3}

    send "setenv serverip $tftpserver\r"

    log_progress 12 "Set server IP"
    
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } "ar7240>"
    
    send "setenv ipaddr $ip\r"
    
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } "ar7240>"
    
    log_progress 17 "Set local IP"
    
    send "printenv\r"
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } "ar7240>"


    #check board SSID
    log_debug "Getting ssid"
    send "md.b 0xbfff1016 2\r"

    expect timeout {
        error_critical "Unable to get SSID"
    } -re "(bfff1016: .{2} .{2})"

    set ssid $expect_out(0,string)

    log_debug "found ssid:"
    log_debug $ssid
    
    if {$ssid == "bfff1016: e4 05" || $ssid == "bfff1016: e4 a5"}   {
        send_user "AIRWIRE found\r"
        set ur_str "urescue -f\r"
    } else {
	if { $cmd_prefix == "" } {
           set ur_str "urescue -f -e\r"
	} else {
           set ur_str "set do_urescue TRUE; urescue -e\r"
	}
    }


    send $ur_str

    exec atftp --option "mode octet" -p -l /tftpboot/$fwimg $ip 2>&1 > /dev/null
    
    set timeout 25
    expect timeout {
          error_critical "U-boot prompt not found !"
    } "ar7240>"
    # New firmware 
    if { $cmd_prefix != "" } {
        set timeout 25
        expect timeout {
             error_critical "U-boot prompt not found !"
        } "ar7240>"

	send "$cmd_prefix  uwrite -f \r"
   }
    
    set timeout 30
    
    expect timeout { 
        error_critical "Failed to download firmware !" 
    } "Firmware Version:"
    
    log_progress 30 "Firmware loaded"
    
    set timeout 15
    expect timeout { 
        error_critical "Failed to flash firmware !"
    } "Copying partition 'u-boot' to flash memory:"
    
    log_progress 40 "Flashing firmware..."

    set timeout 15
    expect timeout { 
        error_critical "Failed to flash firmware !"
    } "Copying partition 'kernel' to flash memory:"

    log_progress 50 "Flashing firmware..."

    set timeout 25
    expect timeout { 
        error_critical "Failed to flash firmware !"
    } "Copying partition 'rootfs' to flash memory:"

    log_progress 80 "Flashing firmware..."
    
    
    
    set timeout 180
    expect timeout { 
        error_critical "Failed to flash firmware !" 
    } "Firmware update complete."
    
    log_progress 90 "Firmware flashed"

    set timeout 15
    
    expect timeout { 
        error_critical "Device is not responding after restart !" 
    } "Hit any key to stop autoboot"

    
    log_progress 100 "Complete" 

}

proc handle_login { user passwd } {
    set timeout 20
    log_progress 2 "Detected device in login mode"
    send "$user\r"
    log_debug "Sent username..."
    expect "Password:"
    send "$passwd\r"
    log_debug "Sent password..."
    sleep 2
    send "reboot\r"

    main_detector
}

proc find_version { major_id minor_id } {
    global cmd_prefix
 
    log_debug "Major=$major_id, Minor=$minor_id"

    if { [expr $major_id] == 1 && [expr $minor_id] >= 5 } {
       log_debug "ubntapp firmware"
       set cmd_prefix "go \${ubntaddr} " 
    }
} 

proc main_detector { } {
    set timeout 30
    sleep 1
    send \003
    send "\r"


    expect {
         # check for boards with ubntapp firmware and set appropiate flags.
         -re ".*U-Boot (unifi|unifi-master.|unifi-v|)(\[0-9.]+)-(.*)" {
		set id $expect_out(2,string)
		regexp "(\[0-9]+)\.?(\[0-9]*)\.?(\[0-9]*)(.*)" $id ignore major minor release build

		log_debug "major=$major  minor=$minor"

		if { $minor == "" } {
		  set minor "0"
                }
                find_version $major $minor
                handle_uboot 1
        } "ar7240>" {
                send "reset \r"
                main_detector
        } "(none) login:" {
                 handle_login root 5up
        } "UBNT login:" {
                 handle_login $user $passwd
        } timeout {
                 error_critical "Device not found!"
        }
   }
}


#
# action starts here
#
#set file [open ~/Desktop/version.txt r]
#while {[gets $file buf] != -1} {
#   send_user "FCD version $buf\n\r"
#}
#close $file
send_user "FCD version develop_4_root_KM-Dell_110513_1746\n\r"


spawn -open [open /dev/$dev w+]
stty 115200 < /dev/$dev
stty raw -echo < /dev/$dev

log_progress 1 "Waiting - PLUG in the device..."
main_detector

