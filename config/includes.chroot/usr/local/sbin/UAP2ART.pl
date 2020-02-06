#!/usr/bin/perl
#use Data::Dumper;
use Glib qw(FALSE);
use Gtk2 -init;

my $_VERSION = "SCMVER";

my $script       = '/usr/local/sbin/uswitch2mfg.tcl';
my $setup_script = '/usr/local/sbin/prod-network.sh';
my $log_directory = $ENV{HOME}.'/Desktop/';


my @products = ();
my @ttys = ( 'ttyUSB0', 'ttyUSB1', 'ttyUSB2', 'ttyUSB3' );
my @migrators = ();


my $window      = Gtk2::Window->new;
my $initialized = FALSE;
my $erase_caldata = FALSE;

my $log_file_locked = FALSE;

my $host_ip = '192.168.1.19';
my $script_path = '/usr/local/sbin/';

my $cfg = Configuration->new();
$cfg->load($ENV{HOME}.'/.ls2art.cfg');
my $sc = $cfg->get('script.setup');
$setup_script = $sc if (defined $sc and $sc ne '');
$sc = $cfg->get('script.production');
#$script = $sc if (defined $sc and $sc ne '');

log_debug('setup script = \'' . $setup_script . '\'');
log_debug('production script = \'' . $script . '\'');

END {
    $cfg->save($ENV{HOME}.'/.ls2vx.cfg');
}


{
    package Configuration;

    sub new {
        my ( $class ) = @_;
        my $self = {};
        $self->{_FILENAME} = undef;
        $self->{_DATA} = {};
        bless( $self, $class );
        return $self;
    }
    sub load {
        my ($self, $file) = @_;
        $self->{_FILENAME} = $file;
        open(IN, "<$file") || return 0;
        while (<IN>) {
            if ($_ =~ /^(.*?)\s*=\s*(.*)$/) {
                $self->{_DATA}{$1} = $2;
            }
        }
        close(IN);
        return 1;
    }
    sub save {
        my ($self, $file) = @_;
        $file = $self->{_FILENAME} unless (defined $file and $file ne '');
        open(OUT, ">$file") or return 0;
        foreach my $key (sort keys(%{ $self->{_DATA} })) {
            print OUT $key.' = '.$self->get($key)."\n";
        }
        close(OUT);
        return 1;
    }
    sub dump {
        my $self = shift;
        $log->debug('---DUMP Start');
        while (my ($key, $value) = each(%{ $self->{_DATA} })) {
            $log->debug('\''.$key.'\'=\''.$value.'\'');
        }
        $log->debug('Total ' . scalar keys(%{ $self->{_DATA} }) . ' entries ' . "\n");
    }
    sub get {
        my ($self, $key) = @_;
        return $self->{_DATA}{$key};
    }
    sub set {
        my ($self, $key, $value) = @_;
        $self->{_DATA}{$key} = $value;
    }
    1;
}


{
    package Product;
    sub new {
        my ( $class, $id, $name, $boardid, $script ) = @_;
        #my ( $class, $id, $name, $boardid, $script, $fw ) = @_;
        my $self = {};
        $self->{ID} = $id;
        $self->{_NAME} = $name;
        $self->{_BOARDID} = $boardid;
        $self->{_SCRIPT} = $script;
        #$self->{_FIRMWARE} = $fw;       
        bless( $self, $class );
        return $self;
    }
    
    sub get_id {
        my $self = shift;
        return $self->{ID};
    }
    sub get_name {
        my $self = shift;
        return $self->{_NAME};
    }
    sub get_boardid {
        my $self = shift;
        return $self->{_BOARDID};
    }
    sub get_script {
        my $self = shift;
        return $self->{_SCRIPT};
    }
    #sub get_firmware {
    #    my $self = shift;
    #    return $self->{_FIRMWARE};
    #}
    sub to_string {
        my $self = shift;
        return '[' . $self->get_id() . '] name=\'' . $self->get_name() . '\'' . 
                ' boardid=\''.$self->get_boardid().'\'' .' script=\''.$self->get_script().'\'' if (defined $self);
        #return '[' . $self->get_id() . '] name=\'' . $self->get_name() . '\'' . 
        #        ' boardid=\''.$self->get_boardid().'\'' .' script=\''.$self->get_script().'\'' .
        #        ' fw=\''.$self->get_firmware().'\'' if (defined $self);
    }
    
    1;
}

