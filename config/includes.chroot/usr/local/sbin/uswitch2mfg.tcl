#!/usr/bin/expect --
set erasecal [lindex $argv 0]
set dev [lindex $argv 1]
set idx [lindex $argv 2]
set boardid [lindex $argv 3]
set fwimg [lindex $argv 4]
set tftpserver [lindex $argv 5]
set user "ubnt"
set passwd "ubnt"
set bootloader_prompt "u-boot>"
set cmd_prefix "go \${ubntaddr} "
set use_64mb_flash 0
set fakemac "00:90:4c:06:a5:7$idx"

# model ID
set USW_XG         "eb20"
set USW_6XG_150    "eb23"
set USW_24_PRO     "eb36"
set USW_48_PRO     "eb67"

set flash_mtdparts_64M "mtdparts=spi1.0:1920k(u-boot),64k(u-boot-env),64k(shmoo),31168k(kernel0),31232k(kernel1),1024k(cfg),64k(EEPROM)"
set flash_mtdparts_32M "mtdparts=spi1.0:768k(u-boot),64k(u-boot-env),64k(shmoo),15360k(kernel0),15424k(kernel1),1024k(cfg),64k(EEPROM)"

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

proc stop_uboot { {wait_time 30} } {
    global cmd_prefix
    global bootloader_prompt

    log_debug "Stoping U-boot"

    # send "any key"
    set timeout $wait_time
    expect {
        "Hit any key to stop autoboot" {
            send "\r"
        } timeout {
            error_critical "Device not found!"
        }
    }

    # set timeout to see the bootload prompt if there is no prompt after
    # timeout, no error return and just do Enter to see if the prompt
    # show up.
    set timeout 5
    expect timeout {
    } "$bootloader_prompt"

    sleep 1
    send "\r"
    set timeout 30
    expect timeout {
        error_critical "U-boot prompt not found !"
    } "$bootloader_prompt"
}

proc check_mdk {} {
    global bootloader_prompt

    log_debug "Checking if U-boot has MDK"

    send "\r"
    set timeout 30
    expect timeout {
        error_critical "U-boot prompt not found !"
    } "$bootloader_prompt"

    sleep 1
    send "mdk_drv\r"
    expect {
        # DUT with mdk and initialized
        # Goto uboot and do urescure
        "Found MDK device" {
            handle_urescue
            log_progress 100 "Back to ART has completed"
        # DUT with mdk but not initialized
        # Goto uboot and do urescure
        } "MDK initialized failed" {
            handle_urescue
            log_progress 100 "Back to ART has completed"
        # DUT without mdk
        # Goto linux upgrade uboot first
        } "Unknown command" {
            set timeout 30
            expect timeout {
                error_critical "U-boot prompt not found !"
            } "$bootloader_prompt"
            sleep 1
            handle_uboot
        }
    }
}

