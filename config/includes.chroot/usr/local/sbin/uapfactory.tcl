#!/usr/bin/expect --
set boardid [lindex $argv 0]
set regdmn [lindex $argv 1] 
set mac [lindex $argv 2]
set passphrase [lindex $argv 3]
set keydir [lindex $argv 4]
set dev [lindex $argv 5]
set idx [lindex $argv 6]
set tftpserver [lindex $argv 7]
set bomrev [lindex $argv 8]
set qrcode [lindex $argv 9]
set fwimg "$boardid.bin"
set rsa_key dropbear_rsa_host_key
set dss_key dropbear_dss_host_key
set user "ubnt"
set passwd "ubnt"
set prompt "ar7240>"
set devreg_host "-h devreg-prod.ubnt.com"

set UAP_ID          "e502"
set UAPLR_ID        "e512"
set UAPMINI_ID      "e522"
set UAPOUT_ID       "e532"
set UAPHSR_ID       "e562"
set UAPWASP_ID      "e572"
set UAPWASPLR_ID    "e582"
set UAPINWALL_ID    "e592"
set UAPOUT5_ID      "e515"
set UAPPRO_ID       "e507"
set UAPGEN2LITE_ID  "e517"
set UAPGEN2LR_ID    "e527"
set UAPGEN2PRO_ID   "e537"
set UAPGEN2EDU_ID   "e547"
set UAPGEN2MESH_ID  "e557"
set UAPGEN2MESHPRO_ID   "e567"
set UAPGEN2IW_ID    "e587"
set UAPGEN2IWPRO_ID "e597"
set INSTANTLTE_ID   "e611"

set uappaddr "0x80200020"
set uappext_printenv "go $uappaddr uprintenv"
set uappext_saveenv "go $uappaddr usaveenv"
set uappext_setenv "go $uappaddr usetenv"
set uappext "go $uappaddr "

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

proc string2hex {string} {
    set str_len [string length $string]
    set hex_str ""
    for {set i 0} {$i < $str_len} {incr i} {
        set cur_hex [format %02x [scan [string index $string $i] %c]]
        append hex_str $cur_hex
    }
    return $hex_str
}


log_debug "launched with params: boardid=$boardid; regdmn=$regdmn; mac=$mac; passphrase=$passphrase; keydir=$keydir; dev=$dev; idx=$idx; tftpserver=$tftpserver; bomrev=$bomrev; qrcode=$qrcode"

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
    global uappext
    global boardid
    global prompt

    log_debug "Stopping U-boot"
    #send "any key"
    
    set timeout 30
    expect  "Hit any key to stop autoboot" { send "\r"} \
    timeout { error_critical "Device not found!" }  

    log_debug "Stopped U-boot @ $prompt"
    set timeout 5
    expect timeout {
    } $prompt
    
    sleep 1 
    send "\r" 
    set timeout 30
    expect timeout {
        error_critical "U-boot prompt not found !"
    } $prompt

    log_debug "uappext: $uappext"
    if { [string equal -nocase $uappext ""] == 0 } {
        send "$uappext uappinit\r"
        set timeout 30
        expect {
            "uboot env fix. Clearing u-boot env and resetting the board.. " {
                log_debug "uboot env fixed, rebooting..."
                stop_uboot
            } "UBNT application initialized" {
                set timeout 5
                expect timeout {
                    error_critical "U-boot prompt not found !"
                } $prompt
            } timeout {
                error_critical "UBNT Application failed to initialize!"
            }
        }
    }
}

