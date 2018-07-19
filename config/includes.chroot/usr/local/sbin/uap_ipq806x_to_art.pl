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

#my ($ffile, $pfile, $cfile)
#    = ("helper.out.fields.$idx", "helper.out.part.$idx", "client.out.$idx");

# match machid in ART image provided by BSP team
my %machid_hash = (
    'e530' => '1260',
    'e540' => '1260',
    'e560' => '137f',
    'e570' => '137f',
    'e580' => '137f'
);
my $machid = ${machid_hash{$boardid}};

my $exp_env = {
    'u_boot_prompt' => '\(IPQ\) #',
    'prod_dev_ip' => $prod_dev_ip,
    'prod_dev_pfx' => $prod_pfx_len,
    'prod_server_ip' => $prod_server_ip,
    'prod_dev_tmp_mac' => $prod_dev_tmp_mac,
    'prod_machid' => $machid,
    'art_img' => $fwimg
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);
#KMLUOH
##if (1 > 10) {
msg(5, 'Waiting for device ...');
if (!run_ubnt_expect($exp_h, 'IPQ806X_wait_for_u_boot', $exp_env)) {
    error_critical('FAILED to detect device');
}

msg(20, 'Setting up IP address in u-boot ...');
if (!run_ubnt_expect($exp_h, 'IPQ806X_u_boot_set_ip', $exp_env)) {
    error_critical('FAILED to set up IP address in u-boot');
}

msg(30, 'Checking network connection to tftp server in u-boot ...');
my $max_try = 5;
my $cnt = 0;
my $ready = run_ubnt_expect($exp_h, 'IPQ806X_u_boot_check_network', $exp_env);
while ( ($cnt < $max_try) && (!$ready) ) {
    $ready = run_ubnt_expect($exp_h, 'IPQ806X_u_boot_check_network', $exp_env);
    if (!$ready) {
        $cnt = $cnt + 1;
        sleep(1);
    }
}
if (!$ready) {
    error_critical('FAILED to ping tftp server in u-boot');
}

msg(50, 'flash back to ART image...');
if (!run_ubnt_expect($exp_h, 'IPQ806X_u_boot_flash_art_image', $exp_env)) {
    error_critical('FAILED to flash back to ART image');
}

msg(100, '[DONE] Back to ART task completed');
exit 0;