proc handle_urescue {} {
    global bootloader_prompt
    global cmd_prefix
    global fwimg
    global ip
    global tftpserver
    global erasecal
    global boardid
    global USW_XG
    global USW_6XG_150
    global USW_24_PRO
    global USW_48_PRO
    global fakemac

    set max_loop 4

    log_debug "Starting in the urescue mode to program the firmware"

    # Loop for uappinit retry
    # Adding this retry because sometime mdk_drv failed to init
    for { set i 0 } { $i < $max_loop } { incr i } {
        if { $i == $max_loop - 1 } {
            error_critical "U-Boot Init mdk_drv retry max reach"
        }

        set timeout 10

        sleep 1
        send "$cmd_prefix uappinit\r"
        expect timeout {
            error_critical "U-boot prompt not found !"
        } "$bootloader_prompt"

        # set Board ID
        sleep 2
        send "$cmd_prefix usetbid $boardid\r"
        expect timeout {
            log_error "usetbid set failed !"
            continue
        } "Done."
        
        expect timeout {
            error_critical "U-boot prompt not found !"
        } "$bootloader_prompt"

        if { [string equal -nocase $boardid $USW_XG] == 1 ||
            [string equal -nocase $boardid $USW_6XG_150] == 1 ||
            [string equal -nocase $boardid $USW_24_PRO] == 1 ||
            [string equal -nocase $boardid $USW_48_PRO] == 1 } {
            sleep 3

            send "mdk_drv\r"
            expect {
                "Found MDK device" {
                    break
                } "MDK is already initialized" {
                    break
                } "MDK initialized failed" {
                    log_warn  "Fail to init mdk_drv...retrying"
                    continue
                } timeout {
                    error_critical "U-boot prompt not found !"
                }
            }
        }
    }

    set max_loop 4
    # Loop for set network and ping retry
    for { set i 0 } { $i < $max_loop } { incr i } {
        set timeout 10

        if { $i == $max_loop - 1 } {
            error_critical "Ping retry max reach, Stop trying"
        }

        send "setenv ethaddr $fakemac\r"
        expect timeout {
            error_critical "U-boot prompt not found !"
        } "$bootloader_prompt"

        send "setenv serverip $tftpserver\r"
        expect timeout {
            error_critical "U-boot prompt not found !"
        } "$bootloader_prompt"

        send "setenv ipaddr $ip\r"
        expect timeout {
            error_critical "U-boot prompt not found !"
        } "$bootloader_prompt"

        sleep 1
        send "ping $tftpserver\r"
        set timeout 10
        expect timeout {
            log_warn "Can't ping the FCD server !...retrying"
            sleep 3
            continue
        } "host $tftpserver is alive"
        break
    }

    sleep 2
    send "urescue -u\r"
    set timeout 60
    expect {
        "TFTPServer started. Wating for tftp connection..." {
            log_debug "TFTP is waiting for file"
        } "Listening for TFTP transfer" {
            # this expecting phrase that needs from US-6XG-150
            log_debug "TFTP is waiting for file"
        } timeout {
            error_critical "Failed to start urescue"
        }
    }
    log_progress 70 "DUT is requesting the firmware from FCD server"

    sleep 2
    send_user "atftp --option \"mode octet\" -p -l /tftpboot/$fwimg $ip\r"
    exec atftp --option "mode octet" -p -l /tftpboot/$fwimg $ip 2>/dev/null >/dev/null

    set timeout 150
    expect timeout {
        error_critical "U-boot prompt not found !"
    } "$bootloader_prompt"

    log_debug "FCD completed the firmware uploading"

    # Erase cal only at the end as mdk needs mac address
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
        } "$bootloader_prompt"
        log_debug "Calibration Data erased"
    }

    erase_linux_config $boardid

    log_progress 80 "DUT completed erasing the calibration data"

    sleep 1
    send "$cmd_prefix uwrite -f\r"
    set timeout 70
    expect timeout {
        error_critical "Get firmware version error"
    } -re "Firmware Version: .*"

    log_debug "DUT found the firmware version"

    expect timeout {
        error_critical "Download Image file verify failure"
    } "Image Signature Verfied, Success."

    log_debug "Download image verify pass."

    expect timeout {
        error_critical "Failed to flash u-boot !"
    } "Copying 'u-boot' partition. Please wait... :  done"

    log_debug "u-boot flashed"


    set timeout 600
    expect timeout {
        error_critical "Failed to flash kernel0 !"
    } "Copying to 'kernel0' partition. Please wait... :  done."

    log_debug "DUT finish to program the firmware to flash kernel0"

    set timeout 600
    expect timeout {
        error_critical "Failed to flash firmware !"
    } "Firmware update complete."

    log_debug "DUT completed programming the firmware into flash"
}

proc handle_login { user passwd reboot } {
    set timeout 20

    send "$user\r"
    log_debug "Sent username..."
    expect "Password:"
    send "$passwd\r"
    log_debug "Sent password..."
    sleep 2

    if { $reboot == 1 } {
       send "reboot\r"
       handle_uboot 1
   }
}

proc handle_linux {} {
    global user
    global passwd
    global bootloader_prompt
    global tftpserver
    global ip
    set max_loop 5

    set timeout 200
    set reboot_retry 0
    send "reset\r"

    # Loop for reboot retry
    for { set i 0 } { $i < $max_loop } { incr i } {

        if { $i == $max_loop - 1 } {
            error_critical "Linux Network setup failed"
        }

        expect timeout {
              error_critical "Linux Boot Failure"
        } "Please press Enter to activate this console"

        log_debug "Booted Linux..."
        set timeout 10
        send "\r"
        expect timeout {
            error_critical "Linux Boot Failure"
        } "login:"

        log_debug "Got Linux Login prompt..."
        handle_login $user $passwd 0

        sleep 4
        # Loop for ping retry
        for { set j 0 } { $j < $max_loop } { incr j } {

            if { $j == $max_loop-1 } {
                log_warn "Ping retry max reach, rebooting..."
                send "reboot\r"
                set reboot_retry 1
                break
            } 

            send "\rifconfig;ping $tftpserver\r"
            set timeout 60
            expect {
                "ping: sendto: Network is unreachable" {
                    log_warn "Network Unreachable...retrying"
                } -re "64 bytes from $tftpserver" {
                    break
                } timeout {
                    log_error "No response for ping !"
                }
            }
            send \003
            sleep 3
        }

        if { $reboot_retry == 1 } {
            continue
        }

        send \003
        set timeout 2
        expect timeout {
            error_critical "Linux Hung!!"
        } ".*#"
        send "\r"
        set timeout 2
        expect timeout {
            error_critical "Linux Hung!!"
        } ".*#"
        break
    }
}

proc erase_linux_config { boardid } {
    global cmd_prefix
    global bootloader_prompt

    send "$cmd_prefix uclearcfg\r"
    set timeout 30
    expect timeout {
        error_critical "Erase Linux configuration data failed !"
    } "Done."
    set timeout 5
    expect timeout {
        error_critical "U-boot prompt not found !"
    } "$bootloader_prompt"
}