proc setmac {} {
    global mac
    global uappext
    global prompt

    sleep 2
    send "$uappext usetmac $mac\r"
    set timeout 10
    expect timeout { 
        error_critical "MAC setting failed!" 
    } "Done."
    set timeout 5
    expect timeout { 
    } $prompt

    send_user "\r\n * MAC setting succeded *\r\n"
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

        sleep 2
        send "setenv ipaddr $ip\r"
        set timeout 15
        expect timeout { 
            error_critical "U-boot prompt not found !" 
        } $prompt

        sleep 2
        send "setenv serverip $tftpserver\r"
        set timeout 15
        expect timeout { 
            error_critical "U-boot prompt not found !" 
        } $prompt

        sleep 5
    
        send "ping $tftpserver\r"
        set timeout 30
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

proc set_network_env_in_art {} {
    global tftpserver
    global ip
    set max_loop 5
    set pingable 0

    sleep 2
    send "ifconfig br0 $ip\r"
    set timeout 15
    expect timeout {
        error_critical "ART prompt not found !"
    } "#"

    for { set i 0 } { $i < $max_loop } { incr i } {

        sleep 1
        send "ping -c 1 $tftpserver\r"

        set timeout 15
        expect timeout {
            error_critical "Unknown response for ping !"
        } -re ".* packets transmitted, (.*) packets received, .*% packet loss"

        set recv_cnt [expr $expect_out(1,string) + 0]

        set timeout 5
        expect timeout {
            error_critical "ART prompt not found !"
        } "#"

        if {$recv_cnt == 1} {
            set pingable 1
            break
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
    global UAPGEN2MESHPRO_ID
    global UAPGEN2IW_ID
    global UAPGEN2IWPRO_ID
    global INSTANTLTE_ID

    if {
            [string equal -nocase $boardid $UAPGEN2LITE_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2LR_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2PRO_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2EDU_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2MESH_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2MESHPRO_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2IW_ID] == 1
            || [string equal -nocase $boardid $UAPGEN2IWPRO_ID] == 1
            || [string equal -nocase $boardid $INSTANTLTE_ID] == 1
                                                                    } {
         return 1
    } else {
        return 0
    }
}

proc update_uboot_in_art { boardid } {
    global tftpserver
    set ubootimg    $boardid.uboot

    sleep 1

    set timeout 20
    send "cd /tmp\r"
    expect timeout {
        error_critical "ART prompt not found !"
    } "#"
    set timeout 30
    send "tftp -g -r $ubootimg $tftpserver 2>/dev/null ; echo \$?\r"
    expect timeout {
        error_critical "Failed to download u-boot image ($ubootimg)"
    } "0"
    set timeout 5
    expect timeout {
        error_critical "ART prompt not found !"
    } "#"

    sleep 1
    send "dd if=/tmp/$ubootimg of=/dev/mtdblock0 bs=64k >/dev/null 2>&1 ; echo \$?\r"
    expect timeout {
        error_critical "Failed to dd uboot file (to mtdblock0)"
    } "0"
    set timeout 5
    expect timeout {
        error_critical "ART prompt not found !"
    } "#"

    sleep 1
    send "reboot\r"

    set timeout 10
    expect timeout {
        error_critical "ART Linux doesn't restart !"
    } "Restarting system."
}

proc update_uboot { boardid } {
    set ubootimg    $boardid.uboot
    set tftpaddr    0x80800000
    set ubootaddr   0x9f000000

    sleep 1
    set timeout 30
    send "tftp $tftpaddr $ubootimg\r"
    expect timeout {
        error_critical "Failed to download u-boot image ($ubootimg)"
    } -re "Bytes transferred = (.*)\r"

    sleep 1
    send "erase $ubootaddr +\$filesize\r"
    expect timeout {
        error_critical "Failed to erase uboot sectors ($ubootaddr +\$filesize)"
    } -re "Erased (\\d+) sectors\r"

    sleep 1
    send "cp.b \$fileaddr $ubootaddr \$filesize\r"
    expect timeout {
        error_critical "Failed to copy uboot ($tftpaddr $ubootaddr \$filesize)"
    } "done"

    sleep 1
    send "reset\r"
}

proc update_uboot_fixedsize { boardid } {
    set ubootimg    $boardid.uboot
    set tftpaddr    0x80800000
    set ubootaddr   0x9f000000

    if  { [may_have_non_ubntapp_uboot $boardid] == 1 } {
        set ubootsize 0x00040000
    } else {
        set ubootsize 0x00060000
    }

    sleep 1
    set timeout 30
    send "tftp $tftpaddr $ubootimg\r"
    expect timeout {
        error_critical "Failed to download u-boot image ($ubootimg)"
    } -re "Bytes transferred = (.*)\r"

    sleep 1
    send "erase $ubootaddr +$ubootsize\r"
    expect timeout {
        error_critical "Failed to erase uboot sectors ($ubootaddr +$ubootsize)"
    } -re "Erased (\\d+) sectors\r"

    sleep 1
    send "cp.b $tftpaddr $ubootaddr $ubootsize\r"
    expect timeout {
        error_critical "Failed to copy uboot ($tftpaddr $ubootaddr $ubootsize)"
    } "done"

    sleep 1
    send "reset\r"
}

proc update_firmware { boardid } {
    global fwimg
    global ip
    global uappext
    global prompt
    global INSTANTLTE_ID

    log_debug "Firmware $fwimg\r"

    #start firmware flashing
    sleep 1
    set timeout 10 
    if { [string equal -nocase $uappext ""] == 0 } {
        send "setenv do_urescue TRUE;urescue -u -e\r"
    } else {
        send "urescue -f -e\r"
    }
        expect timeout { 
        error_critical "Failed to start urescue" 
    } "Waiting for connection"
    
    exec atftp --option "mode octet" -p -l /tftpboot/$fwimg $ip 2>/dev/null >/dev/null
    
    set timeout 30
    if { [string equal -nocase $uappext ""] == 0 } {
        expect timeout { 
            error_critical "Failed to tftp firmware !" 
        } "TFTP Transfer Complete"

        log_debug  "Download complete\n"

        set timeout 15
        expect timeout { 
        } $prompt
        send "$uappext uwrite -f\r"
    }
    expect timeout { 
        error_critical "Failed to correct firmware !" 
    } "Firmware Version:"
    
    log_progress 10 "Firmware loaded"
    
    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 0} {
        set timeout 15
        expect timeout {
            error_critical "Failed to flash firmware (u-boot) !"
        } "Copying partition 'u-boot' to flash memory:"
    }
    
    log_progress 15 "Flashing firmware..."

    set dual [has_ubntfsboot_dual_image $boardid]
    if { $dual == 1 } {
        set timeout 15
        expect timeout { 
            error_critical "Failed to flash firmware (jffs2) !"
        } "Copying partition 'jffs2' to flash memory:"

        log_progress 30 "Flashing firmware..."
    } else {
        set timeout 15
        expect timeout { 
            error_critical "Failed to flash firmware (kernel) !"
        } -re "Copying partition 'kernel(.*)' to flash memory:"

        log_progress 20 "Flashing firmware..."

        set has_squashfs [rootfs_is_squashfs $boardid]
        if { $has_squashfs == 1 } {
            set timeout 15
            expect timeout { 
                error_critical "Failed to flash firmware (rootfs) !"
            } "Copying partition 'rootfs' to flash memory:"

            log_progress 30 "Flashing firmware..."
        }
    }
    
    set timeout 180
    expect timeout { 
        error_critical "Failed to flash firmware !" 
    } "Firmware update complet"
    
    log_progress 45 "Firmware flashed"
}

proc gen_sshkeys {} {
    global rsa_key
    global dss_key
    global idx

    set full_rsa_key /tftpboot/$rsa_key.$idx
    set full_dss_key /tftpboot/$dss_key.$idx
    
    exec rm -f $full_rsa_key
    exec rm -f $full_dss_key

    exec dropbearkey -t rsa -f $full_rsa_key 2>/dev/null >/dev/null
    exec dropbearkey -t dss -f $full_dss_key 2>/dev/null >/dev/null
    
    exec chmod +r $full_rsa_key
    exec chmod +r $full_dss_key
}

proc upload_sshkeys {} {
    global rsa_key
    global dss_key
    global idx
    global uappext
    global prompt

    set dl_addr 80800000

    sleep 2
    send "tftp $dl_addr $rsa_key.$idx\r"
    set timeout 15
    expect timeout { 
        error_critical "TFTP failed on $rsa_key.$idx!" 
    } "Bytes transferred ="
    set timeout 5
    expect timeout { 
    } $prompt

    sleep 2
    send "$uappext usetsshkey \${fileaddr} \${filesize}\r"
    set timeout 15
    expect timeout { 
        error_critical "setsshkey failed on $rsa_key.$idx!" 
    } "Done."
    set timeout 5
    expect timeout { 
    } $prompt

    sleep 2
    send "tftp $dl_addr $dss_key.$idx\r"
    set timeout 15
    expect timeout { 
        error_critical "TFTP failed on $dss_key.$idx!" 
    } "Bytes transferred ="
    set timeout 5
    expect timeout { 
    } $prompt

    sleep 2
    send "$uappext usetsshkey \${fileaddr} \${filesize}\r"
    set timeout 15
    expect timeout { 
        error_critical "setsshkey failed on $dss_key.$idx!" 
    } "Done."
    set timeout 5
    expect timeout { 
    } $prompt
   
    sleep 1 
    # Clear the temp variables so that its not confused with
    # uwrite in uappinit later.
    send "setenv fileaddr;setenv filesize\r"
    set timeout 5
    expect timeout { 
    } $prompt

    send_user "\r\n * ssh keys uploaded successfully *\r\n"
}

proc run_client { idx eeprom_txt eeprom_bin eeprom_signed passphrase keydir} {
    global qrcode
    global devreg_host
    log_debug "Connecting to server:"
    
    set outfile [open "/tmp/client$idx.sh" w]
    puts $outfile "#!/bin/sh\n"
    puts $outfile "set -o verbose\n"
    if {$qrcode eq ""} {
        puts $outfile "/usr/local/sbin/client_x86 $devreg_host -i field=product_class_id,value=radio \$(cat /tftpboot/$eeprom_txt  | sed -r -e \"s~^field=(.*)\$~-i field=\\1 ~g\" | grep -v \"eeprom\" | tr '\\n' ' ') -i field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_bin -o field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_signed -k $passphrase -o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message -x $keydir/ca.pem -y $keydir/key.pem -z $keydir/crt.pem "
    } else {
        set qrhex [string2hex $qrcode]
        puts $outfile "/usr/local/sbin/client_x86 $devreg_host -i field=product_class_id,value=radio \$(cat /tftpboot/$eeprom_txt  | sed -r -e \"s~^field=(.*)\$~-i field=\\1 ~g\" | grep -v \"eeprom\" | tr '\\n' ' ') -i field=qr_code,format=hex,value=$qrhex -i field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_bin -o field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_signed -k $passphrase -o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message -x $keydir/ca.pem -y $keydir/key.pem -z $keydir/crt.pem $qrcode"
    }
    close $outfile

    if { [catch "spawn sh /tmp/client$idx.sh" reason] } {
        error_critical "Failed to spawn client: $reason\n"
    }   
    set sid $spawn_id
    log_debug "sid $sid"

    expect -i $sid { 
        eof { log_debug "Done." }
    }
    catch wait result
    set res [lindex $result 3]
    log_debug "Client result $res"
    if { $res != 0 } {
        error_critical "Registration failure : $res\n"
    }   
}

proc check_unifiOS_network_ready { boardid } {
    global tftpserver
    global INSTANTLTE_ID

    set max_loop 5
    set pingable 0

    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        set x 0
        while { $x < 25 } {
            send "ifconfig\r"
            sleep 2
            expect "192.168.1." {
                break
            }
            sleep 5
            incr x
        }
        if { $x == 25 } {
            error_critical "Can't get DHCP IP address"
        }
    } else {
        set timeout 90
        send "while \[ ! -f /etc/udhcpc/info.br0 \]; do ifconfig; ls /etc/udhcpc; sleep 5; done\r"
        expect timeout { error_critical "Can't get DHCP IP address" } "#"
    }

    for { set i 0 } { $i < $max_loop } { incr i } {

        sleep 1
        send "ping -c 1 -W 2 $tftpserver\r"

        set timeout 10
        expect timeout {
            error_critical "Unknown response for ping !"
        } -re ".* packets transmitted, (.*) packets received, .*% packet loss"

        set recv_cnt [expr $expect_out(1,string) + 0]

        set timeout 5
            expect timeout { 
        } "#"

        if {$recv_cnt == 1} {
            set pingable 1
            break
        }
    }

    if { $pingable != 1 } {
        error_critical "$tftpserver is not reachable !"
    }
}

proc turn_on_burnin_mode { boardid } {
    global INSTANTLTE_ID
    global tftpserver
    set timeout 10
    set burnin_cfg "e611-burnin.cfg"
    set burnin_flag "lte.burnin.enabled=enabled"

    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        send "cd /tmp\r"
        expect timeout { error_critical "Command promt not found" } "#"

        send "tftp -g -r $burnin_cfg $tftpserver -l system.cfg\r"
        sleep 1
        expect timeout { error_critical "Command promt not found" } "#"

        send "grep \"burnin\" system.cfg\r"
        expect timeout {
            error_critical "Burnin config is not set correctly"
        } -re $burnin_flag

        # save config
        send "cfgmtd -w -p /etc/ && killall -9 mcad && /etc/rc.d/rc restart\r"
        expect timeout { error_critical "Command promt not found" } "#"

    } else {
        log_debug "Skip burnin mode enabling"
    }
}

