#!/usr/bin/expect --
set erasecal [lindex $argv 0]
set dev [lindex $argv 1]
set idx [lindex $argv 2]
set boardid [lindex $argv 3]
set fwimg [lindex $argv 4]
set tftpserver [lindex $argv 5]
set prompt "ar7240>"
set user "ubnt"
set passwd "ubnt"
set cmd_prefix ""

set UAP_ID          "e502"
set UAPLR_ID        "e512"
set UAPMINI_ID      "e522"
set UAPOUT_ID       "e532"
set UAPWASP_ID      "e572"
set UAPWASPLR_ID    "e582"
set UAPHSR_ID       "e562"
set UAPOUT5_ID      "e515"
set UAPPRO_ID       "e507"
set UAPGEN2LR_ID    "e527"
set UAPGEN2LITE_ID  "e517"
set UAPGEN2PRO_ID   "e537"
set UAPGEN2EDU_ID   "e547"
set UAPGEN2MESH_ID  "e557"
set UAPGEN2OUT_ID   "e567"
set UAPGEN2IW_ID    "e587"
set UAPGEN2IWPRO_ID "e597"

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



log_debug "launched with params: erasecal=$erasecal dev=$dev; idx=$idx; boardid=$boardid; fwimg=$fwimg; tftpserver=$tftpserver"

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

proc uboot_finish { } {
   global prompt

    log_progress 50 "Restarting..."
    send "\r"
    expect $prompt
    send "re\r"
}

proc stop_uboot {} {
    global prompt
    log_debug "Stoping U-boot"
    #send "any key"
    
    set timeout 30
    expect  "Hit any key to stop autoboot" { send "\r"} \
    timeout { error_critical "Device not found!" }  

    set timeout 5
    expect timeout {
    } $prompt
    
    sleep 1 
    send "\r" 
    set timeout 30
    expect timeout {
        error_critical "U-boot prompt not found !"
    } $prompt
}

proc set_network_env {} {
    global tftpserver
    global ip
    global prompt

    set max_loop 3
    set pingable 0

    for { set i 0 } { $i < $max_loop } { incr i } {

        if { $i != 0 } {
            stop_uboot
        }

        sleep 1
        send "setenv ipaddr $ip\r"
        set timeout 15
        expect timeout { 
            error_critical "U-boot prompt not found !" 
        } $prompt

        sleep 1
        send "setenv serverip $tftpserver\r"
        set timeout 15
        expect timeout { 
            error_critical "U-boot prompt not found !" 
        } $prompt

        sleep 5
    
        send "ping $tftpserver\r"
        set timeout 15
        expect timeout {
            error_critical "Unknown response for ping !"
        } -re ".*host $tftpserver (.*) alive"

        set alive_str $expect_out(1,string)

        set timeout 5
        expect timeout { 
        } $prompt

        if { [string equal $alive_str "is"] == 1 } {
            set pingable 1
            break
        } else {
            send "re\r"
        }
    }

    if { $pingable != 1 } {
        error_critical "$tftpserver is not reachable !"
    }
}

proc may_have_non_ubntapp_uboot { boardid } {
    global UAP_ID
    global UAPLR_ID
    global UAPMINI_ID
    global UAPOUT_ID
    global UAPHSR_ID
    global UAPOUT5_ID
    global UAPPRO_ID

    if { [string equal -nocase $boardid $UAP_ID] == 1
         || [string equal -nocase $boardid $UAPLR_ID] == 1
         || [string equal -nocase $boardid $UAPMINI_ID] == 1
         || [string equal -nocase $boardid $UAPOUT_ID] == 1
         || [string equal -nocase $boardid $UAPHSR_ID] == 1
         || [string equal -nocase $boardid $UAPOUT5_ID] == 1
         || [string equal -nocase $boardid $UAPPRO_ID] == 1 } {
         return 1
    } else {
        return 0
    }
}

proc rootfs_is_squashfs { boardid } {
    global UAP_ID
    global UAPLR_ID
    global UAPMINI_ID
    global UAPOUT_ID
    global UAPOUT5_ID
    
    if { [string equal -nocase $boardid $UAP_ID] == 1
         || [string equal -nocase $boardid $UAPLR_ID] == 1
         || [string equal -nocase $boardid $UAPMINI_ID] == 1
         || [string equal -nocase $boardid $UAPOUT_ID] == 1
         || [string equal -nocase $boardid $UAPOUT5_ID] == 1 } {
         return 1
    } else {
        return 0
    }
}

