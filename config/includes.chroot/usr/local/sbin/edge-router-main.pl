#!/usr/bin/perl
use Glib qw(FALSE);
use Gtk2 -init;

my $_VERSION = "0.1.0.0";
if (open(my $vf, '<', '/etc/skel/Desktop/version.txt')) {
    $_VERSION = <$vf>;
    close($vf);
    chomp($_VERSION);
}

my $setup_script = '/usr/local/sbin/prod-network.sh';

my $log_directory = $ENV{HOME}.'/Desktop/';

my $macstr_len = 12;
my $qrcode_len  = 6;

my $pass_phrase = "";

my @products = ();
my @ttys = ( 'ttyUSB0', 'ttyUSB1', 'ttyUSB2', 'ttyUSB3' );
my @regdmn_codes = ( '0000' );
my @regdmn_names = ( 'world' );
my @migrators = ();

my $window      = Gtk2::Window->new;
my $initialized = FALSE;

my $log_file_locked = FALSE;

my $min_board_rev = 5;
my $max_board_rev = 36;
my $board_revision = 0;
my $regdmn_idx = 0;

my $cfg = Configuration->new();
$cfg->load($ENV{HOME}.'/.lsf.cfg');
my $sc = $cfg->get('script.setup');
$setup_script = $sc if (defined $sc and $sc ne '');

my $color_fail = Gtk2::Gdk::Color->new (0xFFFF,0,0);
my $color_running = Gtk2::Gdk::Color->new (0xFFFF,0xFFFF,0);
my $color_pass = Gtk2::Gdk::Color->new (0,0xFFFF,0);
my $greyl = Gtk2::Gdk::Color->new (0xa9a9,0xa9a9,0xa9a9);

sub quit_hooks {
    $cfg->save($ENV{HOME}.'/.lsf.cfg') if ($cfg);
}

END {
    quit_hooks();
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
        my ( $class, $id, $name ) = @_;
        my $self = {};
        $self->{ID} = $id;
        $self->{_NAME} = $name;
        $self->{_DESC} = $name;
        $self->{_SCRIPT} = undef;
#       $self->{_BOOTLOADER} = $bootloader;
#       $self->{_FIRMWARE} = $fw;
#       $self->{_BOOTLOADER} = undef;
        $self->{_FIRMWARE} = undef;
        $self->{_FIRMWARE_FILE} = undef;
        $self->{_FIRMWARE_VERSION} = undef;
        $self->{_BOARDID} = undef;
        $self->{_PLATFORMID} = undef;
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
    sub get_description {
        my $self = shift;
        return $self->{_DESC};
    }
    sub get_script {
        my $self = shift;
        return $self->{_SCRIPT};
    }
#   sub get_bootloader {
#       my $self = shift;
#       return $self->{_BOOTLOADER};
#   }
    sub get_firmware {
        my $self = shift;
        return $self->{_FIRMWARE};
    }
    sub get_boardid {
        my $self = shift;
        return $self->{_BOARDID};
    }
    sub get_platformid {
        my $self = shift;
        return $self->{_PLATFORMID};
    }
    sub get_firmware_file {
        my $self = shift;
        if (defined $self->{_FIRMWARE_FILE}) {
            return $self->{_FIRMWARE_FILE};
        }
        my @f;
        push(@f, '/tftpboot/' . $self->get_firmware());
        push(@f, $self->get_firmware());
        push(@f, 'data/' . $self->get_firmware());
        foreach (@f) {
            if (-e $_) {
                $self->{_FIRMWARE_FILE} = $_;
                last;
            }
        }
        return $self->{_FIRMWARE_FILE};
    }
    sub get_firmware_version {
        my $self = shift;
        if (defined $self->{_FIRMWARE_VERSION}) {
            return $self->{_FIRMWARE_VERSION};
        }
        my $f = $self->get_firmware_file();
        return fw_get_version($f);
    }
    sub set_description {
        my ($self,$desc) = @_;
        $self->{_DESC} = $desc;
    }
    sub set_script {
        my ($self,$scrpt) = @_;
        $self->{_SCRIPT} = $scrpt;
    }
    sub set_firmware {
        my ($self,$fw) = @_;
        $self->{_FIRMWARE} = $fw;
    }
    sub set_boardid {
        my ($self,$bid) = @_;
        $self->{_BOARDID} = $bid;
    }
    sub set_platformid {
        my ($self,$pid) = @_;
        $self->{_PLATFORMID} = $pid;
    }
    
#   sub to_string {
#       my $self = shift;
#       return '[' . $self->get_id() . '] name=\'' . $self->get_name() . '\'' .
#               ' boot=\''.$self->get_bootloader().'\'' .
#               ' fw=\''.$self->get_firmware().'\'' if (defined $self);
#   }

    sub fw_get_version {
        my ($file) = @_;
        open(FW, "<$file") || return 0;
        my $rc = read(FW, my $sig, 4);
        if (!defined $rc || $rc == 0 || $sig ne 'UBNT') {
            close(FW);
            return undef;
        }
        $rc = read(FW, my $version, 256);
        if (!defined $rc || $rc == 0) {
            close(FW);
            return undef;
        }
        close(FW);
        $version =~ s/\0+$//;
        $version =~ s/\s+$//;
        return $version;
    }

    1;
}