proc check_LTE_ver { boardid } {
    global INSTANTLTE_ID
    set timeout 5

    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        set x 0
        while { $x < 5 } {
            send "echo -e \"ati\" > /dev/ttyUSB2\r"
            sleep 1
            send "grep \"Revision\" /dev/ttyUSB2\r"

            expect -re "Revision: (.*)" {
                # send ctrl+c to terminate grep
                send \003
                expect timeout { error_critical "Command promt not found" } "#"
                break
            }

            sleep 2
            incr x
        }
        if { $x == 5 } {
            error_critical "Unable to get version of LTE firmware"
        }

        set lte_ver $expect_out(1,string)
        log_debug "LTE Version: $lte_ver"
    } else {
        log_debug "Skip the version of LTE firmware checking"
    }
}

proc check_ICCID { boardid } {
    global INSTANTLTE_ID
    set timeout 5

    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        set x 0
        while { $x < 5 } {
            send "echo -e \"at+ccid\" > /dev/ttyUSB2\r"
            sleep 1
            send "grep \"+CCID:\" /dev/ttyUSB2\r"

            expect -re "CCID: (\\d*)" {
                # send ctrl+c to terminate grep
                send \003
                expect timeout { error_critical "Command promt not found" } "#"
                break
            }

            sleep 2
            incr x
        }
        if { $x == 5 } {
            error_critical "Unable to get ICCID!"
        }

        set ccid $expect_out(1,string)
        set ccid_len [string length $ccid]
        set ccid_len_max 22

        log_debug "ccid: $ccid ccid_len: $ccid_len"

        # clear eeprom
        send "tr '\\000' '\\377' < /dev/zero | dd of=/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd"
        send " | sed 's~mtd~mtdblock~g'` bs=1 seek=33024 count=$ccid_len_max\r"
        expect timeout { error_critical "Command promt not found" } "#"

        # write ccid to eeprom
        send "echo -e $ccid | dd of=/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd"
        send " | sed 's~mtd~mtdblock~g'` bs=1 seek=33024 count=$ccid_len\r"
        expect timeout { error_critical "Command promt not found" } "#"

        send "hexdump -C -s 0x8100 -n $ccid_len -e '$ccid_len/1 \"%x\" \"\\n\"' /dev/mtdblock5\r"
        expect timeout {
             error_critical "Unable to get CCID from EEPROM"
        } [string2hex $ccid]


        log_debug "Completed to check CCID"
    } else {
        log_debug "Skip CCID checking"
    }
}

