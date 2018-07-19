package UBNT::Expect;

use strict;
use warnings;

use Exporter 'import';
our @EXPORT_OK = qw(run_ubnt_expect);

use Expect;

my $exp_scripts_dir = '/usr/local/ubnt-expect';

sub run_expect_op {
    my ($exp, $oref) = @_;
    my $timeout = shift(@$oref);
    my $send_cmd = pop(@$oref);
    if (ref(${$oref}[0]) eq 'ARRAY' or ${$oref}[0] ne '') {
        return if (!$exp->expect($timeout, @$oref));
    }
    $exp->send($send_cmd) if ($send_cmd ne '');
    return 1;
}

sub run_ubnt_expect {
    my ($exp, $sname, $eref) = @_;
    my $sfile = "$exp_scripts_dir/$sname";
    if (! -f $sfile) {
        print "Invalid script $sname\n";
        return;
    }

    my $env = '';
    for my $key (keys %$eref) {
        $env .= "my \$$key = '$eref->{$key}';\n";
    }

    my ($ml_data, $ret, $script_h, $line) = ('', 1);
    return if (!open($script_h, '<', $sfile));
    while ($line = <$script_h>) {
        chomp($line);
        next if ($line =~ /^#/);
        if ($line =~ /^!(\w+)/) {
            my $rscr = $1;
            $ret = run_ubnt_expect($exp, $rscr, $eref);
            last if (!$ret);
            next;
        } elsif ($line =~ /^\*(.*)$/) {
            eval "\$exp->$1";
            next;
        } elsif ($line =~ /^\@(.*)$/) {
            eval "$1";
            next;
        } elsif ($line =~ /\\$/) {
            $line =~ s/\\$//;
            $ml_data .= $line;
            next;
        } elsif ($ml_data ne '') {
            $ml_data .= $line;
            $line = $ml_data;
            $ml_data = '';
        }

        my @op = ();
        eval "$env\@op = ($line);";
        next if (scalar(@op) < 2);
        unshift(@op, 5) if (scalar(@op) < 3);
        $ret = run_expect_op($exp, \@op);
        last if (!$ret);
    }
    close($script_h);
    return $ret;
}

1;
