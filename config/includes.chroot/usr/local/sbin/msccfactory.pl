#!/usr/bin/perl -w

use strict;
use warnings;

use POSIX;
use IO::File;
use Expect;
use UBNT::Expect qw(run_ubnt_expect);

sub msg {
    my $p = shift;
    my $pstr = '';
    if ($p ne '') {
        $pstr = "\n=== $p ===";
    }
    my $t = strftime('%Y-%m-%d %H:%M:%S', localtime);
    print "\n$pstr\n[FCD $t] @_\n\n";
}

sub log_error {
    my $pstr = "\n* * * ERROR: * * *";
    my $t = strftime('%Y-%m-%d %H:%M:%S', localtime);
    print "\n$pstr\n[FCD $t] @_\n\n";
}

sub error_critical {
    log_error(@_);
    exit 2;
}

sub log_warn {
    my $pstr = "\n* WARN: *";
    my $t = strftime('%Y-%m-%d %H:%M:%S', localtime);
    print "\n$pstr\n[FCD $t] @_\n\n";
}

sub log_debug {
    my $pstr = "\nDEBUG:";
    my $t = strftime('%Y-%m-%d %H:%M:%S', localtime);
    print "\n$pstr\n[FCD $t] @_\n\n";
}

sub get_console_expect {
    my ($d) = @_;
    my $devfile = "/dev/$d";
    if (! -c "$devfile") {
        error_critical("Invalid console device $d");
    }

    my @stty_opts = qw(sane 115200 raw -parenb -cstopb cs8 -echo onlcr);
    system('stty', '-F', $devfile, @stty_opts);

    my $dev_h;
    open($dev_h, '+<', "$devfile") or error_critical("Cannot open console device $d");

    my $e = Expect->exp_init(\*$dev_h);
    $e->log_stdout(1);
    return $e;
}

sub del_server_file {
    foreach (@_) {
        if (-e "$_") {
            system("rm -f $_");
            if ($? < 0) {
                log_warn("Can't delete the $_");
            } else {
                log_debug("delete the $_ successfully");
            }
        } else {
            log_debug("Delete file: No $_");
        }
    }
}

sub system_log {
    my @cmd = @_;
    log_debug(@cmd);
    system(@cmd);
}

###### main ######

my ($boardid, $mac, $passphrase, $keydir, $dev, $idx, $hostip, $bomrev, $qrcode)
    = @ARGV;

for my $p ($boardid, $mac, $passphrase, $keydir, $dev, $idx, $hostip, $bomrev, $qrcode) {
    if (!defined($p)) {
        error_critical('Required parameter(s) missing');
    }
}

my $capslock = `xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'`;
if ($capslock > 0) {
    error_critical('Caps Lock is on');
}

msg(1, "Starting: boardid=$boardid mac=$mac passphrase=$passphrase keydir=$keydir "
    . "dev=$dev idx=$idx hostip=$hostip bomrev=$bomrev qrcode=$qrcode");

my ($prod_ip_pfx, $prod_ip_base, $prod_pfx_len) = ('192.168.1.', 21, 24);
my ($prod_tmp_mac_pfx, $prod_tmp_mac_base) = ('00:15:6d:00:00:0', 0);

my $prod_dev_ip_base = $prod_ip_base + $idx;
my $prod_dev_ip = "${prod_ip_pfx}$prod_dev_ip_base";
my $prod_dev_tmp_mac_base = $prod_tmp_mac_base + $idx;
my $prod_dev_tmp_mac = "${prod_tmp_mac_pfx}$prod_dev_tmp_mac_base";

my %modelname = (
    'ed01' => 'UniFi USC-8!',
    'ed02' => 'UniFi USC-8P-60!',
    'ed03' => 'UniFi USC-8P-150!'
);

my $timeout = '';
my $ret = '';
my $prod_dir = "usc8";
my $fullbomrev = "113-$bomrev";
my $do_devreg = "1";
my $tftpdir = "/tftpboot";
my $devregcmd = "vsc7514-ee";
my $cpuname = "VSC7514";
my $eeprom_bin = "e.b.$idx";
my $eeprom_txt = "e.t.$idx";
my $eeprom_tgz = "e.$idx.tgz";
my $eeprom_signed = "e.s.$idx";
my $eeprom_check = "e.c.$idx";
my $e_s_gz = "$eeprom_signed.gz";
my $e_c_gz = "$eeprom_check.gz";
my $helper = "helper_VSC7514";
my $helpercmd = "/tmp/$helper -q -c product_class=basic -o field=flash_eeprom,format=binary,pathname=$eeprom_bin > $eeprom_txt";

