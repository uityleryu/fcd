#!/usr/bin/expect --
set erasecal [lindex $argv 0]
set dev [lindex $argv 1]
set idx [lindex $argv 2]
set boardid [lindex $argv 3]
set calimg [lindex $argv 4]
set tftpserver [lindex $argv 5]
#set facimg "$boardid.factorybin"
set cfeimg "$boardid.cfe"
set user "ubnt"
set passwd "ubnt"

set UAP_ID "e502"
set UAPLR_ID "e512"
set UAPMINI_ID "e522"
set UAPOUT_ID "e532"
set UAPWASP_ID "e572"
set UAPWASPLR_ID "e582"
set UAPHSR_ID "e562"
set UAPOUT5_ID "e515"
set UAPPRO_ID "e507"

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



log_debug "launched with params: erasecal=$erasecal dev=$dev; idx=$idx; boardid=$boardid; calimg=$calimg; tftpserver=$tftpserver"

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

proc stop_cfe {} {

    log_debug "Stoping CFE"
    #send "any key"
    
    set timeout 30
    expect  { 
       "Device eth0:" { 
            sleep 2
            send \003 
      } timeout {  
            error_critical "Device not found!"
      }  
 
    }
    set timeout 5
    expect timeout {
    } "CFE>"
    
    sleep 2 
    send \003
    set timeout 30
    expect timeout {
        error_critical "CFE prompt not found !"
    } "CFE>"
}

proc set_network_env { {use_temp_mac 0} } {
    global tftpserver
    global ip
    global idx
    global netmask
    set max_loop 3
    set pingable 0

    if { $use_temp_mac == 1 } {
        set somehex [format %02x [expr { $idx & 0xff }]]
        set temp_mac "00156de900$somehex"
    }

    for { set i 0 } { $i < $max_loop } { incr i } {

        if { $i != 0 } {
            stop_cfe
        }

        sleep 2
        if { $use_temp_mac == 1 } {
            #send "ifconfig eth0 -addr=$ip -mask=$netmask -hwaddr=$temp_mac\r"
            send "ifconfig eth0 -hwaddr=$temp_mac -auto\r"
        } else {
            #send "ifconfig eth0 -addr=$ip -mask=$netmask\r"
            send "ifconfig eth0 -auto\r"
        }
        set timeout 15
        expect timeout { 
            error_critical "CFE prompt not found !" 
        } "CFE>"

        sleep 1
    
        send "ping $tftpserver\r"
        set timeout 15
        expect timeout {
            error_critical "Unknown response for ping !"
        } -re ".* is (.*)\r.*"

        set alive_str $expect_out(1,string)

        set timeout 5
        expect timeout { 
            error_critical "CFE prompt not found !"
        } "CFE>"

        if { [string equal $alive_str "alive"] == 1 } {
            set pingable 1
            break
        } else {
            send "reboot\r"
        }
    }

    if { $pingable != 1 } {
        error_critical "$tftpserver is not reachable !"
    }
}

proc update_cfe { cfeimg } {
    global tftpserver

    #log_debug "CFE image $cfeimg\r"

    #start CFE flashing
    sleep 1
    send "flash -noheader $tftpserver:$cfeimg flash1.boot\r"
    set timeout 30 
    expect timeout { 
        error_critical "Timeout downloading CFE" 
    } "Programming.*"
    set timeout 60
    expect timeout {
        error_critical "Fail to program CFE"
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    send "nvram erase\r"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    sleep 5

    send "reboot\r"
    set timeout 15
    expect timeout { 
        error_critical "Timeout regenerating NVRAM" 
    } "Committing NVRAM.*\r"
}

proc update_firmware { fwimg {partid 0} } {
    global tftpserver

    #log_debug "firmware image $fwimg\r"

    #start firmware flashing
    sleep 1
    if { $partid != 1 } {
        send "flash -noheader $tftpserver:$fwimg flash1.trx\r"
    } else {
        send "flash -noheader $tftpserver:$fwimg flash1.trx2\r"
    }
    set timeout 30 
    expect timeout { 
        error_critical "Timeout downloading $tftpserver:$fwimg" 
    } "Programming.*"
    set timeout 180
    expect timeout {
        error_critical "Fail programming $fwimg to part $partid"
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"
}

proc handle_cfe { {wait_prompt 0} } {
    global calimg
    #global facimg
    global cfeimg
    global erasecal

    if { $wait_prompt == 1 } {
        stop_cfe
    }

    log_progress 5 "Got INTO CFE"

    set_network_env 1

    update_cfe $cfeimg
    log_progress 10 "bootloader updated"

    stop_cfe

    set_network_env 1

    if { [string equal $erasecal "-e"] == 1 } {
        # erase Calibration Data
        sleep 1
        send "uclearcal\r"
        set timeout 20 
        expect timeout {
            error_critical "Erase calibration data failed !" 
        } "*** command status = 0"
        set timeout 5
        expect timeout { 
            error_critical "CFE prompt not found !"
        } "CFE>"
        log_progress 20 "Calibration Data erased"
    }

    sleep 1
    send "uclearcfg\r"
    set timeout 30 
    expect timeout {
        error_critical "Erase configuration failed !" 
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"
    log_progress 30 "Configuration erased"

    update_firmware $calimg 0
    log_progress 60 "Calibration firmware image updated"
    #update_firmware $facimg 1
    #log_progress 90 "Manufacturing firmware image updated"

    sleep 1
    send "uclearnvram\r"
    set timeout 20 
    expect timeout {
        error_critical "Erase NVRAM failed !" 
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    sleep 1
    send "reboot\r"
    
    set timeout 40
    expect timeout {
        error_critical "Device is not responding after restart !" 
    } "Hit enter to continue"

    log_progress 100 "Completed" 

}

proc handle_login { user passwd } {
    set timeout 20
    send "$user\r"
    log_debug "Sent username..."
    expect "Password:"
    send "$passwd\r"
    log_debug "Sent password..."
    sleep 2
    send "reboot\r"

    handle_cfe 1
}


proc main_detector { } {
    global user
    global passwd

    set timeout 30
    sleep 1
    send \003
    send "\r"
    sleep 1
    send "\r"

    log_progress 1 "Waiting - PLUG in the device..."

    # FIXME: what's the prompt of broadcom image?
    expect  "CFE mem:" { handle_cfe 1 } \
        "CFE>" { handle_cfe } \
        "UBNT login:" { handle_login $user $passwd } \
        timeout { error_critical "Device not found!" }
}

#
# action starts here
#
set file [open ~/Desktop/version.txt r]
while {[gets $file buf] != -1} {
    send_user "FCD version $buf\n\r"
}
close $file


spawn -open [open /dev/$dev w+]
stty 115200 < /dev/$dev
stty raw -echo < /dev/$dev

main_detector

