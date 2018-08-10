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

###### main ######

my ($boardid, $regdmn, $mac, $passphrase, $keydir, $dev, $idx, $hostip, $bomrev, $qrcode)
    = @ARGV;

for my $p ($boardid, $regdmn, $mac, $passphrase, $keydir, $dev, $idx, $hostip, $bomrev) {
    if (!defined($p)) {
        error_critical('Required parameter(s) missing');
    }
}

my $capslock = `xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'`;
if ($capslock > 0) {
    error_critical('Caps Lock is on');
}

if (defined($qrcode)) {
    msg(1, "Starting: boardid=$boardid mac=$mac passphrase=$passphrase keydir=$keydir "
        . "dev=$dev idx=$idx hostip=$hostip bomrev=$bomrev qrcode=$qrcode");
} else {
    msg(1, "Starting: boardid=$boardid mac=$mac passphrase=$passphrase keydir=$keydir "
        . "dev=$dev idx=$idx hostip=$hostip bomrev=$bomrev");
}

my ($prod_ip_pfx, $prod_ip_base, $prod_pfx_len) = ('192.168.1.', 21, 24);
my ($prod_tmp_mac_pfx, $prod_tmp_mac_base) = ('00:15:6d:00:00:0', 0);

my $prod_server_ip = $hostip;
my $prod_dev_ip_base = $prod_ip_base + $idx;
my $prod_dev_ip = "${prod_ip_pfx}$prod_dev_ip_base";
my $prod_dev_tmp_mac_base = $prod_tmp_mac_base + $idx;
my $prod_dev_tmp_mac = "${prod_tmp_mac_pfx}$prod_dev_tmp_mac_base";

my ($ffile, $pfile, $cfile, $sfile)
    = ("helper.out.fields.$idx", "helper.out.part.$idx", "client.out.$idx", "helper.out.md5sum.$idx");

my $hex = sprintf("%x", (hex(substr(lc($mac), 1, 1)) | 0x2));
my $local_admin_mac0 = substr(lc($mac), 0, 1) . $hex . substr(lc($mac), 2);
$local_admin_mac0 =~ s/([[:xdigit:]]{2})\B/$1:/g;

my %ethcnt_hash = (
    'ec20' => 1,
    'ec22' => 1
);
my $ethcnt = ${ethcnt_hash{$boardid}};

my %wificnt_hash = (
    'ec20' => 2,
    'ec22' => 2
);
my $wificnt = ${wificnt_hash{$boardid}};

my %btcnt_hash = (
    'ec20' => 0,
    'ec22' => 1
);
my $btcnt = ${btcnt_hash{$boardid}};

my %loadaddr_hash = (
    'ec20' => '84000000',
    'ec22' => '84000000'
);
my $loadaddr = ${loadaddr_hash{$boardid}};

my %sbdversion_hash = (
    'ec20' => '0x0001',
    'ec22' => '0x0002',
);
my $sbdversion = ${sbdversion_hash{$boardid}};

my %sbdlen_hash = (
    'ec20' => '100',
    'ec22' => '101'
);
my $sbdlen = ${sbdlen_hash{$boardid}};

my $kernel = "${boardid}.kernel";
my $kernelsize = -s "/tftpboot/$kernel";

my $uboot = "${boardid}.uboot";
my $ubootsize = -s "/tftpboot/$uboot";

my $exp_env = {
    'u_boot_prompt' => 'MT7621 #',
    'prod_dev_mac' => lc($mac),
    'prod_dev_ip' => $prod_dev_ip,
    'prod_dev_pfx' => $prod_pfx_len,
    'prod_server_ip' => $prod_server_ip,
    'prod_dev_tmp_mac' => $prod_dev_tmp_mac,
    'prod_img' => "${boardid}.bin",
    'prod_uboot' => $uboot,
    'prod_ubootsize' => $ubootsize,
    'prod_kernel' => $kernel,
    'prod_kernelsize' => $kernelsize,
    'prod_ethcnt' => $ethcnt,
    'prod_wificnt' => $wificnt,
    'prod_btcnt' => $btcnt,
    'prod_loadaddr' => $loadaddr,
    'prod_sbdversion' => $sbdversion,
    'prod_sbdlen' => $sbdlen,
#    'num_macs' => $num_macs,
    'board_id' => $boardid,
#    'bom_part' => $bom_part,
    'bom_rev' => $bomrev,
#    'board_serial' => $serial_num,
    'passphrase' => $passphrase,
    'u_boot_tftp_file' => "${boardid}-fcd.kernel",
#    'u_boot_linux_cmdline' => 'mtdparts=$(mtdparts) rw',
#    'flash_base' => $flash_base,
    'reg_ffile' => $ffile,
    'reg_pfile' => $pfile,
    'reg_cfile' => $cfile,
    'reg_sfile' => $sfile,
    'temp_kern_prompt' => '# ',
    'os_prompt' => '# ',
#    'edgeos_cfg_prompt' => '@ubnt# ',
#    'systemid' => $system_id,
    'prod_dev_regdmn' => $regdmn,
    'qr_code' => $qrcode
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);
#KMLUOH
##if (1 > 10) {
msg(2, 'Waiting for device, 1st time...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_u_boot', $exp_env)) {
    error_critical('FAILED to detect device');
}