proc do_security { boardid } {
    global passphrase
    global keydir
    global idx
    global tftpserver
    global user
    global passwd
    global INSTANTLTE_ID

    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        set helper helper_ARxxxx_musl
    } else {
        set helper helper_ARxxxx
    }
    set eeprom_bin e.b.$idx
    set eeprom_txt e.t.$idx
    set eeprom_signed e.s.$idx
    set eeprom_check e.c.$idx

    set timeout 60
    # login    
    expect timeout { 
        error_critical "Failed to boot firmware !" 
    } "Please press Enter to activate this console."

    sleep 1
    send "\r"
    
    expect "login:" { send "$user\r" } \
        timeout { error_critical "Login failed" }

    expect "Password:" { send "$passwd\r" } \
        timeout { error_critical "Login failed" }
        
    expect timeout { error_critical "Login failed" } "#"
    set timeout 20
    send "dmesg -n 1\r"
    expect timeout { error_critical "Command promt not found" } "#"
    sleep 3


    if { [ catch { exec rm -f /tftpboot/$eeprom_bin } msg ] } {
        puts "$::errorInfo"
    }
    if { [ catch { exec rm -f /tftpboot/$eeprom_txt } msg ] } {
        puts "$::errorInfo"
    }
    if { [ catch { exec rm -f /tftpboot/$eeprom_signed } msg ] } {
        puts "$::errorInfo"
    }
    if { [ catch { exec rm -f /tftpboot/$eeprom_check } msg ] } {
        puts "$::errorInfo"
    }
    
    exec touch /tftpboot/$eeprom_bin
    exec touch /tftpboot/$eeprom_txt
    exec touch /tftpboot/$eeprom_check
    exec chmod 666 /tftpboot/$eeprom_bin
    exec chmod 666 /tftpboot/$eeprom_txt
    exec chmod 666 /tftpboot/$eeprom_check

    check_unifiOS_network_ready $boardid
    check_ICCID $boardid

    if {[string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        set timeout 20
        send "cd /tmp\r"
        expect timeout { error_critical "Command promt not found" } "#"

        send "tftp -g -r deloutput.sh $tftpserver\r"
        sleep 1
        expect timeout { error_critical "Command promt not found" } "#"

        send "sh /tmp/deloutput.sh $idx\r"
        sleep 2
        expect timeout { error_critical "Command promt not found" } "#"
    } else {
        set timeout 20
        send "\[ ! -f /tmp/$eeprom_bin \] || rm /tmp/$eeprom_bin\r"
        expect timeout { error_critical "Command promt not found" } "#"
        send "\[ ! -f /tmp/$eeprom_txt \] || rm /tmp/$eeprom_txt\r"
        expect timeout { error_critical "Command promt not found" } "#"
        send "\[ ! -f /tmp/$eeprom_signed \] || rm /tmp/$eeprom_signed\r"
        expect timeout { error_critical "Command promt not found" } "#"
        send "\[ ! -f /tmp/$eeprom_check \] || rm /tmp/$eeprom_check\r"
        expect timeout { error_critical "Command promt not found" } "#"
    }

    send "cd /tmp\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "tftp -g -r $helper $tftpserver\r"
    expect timeout { error_critical "Command promt not found" } "#" 
    
    set timeout 20
    send "chmod +x $helper\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "./$helper -q -c product_class=radio -o"
    send " field=flash_eeprom,format=binary,"
    send "pathname=$eeprom_bin > $eeprom_txt" 
    send "\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    # FIXME, run helper once more, to workaround bug in helper 
    send "./$helper -q -c product_class=radio -o"
    send " field=flash_eeprom,format=binary,"
    send "pathname=$eeprom_bin > $eeprom_txt" 
    send "\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    log_debug "Downloading files"
    
    set timeout 30
    send "tftp -p -l $eeprom_bin $tftpserver\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    # FIXME, upload file once more, to workaround bug in UAP-Pro Ethernet driver?
    send "tftp -p -l $eeprom_bin $tftpserver\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "tftp -p -l $eeprom_txt $tftpserver\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    sleep 2

    set file_size [file size  "/tftpboot/$eeprom_bin"]
    
    if { $file_size == 0 } then { ; # check for file exist
        error_critical "EEPROM (bin) download failure"
    } 

    set file_size [file size  "/tftpboot/$eeprom_txt"]

    if { $file_size == 0 } then { ; # check for file exist
        error_critical "EEPROM (txt) download failure"
    } 
    
    run_client $idx $eeprom_txt $eeprom_bin $eeprom_signed $passphrase $keydir
    
    log_debug "Uploading eeprom..."
    
    send "tftp -g -r $eeprom_signed $tftpserver\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "\[ ! -f /proc/ubnthal/.uf \] || echo 5edfacbf > /proc/ubnthal/.uf\r"
    expect timeout { error_critical "Command promt not found" } "#" 
    
    log_debug "File sent."
    
    log_debug "Writing eeprom..."
   
    send "./$helper -q -i "
    send "field=flash_eeprom,format=binary,pathname=$eeprom_signed\r"
    expect timeout { error_critical "Command promt not found" } "#" 
    
    send "dd if=/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd"
    send " | sed 's~mtd~mtdblock~g'` of=/tmp/$eeprom_check\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "tftp -p -l $eeprom_check $tftpserver\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "\[ ! -f /proc/ubnthal/.uf \] || echo 1 > /proc/ubnthal/.uf\r"
    expect timeout { error_critical "Command promt not found" } "#"
    
    send "reboot\r"
    expect timeout { error_critical "Command promt not found" } "#" 

    send "exit\r"
    
    log_debug "Checking EEPROM..."
    if { [ catch { exec /usr/bin/cmp /tftpboot/$eeprom_signed /tftpboot/$eeprom_check } results ] } {
        #set details [dict get $results -errorcode]
        
        #if {[lindex $details 0] eq "CHILDSTATUS"} {
        #   set status [lindex $details 2]
            error_critical "EEPROM check failed"
        #} else {
        #}
    }
    #log_debug $results 
    log_debug "EEPROM check OK..."

    log_progress 90 "Rebooting"
    
}

