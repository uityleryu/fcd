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

my ($erasecal, $dev, $idx, $boardid, $fwimg, $hostip)
    = @ARGV;

for my $p ($erasecal, $dev, $idx, $boardid, $fwimg, $hostip) {
    if (!defined($p)) {
        error_critical('Required parameter(s) missing');
    }
}

msg(1, "Starting: erasecal=$erasecal dev=$dev idx=$idx boardid=$boardid fwimg=$fwimg hostip=$hostip");

my ($prod_ip_pfx, $prod_ip_base, $prod_pfx_len) = ('192.168.1.', 21, 24);
my ($prod_tmp_mac_pfx, $prod_tmp_mac_base) = ('00:15:6d:00:00:0', 0);

my $prod_server_ip = $hostip;
my $prod_dev_ip_base = $prod_ip_base + $idx;
my $prod_dev_ip = "${prod_ip_pfx}$prod_dev_ip_base";
my $prod_dev_tmp_mac_base = $prod_tmp_mac_base + $idx;
my $prod_dev_tmp_mac = "${prod_tmp_mac_pfx}$prod_dev_tmp_mac_base";

my %loadaddr_hash = (
    'ec20' => '84000000',
    'ec22' => '84000000'
);
my $loadaddr = ${loadaddr_hash{$boardid}};

my $cal_kernel = "${boardid}-cal.kernel";
my $cal_kernelsize = -s "/tftpboot/$cal_kernel";

my $cal_uboot = "${boardid}-cal.uboot";
my $cal_ubootsize = -s "/tftpboot/$cal_uboot";

my $exp_env = {
    'u_boot_prompt' => 'MT7621 #',
    'prod_dev_ip' => $prod_dev_ip,
    'prod_dev_pfx' => $prod_pfx_len,
    'prod_server_ip' => $prod_server_ip,
    'prod_dev_tmp_mac' => $prod_dev_tmp_mac,
#    'cal_img' => $fwimg,
    'prod_loadaddr' => $loadaddr,
    'prod_uboot' => $cal_uboot,
    'prod_ubootsize' => $cal_ubootsize,
    'prod_kernel' => $cal_kernel,
    'prod_kernelsize' => $cal_kernelsize,
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);
#KMLUOH
##if (1 > 10) {
msg(5, 'Waiting for device ...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_u_boot', $exp_env)) {
    error_critical('FAILED to detect device');
}

msg(20, 'Setting up IP address in u-boot ...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_set_ip', $exp_env)) {
    error_critical('FAILED to set up IP address in u-boot');
}

msg(30, 'Checking network connection to tftp server in u-boot ...');
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


msg(40, 'flash back to calibration kernel ...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_flash_kernel', $exp_env)) {
    error_critical('FAILED to update kernel');
}

msg(60, 'Erase bootselect partition ...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_erase_bootselect', $exp_env)) {
    error_critical('FAILED to erase bootselect partition');
}

msg(70, 'flash back to calibration u-boot ...');
if (!run_ubnt_expect($exp_h, 'MT7621_u_boot_flash_uboot', $exp_env)) {
    error_critical('FAILED to update u-boot');
}

msg(80, 'Waiting for Calibration Linux ...');
if (!run_ubnt_expect($exp_h, 'MT7621_wait_for_cal_linux', $exp_env)) {
    error_critical('FAILED to boot Calibration Linux');
}

msg(100, '[DONE] Back to Calibration task completed');
exit 0;