{
    package Migrator;
    use Data::Dumper;
    use Glib qw(FALSE);
    use Gtk2 -init;

    sub new {
        my ( $class, $id, $name ) = @_;
        my $self = {};
        $self->{ID}             = $id;
        $self->{_NAME}          = $name;
        $self->{_PRODUCT}       = undef;
        $self->{_PRODUCT_COMBO} = Gtk2::ComboBox->new_text();
        $self->{_SERIAL_COMBO}  = Gtk2::ComboBox->new_text();
        $self->{_ERASECAL_CHK}  = Gtk2::CheckButton->new("Erase Calibration Data");
        $self->{_PROGRESS}      = Gtk2::ProgressBar->new();
        $self->{_START}         = Gtk2::Button->new_with_label(' Start ');
        $self->{_TEXTVIEW}      = Gtk2::TextView->new();
        $self->{_OUTPUTBUFFER}  = $self->{_TEXTVIEW}->get_buffer();

        $self->{_VIEW}        = undef;
        $self->{_OUTPUTVIEW}  = undef;
        $self->{_INITIALIZED} = 0;
        $self->{_BUSY}        = 0;
        $self->{_CHILD_PID}   = 0;

        $self->{_START_TIME} = 0;
        $self->{_END_TIME}   = 0;

        bless( $self, $class );
        return $self;
    }

    sub initialize {
        my $self = shift;
        if ( $self->{_INITIALIZED} == 0 ) {
            $self->set_products(@products);
            $self->set_ttys(@ttys);

            $self->{_START}->set_focus_on_click(FALSE);
            $self->{_START}
              ->signal_connect( 'clicked', \&Migrator::_start, $self );

            my $hbox = Gtk2::HBox->new( FALSE, 5 );
            $hbox->set_border_width(5);
            $hbox->pack_start( $self->{_PRODUCT_COMBO}, 0, 0, 0 );
            $hbox->pack_start( $self->{_SERIAL_COMBO},  0, 0, 0 );
            $hbox->pack_start( $self->{_ERASECAL_CHK},  0, 0, 0 );
            $hbox->pack_start( $self->{_PROGRESS},      1, 1, 0 );
            $hbox->pack_start( $self->{_START},         0, 0, 0 );

            my $frame = Gtk2::Frame->new( ' ' . $self->{_NAME} . ' ' );
            $frame->add($hbox);
            $frame->set_border_width(5);
            $self->{_VIEW} = $frame;

            # output view
            $self->{_TEXTVIEW}->set_editable(0);
            $self->{_ENDMARK} =
              $self->{_OUTPUTBUFFER}
              ->create_mark( 'end', $self->{_OUTPUTBUFFER}->get_end_iter,
                FALSE );
            $self->{_OUTPUTBUFFER}->signal_connect(
                'insert_text' => \&Migrator::_autoscroll,
                $self
            );

            $self->{_OUTPUTVIEW} = Gtk2::ScrolledWindow->new();
            $self->{_OUTPUTVIEW}->add( $self->{_TEXTVIEW} );

            $self->{_INITIALIZED} = 1;
        }
    }

    sub is_busy {
        my $self = shift;
        return $self->{_BUSY};
    }

    sub set_products {
        my ( $self, @p ) = @_;
        $self->{_PRODUCT_COMBO}->get_model()->clear;
        my $active = 0;
        my $id = 0;
        foreach (@p) {
            $self->{_PRODUCT_COMBO}->append_text($_->get_name());
            if ($_->get_name() eq $cfg->get('slot.'.$self->{ID}.'.product')) {
                $active = $id;
            }
            $id++;
        }
        $self->{_PRODUCT_COMBO}->set_active($active);
    }

    sub set_ttys {
        my ( $self, @t ) = @_;
        $self->{_SERIAL_COMBO}->get_model()->clear;
        foreach (@t) {
            $self->{_SERIAL_COMBO}->append_text($_);
        }
        $self->{_SERIAL_COMBO}->set_active( $self->{ID} );
    }

    sub select_product {
        my $self    = shift;
        my $product = shift;

        if ( $product =~ /^\d+$/ ) {
            $self->{_PRODUCT_COMBO}->set_active($product);
            # TODO: fix this bug
            $cfg->set('slot.'.$self->{ID}.'.product', $self->{_PRODUCT_COMBO}->get_active_text())
        }
        else {

            # TODO: find a product by given name and activate it
        }
    }

    sub set_erase_caldata {
        my $self    = shift;
        my $erase_cal = shift;

        $self->{_ERASECAL_CHK}->set_active($erase_cal);
    }

    sub get_view {
        my $self = shift;
        if ( $self->{_VIEW} == undef ) {
            $self->initialize();
        }

        return $self->{_VIEW};
    }

    sub get_outputview {
        my $self = shift;
        if ( $self->{_OUTPUTVIEW} == undef ) {
            $self->initialize();
        }
        return $self->{_OUTPUTVIEW};
    }

    sub append_output {
        my $self = shift;
        my $text = shift;

        $self->{_OUTPUTBUFFER}
          ->insert( $self->{_OUTPUTBUFFER}->get_end_iter, $text );
    }

    sub _autoscroll {
        my $buffer = shift;
        shift;
        shift;
        shift;
        my $self = shift;
        $self->{_TEXTVIEW}
          ->scroll_to_mark( $self->{_ENDMARK}, 0.0, TRUE, 0.0, 1.0 );
    }

    sub _start {
        my $button = shift;
        my $this   = shift;

        $this->start();
        return TRUE;
    }

    sub _progress_timeout {
        my $self = shift;

        # TODO: instead of pulsing, read current progress and display progress
        #$self->{_PROGRESS}->pulse();
        $self->{_PROGRESS}->set_fraction($self->{_DONE} / 100);
        if ($self->{_DONE} == 1) {
            $self->{_PROGRESS}->set_text(' ' . 'Ready - plug in ' . $self->{_PRODUCT}->get_name() . ' board ');
        } elsif ($self->{_DONE}) {
            $self->{_PROGRESS}->set_text(' '. $self->{_DONE} . '% ');
        }
        return TRUE;
    }

    sub __format_duration {
        my $total = shift;
        my $mins  = $total / 60;
        my $secs  = $total % 60;

        return sprintf( "%02d minutes %02d seconds", $mins, $secs );
    }

    sub __migration_started {
        my ( $self, $child_pid, $cmd ) = @_;

        my $tty     = $self->{_SERIAL_COMBO}->get_active_text();
        my $erase_cal = $self->{_ERASECAL_CHK}->get_active();
        my $devid   = $self->{_DEVICE_ID};

        my $p = $self->{_PRODUCT};
        $self->{_BUSY} = 1;
        $self->{_CHILD_PID} = $child_pid;

        $self->append_output("\n--------[STARTED: $cmd]\n");
        @controls =
          ( $self->{_START}, $self->{_PRODUCT_COMBO}, $self->{_ERASECAL_CHK}, $self->{_SERIAL_COMBO} );
        foreach (@controls) {
            $_->set_sensitive(0);
        }
        $self->{_TIMER} =
          Glib::Timeout->add( 200, \&Migrator::_progress_timeout, $self );
        $self->{_START_TIME} = time();
    }

    sub __migration_step {
        my ( $self, $data ) = @_;
        $self->append_output($data);
        if ($data =~ /^=== (\d+) .*$/m) {
            $self->{_DONE} = $1;
        } 
    }

    sub __migration_ended {
        my $self   = shift;
        my $status = shift;
        $self->{_END_TIME} = time();
        @controls =
          ( $self->{_START}, $self->{_PRODUCT_COMBO}, $self->{_ERASECAL_CHK}, $self->{_SERIAL_COMBO} );
        foreach (@controls) {
            $_->set_sensitive(1);
        }
        $self->{_START}->grab_focus();
        $self->{_PROGRESS}->set_fraction(0);
        Glib::Source->remove( $self->{_TIMER} );
        $self->{_BUSY} = 0;
        $self->{_DONE} = 0;
        $self->{_CHILD_PID} = 0;

        my $duration     = $self->{_END_TIME} - $self->{_START_TIME};
        my $duration_str = Migrator::__format_duration($duration);

        my $msg = "";
        if ( $status == 0 ) {
            $msg = "Completed in $duration_str.";
        }
        else {
            $msg = "FAILED with error code $status after $duration_str.";
        }
        $self->{_PROGRESS}->set_text($msg);
        $self->append_output("\n--------[$msg\n");
    }

    sub start {
        my $self = shift;

        my $tty     = $self->{_SERIAL_COMBO}->get_active_text();
        my $product = $self->{_PRODUCT_COMBO}->get_active_text();
        my $erasecal = $self->{_ERASECAL_CHK}->get_active();
        my $id      = $self->{ID};

        my $p = ::find_product_by_name(\@products, $product);
        $self->{_PRODUCT} = $p;

        #
        # ID is used for IP address generation in production script
        # so we should be very careful with it, we should support as
        # many serial ports as possible
        #
        if ( $tty =~ /^ttyUSB(\d+)$/ ) {
            $id = $1;
        }
        elsif ( $tty =~ /^ttyS(\d+)$/ ) {
            $id = $1 + 50;
        }
        else {
            $id += 100;
        }
        $self->{_DEVICE_ID} = $id;
        
        my ($sec,$min,$hour,$mday,$mon,$year, $wday,$yday,$isdst) = localtime time;
        $year += 1900;      
        $mon += 1;
                
        my $directory = $log_directory.'/'.$p->{_NAME};
        
        if (not -e $directory)
        {
            system "mkdir ".$directory;
        }
        
        my $temp_file = ''.$directory.'/'.$sec.$min.$hour.rand(200).'.log';

        system "stty -F /dev/$tty speed 115200";

        my $cmd;
        if ( $p->get_script() eq "python2art.tcl" ) {
            my $firmware;
            if ( $erasecal ) {
                $firmware = $p->get_boardid().'-ART.bin';
            } else {
                $firmware = $p->get_boardid().'-ART-NOEEPROM.bin';
            }
            $cmd = $script_path . $p->get_script() . ' ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
        } elsif ( $p->get_script() eq "uswitch2mfg.tcl" ) {
            $firmware = $p->get_boardid().'-mfg.bin';
            if ( $erasecal ) {
                $cmd = $script_path . $p->get_script() . ' -e ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
            } else {
                $cmd = $script_path . $p->get_script() . ' -k ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
            }
        } elsif ( $p->get_script() eq "mscc2mfg.pl" ) {
            $firmware = $p->get_boardid().'-mfg.bin';
            if ( $erasecal ) {
                $cmd = $script_path . $p->get_script() . ' -e ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
            } else {
                $cmd = $script_path . $p->get_script() . ' -k ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
            }
        } else {
            $firmware = $p->get_boardid().'-ART.bin';
            if ( $erasecal ) {
                $cmd = $script_path . $p->get_script() . ' -e ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
            } else {
                $cmd = $script_path . $p->get_script() . ' -k ' . $tty . ' ' . $id . ' ' . $p->get_boardid() . ' ' . '\'' .$firmware. '\' ' . $host_ip;
            }
        }

        ::log_debug('Opening pipe to \'' . $cmd . '\'');
        my $child_pid = open my $pipe, "$cmd |";
        $self->__migration_started($child_pid, $cmd);

        Glib::IO->add_watch(
            fileno $pipe,
            [ 'in', 'hup' ],
            sub {
                my ( $fd, $condition ) = @_;
                if ( $condition >= 'in' ) {
                    my $data = "";
                    my $nread = sysread( $pipe, $data, 80 );
                    #remove zeros in null-terminated strings    
                    $data =~ s/\000//g;
                    system 'echo -n "'.$data.'" >> '.$temp_file;
                    $self->__migration_step($data);
                }
                if ( $condition >= 'hup' ) {
                    close $pipe;
                    $self->__migration_ended($?);
                    
#                   print("Waiting for log unlock\n");
#                   print($log_file_locked."\n");
                    while ($log_file_locked) #wait for log file unlock
                    {
                    }
                    $log_file_locked = TRUE;
                    
                    my $log_file = ''.$directory.'/'.$year.'-'.$mon.'-'.$mday.'.log';
#                   print('adding to file: '.$log_file."\n");
                    
                    system "cat ".$temp_file.' >> '.$log_file; 
                    system "rm ".$temp_file;
                    
                    $log_file_locked = FALSE;                   
                    return FALSE;
                    
                }
                return TRUE;
            }
        );

        return TRUE;
    }
    
    sub stop {
        my $self = shift;
        if ($self->{_BUSY} && $self->{_CHILD_PID}) {
            kill(1, $self->{_CHILD_PID});
        }
        return TRUE;
    }

    1;
}

