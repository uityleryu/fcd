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
            log_warn("No such file $_");
        }
    }
}

sub system_log {
    my @cmd = @_;
    log_debug(@cmd);
    system(@cmd);
}

###### main ######

my ($erasecal, $dev, $idx, $boardid, $fwimg, $hostip)
    = @ARGV;

for my $p ($erasecal, $dev, $idx, $boardid, $fwimg, $hostip) {
    if (!defined($p)) {
        error_critical('Required parameter(s) missing');
    }
}

my $capslock = `xset -q | grep -c '00:\ Caps\ Lock:\ \ \ on'`;
if ($capslock > 0) {
    error_critical('Caps Lock is on');
}

msg(1, "Starting: erasecal=$erasecal dev=$dev; idx=$idx; boardid=$boardid; fwimg=$fwimg; FCD_server_IP=$hostip");

my ($prod_ip_pfx, $prod_ip_base, $prod_pfx_len) = ('192.168.1.', 21, 24);
my ($prod_tmp_mac_pfx, $prod_tmp_mac_base) = ('00:15:6d:00:00:0', 0);

my $prod_dev_ip_base = $prod_ip_base + $idx;
my $prod_dev_ip = "${prod_ip_pfx}$prod_dev_ip_base";
my $prod_dev_tmp_mac_base = $prod_tmp_mac_base + $idx;
my $prod_dev_tmp_mac = "${prod_tmp_mac_pfx}$prod_dev_tmp_mac_base";

my $prod_dir = "usc8";
my $tftpdir = "/tftpboot";
my $cpuname = "VSC7514";
my $timeout = '';
my $ret = '';

my $exp_env = {
    'exp_uboot_prompt'          => 'uboot>',
    'exp_os_prompt'             => '# ',
    'exp_boardid'               => $boardid,
    'exp_hostip'                => $hostip,
    'exp_prod_dev_ip'           => $prod_dev_ip,
    'exp_prod_dev_tmp_mac'      => $prod_dev_tmp_mac,
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);

msg(2, 'Run U-boot checking');
if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_wait_for_u_boot", $exp_env)) {
    error_critical('FAILED to run to U-boot console');
}
sleep 1;

msg(20, 'Run uploading the MFG to DUT from FCD server');
if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_mfg_update", $exp_env)) {
    error_critical('FAILED to upload the MFG to DUT from FCD server');
}
sleep 1;

system_log("curl tftp://$prod_dev_ip -T /tftpboot/$boardid-mfg.bin");
$timeout = 150;
$ret = $exp_h->expect($timeout, -re=>'Bytes transferred');
if ($ret) {
    msg(60, 'DUT receives the MFG FW from the FCD server completed');
} else {
    error_critical("FAILED to receive the MFG FW from the FCD server");
}

if (!run_ubnt_expect($exp_h, "${prod_dir}/${cpuname}_wait_for_linux", $exp_env)) {
    error_critical('FAILED to login the MFG linux console');
}

msg(100, '[DONE] Back to ART completed');
exit 0;
