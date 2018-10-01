#!/usr/bin/perl -w

use strict;
use warnings;

use POSIX;
use IO::File;
use Expect;
use UBNT::Expect qw(run_ubnt_expect);

sub get_console_expect {
    my ($d) = @_;
    my $devfile = "/dev/$d";
    die "Invalid console device $d" if (! -c "$devfile");

    my @stty_opts = qw(sane 115200 raw -parenb -cstopb cs8 -echo onlcr);
    system('stty', '-F', $devfile, @stty_opts);

    my $dev_h;
    open($dev_h, '+<', "$devfile") or die "Cannot open console device $d";

    my $e = Expect->exp_init(\*$dev_h);
    $e->log_stdout(1);
    return $e;
}

sub msg {
    my $p = shift;
    my $pstr = '';
    if ($p ne '') {
        $pstr = "\n=== $p ===";
    }
    my $t = strftime('%Y-%m-%d %H:%M:%S', localtime);
    print "\n$pstr\n[FCD $t] @_\n\n";
}

###### main ######

my ($platformid, $boardid, $mac, $passphrase, $keydir, $dev, $idx, $boardrev, $serial_num, $qr_code)
    = @ARGV;

for my $p ($boardid, $mac, $passphrase, $dev, $idx, $boardrev, $serial_num) {
    die "Required parameter(s) missing\n" if (!defined($p));
}

my %bom_part_hash = (
    'e101' => 290,
    'e102' => 318,
    'e120' => 2044
);
my $bom_part = ${bom_part_hash{$boardid}};

msg(1, "Starting: platformid=$platformid boardid=$boardid dev=$dev mac=$mac "
    . "idx=$idx boardrev=$boardrev serial_num=$serial_num "
    . "bom=${bom_part}-$boardrev qr_code=$qr_code");

my ($prod_ip_pfx, $prod_ip_base, $prod_pfx_len) = ('192.168.1.', 19, 24);

my $prod_id = "${platformid}";
my $prod_server_ip = "${prod_ip_pfx}$prod_ip_base";
my $prod_dev_ip_base = $prod_ip_base + 1 + $idx;
my $prod_dev_ip = "${prod_ip_pfx}$prod_dev_ip_base";

my %num_macs_hash = (
    'e101' => 6,
    'e102' => 3,
    'e120' => 3
);
my $num_macs = ${num_macs_hash{$boardid}};

my %u_boot_file_hash = (
    'e101' => 'e100.bin',
    'e102' => 'e102.bin',
    'e120' => 'e120.uboot'
);
my $u_boot_file = ${u_boot_file_hash{$boardid}};

my %flash_str_hash = (
    'e101' => '8/135',
    'e102' => '4/71',
    'e120' => '8/135'
);
my $flash_str = ${flash_str_hash{$boardid}};

my %flash_base_hash = (
    'e101' => '0x1f400000',
    'e102' => '0x1f800000',
    'e120' => '0x1f400000'
);
my $flash_base = ${flash_base_hash{$boardid}};

my %systemid_hash = (
    'e101' => 'ee02',
    'e102' => 'ee01',
    'e120' => 'ee21'
);

my $system_id = ${systemid_hash{$boardid}};
my $prod_dir = "usgpro3";


my ($ffile, $pfile, $cfile)
    = ("helper.out.fields.$idx", "helper.out.part.$idx", "client.out.$idx");
my $mtdparts = 'phys_mapped_flash:512k(boot0),512k(boot1),64k@1024k(eeprom)';
my $exp_env = {
    'u_boot_prompt'         => 'Octeon ubnt_e1\d+# ',
    'prod_dev_mac'          => "$mac",
    'prod_dev_eth'          => 'eth0',
    'prod_dev_ip'           => $prod_dev_ip,
    'prod_dev_pfx'          => $prod_pfx_len,
    'prod_server_ip'        => $prod_server_ip,
    'prod_img_tar'          => "${prod_id}.bin",
    'num_macs'              => $num_macs,
    'board_id'              => $boardid,
    'bom_part'              => $bom_part,
    'board_rev'             => $boardrev,
    'board_serial'          => lc($serial_num),
    'passphrase'            => $passphrase,
    'u_boot_bin_file'       => $u_boot_file,
    'u_boot_flash_str'      => $flash_str,
    'u_boot_tftp_file'      => "$prod_id-fcd.kernel",
    'u_boot_linux_cmdline'  => "mtdparts=$mtdparts rw",
    'flash_base'            => $flash_base,
    'reg_ffile'             => $ffile,
    'reg_pfile'             => $pfile,
    'reg_cfile'             => $cfile,
    'linux_usb_dev'         => 'sda',
    'edgeos_prompt'         => '@ubnt:~$ ',
    'edgeos_cfg_prompt'     => '@ubnt# ',
    'systemid'              => $system_id,
    'qrcode'                => "$qr_code"
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);
msg(2, 'Device detected');
die 'FAILED to detect device'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot", $exp_env));

