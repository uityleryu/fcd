#!/usr/bin/expect --
set boardid [lindex $argv 0]
set countrycode [lindex $argv 1] 
set mac [lindex $argv 2]
set passphrase [lindex $argv 3]
set keydir [lindex $argv 4]
set dev [lindex $argv 5]
set idx [lindex $argv 6]
set tftpserver [lindex $argv 7]
set bomrev [lindex $argv 8]
set bitmask [lindex $argv 9]
set qrcode [lindex $argv 10]
set netmask "255.255.255.0"
set fwimg "$boardid.trx"
set cfeimg "$boardid.cfe"
set rsa_key dropbear_rsa_host_key
set dss_key dropbear_dss_host_key
set user "ubnt"
set passwd "ubnt"
set addrbits [expr 48 - $bitmask]

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



log_debug "launched with params: boardid=$boardid; countrycode=$countrycode; mac=$mac; passphrase=$passphrase; keydir=$keydir; dev=$dev; idx=$idx; tftpserver=$tftpserver; bomrev=13-$bomrev; bitmask=$bitmask"

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

#proc cfe_finish { } {
#
#    log_progress 50 "Restarting..."
#    send "\r"
#    expect "CFE>"
#    send "re\r"
#}

proc stop_cfe {} {

    log_debug "Stoping CFE"
    #send "any key"
    
    set timeout 30
    expect  "Device eth0:" { sleep 2; send \003 } \
    timeout { error_critical "Device not found!" }  

    set timeout 5
    expect timeout {
    } "CFE>"
    
    sleep 1 
    send \003
    set timeout 30
    expect timeout {
        error_critical "CFE prompt not found !"
    } "CFE>"
}

proc setmac { mac } {

    sleep 2
    send "usetmac $mac\r"
    set timeout 15
    expect timeout { 
        error_critical "set MAC failed!" 
    } "*** command status = 0"
    set timeout 5
    expect timeout {
        error_critical "CFE prompt not found !"
    } "CFE>"

    send_user "\r\n * MAC setting succeded *\r\n"
}