my $exp_env = {
    'exp_uboot_prompt'          => 'uboot>',
    'exp_os_prompt'             => '# ',
    'exp_mac'                   => lc($mac),
    'exp_fullbomrev'            => $fullbomrev,
    'exp_boardid'               => $boardid,
    'exp_devregcmd'             => $devregcmd,
    'exp_helper'                => $helper,
    'exp_helpercmd'             => $helpercmd,
    'exp_eeprom_bin'            => $eeprom_bin,
    'exp_eeprom_txt'            => $eeprom_txt,
    'exp_eeprom_tgz'            => $eeprom_tgz,
    'exp_eeprom_signed'         => $eeprom_signed,
    'exp_eeprom_check'          => $eeprom_check,
    'exp_e_s_gz'                => $e_s_gz,
    'exp_e_c_gz'                => $e_c_gz,
    'exp_hostip'                => $hostip,
    'exp_prod_dev_ip'           => $prod_dev_ip,
    'exp_modelname'             => $modelname{$boardid},
    'exp_qrcode'                => $qrcode,
    'exp_prod_dev_tmp_mac'      => $prod_dev_tmp_mac,
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);

msg(2, 'Run U-boot and FCD server link check');
if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_linkchk_for_u_boot", $exp_env)) {
    error_critical('FAILED to make a connection with FCD server');
}

msg(5, 'Run devreg registration');
if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_wait_for_linux", $exp_env)) {
    error_critical('FAILED to run to linux console');
}

if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_do_vsc7514-ee", $exp_env)) {
    error_critical('FAILED to complete the devreg vsc7514-ee');
}
msg(7, 'Finish do the devreg command');