proc check_security { boardid } {
    global user
    global passwd
    global qrcode
    global INSTANTLTE_ID

    set timeout 120
    # login    
    expect timeout { 
        error_critical "Failed to boot firmware !" 
    } "Please press Enter to activate this console."

    sleep 1
    send "\r"
    
    expect "login:" { send "$user\r" } \
        timeout { error_critical "Login failed" }

    expect "Password:" { send "$passwd\r" } \
        timeout { error_critical "Login failed" }
        
    expect timeout { error_critical "Login failed" } "#"
    set timeout 20
    send "dmesg -n 1\r"
    expect timeout { error_critical "Command promt not found" } "#"
    sleep 3

    # to get rid of the br0 state change or no IPv6 routers present messages from console
    check_unifiOS_network_ready $boardid

    send "grep -c flashSize /proc/ubnthal/system.info\r"
    expect timeout {
        error_critical "Unable to get flashSize!"
    } -re "(\\d+)\r"
    
    set signed [expr $expect_out(1,string) + 0]
    expect timeout { error_critical "Command promt not found" } "#" 

    log_debug "signed: $signed"
    if {$signed ne 1} {
        error_critical "Device Registration check failed!"
    }

    if {$qrcode ne ""} {
        send "grep qrid /proc/ubnthal/system.info\r"
        expect timeout {
            error_critical "Unable to get qrid!"
        } -re "qrid=(.*)\r"
    
        set qrid $expect_out(1,string)
        expect timeout { error_critical "Command promt not found" } "#" 

        log_debug "qrid: $qrid"
        if {$qrid ne $qrcode} {
            error_critical "QR code doesn't match!"
        }

    }

    log_progress 95 "Device Registration check OK..."

}