msg(3, 'Writing MAC address...');
die 'FAILED to write MAC address'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_write_mac", $exp_env));

msg(5, 'Restarting u-boot...');
die 'FAILED to restart u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_reset", $exp_env));

die 'FAILED to wait for U-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot", $exp_env));

msg(10, 'Upgrading u-boot...');
die 'FAILED to upgrade u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_upgrade", $exp_env));

msg(20, 'Restarting u-boot...');
die 'FAILED to restart u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_reset", $exp_env));

die 'FAILED to wait for U-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot", $exp_env));

msg(25, 'Writing MAC address with updated u-boot...');
die 'FAILED to write MAC address'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_write_mac_new", $exp_env));

msg(30, 'Restarting u-boot...');
die 'FAILED to restart u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_reset_only", $exp_env));

if ($boardid eq 'e102') {
    msg(31, 'Verifying e102 HW...');
    die 'FAILED to verify e102 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e102_hw_check", $exp_env));
} elsif ($boardid eq 'e101') {
    msg(31, 'Verifying e101 HW...');
    die 'FAILED to verify e101 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e101_hw_check", $exp_env));
} elsif ($boardid eq 'e120') {
    msg(31, 'Verifying e120 HW...');
    die 'FAILED to verify e120 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e120_hw_check", $exp_env));
} else {
    die 'FAILED to restart u-boot'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot", $exp_env));
}

msg(35, 'Booting temporary kernel...');
die 'FAILED to boot temporary kernel'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_linux_tftp", $exp_env)
        or !run_ubnt_expect($exp_h, "${prod_dir}/wait_for_temp_kern", $exp_env));

msg(45, 'Set up device...');
die 'FAILED to set up device'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_setup", $exp_env));

my $tdir = '/tftpboot';
my ($fpath, $ppath) = ("$tdir/$ffile", "$tdir/$pfile");
system("touch $fpath $ppath; chmod 777 $fpath $ppath ; sync ; sleep 1");
msg(50, 'Performing device registration...');
die 'FAILED to perform device registration'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_devreg", $exp_env));

my $fpath1 = "$fpath-1";
my $cmd = "grep 'field=' $fpath | grep -v flash_eeprom "
          . '| while read line; do echo -n "-i $line "; done ' . ">$fpath1";
system("sync");
sleep(1);
system($cmd);

my $qrhex = $qr_code;
$qrhex =~ s/(.)/sprintf("%x",ord($1))/eg;

my $kdir = '/media/usbdisk/keys';
my $cpath = "$tdir/$cfile";
my $params = "-h devreg-prod.ubnt.com -k $passphrase "
             . "-i field=flash_eeprom,format=hex,pathname=$ppath "
             . "-i field=qr_code,format=hex,value=$qrhex "
             . "-x $kdir/ca.pem -y $kdir/key.pem -z $kdir/crt.pem "
             . "\$(cat $fpath1) "
             . "-o field=flash_eeprom,format=binary,pathname=$cpath "
             . '-o field=registration_id -o field=result -o field=device_id -o field=registration_status_id -o field=registration_status_msg -o field=error_message ';

system("/usr/local/sbin/client_x86 $params");

if (-f $cpath) {
    system("touch ${ppath}-1; chmod 777 ${ppath}-1");
    msg(55, 'Finalizing device registration...');
    die 'FAILED to complete device registration'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_devreg_2", $exp_env));

    system("sync");
    sleep(1);
    system("diff -q $cpath ${ppath}-1");
    if ($? != 0) {
        die 'FAILED to match device registration EEPROM';
    }
} else {
    die 'FAILED to register device';
}

system("rm -f ${fpath}* ${ppath}* ${cpath}*");

msg(60, 'Preparing USB storage...');
die 'FAILED to prepare USB storage'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_prep_usb", $exp_env));

msg(80, 'Booting into EdgeOS...');
die 'FAILED to boot EdgeOS'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_edgeos", $exp_env));

die 'FAILED to boot EdgeOS'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/edgeos_console_login", $exp_env));

msg(90, 'Checking Board info in EdgeOS (UniFi) ...');
die 'FAILED to check board info in EdgeOS (UniFi)'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/edgeos_unifi_hw_check", $exp_env));

msg(95, 'Rebooting...');
run_ubnt_expect($exp_h, "${prod_dir}/edgeos_reboot", $exp_env);

die 'FAILED to reboot EdgeOS'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot", $exp_env));

msg(100, '[DONE] Production tasks completed');
exit 0;