proc has_ubntfsboot_dual_image { boardid } {
    global UAPHSR_ID
    global UAPPRO_ID

    if { [string equal -nocase $boardid $UAPPRO_ID] == 1 
         || [string equal -nocase $boardid $UAPHSR_ID] == 1 } {
         return 1
    } else {
        return 0
    }
}

proc has_dragonfly_cpu { boardid } {
    global UAPGEN2LITE_ID
    global UAPGEN2LR_ID
    global UAPGEN2PRO_ID
    global UAPGEN2EDU_ID
    global UAPGEN2MESH_ID
    global UAPGEN2OUT_ID
    global UAPGEN2IW_ID
    global UAPGEN2IWPRO_ID

    if {
            [string equal -nocase $boardid $UAPGEN2LITE_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2LR_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2PRO_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2EDU_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2MESH_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2OUT_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2IW_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2IWPRO_ID] == 1
                                                                    } {
         return 1
    } else {
        return 0
    }
}

proc update_new_firmware { boardid } {                                              
    global cmd_prefix
    global bootloader_prompt
    global fwimg
    global ip
    global prompt
    log_debug "Firmware $fwimg\r"

    sleep 1

    set is_dragonfly [has_dragonfly_cpu $boardid]
    if { $is_dragonfly == 1 }  {
        send "$cmd_prefix uclearenv; setenv mtdparts \"mtdparts=ath-nor0:384k(u-boot),64k(u-boot-env),1280k(uImage),14528k(rootfs),64k(mib0),64k(ART)\";$cmd_prefix uappinit \r"
        set timeout 30
        expect timeout {
            error_critical "UBNT Application failed to initialize!"
        } "UBNT application initialized"
    } else {
        send "$cmd_prefix uclearenv\r"
        set timeout 20
        expect timeout {
            error_critical "u-boot-env clear failure"
        } "done"
    }
    set timeout 5
    expect timeout {
        error_critical "U-boot prompt not found !"
    } $prompt

    #start firmware flashing
    sleep 1
    send "setenv do_urescue TRUE;urescue -u -e\r"
    set timeout 10       
        expect timeout {
        error_critical "Failed to start urescue"
    } "Waiting for connection"

    sleep 2
    send_user "atftp --option \"mode octet\" -p -l /tftpboot/$fwimg $ip"
    exec atftp --option "mode octet" -p -l /tftpboot/$fwimg $ip 2>/dev/null >/dev/null

    sleep 2
    set timeout 60
    send "$cmd_prefix uwrite -f \r"
    expect timeout {
        error_critical "Failed to download firmware !"
    } "Firmware Version:"
    log_progress 65 "Firmware loaded"
    set timeout 15
    expect timeout {
        error_critical "Failed to flash firmware (u-boot) !"
    } "Copying partition 'u-boot' to flash memory:"
    
    log_progress 60 "Flashing firmware..."

    set dual [has_ubntfsboot_dual_image $boardid]
    if { $dual == 1 } {
        set timeout 15
        expect timeout {
            error_critical "Failed to flash firmware (jffs2) !"
        } "Copying partition 'jffs2' to flash memory:"

        log_progress 80 "Flashing firmware..."
    } else {
        set timeout 60
        expect timeout { 
            error_critical "Failed to flash kernel firmware (kernel|uImage) !"
        } -re "Copying partition '(kernel|uImage)' to flash memory:"

        log_progress 70 "Flashing firmware..."

        set has_squashfs [rootfs_is_squashfs $boardid]
        if { $has_squashfs == 1 } {
       	   set timeout 15
           expect timeout {
               error_critical "Failed to flash rootfs firmware (rootfs) !"
           } "Copying partition 'rootfs' to flash memory:"
           log_progress 90 "Flashing firmware..."
	    }
    }
    
    set timeout 180
    expect timeout {
        error_critical "Failed to flash firmware !"
    } "Firmware update complet"
    
    log_progress 90 "Firmware flashed"
}