proc erase_linux_config { boardid } {
    #global UAPPRO_ID
    global uappext
    global prompt

    #if { [string equal -nocase $boardid $UAPPRO_ID] == 1 } {
    #    send "erase 0x9ffb0000 +40000\r"
    #} else {
    #    send "erase 0x9f7b0000 +40000\r"
    #}
    send "$uappext uclearcfg\r"
    set timeout 30
    #expect timeout { 
    #    error_critical "Erase Linux configuration data failed !" 
    #} " done"
    expect timeout { 
        error_critical "Erase Linux configuration data failed !" 
    } " done"
    set timeout 5
    expect timeout { 
    } $prompt
}

proc turn_on_console { boardid } {
    #global uappext_setenv
    global prompt

    set has_squashfs [rootfs_is_squashfs $boardid]
    if { $has_squashfs == 1 } {
        send "setenv bootargs 'quiet console=ttyS0,115200 root=31:03 rootfstype=squashfs init=/init nowifi'\r"
    } else {
        send "setenv bootargs 'quiet console=ttyS0,115200 init=/init nowifi'\r"
    }
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } $prompt
}

proc check_macaddr { boardid mac } {
    global UAPPRO_ID
    global uappext
    global prompt

    set timeout 20
    send "$uappext usetmac\r"
    if { [string equal -nocase $boardid $UAPPRO_ID] == 1 } {
        expect timeout {
            error_critical "Unable to get MAC !"
        } -re "MAC0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*MAC1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*WIFI0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*WIFI1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2})"
    
        set mac_str $expect_out(1,string)
        regsub -all {:} $expect_out(1,string) {} mac0_read
        regsub -all {:} $expect_out(2,string) {} mac1_read
        regsub -all {:} $expect_out(3,string) {} wifi0_read
        regsub -all {:} $expect_out(4,string) {} wifi1_read
        regsub -all {:} $mac {} mac0_write
        set somehex [format %X [expr 0x[string range $mac0_write 1 1] | 0x2]]
        set mac1_write [string replace $mac0_write 1 1 $somehex]
        set somehex [format %02X [expr (0x[string range $mac0_write 6 7] + 0x1) & 0xff]]
        set wifi0_write [string replace $mac0_write 6 7 $somehex]
        set somehex [format %02X [expr (0x[string range $wifi0_write 6 7] + 0x1) & 0xff]]
        set wifi1_write [string replace $wifi0_write 6 7 $somehex]

        if { [string equal -nocase $mac0_write $mac0_read] != 1 
             || [string equal -nocase $mac1_write $mac1_read] != 1
             || [string equal -nocase $wifi0_write $wifi0_read] != 1
             || [string equal -nocase $wifi1_write $wifi1_read] != 1} {
            error_critical "MAC address doesn't match!"
        }
    } else {
        expect timeout {
            error_critical "Unable to get MAC !"
        } -re "MAC0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*MAC1: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2}).*WIFI0: (.{2}:.{2}:.{2}:.{2}:.{2}:.{2})"
    
        set mac_str $expect_out(1,string)
        regsub -all {:} $expect_out(1,string) {} mac0_read
        regsub -all {:} $expect_out(2,string) {} mac1_read
        regsub -all {:} $expect_out(3,string) {} wifi0_read
        regsub -all {:} $mac {} mac0_write
        set somehex [format %X [expr 0x[string range $mac0_write 1 1] | 0x2]]
        set mac1_write [string replace $mac0_write 1 1 $somehex]
        set somehex [format %02X [expr (0x[string range $mac0_write 6 7] + 0x1) & 0xff]]
        set wifi0_write [string replace $mac0_write 6 7 $somehex]

        if { [string equal -nocase $mac0_write $mac0_read] != 1 
             || [string equal -nocase $mac1_write $mac1_read] != 1
             || [string equal -nocase $wifi0_write $wifi0_read] != 1} {
            error_critical "MAC address doesn't match!"
        }
    }
    set timeout 5
    expect timeout { 
    } $prompt

}