###
# Functions for main
###
sub quit_confirm {
    my $parent  = $window;
    my $message = "\nExit now?";

    foreach (@migrators) {
        if ( $_->is_busy() == 1 ) {
            $message =
"\n There are jobs in progress -\nAre you sure you want to exit?";
            last;
        }
    }

    my $dialog = Gtk2::MessageDialog->new(
        $parent,
        'destroy-with-parent',
        'question',    # message type
        'yes-no',      # which set of buttons?
        $message
    );
    $response = $dialog->run;
    $dialog->destroy;
    if ( $response eq 'yes' ) {
        foreach (@migrators) {
                $_->stop();
        }
        $parent->destroy;
        return FALSE;
    }
    return TRUE;
}

sub help_about {
    my $parent = $window;
    my $dialog = Gtk2::MessageDialog->new(
        $parent,
        'modal',
        'info',     # message type
        'close',    # set of buttons
        "<b>UniFiAP - back to ART Converter $_VERSION</b>\n(c) 2006 - 2011 Ubiquiti Networks, Inc."
    );
    my $response = $dialog->run;
    $dialog->destroy;
    return TRUE;
}

sub create_menubar {
    my $file_menu = Gtk2::Menu->new;
    my $quit_item = Gtk2::MenuItem->new("E_xit");
    $quit_item->signal_connect( 'activate', sub { return !quit_confirm; } );
    $file_menu->append($quit_item);
    my $file_item = Gtk2::MenuItem->new("_File");
    $file_item->set_submenu($file_menu);
    my $help_menu  = Gtk2::Menu->new;
    my $about_item = Gtk2::MenuItem->new("_About");
    $about_item->signal_connect( 'activate', sub { return !help_about; } );
    $help_menu->append($about_item);
    my $help_item = Gtk2::MenuItem->new("_Help");
    $help_item->set_submenu($help_menu);
    my $menubar = Gtk2::MenuBar->new;
    $menubar->append($file_item);
    $menubar->append($help_item);

    return $menubar;
}