msg(4, 'Setting up IP address in u-boot, 1st time...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_set_ip', $exp_env)) {
    error_critical('FAILED to set up IP address in u-boot');
}

msg(6, 'Checking network connection to tftp server in u-boot, 1st time...');
my $max_try = 5;
my $cnt = 0;
my $ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
while ( ($cnt < $max_try) && (!$ready) ) {
    $ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to ping tftp server in u-boot');
}

msg(8, 'Updating u-boot ...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_flash_uboot', $exp_env)) {
    error_critical('FAILED to update u-boot');
}

msg(10, 'Waiting for device, 2nd time...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_u_boot', $exp_env)) {
    error_critical('FAILED to detect device');
}

msg(11, 'Setting up IP address in u-boot, 2nd time...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_set_ip', $exp_env)) {
    error_critical('FAILED to set up IP address in u-boot');
}

msg(12, 'Checking network connection to tftp server in u-boot, 2nd time...');
$max_try = 5;
$cnt = 0;
$ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
while ( ($cnt < $max_try) && (!$ready) ) {
    $ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to ping tftp server in u-boot');
}

msg(13, 'Booting manufacturing kernel, 1st time...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_linux_tftp', $exp_env)) {
    error_critical('FAILED to boot manufacturing kernel');
}

msg(14, 'Waiting for manufacturing kernel ready, 1st time...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_temp_kern', $exp_env)) {
    error_critical('FAILED to boot manufacturing kernel');
}

if ($btcnt == 1) {
    msg(15, 'Waiting for BT device ready, 1st time...');
    $max_try = 10;
    $cnt = 0;
    $ready = run_ubnt_expect($exp_h, 'MT7621_temp_kern_wait_for_bt', $exp_env);
    while ( ($cnt < $max_try) && (!$ready) ) {
        $ready = run_ubnt_expect($exp_h, 'MT7621_temp_kern_wait_for_bt', $exp_env);
        if (!$ready) {
            $cnt = $cnt + 1;
            sleep(1);
        }
    }
    if (!$ready) {
        error_critical('FAILED to initialize BT in manufacturing kernel');
    }
}

if ($btcnt > 1) {
    error_critical('FAILED because btcnt > 1 is not supported');
}

msg(16, 'Setting hardware ID in EEPROM...');
if (!run_ubnt_expect($exp_h, 'MT7621_temp_kern_set_eeprom', $exp_env)) {
    error_critical('FAILED to set hardware ID in EEPROM');
}

msg(18, 'Rebooting manufacturing kernel...');
if (!run_ubnt_expect($exp_h, 'MT7621_temp_kern_reboot', $exp_env)) {
    error_critical('FAILED to reboot manufacturing kernel');
}

msg(20, 'Waiting for device, 3rd time...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_u_boot', $exp_env)) {
    error_critical('FAILED to detect device');
}

msg(21, 'Setting up IP address in u-boot, 3rd time...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_set_ip', $exp_env)) {
    error_critical('FAILED to set up IP address in u-boot');
}

msg(22, 'Checking network connection to tftp server in u-boot, 3rd time...');
$max_try = 5;
$cnt = 0;
$ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
while ( ($cnt < $max_try) && (!$ready) ) {
    $ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to ping tftp server in u-boot');
}

msg(23, 'Booting manufacturing kernel, 2nd time...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_linux_tftp', $exp_env)) {
    error_critical('FAILED to boot manufacturing kernel');
}

msg(24, 'Waiting for manufacturing kernel ready, 2nd time...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_temp_kern', $exp_env)) {
    error_critical('FAILED to boot manufacturing kernel');
}

msg(26, 'Checking hardware ID in EEPROM...');
if (!run_ubnt_expect($exp_h, 'MT7621_temp_kern_check_eeprom', $exp_env)) {
    error_critical('FAILED to check hardware ID in EEPROM');
}

run_ubnt_expect($exp_h, 'MT7621_temp_kern_config_ethernet_switch', $exp_env);

msg(30, 'Checking network connection to tftp server in manufacturing kernel...');
$max_try = 5;
$cnt = 0;
$ready = run_ubnt_expect($exp_h, 'MT7621_temp_kern_check_network', $exp_env);
while ( ($cnt < $max_try) && (!$ready) ) {
    $ready = run_ubnt_expect($exp_h, 'MT7621_temp_kern_check_network', $exp_env);
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to ping tftp server in manufacturing kernel');
}

my $tdir = '/tftpboot';
my ($fpath, $ppath, $spath) = ("$tdir/$ffile", "$tdir/$pfile", "$tdir/$sfile");
msg(32, 'Running registration helper...');
if (!run_ubnt_expect($exp_h, 'MT7621_temp_kern_gen_helper_out', $exp_env)) {
    error_critical('FAILED to generate helper output files');
}