if ($do_devreg) {
    my $ret;
    my $timeout;

    # would delete all the previous EEPROM outputs if they were existed
    my @files = ("$tftpdir/$eeprom_bin",
                 "$tftpdir/$eeprom_txt",
                 "$tftpdir/$eeprom_signed",
                 "$tftpdir/$eeprom_check",
                 "$tftpdir/$eeprom_tgz",
                 "$tftpdir/$e_s_gz",
                 "$tftpdir/$e_c_gz");
    del_server_file(@files);

    msg(10, 'FCD sends helper to DUT');
    # DUT will ask for the FCD server to send the helper command to it.
    if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_request_helper", $exp_env)) {
        error_critical('FAILED to access the helper from FCD server to DUT');
    }
    system_log("sz -e -v -b $tftpdir/$helper > /dev/$dev < /dev/$dev");
    $timeout = 30;
    $ret = $exp_h->expect($timeout, -re=>'Transfer complete');
    if ($ret) {
        log_debug("FCD server sends $tftpdir/$helper to DUT successfully\n");
    } else {
        error_critical("FCD server sends $tftpdir/$helper to DUT failed");
    }

    # DUT will do the helper command to generate a pile of EEPROM files
    if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_execute_helper_cmd", $exp_env)) {
        error_critical('FAILED to execute the helper command');
    }

    # DUT will send EEPROM.tgz file to the FCD server.
    if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_send_EEPROM_TGZ", $exp_env)) {
        error_critical('FAILED to send the EEPROM TGZ file to FCD server');
    }
    system_log("cd $tftpdir; rz -v -b -y < /dev/$dev > /dev/$dev");

    # Check if the EERPOM TGZ file is existed or not
    if (! -e "$tftpdir/$eeprom_tgz") {
        error_critical("$eeprom_tgz download failure");
    }
    system_log("cd $tftpdir; tar zxf $tftpdir/$eeprom_tgz");
    if ($? < 0) {
        error_critical("Unzipping the file, $tftpdir/$eeprom_tgz failed");
    }
    if (! -e "$tftpdir/$eeprom_bin") {
        error_critical("$tftpdir/$eeprom_txt is not existed");
    } else {
        log_debug("$tftpdir/$eeprom_txt is existed\n");
    }
    if (! -e "$tftpdir/$eeprom_txt") {
        error_critical("$tftpdir/$eeprom_txt is not existed");
    } else {
        log_debug("$tftpdir/$eeprom_txt is existed\n");
    }

    msg(20, 'Start doing the client_x86');
    # Do the devreg registration from FCD server
    my $qrhex = $qrcode;
    my $subparams = `cat /tftpboot/$eeprom_txt  | sed -r -e \"s~^field=(.*)\$~-i field=\\1~g\" | grep -v \"eeprom\" | tr '\\n' ' '`;
    $qrhex =~ s/(.)/sprintf("%x",ord($1))/eg;
    my $params = "-k $passphrase "
             . "-i field=product_class_id,value=radio "
             . $subparams
             . "-i field=qr_code,format=hex,value=$qrhex "
             . "-i field=flash_eeprom,format=binary,pathname=$tftpdir/$eeprom_bin "
             . "-o field=flash_eeprom,format=binary,pathname=$tftpdir/$eeprom_signed "
             . '-o field=registration_id '
             . '-o field=result '
             . '-o field=device_id '
             . '-o field=registration_status_id '
             . '-o field=registration_status_msg '
             . '-o field=error_message '
             . "-x $keydir/ca.pem "
             . "-y $keydir/key.pem "
             . "-z $keydir/crt.pem "
             . "$qrcode "
             . '-h devreg-prod.ubnt.com';
    system_log("/usr/local/sbin/client_x86 $params");
    sleep 2;

    # Uploading the signed EEPROM from FCD server to DUT
    system_log("gzip $tftpdir/$eeprom_signed");
    sleep 2;
    if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_request_EEPROM_signed", $exp_env)) {
        error_critical('FAILED to send the signed EEPROM file from FCD server to DUT');
    }
    system_log("cd $tftpdir; sz -e -v -b $e_s_gz > /dev/$dev < /dev/$dev");
    $timeout = 90;
    $ret = $exp_h->expect($timeout, -re=>'Transfer complete');
    if ($ret) {
        log_debug("FCD server sends $tftpdir/$e_s_gz to DUT successfully\n");
    } else {
        error_critical("FCD server failed to send $tftpdir/$e_s_gz to DUT");
    }

    # programming the signed EEPROM to the flash on DUT
    # And then send back the check EEPROM file from DUT back to FCD server
    if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_DUT_EEPROM_verification", $exp_env)) {
        error_critical('FAILED to EEPROM verification in the DUT');
    }
    system_log("cd $tftpdir; rz -v -b -y < /dev/$dev > /dev/$dev");

    # Checking the signed EEPROM and checked EEPROM
    system_log("cd $tftpdir; gunzip $e_c_gz");
    sleep 1;
    system_log("cd $tftpdir; gunzip $e_s_gz");
    sleep 1;
    if (! -e "$tftpdir/$eeprom_check") {
        error_critical("$tftpdir/$eeprom_check is not existed");
    } else {
        log_debug("$tftpdir/$eeprom_check is existed\n");
    }
    if (! -e "$tftpdir/$eeprom_signed") {
        error_critical("$tftpdir/$eeprom_signed is not existed");
    } else {
        log_debug("$tftpdir/$eeprom_signed is existed\n");
    }

    system_log("/usr/bin/cmp /tftpboot/$eeprom_signed /tftpboot/$eeprom_check");
    if ($? == 0) {
        msg(40, 'Registration to devreg server completed');
        $exp_h->send("reboot\n");
    } else {
        error_critical("Registration failed");
    }
} else {
    msg(40, 'Skip doing the registration');
}

if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_wait_for_u_boot", $exp_env)) {
    error_critical('FAILED to run to U-boot console');
}
sleep 1;

if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_firmware_update", $exp_env)) {
    error_critical('FAILED to run firmware update');
}
sleep 2;

system_log("curl tftp://$prod_dev_ip -T /tftpboot/$boardid.bin");
if ($? == 0) {
    msg(50, 'Firmware uploading from FCD server is completed');
} else {
    error_critical("Firmware uploading from FCD server is failed");
}

$timeout = 120;
$ret = $exp_h->expect($timeout, -re=>'Bytes transferred');
if ($ret) {
    msg(60, 'DUT receives the firmware from the FCD server completed');
} else {
    error_critical("DUT failed to receive the firmware from the FCD server");
}

if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_wait_for_linux", $exp_env)) {
    error_critical('FAILED to run to linux console');
}

if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_firmware_check", $exp_env)) {
    error_critical('FAILED to check the release firmware');
}

msg(100, '[DONE] Production tasks completed');
exit 0;