sub create_controls {
    my $hbox = Gtk2::HBox->new( FALSE, 5 );
    $hbox->set_border_width(5);

    my $l = Gtk2::Label->new("Product (for all slots): ");
    my $p = Gtk2::ComboBox->new_text();
    my $erasecheck = Gtk2::CheckButton->new("Erase Calibration Data");

    my $active = 0;
    my $id = 0;
    foreach (@products) {
        $p->append_text($_->get_name());
        if ($_->get_name() eq $cfg->get('common.product')) {
            $active = $id;
        }
        $id++;
    }
    $p->set_active($active);
    
    $p->signal_connect(
        'changed',
        sub {
            my $index = $p->get_active;
            foreach (@migrators) {
                $_->select_product($index);
            }
            $cfg->set('common.product', $p->get_active_text);
        }
    );

    $erasecheck->set_active($erase_caldata);
    $erasecheck->signal_connect(
        'clicked',
        sub {
            $erase_caldata = $erasecheck->get_active;
            foreach (@migrators) {
                $_->set_erase_caldata($erase_caldata);
            }
        }
    );

    $hbox->pack_start( $l, 0, 0, 0 );
    $hbox->pack_start( $p, 0, 0, 0 );
    $hbox->pack_start( $erasecheck, 0, 0, 0 );

    my $frame = Gtk2::Frame->new(' Common controls ');
    $frame->add($hbox);
    $frame->set_border_width(5);

    return $frame;
}

