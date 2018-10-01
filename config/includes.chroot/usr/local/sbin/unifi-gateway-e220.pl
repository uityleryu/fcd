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

for my $p ($boardid, $mac, $passphrase, $dev, $idx, $boardrev, $serial_num, $qr_code) {
    die "Required parameter(s) missing\n" if (!defined($p));
}

my %bom_part_hash = (
    'e200' => 317,
    'e201' => 2033,
    'e220' => 2102,
    'e221' => 2102
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
my $serial_num_lc = lc $serial_num;

my %num_macs_hash = (
    'e200' => 8,
    'e201' => 8,
    'e220' => 8,
    'e221' => 4
);
my $num_macs = ${num_macs_hash{$boardid}};

my %u_boot_file_hash = (
    'e200' => 'e200.bin',
    'e201' => 'e200.bin',
    'e220' => 'e220.bin',
    'e221' => 'e220.uboot'
);
my $u_boot_file = ${u_boot_file_hash{$boardid}};

my %flash_base_hash = (
    'e200' => '0x1f400000',
    'e201' => '0x1f400000',
    'e220' => '0x1f400000',
    'e221' => '0x1f400000'
);
my $flash_base = ${flash_base_hash{$boardid}};

my %systemid_hash = (
    'e200' => 'ee11',
    'e201' => 'ee12',
    'e220' => 'ee31',
    'e221' => 'ee32'
);

my $system_id = ${systemid_hash{$boardid}};

my $prod_dir = "usgpro4";

my ($ffile, $pfile, $cfile)
    = ("helper.out.fields.$idx", "helper.out.part.$idx", "client.out.$idx");
my $exp_env = {
    'u_boot_prompt'         => 'Octeon ubnt_e2\d+# ',
    'prod_dev_mac'          => "$mac",
    'prod_dev_eth'          => 'octeth0',
    'prod_dev_ip'           => $prod_dev_ip,
    'prod_dev_pfx'          => $prod_pfx_len,
    'prod_server_ip'        => $prod_server_ip,
    'prod_img_tar'          => "${prod_id}.bin",
    'num_macs'              => $num_macs,
    'board_id'              => $boardid,
    'bom_part'              => $bom_part,
    'board_rev'             => $boardrev,
    'board_serial'          => $serial_num,
    'board_serial_lc'       => $serial_num_lc,
    'passphrase'            => $passphrase,
    'u_boot_bin_file'       => $u_boot_file,
    'u_boot_tftp_file'      => "$prod_id-fcd.kernel",
    'u_boot_linux_cmdline'  => 'mtdparts=$(mtdparts) rw',
    'flash_base'            => $flash_base,
    'reg_ffile'             => $ffile,
    'reg_pfile'             => $pfile,
    'reg_cfile'             => $cfile,
    'linux_mmc_dev'         => 'mmcblk0',
    'edgeos_prompt'         => '@ubnt:~$ ',
    'edgeos_cfg_prompt'     => '@ubnt# ',
    'systemid'              => $system_id,
    'qrcode'                => "$qr_code"
};

my $exp_h = get_console_expect($dev);
$exp_h->debug(0);
msg(2, 'Device detected');
die 'FAILED to detect device'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot_e200", $exp_env));

msg(3, 'Writing MAC address...');
die 'FAILED to write MAC address'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_write_mac_tmp", $exp_env));

msg(5, 'Restarting u-boot...');
die 'FAILED to restart u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_reset_e200", $exp_env));

die 'FAILED to detect device'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot_e200", $exp_env));

msg(10, 'Upgrading u-boot...');
die 'FAILED to upgrade u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_upgrade", $exp_env));

msg(20, 'Restarting u-boot...');
die 'FAILED to restart u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_reset_e200", $exp_env));

die 'FAILED to detect device'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot_e200", $exp_env));

msg(25, 'Writing MAC address with updated u-boot...');
die 'FAILED to write MAC address'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_write_mac_new", $exp_env));

msg(30, 'Restarting u-boot...');
die 'FAILED to restart u-boot'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_reset_only", $exp_env));

if ($boardid eq 'e200') {
    msg(31, 'Verifying e200 HW...');
    die 'FAILED to verify e200 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e200_hw_check", $exp_env));
} elsif ($boardid eq 'e201') {
    msg(31, 'Verifying e201 HW...');
    die 'FAILED to verify e201 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e201_hw_check", $exp_env));
} elsif ($boardid eq 'e220') {
    msg(31, 'Verifying e220 HW...');
    die 'FAILED to verify e220 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e220_hw_check", $exp_env));
} elsif ($boardid eq 'e221') {
    msg(31, 'Verifying e221 HW...');
    die 'FAILED to verify e221 HW'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_e221_hw_check", $exp_env));
} else {
    die 'FAILED to restart u-boot'
        if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot_e200", $exp_env));
}

msg(35, 'Booting temporary kernel...');
die 'FAILED to boot temporary kernel'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/u_boot_linux_tftp", $exp_env)
        or !run_ubnt_expect($exp_h, "${prod_dir}/wait_for_temp_kern_e200", $exp_env));

msg(45, 'Set up device...');
die 'FAILED to set up device'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_setup_e200", $exp_env));

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

msg(60, 'Preparing MMC storage...');
die 'FAILED to prepare MMC storage'
    if (!run_ubnt_expect($exp_h, "${prod_dir}/temp_kern_prep_mmc", $exp_env));

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
    if (!run_ubnt_expect($exp_h, "${prod_dir}/wait_for_u_boot_e200", $exp_env));

msg(100, '[DONE] Production tasks completed');
exit 0;