proc update_old_firmware { boardid } {
    global fwimg
    global ip

    log_debug "Firmware $fwimg\r"

    #start firmware flashing
    sleep 1
    send "urescue -f -e\r"
    set timeout 10 
        expect timeout { 
        error_critical "Failed to start urescue" 
    } "Waiting for connection"
    
    exec atftp --option "mode octet" -p -l /tftpboot/$fwimg $ip 2>/dev/null >/dev/null
    
    set timeout 30
    
    expect timeout {
        error_critical "Failed to download firmware !" 
    } "Firmware Version:"
    
    log_progress 50 "Firmware loaded"
    
    set timeout 15
    expect timeout { 
        error_critical "Failed to flash firmware !"
    } "Copying partition 'u-boot' to flash memory:"
    
    log_progress 60 "Flashing firmware..."

    set dual [has_ubntfsboot_dual_image $boardid]
    if { $dual == 1 } {
        set timeout 15
        expect timeout { 
            error_critical "Failed to flash firmware !"
        } "Copying partition 'jffs2' to flash memory:"

        log_progress 80 "Flashing firmware..."
    } else {
        set timeout 15
        expect timeout { 
            error_critical "Failed to flash kernel firmware !"
        } "Copying partition 'kernel' to flash memory:"

        log_progress 70 "Flashing firmware..."

        set has_squashfs [rootfs_is_squashfs $boardid]
        if { $has_squashfs == 1 } {
       	   set timeout 15
           expect timeout { 
               error_critical "Failed to flash rootfs firmware !"
           } "Copying partition 'rootfs' to flash memory:"
           log_progress 90 "Flashing firmware..."
	    }
    }
    
    set timeout 180
    expect timeout { 
        error_critical "Failed to flash firmware !" 
    } "Firmware update complet"
    
    log_progress 90 "Firmware flashed"
}

proc handle_uboot { {wait_prompt 0} } {
    global fwimg
    global mac
    global ip
    global regdmn
    global boardid
    global erasecal
    global cmd_prefix
    global prompt

    if { $wait_prompt == 1 } {
        stop_uboot
    }

    log_progress 5 "Got INTO U-boot"
    
    set_network_env
    log_progress 10 "Network environment set"

    if { [string equal $cmd_prefix ""] == 0 } {
        send "$cmd_prefix uappinit\r"
        set timeout 20 
        expect timeout { 
            error_critical "Erase calibration data failed !" 
        } "UBNT application initialized"
        set timeout 5
        expect timeout { 
        } $prompt
    }

    if { [string equal $erasecal "-e"] == 1 } {
        # erase Calibration Data
        sleep 2
        send "$cmd_prefix uclearcal -f -e\r"
        set timeout 20 
        expect timeout { 
            error_critical "Erase calibration data failed !" 
        } "Done."
        set timeout 5
        expect timeout { 
        } $prompt
        log_progress 30 "Calibration Data erased"
    }

    if { [string equal $cmd_prefix ""] == 1 } {
        update_old_firmware $boardid
    } else {
        update_new_firmware $boardid
    }

    set timeout 15
    expect timeout {
        error_critical "Device is not responding after restart !" 
    } "Hit any key to stop autoboot"

    log_progress 100 "Completed" 

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

    if { [expr $major_id] == 99 || [expr $major_id] == 1 && [expr $minor_id] >= 5 } {
       log_debug "ubntapp firmware"
       set cmd_prefix "go \${ubntaddr} " 
    }
} 

proc main_detector { } {
    global cmd_prefix
    global prompt
    global boardid
    set timeout 30
    sleep 1
    send \003
    send "\r"

    if { [may_have_non_ubntapp_uboot $boardid] == 1 } {
        expect {
            # check for boards with ubntapp firmware and set appropiate flags.
            -re ".*U-Boot (unifi|unifi-master.|unifi-v|)(\[0-9.]+)-(.*)" {
                set id $expect_out(2,string)
                regexp "(\[0-9]+)\.?(\[0-9]*)\.?(\[0-9]*)(.*)" $id ignore major minor release build

                if { $minor == "" } {
                    set minor "0"
                }
                find_version $major $minor
                handle_uboot 1
            } $prompt {
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
    } else {
        expect {
            # check for boards with ubntapp firmware and set appropiate flags.
            "Board: Copyright Ubiquiti Networks Inc" {
                log_debug "ubntapp firmware"
                set cmd_prefix "go \${ubntaddr} " 
                handle_uboot 1
            } $prompt {
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

set is_dragonfly [has_dragonfly_cpu $boardid]
if { $is_dragonfly == 1 }  {
    set prompt "ath>"
}

log_progress 1 "Waiting - PLUG in the device..."
main_detector