sub collect_serials {
    opendir( DIR, '/dev' );
    my @found = grep { /^ttyS./ || /^ttyUSB./ } readdir(DIR);
    closedir(DIR);

    my @active_ttys;
    foreach (@found) {
        if ( !system("stty -F /dev/$_ speed 115200 >/dev/null 2>/dev/null") ) {
            push( @active_ttys, $_ );
        }
    }
    my @ttys = sort( grep { /^ttyS./ } @active_ttys );
    my @usbs = sort( grep { /^ttyUSB./ } @active_ttys );
    my @all = ( @usbs, @ttys );
    return wantarray ? @all : $all[0];
}

sub find_usb_storage {
#   opendir( DIR, '/dev/disk/by-id' );
#   my @found = grep { /^usb-./} readdir(DIR);
#   closedir(DIR);
    
    
    @lines = `ls -ls /dev/disk/by-id| grep usb-`;
#   print "@lines";
    
    my $device;
    
    #seerchin for usb storage mount point
    foreach my $line (@lines) {
            
            my @dev = split('/',$line);
            $device = ''.@dev[-1];      
#           if ($device =~ /\d$/)
            {
                print $device;
                my $procMountFile = '/proc/mounts';
                # Open the proc mount file
                open(FILE,"$procMountFile");
                while (<FILE>)
                {
                    my $line = "$_";
                    
                    if (grep { /$device* /} $line)
                    {
#                       print $line."\n";                   
                        my @tags = split(' ',$line);
#                       print @tags[0]."    ".@tags[1]."\n";
                        if (@tags[1])
                        {
                            $log_directory = @tags[1];
                            print "Found storage at ".$log_directory."\n";
                            close(FILE);    
                            return 1;
                        }
                    }
                }
                close(FILE);    
            }

            
    }   
    print "No USB storage found";
    return 0;           
}