msg(33, 'Uploading registration helper output files...');
$max_try = 5;
$cnt = 0;
system("rm -f $fpath $ppath $spath; touch $fpath $ppath $spath; chmod 777 $fpath $ppath $spath; sync; sleep 1");
$ready = run_ubnt_expect($exp_h, 'MT7621_temp_kern_upload_helper_out', $exp_env);
if ($ready) {
    system("cd $tdir && md5sum -c $sfile");
    if ($? != 0) {
        $ready = 0;
    }
}
while ( ($cnt < $max_try) && (!$ready) ) {
    system("rm -f $fpath $ppath $spath; touch $fpath $ppath $spath; chmod 777 $fpath $ppath $spath; sync; sleep 1");
    $ready = run_ubnt_expect($exp_h, 'MT7621_temp_kern_upload_helper_out', $exp_env);
    if ($ready) {
        system("cd $tdir && md5sum -c $sfile");
        if ($? != 0) {
            $ready = 0;
        }
    }
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to upload helper output files');
}

my $skip_devreg = 0;	# for development purpose
if ($skip_devreg != 1) {

my $fpath1 = "$fpath-1";
my $cmd = "grep 'field=' $fpath | grep -v flash_eeprom "
          . '| while read line; do echo -n "-i $line "; done ' . ">$fpath1";
system("sync");
sleep(1);
system($cmd);

my $cpath = "$tdir/$cfile";

my $params = "-k $passphrase "
             . "-i field=flash_eeprom,format=binary,pathname=$ppath "
             . "-h devreg-prod.ubnt.com "
             . "-x $keydir/ca.pem -y $keydir/key.pem -z $keydir/crt.pem "
             . "\$(cat $fpath1) "
             . "-o field=flash_eeprom,format=binary,pathname=$cpath "
             . '-o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message ';

if (defined($qrcode)) {
    my $qrhex = $qrcode;
    $qrhex =~ s/(.)/sprintf("%x",ord($1))/eg;
    $params = $params . "-i field=qr_code,format=hex,value=$qrhex ";
}

system("rm -f $cpath; sync; sleep 1");
system("/usr/local/sbin/client_x86 $params");

if (-f $cpath) {
    system("rm -f ${ppath}-1; touch ${ppath}-1; chmod 777 ${ppath}-1; sync; sleep 1");
    msg(35, 'Finalizing device registration...');
    if (!run_ubnt_expect($exp_h, 'MT7621_temp_kern_devreg_2', $exp_env)) {
        error_critical('FAILED to complete device registration');
    }

    system("sync");
    sleep(1);
    system("diff -q $cpath ${ppath}-1");
    if ($? != 0) {
        error_critical('FAILED to match device registration EEPROM');
    }
} else {
    error_critical('FAILED to register device');
}

##system("cp $cpath /media/disk/UAPACHD_EEPROM/${mac}.eeprom");

system("rm -f ${fpath}* ${ppath}* ${cpath}*");

} else {	# if ($skip_devreg != 1)
    run_ubnt_expect($exp_h, 'MT7621_temp_kern_reboot', $exp_env);
}

msg(40, 'Waiting for device, 4th time...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_u_boot', $exp_env)) {
    error_critical('FAILED to detect device');
}

msg(42, 'Setting up IP address in u-boot, 4th time...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_set_ip', $exp_env)) {
    error_critical('FAILED to set up IP address in u-boot');
}

msg(44, 'Checking network connection to tftp server in u-boot, 4th time...');
$max_try = 5;
$cnt = 0;
$ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
while ( ($cnt < $max_try) && (!$ready) ) {
    $ready = run_ubnt_expect($exp_h, 'MT7621_u_boot_check_network', $exp_env);
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to ping tftp server in u-boot');
}

msg(46, 'Putting AP to urescue mode...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_start_urescue', $exp_env)) {
    error_critical('FAILED to enable urescue mode');
}

sleep(1);
msg(50, 'Uploading release firmware...');
system("atftp --option \"mode octet\" -p -l /tftpboot/${boardid}.bin ${prod_dev_ip}");

msg(52, 'Checking firmware...');
if (!run_ubnt_expect($exp_h, 'MT7621_urescue_check_fwcheck', $exp_env)) {
    error_critical('FAILED in firmware checking');
}

# watch upgrade messages
msg(55, 'Updating release firmware...');
if (!run_ubnt_expect($exp_h, 'MT7621_urescue_check_fwupdate', $exp_env)) {
    error_critical('FAILED to update release firmware');
}

##KMLUOH
##}
msg(60, 'Booting into UniFi AP firmware...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_linux', $exp_env)) {
    error_critical('FAILED to boot UniFi AP');
}

msg(90, 'Checking EEPROM...');
if (!run_ubnt_expect($exp_h, 'MT7621_linux_check_eeprom', $exp_env)) {
    error_critical('FAILED to match final EEPROM info');
}

msg(100, '[DONE] Production tasks completed');
exit 0;