proc check_booting { boardid } {
    global UAPMINI_ID
    global UAPWASP_ID
    global UAPWASPLR_ID
    global UAPINWALL_ID
    global UAPPRO_ID

    set timeout 60

    if { [string equal -nocase $boardid $UAPPRO_ID] == 1
         || [string equal -nocase $boardid $UAPWASP_ID] == 1
         || [string equal -nocase $boardid $UAPWASPLR_ID] == 1} {
        expect timeout {
            error_critical "Kernel boot failure !"
        } "Booting Atheros AR934x"
    } elseif { [string equal -nocase $boardid $UAPMINI_ID] == 1
               ||[string equal -nocase $boardid $UAPINWALL_ID] == 1 } {
        expect timeout {
            error_critical "Kernel boot failure !"
        } "Booting AR9330(Hornet)..."
    } elseif { [has_dragonfly_cpu $boardid] } {
        expect timeout {
            error_critical "QCA956x Kernel boot failure !"
        } "Starting kernel ..."
    } else {
        expect timeout {
            error_critical "Kernel boot failure !"
        } "Booting..."
    }
}

proc handle_art { boardid } {
    global UAPGEN2IW_ID
    global UAPGEN2IWPRO_ID

    send "root\r"
    log_debug "Sent username..."
    expect "Password:"
    send "5up\r"
    log_debug "Sent password..."
    set timeout 5
    expect timeout {
    } "#"

    if  { [may_have_non_ubntapp_uboot $boardid] == 1 ||
          [string equal -nocase $boardid $UAPGEN2IW_ID] == 1 ||
          [string equal -nocase $boardid $UAPGEN2IWPRO_ID] == 1 } {

        set_network_env_in_art
        update_uboot_in_art $boardid
    } else {
        sleep 2
        send "reboot\r"
    }
}

proc handle_uboot { {wait_prompt 0} } {
    global fwimg
    global boardid
    global mac
    global ip
    global regdmn
    global bomrev
    global uappext
    global uappext_printenv
    global uappext_saveenv
    global prompt
    global UAPGEN2IW_ID
    global UAPGEN2IWPRO_ID
    global INSTANTLTE_ID

    if { $wait_prompt == 1 } {
        stop_uboot
    }

    log_progress 5 "Got INTO U-boot uappext $uappext"

    sleep 1 
    send "\r" 
    set timeout 30
    expect timeout {
        error_critical "U-boot prompt not found !"
    } $prompt

    if  { [may_have_non_ubntapp_uboot $boardid] == 1 } {
        set_network_env
        update_uboot_fixedsize $boardid
        stop_uboot
    }

    if  { [string equal -nocase $boardid $UAPGEN2IW_ID] == 1 ||
          [string equal -nocase $boardid $UAPGEN2IWPRO_ID] == 1 ||
          [string equal -nocase $boardid $INSTANTLTE_ID] == 1} {
        set_network_env
        update_uboot $boardid
        stop_uboot
    }

    if { [string equal -nocase $uappext ""] == 0 } {
        log_progress 8 "running uappinit"
        send "$uappext uappinit\r"
        set timeout 15
        expect timeout { 
            error_critical "UBNT Application failed to initialize!" 
        } "UBNT application initialized"
        set timeout 5
        expect timeout {
            error_critical "U-boot prompt not found !"
        } $prompt
    }

    # erase uboot-env
    sleep 2
    if { [string equal -nocase $uappext ""] == 0 } {
        log_progress 9 "running uclearenv"
        send "$uappext uclearenv\r"
        set timeout 20 
        expect timeout {
            error_critical "u-boot-env clear failure"
        } "done"
    } else {
        log_progress 9 "erasing uboot-env"
        send "erase 1:4\r"
        set timeout 20 
        expect timeout { 
            error_critical "Erase uboot-env failed !" 
        } "done"
    }
    set timeout 5
    expect timeout {
        error_critical "U-boot prompt not found !"
    } $prompt

    sleep 1
    send "reset \r"
    stop_uboot

    ## RUN 1, update firmware  
    set_network_env
    update_firmware $boardid

    #id_version

    ## RUN 2, set IDs
    stop_uboot

    # set Board ID
    sleep 2
    send "$uappext usetbid -f $boardid\r"
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } "Done."
    set timeout 5
    expect timeout { 
    } $prompt

    # set BOM Revision
    sleep 2
    send "$uappext usetbrev $bomrev\r"
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } "Done."
    set timeout 5
    expect timeout { 
    } $prompt
    log_progress 50 "Board ID/Revision set"

    # set Regulatory Domain
    sleep 2
    send "$uappext usetrd $regdmn\r"
    set timeout 15
    expect timeout { 
        error_critical "U-boot prompt not found !" 
    } "Done."
    set timeout 5
    expect timeout { 
    } $prompt
    log_progress 55 "Regulatory Domain set"

    # erase uboot-env
    sleep 2
    if { [string equal -nocase $uappext ""] == 0 } {
        send "$uappext uclearenv\r"
        set timeout 20 
        expect timeout {
            error_critical "u-boot-env clear failure"
        } "done"
    } else {
        send "erase 1:4\r"
        set timeout 20 
        expect timeout { 
            error_critical "Erase uboot-env failed !" 
        } "done"
    }
    set timeout 5
    expect timeout {
        error_critical "U-boot prompt not found !"
    } $prompt

    # erase linux configuration
    sleep 2 
    erase_linux_config $boardid
    log_progress 60 "Configuration erased"

    # set Ethernet mac address
    setmac
    log_progress 65 "MAC set"

    # reboot
    sleep 1
    send "reset\r"

    ## RUN 3, upload ssh keys & check IDs
    stop_uboot

    #sleep 1 
    #send "$uappext_printenv\r"
    #set timeout 15
    #expect timeout { 
    #    error_critical "U-boot prompt not found !" 
    #} $prompt

    #sleep 1
    #send "$uappext_saveenv\r"
    #set timeout 15
    #expect timeout { 
    #    error_critical "U-boot prompt not found !" 
    #} $prompt
    #log_progress 70 "Environment Variables set"

    sleep 1
    set_network_env

    # upload ssh keys
    gen_sshkeys
    upload_sshkeys
    log_progress 75 "ssh keys uploaded"

    set timeout 20
    send "$uappext usetbid\r"
    expect timeout {
        error_critical "Unable to get Board ID!"
    } -re "Board ID: (.{4})"
    
    set bid_str $expect_out(1,string)
    log_debug "bid_str: $bid_str"

    if { [string equal -nocase $bid_str $boardid] != 1 } {
        error_critical "Board ID doesn't match!"
    }
    set timeout 5
    expect timeout { 
    } $prompt

    sleep 1
    set timeout 20
    send "$uappext usetbrev\r"
    expect timeout {
        error_critical "Unable to get BOM Revision!"
    } -re "BOM Rev: (\\d+\\-\\d+)\r"
    
    set brev_str $expect_out(1,string)
    log_debug "brev_str: $brev_str"

    if { [string equal $brev_str $bomrev] != 1 } {
        error_critical "BOM Revision doesn't match!"
    }
    set timeout 5
    expect timeout { 
    } $prompt

    sleep 1
    set timeout 20
    send "$uappext usetrd\r"
    expect timeout {
        error_critical "Unable to get Regulatory Domain!"
    } -re "RegulatoryDomain: (.{4})"
    
    set rd_str $expect_out(1,string)
    log_debug "rd_str: $rd_str"

    if { [string equal -nocase "$rd_str" "$regdmn"] != 1 } {
        error_critical "Regulatory Domain doesn't match!"
    }
    set timeout 5
    expect timeout { 
    } $prompt

    sleep 1
    check_macaddr $boardid $mac

    log_progress 80 "Board ID/Regulatory Domain/MAC address checked"

    sleep 1
    turn_on_console $boardid

    ## RUN 4, sign flash
    sleep 1
    send "boot\r"

    check_booting $boardid
    do_security $boardid
    stop_uboot
    sleep 1
    turn_on_console $boardid
    sleep 1
    send "boot \r"
    check_security $boardid
    turn_on_burnin_mode $boardid
    check_LTE_ver $boardid

    log_progress 100 "Completed with MAC0: $mac " 

}