proc setwifimac { mac addrbits } {

    set wifimac0 [gen_wifimacaddr $mac $addrbits 0]
    set wifimac1 [gen_wifimacaddr $mac $addrbits 1]

    sleep 2
    send "usetwmac $wifimac0 $wifimac1\r"
    set timeout 15
    expect timeout { 
        error_critical "set WiFi MAC failed!" 
    } "*** command status = 0"
    set timeout 5
    expect timeout {
        error_critical "CFE prompt not found !"
    } "CFE>"

    send_user "\r\n * WiFi MAC setting succeded *\r\n"
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

        sleep 2
    
        send "ping $tftpserver\r"
        set timeout 15
        expect timeout {
            error_critical "Unknown response for ping !"
        } -re ".* is (.*)\r.*\r"

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

#proc has_dual_image { boardid } {
#    global UAP_ID
#    global UAPLR_ID
#    global UAPMINI_ID
#    global UAPOUT_ID
#    global UAPWASP_ID
#    global UAPWASPLR_ID
#    global UAPHSR_ID
#    global UAPOUT5_ID
#    global UAPPRO_ID
#
#    if { [string equal -nocase $boardid $UAPPRO_ID] == 1 
#         || [string equal -nocase $boardid $UAPWASP_ID] == 1 
#         || [string equal -nocase $boardid $UAPWASPLR_ID] == 1
#         || [string equal -nocase $boardid $UAPHSR_ID] == 1 } {
#         return 1
#    } else {
#        return 0
#    }
#}

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

    set timeout 15
    send "nvram erase\r"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    sleep 5

    send "reboot\r"
    set timeout 30
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
    global tftpserver

    sleep 1
    send "usetsshkey $tftpserver:$rsa_key.$idx\r"
    set timeout 30
    expect timeout {
        error_critical "Fail to program $rsa_key.$idx"
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    sleep 1
    send "usetsshkey $tftpserver:$dss_key.$idx\r"
    set timeout 30 
    expect timeout {
        error_critical "Fail to program $dss_key.$idx"
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    send_user "\r\n * ssh keys uploaded successfully *\r\n"
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

proc run_client { idx eeprom_txt eeprom_bin eeprom_signed passphrase keydir} {
    global qrcode
    log_debug "Connecting to server:"
    
    set outfile [open "/tmp/client$idx.sh" w]
    puts $outfile "#!/bin/sh\n"
    puts $outfile "set -o verbose\n"
    if { $qrcode eq "" } {
        puts $outfile "/usr/local/sbin/client_x86 -i field=product_class_id,value=bcmwifi \$(cat /tftpboot/$eeprom_txt  | sed -r -e \"s~^field=(.*)\$~-i field=\\1 ~g\" | grep -v \"eeprom\" | tr '\\n' ' ') -i field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_bin -o field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_signed -k $passphrase -o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message -x $keydir/ca.pem -y $keydir/key.pem -z $keydir/crt.pem "
    } else {
        set qrhex [string2hex $qrcode]
        puts $outfile "/usr/local/sbin/client_x86 -i field=product_class_id,value=bcmwifi \$(cat /tftpboot/$eeprom_txt  | sed -r -e \"s~^field=(.*)\$~-i field=\\1 ~g\" | grep -v \"eeprom\" | tr '\\n' ' ') -i field=qr_code,format=hex,value=$qrhex -i field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_bin -o field=flash_eeprom,format=binary,pathname=/tftpboot/$eeprom_signed -k $passphrase -o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message -x $keydir/ca.pem -y $keydir/key.pem -z $keydir/crt.pem "
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

proc do_security {} {
    global passphrase
    global keydir
    global idx
    global tftpserver
    global user
    global passwd

    set helper helper_BCM4706
    set eeprom_bin e.b.$idx
    set eeprom_txt e.t.$idx
    set eeprom_signed e.s.$idx
    set eeprom_check e.c.$idx

    set timeout 100
    # login    
    expect timeout { 
        error_critical "Failed to boot firmware !" 
    } "Restoring defaults...done"

    expect "Hit enter to continue..." { send "\r" } \
        timeout { error_critical "Login failed" }
    
    #expect "login:" { send "$user\r" } \
    #    timeout { error_critical "Login failed" }

    #expect "Password:" { send "$passwd\r" } \
    #    timeout { error_critical "Login failed" }
        
    expect timeout { error_critical "Login failed" } "\n# "

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

    set timeout 20
    send "PS1=\"UBNT# \"\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# "
    #sleep 1
    send "\[ ! -f /tmp/$eeprom_bin \] || rm /tmp/$eeprom_bin\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# "
    #sleep 1
    send "\[ ! -f /tmp/$eeprom_txt \] || rm /tmp/$eeprom_txt\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# "
    #sleep 1
    send "\[ ! -f /tmp/$eeprom_signed \] || rm /tmp/$eeprom_signed\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    #sleep 1
    send "\[ ! -f /tmp/$eeprom_check \] || rm /tmp/$eeprom_check\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    sleep 4

    #set timeout 90
    #send "while \[ ! -f /etc/udhcpc/info.br0 \]; do sleep 5; done\r"
    #expect timeout { error_critical "Can't get DHCP IP address" } "#"
    #sleep 1

    set timeout 60
    send "udhcpc -i br0 -p /var/run/udhcpc-br0.pid -s /tmp/ldhclnt\r"
    expect timeout { error_critical "Can't get DHCP IP address" } "\nUBNT# "
    sleep 1

    send "cd /tmp\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    #sleep 1

    send "tftp -g -r $helper -b 4096 $tftpserver\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    #sleep 1 
   
    set timeout 20
    send "chmod +x $helper\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    sleep 1

    #send "./$helper -q -c product_class=bcmwifi -o"
    #send " field=flash_eeprom,format=binary,"
    #send "pathname=$eeprom_bin > $eeprom_txt" 
    #send "\r"
    #expect timeout { error_critical "Command prompt not found" } "#" 

    # FIXME, run helper once more, to workaround bug in helper 
    send "./$helper -q -c product_class=bcmwifi -o"
    send " field=flash_eeprom,format=binary,"
    send "pathname=$eeprom_bin > $eeprom_txt" 
    send "\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    sleep 1

    log_debug "Downloading files"
    
    set timeout 30
    send "tftp -p -l $eeprom_bin $tftpserver\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    #sleep 1

    # FIXME, upload file once more, to workaround bug in UAP-Pro Ethernet driver?
    # send "tftp -p -l $eeprom_bin $tftpserver\r"
    # expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    # sleep 1

    send "tftp -p -l $eeprom_txt $tftpserver\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    #sleep 1

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
    
    send "tftp -g -r $eeprom_signed -b 4096 $tftpserver\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    sleep 1
    
    log_debug "File sent."
    
    log_debug "Writing eeprom..."
    
    send "./$helper -q -i "
    send "field=flash_eeprom,format=binary,pathname=$eeprom_signed\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    sleep 1
    
    send "dd if=/dev/`awk -F: '/EEPROM/{print \$1}' /proc/mtd"
    send " | sed 's~mtd~mtdblock~g'` of=/tmp/$eeprom_check\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    sleep 1

    send "tftp -p -l $eeprom_check $tftpserver\r"
    expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 
    #sleep 1
    
    send "reboot\r"
    #expect timeout { error_critical "Command prompt not found" } "\nUBNT# " 

    #send "exit\r"
    
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

}


proc check_security {} {
    global user
    global passwd
    global qrcode
    
    set timeout 120
    # login    
    expect timeout { 
        error_critical "Failed to boot firmware !" 
    } "Please press Enter to activate this console."

    send "\r"
    
    expect "login:" { send "$user\r" } \
        timeout { error_critical "Login failed" }

    expect "Password:" { send "$passwd\r" } \
        timeout { error_critical "Login failed" }
        
    expect timeout { error_critical "Login failed" } "#"

    # for concurrent access issue on /proc/ubnthal/system.info
    # sleep 3 
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


#proc erase_linux_config { boardid } {
    #global UAPPRO_ID

    #if { [string equal -nocase $boardid $UAPPRO_ID] == 1 } {
    #    send "erase 0x9ffb0000 +40000\r"
    #} else {
    #    send "erase 0x9f7b0000 +40000\r"
    #}
#    send "uclearcfg\r"
#    set timeout 30
    #expect timeout { 
    #    error_critical "Erase Linux configuration data failed !" 
    #} " done"
#    expect timeout { 
#        error_critical "Erase Linux configuration data failed !" 
#    } "Done."
#    set timeout 5
#    expect timeout { 
#    } "CFE>"
#}

#proc turn_on_console { boardid } {
#
#    set dual [has_dual_image $boardid]
#    if { $dual == 1 } {
#        send "setenv bootargs 'quiet console=ttyS0,115200"
#        send " init=/init nowifi'\r"
#    } else {
#        send "setenv bootargs 'quiet console=ttyS0,115200"
#        send " root=31:03 rootfstype=squashfs"
#        send " init=/init nowifi'\r"
#    }
#    set timeout 15
#    expect timeout { 
#        error_critical "CFE prompt not found !" 
#    } "CFE>"
#}

proc gen_wifimacaddr { mac addrbits { idx 0 } } {
    if { $addrbits < 10 || $addrbits > 24 } {
        #send_user "addrbits donesn't fit \n"
        return 0xffffffffffff
    }

    set addrmask [expr ((1 << $addrbits) - 1)]
    set base_vsid [expr (0x[string range $mac 6 11] & $addrmask)]

    if {    $base_vsid > [expr ((1 << ($addrbits - 5)) - 1)]
            || $base_vsid < [expr (1 << ($addrbits - 10))] } {
        #send_user "base mac doesn't fit addrbits \n"
        return 0xffffffffffff
    }

    set untouch_vsid [expr ((0x[string range $mac 6 11] >> $addrbits) & 0xffffff)]    
    set new_vsid [format %06x [expr (($untouch_vsid << $addrbits) | (($base_vsid << 5) + ($idx *16)) & $addrmask)]]
    set wifimac "[string range $mac 0 5]$new_vsid"
    #send_user "base_vsid=$base_vsid, new_vsid=$new_vsid\n"
    return $wifimac
}

proc validate_basemac { mac addrbits } {
    if { $addrbits < 10 || $addrbits > 24 } {
        #send_user "addrbits donesn't fit \n"
        return 1
    }

    set addrmask [expr ((1 << $addrbits) - 1)]
    set base_vsid [expr (0x[string range $mac 6 11] & $addrmask)]

    if {    $base_vsid > [expr ((1 << ($addrbits - 5)) - 1)]
            || $base_vsid < [expr (1 << ($addrbits - 10))] } {
        #send_user "base mac doesn't fit addrbits \n"
        return 1
    }

    return 0
}

proc check_macaddr { mac addrbits } {

    set timeout 5
    send "usetmac\r"
    expect timeout {
        error_critical "Unable to get MAC !"
    } -re "MAC Address: (.{2}\[-:].{2}\[-:].{2}\[-:].{2}\[-:].{2}\[-:].{2})"
    expect timeout {
        error_critical "CFE prompt not found !" 
    } "CFE>"

    set mac_str $expect_out(1,string)
    regsub -all {[-:]} $expect_out(1,string) {} mac0_read

    set timeout 5
    send "usetwmac\r"
    expect timeout {
        error_critical "Unable to get WiFi MAC !"
    } -re "WiFi0 MAC Address: (.{2}\[-:].{2}\[-:].{2}\[-:].{2}\[-:].{2}\[-:].{2}).*WiFi1 MAC Address: (.{2}\[-:].{2}\[-:].{2}\[-:].{2}\[-:].{2}\[-:].{2})"
    expect timeout {
        error_critical "CFE prompt not found !" 
    } "CFE>"

    set mac_str $expect_out(1,string)
    regsub -all {[-:]} $expect_out(1,string) {} wifi0_read
    regsub -all {[-:]} $expect_out(2,string) {} wifi1_read

    set wifi0_write [gen_wifimacaddr $mac $addrbits 0]
    set wifi1_write [gen_wifimacaddr $mac $addrbits 1]
    
    if {    [string equal -nocase $mac $mac0_read] != 1
            || [string equal -nocase $wifi0_write $wifi0_read] != 1
            || [string equal -nocase $wifi1_write $wifi1_read] != 1} {
        return 1
    } else {
        return 0
    }
}

proc check_booting { boardid } {

    set timeout 30
    expect timeout {
        error_critical "Kernel boot failure !"
    } "Starting program at 0x80001000"
}

proc do_set_wl_mac { mac } {
    global tftpserver
    set set_script set_wl_mac.sh

    sleep 2
    send "cd /tmp\r"
    set timeout 5
    expect timeout { 
        error_critical "Liunx prompt not found !" 
    } "# "

    sleep 2
    send "tftp -g -r $set_script $tftpserver\r"
    set timeout 5
    expect timeout { 
        error_critical "Liunx prompt not found !" 
    } "# "
    
    sleep 2
    send "chmod +x $set_script\r"
    set timeout 5
    expect timeout { 
        error_critical "Liunx prompt not found !" 
    } "# "

    sleep 2
    send "./$set_script $mac\r"
    set timeout 15 
    expect timeout { 
        error_critical "Liunx prompt not found !" 
    } "# "

    sleep 20
}

proc handle_cfe { {wait_prompt 0} } {
    global fwimg
    global cfeimg
    global boardid
    global mac
    global ip
    global countrycode
    global bomrev
    global addrbits

    if { $wait_prompt == 1 } {
        stop_cfe
    }

    log_progress 5 "Got INTO CFE"

    ## RUN 1, update firmware  
    set_network_env 1
    update_cfe $cfeimg
    log_progress 10 "bootloader updated"

    ## RUN 2, set IDs
    stop_cfe

    # set Board ID
    sleep 2
    send "usetbid $boardid\r"
    set timeout 15
    expect timeout { 
        error_critical "set Board ID failed !" 
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !" 
    } "CFE>"

    # set BOM Revision
    sleep 2
    send "usetbrev $bomrev\r"
    set timeout 15
    expect timeout { 
        error_critical "set BOM Revision failed !" 
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !" 
    } "CFE>"

    # set Country Code
    sleep 2
    send "usetcc $countrycode\r"
    set timeout 15
    expect timeout { 
        error_critical "set Country Code failed !" 
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !" 
    } "CFE>"

    regsub -all {:\-} $mac {} hexmac
    # set Ethernet mac address
    setmac $hexmac

    # set WiFi mac address
    setwifimac $hexmac $addrbits
    log_progress 20 "Board ID/Regulatory Domain/MAC address set"

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

    # reboot
    sleep 1
    send "reboot\r"

    ## RUN 3, upload ssh keys & check IDs
    stop_cfe

    sleep 1
    set_network_env

    # upload ssh keys
    gen_sshkeys
    upload_sshkeys
    log_progress 30 "ssh keys uploaded"

    #update_firmware $boardid.factorybin 1

    sleep 1
    set timeout 5
    send "usetbid\r"
    expect timeout {
        error_critical "Unable to get Board ID!"
    } -re "Board ID: (.{4})\r"
    
    set bid_str $expect_out(1,string)
   
    expect timeout {]
       error_critical "CFE prompt not found !" 
    } "CFE>"

    #log_debug "bid_str: $bid_str"
    if { [string equal -nocase $bid_str $boardid] != 1 } {
        error_critical "Board ID doesn't match!"
    }

    sleep 1
    set timeout 5
    send "usetbrev\r"
    expect timeout {
        error_critical "Unable to get BOM Revision!"
    } -re "BOM Rev: (\\d+\\-\\d+)\r"
    
    set brev_str $expect_out(1,string)
    expect timeout { 
       error_critical "CFE prompt not found !" 
    } "CFE>"

    #log_debug "brev_str: $brev_str"

    if { [string equal $brev_str $bomrev] != 1 } {
        error_critical "BOM Revision doesn't match!"
    }

    sleep 1
    set timeout 5
    send "usetcc\r"
    expect timeout {
        error_critical "Unable to get Country Code!"
    } -re "Country Code: (.*)\r"
   
    set cc_str $expect_out(1,string) 
    expect timeout { 
       error_critical "CFE prompt not found !" 
    } "CFE>"

    set cc [expr $cc_str + 0]
    log_debug "cc_str: $cc_str, cc: $cc"

    if { $cc != $countrycode } {
        error_critical "Country Code doesn't match!"
    }

    sleep 1
    set wrong_mac [check_macaddr $hexmac $addrbits]
    if { $wrong_mac == 1 } {
        error_critical "MAC address doesn't match!"
    }

    log_progress 35 "Board ID/Regulatory Domain/MAC address checked"

    # boot 2nd image
    #sleep 1
    #send "nvram set bootpartition=1\r"
    #set timeout 5
    #expect timeout { 
    #    error_critical "set bootpartition failed !" 
    #} "*** command status = 0"
    #expect timeout { 
    #    error_critical "CFE prompt not found !" 
    #} "CFE>"

    #sleep 1
    #send "nvram commit\r"
    #set timeout 15
    #expect timeout { 
    #    error_critical "set bootpartition failed !" 
    #} "*** command status = 0"
    #expect timeout { 
    #    error_critical "CFE prompt not found !" 
    #} "CFE>"

    #sleep 1
    #send "reboot\r"
    #set timeout 30
    #expect timeout { 
    #    error_critical "Boot manufacturing image failed!" 
    #} "port: 23; interface: br1; login program: /bin/sh"
    #set timeout 15
    #expect timeout { 
    #    error_critical "Boot manufacturing image failed!" 
    #} "Hit enter to continue..."

    #sleep 2
    #send "\r"
    #set timeout 5
    #expect timeout { 
    #    error_critical "Liunx prompt not found !" 
    #} "# "
   
    #sleep 1
    #send "brctl addif br0 eth0\r"
    #set timeout 5
    #expect timeout { 
    #    error_critical "Liunx prompt not found !" 
    #} "# "
     
    # do_set_wl_mac $mac
    # FIXME: not done yet
    # set daughter country code (if necessary)
    # do_security

    #sleep 1
    send "reboot\r"

    check_booting $boardid
    do_security
    log_progress 45 "device registration done"
         
    sleep 1
    send "reboot\r"

    stop_cfe
    sleep 1
    set_network_env

    #FIXME
    update_firmware $fwimg 0
    log_progress 70 "1st firmware updated"
    update_firmware $fwimg 1
    log_progress 95 "2nd firmware updated"

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
    send "uclearcfg\r"
    set timeout 20 
    expect timeout {
        error_critical "Erase CFG failed !" 
    } "*** command status = 0"
    set timeout 5
    expect timeout { 
        error_critical "CFE prompt not found !"
    } "CFE>"

    sleep 1
    set timeout 10
    send "nvram set ubootargs='console=ttyS0,115200 panic=3' \r"
    expect timeout {
        error_critical "Failed setting console parameters "
    } "CFE>"

    sleep 1
    set timeout 10
    send "nvram commit \r"
    expect timeout {
        error_critical "Failed to commit console parameters "
    } "CFE>"

    send " boot -raw -z -addr=0x80001000 -max=0x1eff000 flash0.os: \r"

    check_booting $boardid

    check_security

    sleep 1
    send "reboot\r"
    stop_cfe

    # Undo the bootargs for setting the console
    send "nvram erase \r"
    expect timeout {
        error_critical "Failed to erase nvram "
    } "CFE>"

    log_progress 100 "Completed with MAC0: $mac " 

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
    global mac
    global addrbits

    regsub -all {:\-} $mac {} hexmac
    set wrong_mac [validate_basemac $hexmac $addrbits]
    if { $wrong_mac == 1 } {
        error_critical "Invalid MAC address!"
    }
    
    set timeout 30
    sleep 2
    send \003
    send "\r"
    sleep 3
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