sub check_password_dialog
{
    
    my $controll=shift;
    my $password_ok='passw_fail';
    my $passwd_entry = "";
    
    my $index = $controll->get_active;
    
    my $passwd_edit = Gtk2::Entry->new();
    $passwd_edit->set_visibility(FALSE);
    $passwd_edit->set_activates_default (TRUE);
    
    my $passwd_dialog = Gtk2::Dialog->new ('Enter password', $window,
                            [qw/modal destroy-with-parent/],
                            'gtk-ok'     => 'accept'
                            );
    $passwd_dialog->set_default_response ('accept');                            
    $passwd_dialog->vbox->add (Gtk2::Label->new ('Please enter password for target:'));
    $passwd_dialog->vbox->add (Gtk2::Label->new ($products[$index]->get_name()));
    $passwd_dialog->vbox->add ($passwd_edit);
    
     $passwd_edit->signal_connect (changed => sub {
            $passwd_entry = $passwd_edit->get_text;
        });

    $passwd_dialog->signal_connect (response => sub 
    { 
        if($_[1] =~ m/accept/){
            my $rev_string = reverse $products[$index]->get_name(); 
            if ($rev_string ne $passwd_entry)
            {   
                my $dialog = Gtk2::MessageDialog->new(
                $parent, 'modal',
                'error',     # message type
                'close',    # set of buttons
                "Wrong password..."
                );
                $dialog->run;
                $dialog->destroy;
                $password_ok='passw_fail';
            }
            else
            {
                $password_ok='passw_ok';
            }
        }
        
        if($_[1] =~ m/reject/){
            $password_ok='passw_fail';
        }                       
    });
    
    $passwd_dialog->show_all;       
    $passwd_dialog->run;
    $passwd_dialog->destroy;
    
    #print "\nexit form dialog. password_ok:".$password_ok."\n";
    
    return $password_ok;
}

sub confirm_product_dialog
{
    
    my $controll=shift;
    my $confirm_ok='confirm_fail';
    my $confirm_entry = "";
    
    my $index = $controll->get_active;
    
    my $confirm_edit = Gtk2::Entry->new();
    $confirm_edit->set_visibility(TRUE);
    $confirm_edit->set_activates_default (TRUE);

    my $title = 'Please confirm product name by re-typing it:';
    my $confirm_dialog = Gtk2::Dialog->new ('Confirm Product Name', $window,
                            [qw/modal destroy-with-parent/],
                            'gtk-ok'     => 'ok',
                            'gtk-cancel'    => 'cancel'
                            );
    $confirm_dialog->set_default_response ('ok');                           
    $confirm_dialog->vbox->add (Gtk2::Label->new ($title));
    $confirm_dialog->vbox->add (Gtk2::Label->new ($products[$index]->get_name()));
    $confirm_dialog->vbox->add ($confirm_edit);
    
    $confirm_edit->signal_connect (changed => sub {
            $confirm_entry = $confirm_edit->get_text;
        });

    $confirm_dialog->signal_connect (response => sub 
    { 
        if($_[1] =~ m/ok/){
            if ($products[$index]->get_name() ne $confirm_entry)
            {   
                my $dialog = Gtk2::MessageDialog->new(
                $parent, 'modal',
                'error',     # message type
                'close',    # set of buttons
                "product name doesn't match..."
                );
                $dialog->run;
                $dialog->destroy;
                $confirm_ok='confirm_fail';
            }
            else
            {
                $confirm_ok='confirm_ok';
            }
        }
        
        if($_[1] =~ m/cancel/){
            $confirm_ok='confirm_fail';
        }                       
    });
    
    $confirm_dialog->show_all;      
    $confirm_dialog->run;
    $confirm_dialog->destroy;
    
    return $confirm_ok;
}

sub confirm_boardrevision_dialog
{
    
    my $brev= $_[0] + $min_board_rev;
    my $revstr = sprintf("rev.%02d", $brev);
    my $confirm_ok='confirm_fail';
    my $confirm_rev = 0;
    
    my $confirm_edit = Gtk2::Entry->new();
    $confirm_edit->set_visibility(TRUE);
    $confirm_edit->set_activates_default (TRUE);

    my $title = 'Please confirm BOM revision by re-typing it:';
    my $confirm_dialog = Gtk2::Dialog->new ('Confirm BOM Revision', $window,
                            [qw/modal destroy-with-parent/],
                            'gtk-ok'     => 'ok',
                            'gtk-cancel'    => 'cancel'
                            );
    $confirm_dialog->set_default_response ('ok');                           
    $confirm_dialog->vbox->add (Gtk2::Label->new ($title));
    $confirm_dialog->vbox->add (Gtk2::Label->new ($revstr));
    $confirm_dialog->vbox->add ($confirm_edit);
    $confirm_edit->signal_connect (changed => sub {
            $confirm_rev = $confirm_edit->get_text;
        });

    $confirm_dialog->signal_connect (response => sub 
    { 
        if($_[1] =~ m/ok/){
            if ($revstr ne $confirm_rev)
            {   
                my $dialog = Gtk2::MessageDialog->new(
                $parent, 'modal',
                'error',     # message type
                'close',    # set of buttons
                "BOM revision doesn't match ..."
                );
                $dialog->run;
                $dialog->destroy;
                $confirm_ok='confirm_fail';
            }
            else
            {
                $confirm_ok='confirm_ok';
            }
        }
        
        if($_[1] =~ m/cancel/){
            $confirm_ok='confirm_fail';
        }                       
    });
    
    $confirm_dialog->show_all;      
    $confirm_dialog->run;
    $confirm_dialog->destroy;
    
    return $confirm_ok;
}