proc login_and_reboot { user passwd } {
    set timeout 20
    log_progress 2 "Detected device in login mode"
    send "$user\r"
    log_debug "Sent username..."
    expect "Password:"
    send "$passwd\r"
    log_debug "Sent password..."
    sleep 2
    send "reboot\r"
}

#proc id_version { } {
#
#    expect {
#         -re "U-Boot unifi-v(\[1-9])\.(\[1-9])\.(\[1-9]+)\.(\[0-9]+)-(\.*)" {
#        set major $expect_out(1,string)
#        set minor $expect_out(2,string)
#                find_version $major $minor
#        } timeout { 
#                error_critical "Device not found!"
#        } 
#    }
#}

#proc find_version { major minor } {
#    global uappext_printenv
#    global uappext_saveenv
#    global uappext
#    global uappaddr

#    log_debug "Major=$major, Minor=$minor"

#    if { [expr $major] == 1 && [expr $minor] >=5 } {
#       log_debug "ubntapp firmware"
#       set uappext_printenv "go $uappaddr uprintenv"
#       set uappext_saveenv "go $uappaddr usaveenv"
#       set uappext_setenv "go $uappaddr usetenv"
#       set uappext "go $uappaddr "
#    }
#} 


proc main_detector { } {
    global user
    global passwd
    global boardid
    global prompt

    set timeout 60
    sleep 1
    send \003
    send "\r"

    expect {
        "Board: Copyright Ubiquiti Networks Inc" {
            handle_uboot 1
        } $prompt {
            send "reset \r"
            main_detector
        } -re "(\\(none\\)|ART) login:" {
            handle_art $boardid
            main_detector
        } "UBNT login:" {
            login_and_reboot $user $passwd
            main_detector
        } "Please press Enter to activate this console." {
            sleep 1
            send "\r"
            main_detector
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

catch { exec xset -q | grep -c 00:\ Caps\ Lock:\ \ \ on 2>/dev/null } capslock
if { $capslock eq "1" } {
    error_critical "Caps Lock is on!"
}

spawn -open [open /dev/$dev w+]
stty 115200 < /dev/$dev
stty raw -echo < /dev/$dev

set is_dragonfly [has_dragonfly_cpu $boardid]
if { $is_dragonfly == 1 }  {
    set prompt "ath>"
#    set devreg_host "-h DRA5.devreg.ubnt.com"
}

log_progress 1 "Waiting - PLUG in the device!...."

main_detector