proc update_firmware { boardid } {
    global tftpserver
    global fwimg
    set max_loop 3

    log_debug "Firmware $fwimg from $tftpserver\r"

    send "\r"
    set timeout 2
    expect timeout {
        error_critical "Linux Hung!!"
    } -re ".*#"

    #start firmware flashing
    sleep 5
    for { set i 0 } { $i < $max_loop } { incr i } {

        if { $i == $max_loop -1} {
            error_critical "Failed to download Firmware"
        }

        send "cd /tmp/; tftp -r$fwimg -lfwupdate.bin -g $tftpserver\r"
        set timeout 60
        expect {
            "Invalid argument" {
                continue
            } -re ".*#" {
                # Do nothing
            } timeout {
                error_critical "Failed to download Firmware"
            }
        }
        break
    }

    log_debug "Firmware downloaded"

    sleep 2
    set timeout 120
    send "syswrapper.sh upgrade2\r"
    expect timeout {
        error_critical "Failed to download firmware !"
    } "Restarting system."

    log_progress 40 "Firmware flashed"
}

proc handle_uboot { {wait_prompt 0} } {
    global cmd_prefix
    global bootloader_prompt
    global fwimg
    global mac
    global ip
    global boardid
    global erasecal
    global use_64mb_flash
    global flash_mtdparts_64M
    global flash_mtdparts_32M

    if { $wait_prompt == 2 } {
        log_progress 2 "Waiting for self calibration in u-boot ..."
        stop_uboot 90
    }

    if { $wait_prompt == 1 } {
        stop_uboot
    }

    log_progress 5 "Got INTO U-boot"

    # detect flash size
    sleep 1
    send "print mtdparts\r"
    set timeout 5
    expect {
        "$bootloader_prompt" {
        } timeout {
            error_critical "U-boot prompt not found !"
        }
    }

    set mtdparts $expect_out(buffer)
    if { [string first $flash_mtdparts_64M $mtdparts] != -1 } {
        set use_64mb_flash 1
    } elseif { [string first $flash_mtdparts_32M $mtdparts] != -1 } {
    } else {
        error_critical "This mtdparts are not unsupported !"
    }

    sleep 1
    send "$cmd_prefix uappinit\r"
    set timeout 30
    expect timeout {
        error_critical "U-boot prompt not found !"
    } "$bootloader_prompt"

    # erase uboot-env
    sleep 2
    send "sf probe\r"
    set timeout 20
    expect timeout {
        error_critical "Probe serial flash failed !"
    } "$bootloader_prompt"

    if { $use_64mb_flash == 1 } {
        send "sf erase 0x1e0000 0x10000\r"
    } else {
        send "sf erase 0xc0000 0x10000\r"
    }
    set timeout 20
    expect timeout {
        error_critical "Erase uboot-env failed !"
    } "$bootloader_prompt"

    log_progress 10 "uboot-env erased"

    handle_linux

    # Update kernel 0
    update_firmware $boardid

    stop_uboot

    # erase uboot-env
    sleep 2
    send "sf probe\r"
    set timeout 20
    expect timeout {
        error_critical "Probe serial flash failed !"
    } "$bootloader_prompt"

    if { $use_64mb_flash == 1 } {
        send "sf erase 0x1e0000 0x10000\r"
    } else {
        send "sf erase 0xc0000 0x10000\r"
    }
    set timeout 20
    expect timeout {
        error_critical "Erase uboot-env failed !"
    } "$bootloader_prompt"

    log_progress 90 "uboot-env erased"

    # Update Kernel 1
    handle_urescue
    log_progress 95 "DUT complete the firmware programming"

    set timeout 60
    expect timeout {
        error_critical "Device is not responding after restart !"
    } "Hit any key to stop autoboot"

    set  timeout 60
    expect timeout {
        error_critical "MFG kernel did not boot properly"
    } "Verifying Checksum ... OK"

    log_progress 100 "Back to ART has completed"
}

proc main_detector { } {
    global user
    global passwd
    global bootloader_prompt
    global boardid
    global USW_XG
    global USW_6XG_150
    global USW_24_PRO
    global USW_48_PRO

    set timeout 30
    sleep 1
    send \003
    send "\r"

    log_progress 1 "Waiting - PLUG in the device..."

    expect {
        "Switching to RD_DATA_DELAY Step  :  3 (WL = 0)" {
            handle_uboot 2
        } "Board Net Initialization Failed" {
            stop_uboot
            # the proc check_mdk will check the U-boot if it has MDK
            # if it has, then do handle_uboot
            # if it hasn't, then do handle_urescue
            check_mdk
        } "Found MDK device" {
            stop_uboot
            handle_urescue
        } "$bootloader_prompt" {
            handle_uboot
        } "UBNT login:" {
            handle_login $user $passwd  1
        } "counterfeit login:" {
            handle_login $user $passwd 1
        } timeout {
            error_critical "Device not found!"
        }
    }
}


#
# action starts here
#
set file [open /home/user/Desktop/version.txt r]
while {[gets $file buf] != -1} {
    send_user "FCD version $buf\n\r"
}
close $file


spawn -open [open /dev/$dev w+]
stty 115200 < /dev/$dev
stty raw -echo < /dev/$dev

main_detector