sub confirm_regdmn_dialog
{
    
    my $idx=shift;
    my $confirm_ok='confirm_fail';
    my $confirm_text = '0';
    
    my $confirm_edit = Gtk2::Entry->new();
    $confirm_edit->set_visibility(TRUE);
    $confirm_edit->set_activates_default (TRUE);

    my $title = 'Please confirm Region by re-typing it:';
    my $confirm_dialog = Gtk2::Dialog->new ('Confirm Region', $window,
                            [qw/modal destroy-with-parent/],
                            'gtk-ok'     => 'ok',
                            'gtk-cancel'    => 'cancel'
                            );
    $confirm_dialog->set_default_response ('ok');                           
    $confirm_dialog->vbox->add (Gtk2::Label->new ($title));
    $confirm_dialog->vbox->add (Gtk2::Label->new (@regdmn_names[$idx]));
    $confirm_dialog->vbox->add ($confirm_edit);
    $confirm_edit->signal_connect (changed => sub {
        $confirm_text = $confirm_edit->get_text;
    });

    $confirm_dialog->signal_connect (response => sub 
    { 
        if($_[1] =~ m/ok/){
            if (@regdmn_names[$idx] ne $confirm_text)
            {   
                my $dialog = Gtk2::MessageDialog->new(
                $parent, 'modal',
                'error',     # message type
                'close',    # set of buttons
                "Region doesn't match ..."
                );
                $dialog->run;
                $dialog->destroy;
                $confirm_ok='confirm_fail';
            }
            else
            {
                $confirm_ok='confirm_ok';
            }
        }
        
        if($_[1] =~ m/cancel/){
            $confirm_ok='confirm_fail';
        }                       
    });
    
    $confirm_dialog->show_all;      
    $confirm_dialog->run;
    $confirm_dialog->destroy;
    
    return $confirm_ok;
}