my $initializer;

sub initialize {
    my $msg = ' Initializing environment - please wait...';

    my $parent = $window;
    my $dialog =
      Gtk2::MessageDialog->new( $parent, 'modal', 'info', 'none', $msg );

    my $cmd = $setup_script . ' ' . $host_ip;

    open my $pipe, "$cmd |";
    Glib::IO->add_watch(
        fileno $pipe,
        ['hup'],
        sub {
            my ( $fd, $condition ) = @_;
            if ( $condition >= 'hup' ) {
                close IN;
                $dialog->response(0);
                return FALSE;
            }
            return TRUE;
        }
    );

    $dialog->run();
    $dialog->destroy;
    
    if (!find_usb_storage())
    {
        my $dialog = Gtk2::MessageDialog->new(
        $parent, 'modal',
        'info',     # message type
        'close',    # set of buttons
        "No USB storage found. Files will be saved to Desktop"
        );
        $dialog->run;
        $dialog->destroy;
    }   

    my @serials = collect_serials;
    foreach (@migrators) {
        $_->set_ttys(@serials);
    }

    foreach (@migrators) {
        $_->set_erase_caldata($erase_caldata);
    }

    $initialized = TRUE;
    Glib::Source->remove($initializer);
    return FALSE;
}

sub load_products {
    my $product; 
    my @list;
    
    my $pcfg = Configuration->new();
    
    $product = Product->new(1, 'UAP-Outdoor5-ART', 'e515', 'python2art.tcl');
    push @list, $product;
    $product = Product->new(2, 'UAP-Pro-ART', 'e507', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(3, 'UAP-InWall-ART', 'e592', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(4, 'UAP-AC-Lite-ART', 'e517', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(5, 'UAP-AC-LR-ART', 'e527', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(6, 'UAP-AC-Pro-ART', 'e537', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(7, 'UAP-AC-Edu-ART', 'e547', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(8, 'UAP-AC-Mesh-ART', 'e557', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(9, 'UAP-AC-Mesh-Pro-ART', 'e567', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(10, 'UAP-AC-InWall-ART', 'e587', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(11, 'UAP-WASP-ART', 'e572', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(12, 'UAP-WASP-LR-ART', 'e582', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(13, 'US-8-MFG', 'eb19', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(14, 'US-8-60-MFG', 'eb18', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(15, 'US-8-150-MFG', 'eb10', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(16, 'US-XG-MFG', 'eb20', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(17, 'US-16-150-MFG', 'eb21', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(18, 'US-24-MFG', 'eb30', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(19, 'US-24-250-MFG', 'eb31', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(20, 'US-24-500-MFG', 'eb32', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(21, 'UAP-AC-HD-ART', 'e530', 'uap_ipq806x_to_art.pl');
    push @list, $product;
    $product = Product->new(22, 'UAP-AC-SHD-ART', 'e540', 'uap_ipq806x_to_art.pl');
    push @list, $product;
    $product = Product->new(23, 'UAP-AC-IW-PRO-ART', 'e597', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(24, 'US-48-MFG', 'eb60', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(25, 'US-48-500-MFG', 'eb62', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(26, 'US-48-750-MFG', 'eb63', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(27, 'US-24P-L2-MFG', 'eb33', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(28, 'US-48P-L2-MFG', 'eb66', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(29, 'UAP-AC-XG-ART', 'e560', 'uap_ipq806x_to_art.pl');
    push @list, $product;
    $product = Product->new(30, 'UAP-XG-MESH-ART', 'e570', 'uap_ipq806x_to_art.pl');
    push @list, $product;
    $product = Product->new(31, 'UAP-XG-STADIUM-ART', 'e580', 'uap_ipq806x_to_art.pl');
    push @list, $product;
    $product = Product->new(33, 'US-6-XG-150-MFG', 'eb23', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(34, 'USC-8', 'ed01', 'mscc2mfg.pl');
    push @list, $product;
    $product = Product->new(35, 'USC-8-60', 'ed02', 'mscc2mfg.pl');
    push @list, $product;
    $product = Product->new(36, 'USC-8-150', 'ed03', 'mscc2mfg.pl');
    push @list, $product;
    $product = Product->new(37, 'UAP-XG-STADIUM-BL-ART', 'e585', 'uap_ipq806x_to_art.pl');
    push @list, $product;
    $product = Product->new(38, 'U-LTE-ART', 'e611', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(39, 'U-LTE-PRO-EU-ART', 'e612', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(40, 'U-LTE-PRO-US-ART', 'e613', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(41, 'U-LTE-PRO-AU-ART', 'e616', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(42, 'U-LTE-FLEX-EU-ART', 'e614', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(43, 'U-LTE-FLEX-US-ART', 'e615', 'uap2art.tcl');
    push @list, $product;
    $product = Product->new(44, 'UIS-8-450', 'ed04', 'mscc2mfg.pl');
    push @list, $product;
    $product = Product->new(45, 'US-24-PRO-POE', 'eb36', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(46, 'US-48-PRO-POE', 'eb67', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(47, 'US-24-PRO', 'eb37', 'uswitch2mfg.tcl');
    push @list, $product;
    $product = Product->new(48, 'US-48-PRO', 'eb68', 'uswitch2mfg.tcl');
    push @list, $product;

    return @list;
}

sub log_debug {
    my ($msg) = @_;
    open(LOG, ">>/tmp/lsf-debug.log");
    print LOG $msg . "\n";
    close(LOG); 
}

sub find_product_by_name {
    my ($list, $name) = @_;
    foreach (@$list) {
        return $_ if ($_->get_name() eq $name);
    }
    return undef;
}

###
## MAIN
###
push @products, load_products();

my $menubar     = create_menubar();
my $controls    = create_controls();
my $contents    = Gtk2::VBox->new;
my $output_tabs = Gtk2::Notebook->new;



for ( $i = 0 ; $i < 4 ; ++$i ) {
    my $name = 'Slot ' . ( $i + 1 );
    my $migrator = Migrator->new( $i, $name );
    push @migrators, $migrator;
    my $slot = $migrator->get_view();

    $contents->pack_start( $slot, 0, 0, 0 );
    $output_tabs->append_page( $migrator->get_outputview(), $name );
}
my $outputs = Gtk2::Expander->new_with_mnemonic('Conversion Script Output');
$outputs->set_expanded(FALSE);
$outputs->add($output_tabs);

#
# Main Window
#

my $vbox = Gtk2::VBox->new;

my $label = Gtk2::Label->new();
$label->set_markup("<span foreground=\"red\"><b>Warning: EEPROM (calibration) data will be lost!</b></span>");

$vbox->pack_start( $menubar,  0, 0, 0 );
$vbox->pack_start( $controls, 0, 0, 0 );
$vbox->pack_start( $contents, 0, 0, 0 );
$vbox->pack_start( $outputs,  1, 1, 0 );
$vbox->pack_start( $label,  0, 0, 0 );

$window->set_title('UniFiAP - back to ART v'.$_VERSION);
$window->set_border_width(2);
$window->set_default_size( 640, 480 );
$window->set_resizable(TRUE);
$window->set_position('center');
$window->signal_connect( delete_event => sub { quit_confirm; } );
$window->signal_connect( destroy      => sub { Gtk2->main_quit; } );
$window->add($vbox);
$window->show_all;
$window->activate();

$initializer = Glib::Timeout->add( 100, \&initialize );

Gtk2->main;