my $SELECT_MODE = "manual";
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
        $self->{_PROD_IDX}      = 0;
        $self->{_PRODUCT_COMBO} = Gtk2::ComboBox->new_text();
        $self->{_PRODUCT_DESC}  = Gtk2::Label->new("Description ");
        $self->{_SERIAL_COMBO}  = Gtk2::ComboBox->new_text();
        $self->{BOARD_REVISION} = $board_revision;
        $self->{_REV_CBID}      = undef;
        $self->{_REV_COMBO}     = Gtk2::ComboBox->new_text();
        for (my $i = $min_board_rev; $i <= $max_board_rev; $i++) {
            my $rv = sprintf("rev.%02d", $i);
            $self->{_REV_COMBO}->append_text($rv);
        }
        $self->{_REV_COMBO}->set_active($self->{BOARD_REVISION});

        $self->{_REGDMN_IDX}    = $regdmn_idx;
        $self->{_REGDMN_CBID}   = undef;
        $self->{_REGDMN_COMBO}  = Gtk2::ComboBox->new_text();
        foreach (@regdmn_names) {
            $self->{_REGDMN_COMBO}->append_text($_);
        }
        $self->{_REGDMN_COMBO}->set_active($self->{_REGDMN_IDX});

        $self->{_MAC_LABEL}     = Gtk2::Label->new("xx:xx:xx:xx:xx:xx-xxxxxx");
        $self->{_PROGRESS}      = Gtk2::ProgressBar->new();
        $self->{_RESULT_LABEL}  = Gtk2::Label->new('');
        $self->{_RESULT_LABEL}->set_markup('<span foreground="black" size="xx-large"><b>Idle....</b></span>');
        $self->{_RESULT_LABEL}->set_size_request(200, 32);
        $self->{_RESULT_LABEL}->set_alignment(0.0, 0.0);
        $self->{_START}         = Gtk2::Button->new_with_label(' Start ');
        $self->{_TEXTVIEW}      = Gtk2::TextView->new();
        $self->{_OUTPUTBUFFER}  = $self->{_TEXTVIEW}->get_buffer();
        
        $self->{SELECT_MODE}   = 'auto';

        $self->{_VIEW}        = undef;
        $self->{_OUTPUTVIEW}  = undef;
        $self->{_INITIALIZED} = 0;
        $self->{_BUSY}        = 0;
        $self->{_CHILD_PID}   = 0;

        $self->{_START_TIME} = 0;
        $self->{_END_TIME}   = 0;
        
        $self->{PROGRAMMEDMAC} = "";

        bless( $self, $class );
        return $self;
    }
    
    sub set_auto
    {
        $SELECT_MODE = 'auto';
#       print "\nset mode to: ".$SELECT_MODE;
    }
    
    sub set_manual
    {
        
        $SELECT_MODE = 'manual';
#       print "\nset mode to: ".$SELECT_MODE;
    }
    

    sub initialize {
        my $self = shift;
        if ( $self->{_INITIALIZED} == 0 ) {
            $self->set_products(@products);
            $self->set_ttys(@ttys);
            $self->{BOARD_REVISION} = $board_revision;
            $self->{_REV_COMBO}     = Gtk2::ComboBox->new_text();
            for (my $i = $min_board_rev; $i <= $max_board_rev; $i++) {
                my $rv = sprintf("rev.%02d", $i);
                $self->{_REV_COMBO}->append_text($rv);
            }
            $self->{_REV_COMBO}->set_active($self->{BOARD_REVISION});

            $self->{_REGDMN_IDX}    = $regdmn_idx;
            $self->{_REGDMN_COMBO}  = Gtk2::ComboBox->new_text();
            foreach (@regdmn_names) {
                $self->{_REGDMN_COMBO}->append_text($_);
            }
            $self->{_REGDMN_COMBO}->set_active($self->{_REGDMN_IDX});

            $self->{_START}->set_focus_on_click(FALSE);
            $self->{_START}
              ->signal_connect( 'clicked', \&Migrator::_start, $self );

            my $hbox = Gtk2::HBox->new( FALSE, 5 );
            $hbox->set_border_width(5);
            $hbox->pack_start( $self->{_PRODUCT_COMBO}, 0, 0, 0 );
            $hbox->pack_start( $self->{_REV_COMBO},     0, 0, 0 );
            $hbox->pack_start( $self->{_REGDMN_COMBO},  0, 0, 0 );
            $hbox->pack_start( $self->{_SERIAL_COMBO},  0, 0, 0 );
            $hbox->pack_start( $self->{_MAC_LABEL},     0, 0, 0 );
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
            
            $self->{_PROD_CB} =  $self->{_PRODUCT_COMBO}->signal_connect(
                'changed',
                sub {
                    if ( $self->{SELECT_MODE} ne 'self')
                    {

                        if ($SELECT_MODE eq 'manual')
                        {
                            my $confirm_result = ::confirm_product_dialog ($self->{_PRODUCT_COMBO});

                            if ( $confirm_result eq 'confirm_ok')
                            {
                                $self->{_PROD_IDX}
                                    = $self->{_PRODUCT_COMBO}->get_active();
                            }
                            if ( $confirm_result eq "confirm_fail")
                            {
                                $self->{SELECT_MODE} = 'self';
                                $self->select_product($self->{_PROD_IDX});
                            }
                        } else {
                            $self->{_PROD_IDX}
                                = $self->{_PRODUCT_COMBO}->get_active();
                        }
                    }
                    else
                    {
                        $self->{SELECT_MODE} = 'auto';
                    }
                }
            );

            $self->{_REV_CBID} = $self->{_REV_COMBO}->signal_connect( 'changed', 
                sub 
                {
                    my $brev = $self->{_REV_COMBO}->get_active;
                    my $confirm_result = ::confirm_boardrevision_dialog($brev);
                    if ( $confirm_result eq 'confirm_ok') {
                        $self->{BOARD_REVISION} = $brev;
                    } else {
                        $self->{_REV_COMBO}->signal_handler_block($self->{_REV_CBID});
                        $self->{_REV_COMBO}->set_active($self->{BOARD_REVISION});
                        $self->{_REV_COMBO}->signal_handler_unblock($self->{_REV_CBID});
                    }
                }
            );

            $self->{_REGDMN_CBID} = $self->{_REGDMN_COMBO}->signal_connect( 'changed', 
                sub 
                {
                    my $rd_idx = $self->{_REGDMN_COMBO}->get_active;
                    my $confirm_result = ::confirm_regdmn_dialog($rd_idx);
                    if ( $confirm_result eq 'confirm_ok') {
                        $self->{_REGDMN_IDX} = $rd_idx;
                    } else {
                        $self->{_REGDMN_COMBO}->set_active($self->{_REGDMN_IDX});
                    }
                }
            );

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

    sub select_boardrev {
        my $self    = shift;
        my $rev = shift;

        $self->{BOARD_REVISION} = $rev;
        $self->{_REV_COMBO}->signal_handler_block($self->{_REV_CBID});
        $self->{_REV_COMBO}->set_active($self->{BOARD_REVISION});
        $self->{_REV_COMBO}->signal_handler_unblock($self->{_REV_CBID});
    }

    sub select_regdmn_idx {
        my $self    = shift;
        my $idx     = shift;

        $self->{_REGDMN_IDX} = $idx;
        $self->{_REGDMN_COMBO}->signal_handler_block($self->{_REGDMN_CBID});
        $self->{_REGDMN_COMBO}->set_active($self->{_REGDMN_IDX});
        $self->{_REGDMN_COMBO}->signal_handler_unblock($self->{_REGDMN_CBID});
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
        my ($self, $child_pid) = @_;

        my $tty     = $self->{_SERIAL_COMBO}->get_active_text();
        my $devid   = $self->{_DEVICE_ID};

        my $p = $self->{_PRODUCT};
        $self->{_BUSY} = 1;
        $self->{_CHILD_PID} = $child_pid;

        $self->{_RESULT_LABEL}->set_markup('<span background="darkgrey" foreground="yellow" size="xx-large"><b>Working....</b></span>');
        $self->{_PROGRESS}->modify_bg ('normal', $color_running);
        $self->{_PROGRESS}->modify_bg ('prelight', $color_running);
        $self->{_PROGRESS}->modify_bg ('active', $color_running);
        $self->append_output("\n--------[STARTED]\n");
        @controls =
          ( $self->{_START}, $self->{_PRODUCT_COMBO}, $self->{_REV_COMBO}, $self->{_REGDMN_COMBO}, $self->{_SERIAL_COMBO} );
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
            my $progress = $1;
            if ($progress == 100) {
                self->{PROGRAMMEDMAC} = "";
                print ("pipe data ->> ".$data." <<- ");             
                if ($data =~ /^=== (\d+) (\S{2}\:\S{2}\:\S{2}) Completed with MAC0: (\S{2}\:\S{2}\:\S{2}\:\S{2}\:\S{2}\:\S{2}).*$/m) 
                {
                    print "MAC found";
                    
                    $self->{PROGRAMMEDMAC} = " MAC ".$3;#." ".$3." ".$4." ".$5." ".$6." ".$7;
                    $self->{_MAC_LABEL}->set_label($3);
                }
            }
            $self->{_DONE} = $progress;
        }
    }

    sub __migration_ended {
        my $self   = shift;
        my $status = shift;
        $self->{_END_TIME} = time();
        @controls =
          ( $self->{_START}, $self->{_PRODUCT_COMBO}, $self->{_REV_COMBO}, $self->{_REGDMN_COMBO}, $self->{_SERIAL_COMBO} );
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
            $self->{_RESULT_LABEL}->set_markup('<span background="darkgrey" foreground="green" size="xx-large"><b>PASS</b></span>');
            $self->{_PROGRESS}->modify_bg ('normal', $color_pass);
            $self->{_PROGRESS}->modify_bg ('prelight', $color_pass);
            $self->{_PROGRESS}->modify_bg ('active', $color_pass);
            $msg = "Completed in $duration_str.";
        }
        else {
            $self->{_RESULT_LABEL}->set_markup('<span background="darkgrey" foreground="red" size="xx-large"><b>FAIL</b></span>');
            $self->{_PROGRESS}->modify_bg ('normal', $color_fail);
            $self->{_PROGRESS}->modify_bg ('prelight', $color_fail);
            $self->{_PROGRESS}->modify_bg ('active', $color_fail);
            $msg = "FAILED with error code $status after $duration_str.";
        }
        $self->{_PROGRESS}->set_text($msg);
        $self->append_output("\n--------[$msg\n");
    }

    sub check_mac_addr {
        $text = shift;      
        $text = substr($text, -$macstr_len);
        
        if (length($text)<$macstr_len) 
        {
            return FALSE;
        }
        
        if ($text =~ /[^0-9a-fA-F]/)
        {
            return FALSE;
        }
        else 
        {
            return TRUE;
        }
                    
    }

    sub start {
        my $self = shift;

        my $tty     = $self->{_SERIAL_COMBO}->get_active_text();
        my $product = $self->{_PRODUCT_COMBO}->get_active_text();
        my $boardrev = $self->{BOARD_REVISION} + $min_board_rev;
        my $rd_idx  = $self->{_REGDMN_IDX};
        my $id      = $self->{ID};

        my $p = ::find_product_by_name(\@products, $product);
        if (!defined($p) or $product eq 'none') {
            my $parent = $window;
            my $dialog = Gtk2::MessageDialog->new(
                $parent, 'modal',
                'error',     # message type
                'close',    # set of buttons
                "Invalid product name \"$product\""
            );
            $dialog->format_secondary_text($info);
            my $response = $dialog->run;
            $dialog->destroy;
            return FALSE;
        }

        $self->{_PROGRESS}->set_text('');

        $self->{_PRODUCT} = $p;

        my $mac_addr = "";
        my $bid     = lc($p->get_boardid());

        my $barcode = "";
        
        my $manuf_id = "fcd";
        my $mac_label = Gtk2::Label->new ("------------");
        #my $mac_server;
        
        my $mac_edit = Gtk2::Entry->new();
        $mac_edit->set_visibility(TRUE);
        $mac_edit->set_activates_default (TRUE);
        
        
        my $title = 'Waiting for barcode...';
        
        my $dialog = Gtk2::Dialog->new ($title, $window,
                            [qw/modal destroy-with-parent/],
                            'gtk-ok'     => 'ok',
                            'gtk-cancel'     => 'cancel'
                            );                                 
        $dialog->set_default_response ('ok');
        $dialog->vbox->add (Gtk2::Label->new ($title));
        $dialog->vbox->add ($mac_label);
        $dialog->vbox->add ($mac_edit);

        $mac_edit->signal_connect (changed => sub {
            $barcode = $mac_edit->get_text;
        });
        
        my $mac_check_status = 1;
        
        $dialog->signal_connect (response => sub 
        { 
            print "\nsignal $_[1]\n";

            if($_[1] =~ m/ok/){
                chomp($barcode);
                my $barcode_len = length($barcode); 

                if ($barcode_len < ($macstr_len + $qrcode_len + 1) )
                {
            
                    my $parent = $window;
                    my $dialog = Gtk2::MessageDialog->new(
                        $parent, 'modal',
                        'error',     # message type
                        'close',    # set of buttons
                        "barcode invalid"
                    );
                    $dialog->format_secondary_text($info);
                    my $response = $dialog->run;
                    $dialog->destroy;   
                    $mac_check_status = 0;
                    return FALSE;
                }

                if ($barcode_len == ($macstr_len + $qrcode_len + 1)) {
                    $dash_idx = index($barcode, '-');
                    $qrcode_idx = $dash_idx + 1;
                    if (($dash_idx < $macstr_len) || (($barcode_len - $qrcode_idx) < $qrcode_len)) {
                        my $parent = $window;
                        my $dialog = Gtk2::MessageDialog->new(
                            $parent, 'modal',
                            'error',     # message type
                            'close',    # set of buttons
                            "barcode invalid"
                        );
                        $dialog->format_secondary_text($info);
                        my $response = $dialog->run;
                        $dialog->destroy;   
                        $mac_check_status = 0;
                        return FALSE;
                    } else {
                        $qr_code = substr($barcode, $qrcode_idx, $qrcode_len);
                        $mac_addr = substr($barcode, $dash_idx - $macstr_len, $macstr_len);
                    }
                } elsif ($barcode_len == ($macstr_len + $qrcode_len))
                {
                    $qr_code = substr($barcode, -$qrcode_len);
                    $mac_addr = substr($barcode, -($macstr_len + $qrcode_len), $macstr_len);
                } else {
                        my $parent = $window;
                        my $dialog = Gtk2::MessageDialog->new(
                            $parent, 'modal',
                            'error',     # message type
                            'close',    # set of buttons
                            "barcode invalid"
                        );
                        $dialog->format_secondary_text($info);
                        my $response = $dialog->run;
                        $dialog->destroy;   
                        $mac_check_status = 0;
                        return FALSE;
                }
                

                if (!check_mac_addr($mac_addr))
                {
            
                    my $parent = $window;
                    my $dialog = Gtk2::MessageDialog->new(
                        $parent, 'modal',
                        'error',     # message type
                        'close',    # set of buttons
                        "MAC address invalid"
                    );
                    $dialog->format_secondary_text($info);
                    my $response = $dialog->run;
                    $dialog->destroy;   
                    $mac_check_status = 0;
                    return FALSE;
                }

#                $mac_addr = substr($barcode, -$macstr_len);

#                if (length($barcode)>$macstr_len) 
#               {
#                   print "\n--------------------\n";
#                   $manuf_id = substr($barcode, 0, length($barcode)-$macstr_len);
#                }
#                print "\nmanuf_id = $manuf_id, mac_addr = $mac_addr\n";
            }
            
            if($_[1] =~ m/cancel/){
                print "\ncanceled\n";
                $dialog->destroy;
                $mac_check_status = 0;
                return FALSE;
            }                                   
            
        });                          
                                   
        $dialog->show_all;
        $dialog->run;
        $dialog->destroy;
        
        if (!$mac_check_status) 
        {
            return FALSE;
        }
        
        $self->{_MAC_LABEL}->set_label( 
            substr($mac_addr,0,2).":".substr($mac_addr,2,2).":".    
            substr($mac_addr,4,2).":".substr($mac_addr,6,2).":".
            substr($mac_addr,8,2).":".substr($mac_addr,10,2)."-".
            substr($qr_code, 0,6));      

        #
        # ID is used for IP address generation in production script
        # so we should be very careful with it, we should support as
        # many serial ports as possible
        #
        if ( $tty =~ /^ttyUSB(\d+)$/ ) {
            $id = $1;
        }
        elsif ( $tty =~ /^ttyS(\d+)$/ ) {
            $id = $1 + 4;
        }
        else {
            $id += 8;
        }
        $self->{_DEVICE_ID} = $id;
        
        
        my ($sec,$min,$hour,$mday,$mon,$year, $wday,$yday,$isdst) = localtime time;
        $year += 1900;
        $mon += 1;      
      
        $_ = @regdmn_names[$rd_idx];
        s/\//_/g;
        my $rv = sprintf("rev.%02d", $boardrev);
        my $directory = $log_directory.'/'.$p->get_name().'/'.$rv.'/'.$_;
        
        if (not -e $directory)
        {
            system "mkdir -p ".$directory;
        }
        
        my $temp_file = ''.$directory.'/'.$sec.$min.$hour.rand(200).'.log';
        system "stty -F /dev/$tty speed 115200";
        my $cmd = "";

        $cmd = $p->get_script() . ' ' . $p->get_platformid()
               . ' ' . $p->get_boardid()
               . " $mac_addr '$pass_phrase' $log_directory/keys $tty"
               . " $id $boardrev $mac_addr $qr_code";
        print "".$cmd."\n";

        my $child_pid = open my $pipe, "$cmd |";
        $self->__migration_started($child_pid);

        Glib::IO->add_watch(
            fileno $pipe,
            [ 'in', 'hup' ],
            sub {
                my ( $fd, $condition ) = @_;
                if ( $condition >= 'in' ) {
                    my $data = "";
                    my $nread = sysread( $pipe, $data, 160 );
                    #remove zeros in null-terminated strings    
                    $data =~ s/\000//g;
                    system 'echo -n "'.$data.'" >> '.$temp_file;
                    $self->__migration_step($data);
                }
                if ( $condition >= 'hup' ) {
                    my $data = "";
                    while (sysread( $pipe, $data, 160 )){
                        #remove zeros in null-terminated strings
                        $data =~ s/\000//g;
                        system 'echo -n "'.$data.'" >> '.$temp_file;                    
                        $self->__migration_step($data);
                    }
                    close $pipe;
                    $self->__migration_ended($?);
                    
                    while ($log_file_locked) #wait for log file unlock
                    {
                    }
                    $log_file_locked = TRUE;
                    
                    my $log_file = ''.$directory.'/'.$year.'-'.$mon.'-'.$mday.'.log';
                    
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
    my $pdata = '';

    for my $p (@products) {
        my $pname = uc($p->get_name());
        next if ($pname eq 'NONE');
        $pdata .= "$pname\n\n\n";
    }

    my $textbuffer = Gtk2::TextBuffer->new();
    $textbuffer->set_text($pdata);
    my $textview = Gtk2::TextView->new_with_buffer($textbuffer);
    my $dialog = Gtk2::MessageDialog->new_with_markup(
        $parent,
        'modal',
        'info',    # message type
        'ok',      # which set of buttons?
        "<b>EdgeRouter Factory CD $_VERSION</b>\n"
        . '(c) 2012 Ubiquiti Networks, Inc.'
    );

    my $frame = Gtk2::Frame->new(' Contains firmwares ');
    $frame->add($textview,);
    $frame->set_border_width(10);
    $dialog->vbox->add($frame);
    $dialog->signal_connect (response => sub { $_[0]->destroy });
    $dialog->show_all;

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

my $common_rev_cb;
my $common_prod_cb;
my $common_prod_idx = 0;
sub create_controls {
    my $hbox = Gtk2::HBox->new( FALSE, 5 );
    $hbox->set_border_width(5);

    
    my $auth = FALSE;
    $hbox->set_border_width(5);

    my $l = Gtk2::Label->new("(for all slots) Product:");
    my $p = Gtk2::ComboBox->new_text();

    my $r = Gtk2::Label->new("BOM revision:");
    my $rev_edit = Gtk2::ComboBox->new_text();
    for (my $i = $min_board_rev; $i <= $max_board_rev; $i++) {
        my $rv = sprintf("rev.%02d", $i);
        $rev_edit->append_text($rv);
    }
    $rev_edit->set_active($board_revision);

    my $regdmn_label = Gtk2::Label->new("Region:");
    my $regdmn_edit = Gtk2::ComboBox->new_text();
    foreach (@regdmn_names) {
        $regdmn_edit->append_text($_);
    }
    $regdmn_edit->set_active($regdmn_idx);

    my $inf = Gtk2::Label->new("Flavor: ");;
    my $d = Gtk2::Label->new("PD ");;

    my $active = 0;
    my $id = 0;
    foreach (@products) {
        $p->append_text($_->get_name());
        if ($_->get_name() eq $cfg->get('common.product')) {
            $active = $id;
        }
        $id++;
    }
    
    $p->set_active(0);
    $d->set_text($products[0]->get_description());
    
    foreach (@migrators) {
        $_->set_auto;
        $_->select_product(0);
        $_->set_manual;
    }
    $cfg->set('common.product', $p->get_active_text);           

    $common_rev_cb = $rev_edit->signal_connect(
        'changed',
        sub {
            my $brev = $rev_edit->get_active;
            my $confirm_result = &confirm_boardrevision_dialog($brev);
            if ( $confirm_result eq 'confirm_ok') {
                $board_revision = $brev;
                foreach (@migrators) {
                    $_->select_boardrev($board_revision);
                }
            } else {
                $rev_edit->signal_handler_block($common_rev_cb);
                $rev_edit->set_active($board_revision);
                $rev_edit->signal_handler_unblock($common_rev_cb);
            }
        }
    );

    $regdmn_edit->signal_connect(
        'changed',
        sub {
            my $idx = $regdmn_edit->get_active;
            my $confirm_result = &confirm_regdmn_dialog($idx);
            if ( $confirm_result eq 'confirm_ok') {
                $regdmn_idx = $idx;
                foreach (@migrators) {
                    $_->select_regdmn_idx($regdmn_idx);
                }
            } else {
                $regdmn_edit->set_active($regdmn_idx);
            }
        }
    );

    $common_prod_cb = $p->signal_connect(
        'changed',
        sub {
                my $confirm_result = &confirm_product_dialog($p);
                if ( $confirm_result eq 'confirm_ok')
                {
                    my $index = $p->get_active;
                    $common_prod_idx = $index;
                    $d->set_text($products[$index]->get_description());
                    foreach (@migrators) {
                        $_->set_auto;
                        $_->select_product($index);
                        $_->set_manual;
                    }
                    $cfg->set('common.product', $p->get_active_text);
                }
                if ( $confirm_result eq "confirm_fail")
                {
                    $p->signal_handler_block($common_prod_cb);
                    $p->set_active($common_prod_idx);
                    $p->signal_handler_unblock($common_prod_cb);
                }
            });
            

    $hbox->pack_start( $l, 0, 0, 0 );
    $hbox->pack_start( $p, 0, 0, 0 );
    $hbox->pack_start( $r, 0, 0, 0 );
    $hbox->pack_start( $rev_edit, 0, 0, 0 );
    $hbox->pack_start( $regdmn_label, 0, 0, 0 );
    $hbox->pack_start( $regdmn_edit, 0, 0, 0 );
    $hbox->pack_start( $inf, 0, 0, 0 );
    $hbox->pack_start( $d, 0, 0, 0 );

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
    @lines = `ls -ls /dev/disk/by-id| grep usb-`;
    
    my $device;
    
    #searching for usb storage mount point
    foreach my $line (@lines) {
            
            my @dev = split('/',$line);
            $device = ''.@dev[-1];      
#           if ($device =~ /\d$/)
            {
#               print $device;
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
#                           print "Found storage at ".$log_directory."\n";
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


sub enter_pass_phrase
{
    
    my $controll=shift;
    my $password_ok='passw_fail';
    my $passwd_entry1 = '';
    my $passwd_entry2 = '';
    
    
    my $passwd_edit1 = Gtk2::Entry->new();
    $passwd_edit1->set_visibility(FALSE);
    $passwd_edit1->set_activates_default (TRUE);
    
    my $passwd_edit2 = Gtk2::Entry->new();
    $passwd_edit2->set_visibility(FALSE);
    $passwd_edit2->set_activates_default (TRUE);

    my $passwd_dialog = Gtk2::Dialog->new ('Enter pass-phrase', $window,
                            [qw/modal destroy-with-parent/],
                            'gtk-ok'     => 'ok',
                            'gtk-cancel'    => 'cancel'
                            );
    $passwd_dialog->set_default_response ('ok');                            
    $passwd_dialog->vbox->add (Gtk2::Label->new ('Please enter pass-phrase twice:'));
    $passwd_dialog->vbox->add ($passwd_edit1);
    $passwd_dialog->vbox->add ($passwd_edit2);
    
    $passwd_edit1->signal_connect (changed => sub {
            $passwd_entry1 = $passwd_edit1->get_text;
        });
    $passwd_edit2->signal_connect (changed => sub {
            $passwd_entry2 = $passwd_edit2->get_text;
        });

    $passwd_dialog->signal_connect (response => sub 
    { 
        if($_[1] =~ m/ok/) {
            if (($passwd_entry1 ne '') && ($passwd_entry1 eq $passwd_entry2)) {
                $pass_phrase = $passwd_entry1;
                $password_ok='passw_ok';
            } else {    
                my $dialog = Gtk2::MessageDialog->new(
                $parent, 'modal',
                'error',     # message type
                'close',    # set of buttons
                "Pass-phrase doesn't match..."
                );
                $dialog->run;
                $dialog->destroy;
                $password_ok='passw_fail';
            }
        }
        
        if($_[1] =~ m/cancel/) {
            $password_ok='passw_fail';
        }                       
    });
    
    $passwd_dialog->show_all;       
    $passwd_dialog->run;
    $passwd_dialog->destroy;
    
    return $password_ok;
}

sub key_files_missing {
    
    my $key_dir = $log_directory.'/keys/';
    my @key_filenames = ("ca.pem","crt.pem","key.pem");

    foreach $filename (@key_filenames) {
        my $keyfile = $key_dir . $filename;
        if (! -e $keyfile) {
            print "$keyfile doesn't exist!\n";
            return 1;
        }
    }
    
    return 0;           
}

my $initializer;

sub initialize {
    my $msg = ' Initializing production environment - please wait...';

    my $parent = $window;
    my $dialog =
      Gtk2::MessageDialog->new( $parent, 'modal', 'info', 'none', $msg );

    my $cmd = $setup_script;
    my $setup_status = -1;

    open my $pipe, "$cmd |";
    Glib::IO->add_watch(
        fileno $pipe,
        ['hup'],
        sub {
            my ( $fd, $condition ) = @_;
            if ( $condition >= 'hup' ) {
                close $pipe;
                $setup_status = $?;
                print("setup_status = $setup_status\n");
                $dialog->response(0);
                return FALSE;
            }
            return TRUE;
        }
    );

    $dialog->run();
    $dialog->destroy;
    
    if ($setup_status != 0)
    {
        my $dialog = Gtk2::MessageDialog->new(
        $parent, 'modal',
        'error',     # message type
        'close',    # set of buttons
        "License server not responding. Exiting..."
        );
        $dialog->run;
        $dialog->destroy;
        exit 0;
    }

#   if (!find_usb_storage())
#   {
#       my $dialog = Gtk2::MessageDialog->new(
#       $parent, 'modal',
#       'info',     # message type
#       'close',    # set of buttons
#       "No USB storage found. Files will be saved to Desktop"
#       );
#       $dialog->run;
#       $dialog->destroy;
#   }   

    if (!find_usb_storage())
    {
        my $dialog = Gtk2::MessageDialog->new(
        $parent, 'modal',
        'error',     # message type
        'close',    # set of buttons
        "No USB storage found. Exiting..."
        );
        $dialog->run;
        $dialog->destroy;
        exit 0;
    }

    if (key_files_missing())
    {
        my $dialog = Gtk2::MessageDialog->new(
        $parent, 'modal',
        'error',     # message type
        'close',    # set of buttons
        "Key files missing. Exiting..."
        );
        $dialog->run;
        $dialog->destroy;
        exit 0;
    }

    if (enter_pass_phrase() eq "passw_fail") {
        my $dialog = Gtk2::MessageDialog->new(
        $parent, 'modal',
        'error',     # message type
        'close',    # set of buttons
        "Pass-phrase not entered correctly. Exiting..."
        );
        $dialog->run;
        $dialog->destroy;
        exit 0;
        
    }

    my @serials = collect_serials;
    foreach (@migrators) {
        $_->set_ttys(@serials);
    }

    $initialized = TRUE;
    Glib::Source->remove($initializer);
    $manual_select = TRUE;  
    return FALSE;
}

sub default_products {
    my @list;
    $product = Product->new(1, 'none');
    $product->set_description('No product');
    push @list, $product;
    return @list;
}

sub load_products {
    my $product;
    my @list;

    my $pcfg = Configuration->new();
    
    $product = Product->new($0, "none");
    $product->set_description("No product");
    $product->set_script("none");
    push @list, $product;

    # TODO: add support for product loading from USB flash
    if ($pcfg->load('/tftpboot/products.txt')) {
        for (my $i = 1; $i < 16; $i++) {
            my $name = $pcfg->get('product.'.$i.'.name');
            last if (!defined $name);

            my $desc = $pcfg->get('product.'.$i.'.description');
            my $scr = $pcfg->get('product.'.$i.'.script');
            my $bid = $pcfg->get('product.'.$i.'.boardid');
            my $pid = $pcfg->get('product.'.$i.'.platformid');
            $product = Product->new($i, $name);
            $product->set_description($desc);
            $product->set_script($scr);
            $product->set_boardid($bid);
            $product->set_platformid($pid);
            $product->set_firmware($pid.bin);

            push @list, $product;
        }
    } else {
        push @list, default_products();
    }

    return @list;
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
my $controls    = create_controls();
my $outputs = Gtk2::Expander->new_with_mnemonic('Output of production scripts');
$outputs->set_expanded(FALSE);
$outputs->add($output_tabs);

#
# Main Window
#

my $vbox = Gtk2::VBox->new;
$vbox->pack_start( $menubar,  0, 0, 0 );
$vbox->pack_start( $controls, 0, 0, 0 );
$vbox->pack_start( $contents, 0, 0, 0 );
$vbox->pack_start( $outputs,  1, 1, 0 );

#$vbox->pack_start($statusbar, FALSE, FALSE, 0);

$window->set_title("EdgeRouter Factory CD $_VERSION");
$window->modify_bg ('normal', $greyl);
$window->set_border_width(2);
$window->set_default_size( 640, 480 );
$window->set_resizable(TRUE);
$window->set_position('center');
$window->signal_connect( delete_event => sub { quit_confirm; } );
$window->signal_connect( destroy      => sub { quit_hooks; Gtk2->main_quit; } );
$window->add($vbox);
$window->show_all;
$window->activate();

$initializer = Glib::Timeout->add( 100, \&initialize );

Gtk2->main;
