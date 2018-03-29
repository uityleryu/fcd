#!/usr/bin/perl
#use Data::Dumper;
use Getopt::Long;
use Glib qw(FALSE);
use Gtk2 -init;
use feature qw(switch);

sub collect_serials;

my $_VERSION = "1.2.733";

my $local = 0;
my $autoip = 0;
my $install_dir = '/usr/local/sbin/';
my $data_dir = '/tftpboot/';
my $pass_phrase = "";
my $hw_pref = 0;
my $hw_dev_id = 0;
my $hw_revision = 0;
my $hw_revision_txt = "";
my $model_string = "";
my $selected_product = "";
my $selected_name = "";
my $selected_short_name = "";
my $last_selected_target = 0;
my $macstr_len = 12;
my $appname = "";
my $portcnt = 0;
my $usetty = 0;
my $indsel = 0;
my @controls=();
my $use_barcode_overide = undef;
my $use_qrcode_overide = undef;

my $contents    = Gtk2::VBox->new;
my $output_tabs = Gtk2::Notebook->new;

GetOptions('local' => \$local,'autoip' => \$autoip,'data=s' => \$data_dir);

if ($local) {
	$install_dir = './';
}

my $script       = $install_dir.'python-production.tcl';
my $product_ssid_file = $data_dir.'product_ssid.txt';
my $products_file = $data_dir.'products.txt';

my $init_script = 'prod-network-sec-autoip.sh';
my $product_cfg = Configuration->new();
if ($product_cfg->load($products_file)) {
	my $init_script_cfg = "";
	$init_script_cfg = $product_cfg->get('init_script');
	if ($init_script_cfg ne "") {
		$init_script=$init_script_cfg;
	}
}
my $setup_script = $install_dir.$init_script;
print "$setup_script\n";

my $log_directory = $ENV{HOME}.'/Desktop/';

my @products = ();
my @ttys = ();
my @migrators = ();

my $window      = Gtk2::Window->new;
my $initialized = FALSE;

my $log_file_locked = FALSE;

my $host_ip = '169.254.1.19';
my $target_ip = '169.254.1.20';

if (!$autoip) {
	$host_ip = '192.168.1.19';
	$target_ip = '192.168.1.20';
}

my $cfg = Configuration->new();
$cfg->load($ENV{HOME}.'/.lsf.cfg');
my $sc = $cfg->get('script.setup');
$setup_script = $sc if (defined $sc and $sc ne '');
$sc = $cfg->get('script.production');
$script = $sc if (defined $sc and $sc ne '');

my $color_fail = Gtk2::Gdk::Color->new(0xFFFF,0,0);
my $color_running = Gtk2::Gdk::Color->new(0xFFFF,0xFFFF,0);
my $color_pass = Gtk2::Gdk::Color->new(0,0xFFFF,0);
my $greyl = Gtk2::Gdk::Color->new(0xa9a9,0xa9a9,0xa9a9);

log_debug('setup script = \'' . $setup_script . '\'');
log_debug('production script = \'' . $script . '\'');


sub quit_hooks {
	$cfg->save($ENV{HOME}.'/.lsf.cfg') if ($cfg);
}


END {
	quit_hooks();
}

{

	package Configuration;


	sub new {
		my ($class) = @_;
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
		$self->{_SCRIPT_PARAMS} = undef;
		$self->{_BOOTLOADER} = undef;
		$self->{_FIRMWARE} = undef;
		$self->{_FIRMWARE_FILE} = undef;
		$self->{_FIRMWARE_VERSION} = undef;
		$self->{_USE_BARCODE} = undef;
		$self->{_USE_QRCODE} = undef;
		$self->{_USE_FULLBOM} = undef;
		$self->{_INIT_FILE} = undef;
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


	sub get_script_params {
		my $self = shift;
		return $self->{_SCRIPT_PARAMS};
	}


	sub get_use_barcode {
		my $self = shift;
		return $self->{_USE_BARCODE};
	}


	sub get_use_qrcode {
		my $self = shift;
		return $self->{_USE_QRCODE};
	}


	sub get_use_fullbom {
		my $self = shift;
		return $self->{_USE_FULLBOM};
	}


	sub get_bootloader {
		my $self = shift;
		return $self->{_BOOTLOADER};
	}


	sub get_firmware {
		my $self = shift;
		return $self->{_FIRMWARE};
	}


	sub get_init_file {
		my $self = shift;
		return $self->{_INIT_FILE};
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


	sub set_req_barcode {
		my ($self,$u_barc) = @_;
		$self->{_USE_BARCODE} = $u_barc;
	}


	sub set_req_qrcode {
		my ($self,$u_qrc) = @_;
		$self->{_USE_QRCODE} = $u_qrc;
	}


	sub set_req_fullbom {
		my ( $self, $u_fbom ) = @_;
		$self->{_USE_FULLBOM} = $u_fbom;
	}


	sub set_script {
		my ($self,$scrpt) = @_;
		$self->{_SCRIPT} = $scrpt;
	}


	sub set_script_params {
		my ($self,$params) = @_;
		$self->{_SCRIPT_PARAMS} = $params;
	}


	sub set_init_file {
		my ($self,$params) = @_;
		$self->{_INIT_FILE} = $params;
	}

	sub to_string {
		my $self = shift;
		return '[' . $self->get_id() . '] name=\'' . $self->get_name() . '\'' .' boot=\''.$self->get_bootloader().'\'' .' fw=\''.$self->get_firmware().'\'' if (defined $self);
	}


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


sub enter_prod_info{

	my $controll=shift;
	my $info_ok='passw_ok';
	my $passwd_entry = "";

	my $passwd_edit = Gtk2::Entry->new();
	$passwd_edit->set_visibility(FALSE);
	$passwd_edit->set_activates_default(TRUE);

	my $custom_ssid = 0;
	my $adjustment = Gtk2::Adjustment->new( 0, 0, 4294967295, 1, 0, 0 );
	my $hw_rev_edit = Gtk2::Entry->new();
	$hw_rev_edit->set_max_length(3);
	$hw_rev_edit->set_width_chars(3);
	my $hw_dev_id_edit = Gtk2::Entry->new();
	$hw_dev_id_edit->set_max_length(5);
	$hw_dev_id_edit->set_width_chars(5);
	my $hw_pref_edit = Gtk2::Entry->new();
	$hw_pref_edit->set_max_length(2);
	$hw_pref_edit->set_width_chars(2);

	#fill product list
	my $product  = Gtk2::ComboBox->new_text();
	my $p = ::find_product_by_name( \@products, $controll->get_active_text() );
	my $product_ssid = Configuration->new();
	my $list_store = Gtk2::ListStore->new(qw/Glib::String/);
	my $wrap_width = 1;
	my $real_cnt = 0;
	my %ssid_devtype = ();
	my @product_aray = ();

	if ($product_ssid->load($product_ssid_file)) {
		my $count = $product_ssid->get('count');
		$real_cnt = 0;
		for (my $i = 1; $i <= $count; $i++) {
			my $name = $product_ssid->get('product.'.$i.'.name');
			my $ssid = $product_ssid->get('product.'.$i.'.ssid');
			my $device  = $product_ssid->get( 'product.' . $i . '.device' );
			my $hidden = $product_ssid->get('product.'.$i.'.hidden');
			my $cap_gps = $product_ssid->get('product.'.$i.'.gps');
			my $cap_3g = $product_ssid->get('product.'.$i.'.3g');
			my $use_barcode = $product_ssid->get('product.'.$i.'.barcode');
			my $use_qrcode = $product_ssid->get('product.'.$i.'.qrcode');
			my $region_fix = $product_ssid->get('product.'.$i.'.regfix');
			my $pr_model_string = $product_ssid->get('product.'.$i.'.model_string');

			if (index($p->get_name(), $region_fix) == -1) {
				print("Region fixed (".$region_fix."): skiping ".$name."[13-".$device."-xx]\n");
				next;
			}
			my $is_gps = "";
			if ($cap_gps == 1) {
				$is_gps = " (GPS)";
			}
			my $is_3g = "";
			if ($cap_3g == 1) {
				$is_3g = " (3G)";
			}
			$product_string = $name;
			if ($use_barcode) {
				$product_string = $product_string.'(w)';
			}
			$product_string = $product_string.$is_gps.$is_3g.' - '.$ssid;

			if ($hidden == 0) {
				push(@product_aray, $product_string);
				$real_cnt++;
			}
			$ssid_devtype{"$product_string"} = $device;
			$ssid_model_string{"$product_string"} = $pr_model_string;
			$ssid_barcode{"$product_string"} = $use_barcode;
			$ssid_qrcode{"$product_string"} = $use_qrcode;
		}
	}

	@product_aray = sort @product_aray;
	foreach (@product_aray) {
		my $iter = $list_store->append;
		$list_store->set($iter,0 => $_);
	}

	$product->set_model($list_store);
	if ($real_cnt > 20) {
		$wrap_width = 5;
	}

	$product->set_wrap_width($wrap_width);

	my $custom = Gtk2::CheckButton->new("Custom SSID:");
	my $custom_edit = Gtk2::Entry->new();

	my $checked = 0;
	my $full_name = "";

	my $hbox = Gtk2::HBox->new( FALSE, 5 );
	$hbox->set_border_width(5);
	$hbox->add($custom);
	$hbox->add($custom_edit);

	$product->set_sensitive(TRUE);
	$custom_edit->set_sensitive(FALSE);


	$custom->signal_connect(
		clicked => sub {
			if ($custom->get_active) {
				$checked = 1;
				$product->set_sensitive(FALSE);
				$custom_edit->set_sensitive(TRUE);
			} else {
				$checked = 0;
				$product->set_sensitive(TRUE);
				$custom_edit->set_sensitive(FALSE);
			}
		}
	);

	my $passwd_dialog = Gtk2::Dialog->new(
		'Production info', $window,
		[qw/modal destroy-with-parent/],
		'gtk-ok'     => 'ok',
		'gtk-cancel'     => 'cancel'
	);
	$passwd_dialog->set_default_response('accept');
	$passwd_dialog->vbox->add(Gtk2::Label->new('Pass-phrase:'));
	$passwd_dialog->vbox->add($passwd_edit);
	$passwd_dialog->vbox->add(Gtk2::Label->new('BOM revision:'));

	my $hbox_bom = Gtk2::HBox->new( FALSE, 5 );
	$hbox_bom->set_border_width(0);

	if ( $p->get_use_fullbom() == 1 ) {
		$hbox_bom->pack_start( $hw_pref_edit, 0, 0, 0 );
		$hw_pref_edit->signal_connect( insert_text => \&validate_int );

		$hbox_bom->pack_start( Gtk2::Label->new('-'), 0, 0, 0 );
		$hbox_bom->pack_start( $hw_dev_id_edit,       1, 1, 0 );
		$hw_dev_id_edit->signal_connect( insert_text => \&validate_int );
		$hbox_bom->pack_start( Gtk2::Label->new('-'), 0, 0, 0 );

	}
	$hbox_bom->pack_start( $hw_rev_edit, 0, 0, 0 );
	$hw_rev_edit->signal_connect( insert_text => \&validate_int );


	sub validate_int {
		my ( $entry, $text, $len, $pos ) = @_;
		my $newtext = $text;
		$newtext =~ s/\D//g;
		$_[1] = reverse $newtext;
		$_[3] = $pos;
		return ();
	}

	$passwd_dialog->vbox->add($hbox_bom);
	$passwd_dialog->vbox->add(Gtk2::Label->new('Product:'));
	$passwd_dialog->vbox->add($product);
	$passwd_dialog->vbox->add($hbox);


	$passwd_edit->signal_connect(
		changed => sub {
			$pass_phrase = $passwd_edit->get_text;
		}
	);

	$info_ok='info_fail';

	#	$hw_rev_edit->signal_connect (changed => sub {
	#			$hw_revision = $hw_rev_edit->get_text;
	#			$hw_revision_txt = $hw_revision;
	#			$hw_revision =~ s/\D//g;
	#		});

	$product->signal_connect(
		changed => sub {
			my @product_str = split(' ',$product->get_active_text);
			$selected_product = $product_str[-1];
			$full_name = $product->get_active_text;
			$custom_ssid = 0;
		}
	);

	$custom_edit->signal_connect(
		changed => sub {
			$selected_product = $custom_edit->get_text;
			$custom_ssid = 1;
		}
	);

	$passwd_dialog->show_all;
	my $response = $passwd_dialog->run;

	$hw_pref = 0;
	$hw_dev_id = 0;
	$hw_revision = 0;

	$hw_revision = $hw_rev_edit->get_text;
	if ( $p->get_use_fullbom() == 1 ) {
		$hw_pref     = $hw_pref_edit->get_text;
		$hw_dev_id   = $hw_dev_id_edit->get_text;
	}

	if ( $response eq 'ok' ) {
		my $param_err = 0;
		my $param_txt = "Wrong parameters:\n";

		if ( $pass_phrase eq "" ) {
			$param_txt .= "Passphrase\n";
			$param_err = 1;
		}

		if ( $selected_product eq "" ) {
			$param_txt .= "Device type\n";
			$param_err = 1;
		}

		$use_barcode_overide = $ssid_barcode{"$full_name"};
		$use_qrcode_overide = $ssid_qrcode{"$full_name"};
		$model_string = $ssid_model_string{"$full_name"};

		if (
			(( $hw_revision <= 0 ) or ( $hw_revision > 255 ))
			or(    ( $p->get_use_fullbom() == 1 )
				and(( $hw_dev_id > 99999 ) or ( $hw_dev_id < 1 ) or ( $hw_pref != 13 )))
		  ) {
			$param_txt .= "BOM: ";
			if( $hw_pref != 13 ) {
				$param_txt .= "[PREF]";
			}
			if (( $hw_dev_id > 99999 ) or ( $hw_dev_id < 1 )) {
				$param_txt .= "[DEV_ID]";
			}
			if (( $hw_revision <= 0 ) or ( $hw_revision > 255 )) {
				$param_txt .= "[HW_REV]";
			}
			$param_txt .= "\n";
			$param_err = 1;
		}
		if (($ssid_devtype{"$full_name"} != $hw_dev_id) and ($custom_ssid ==0)){
			$param_txt .= "Product type mistmach\n";
			$param_err = 1;
		}

		if ($param_err == 0){
			$info_ok = 'info_ok';
			if ( $p->get_use_fullbom() == 1 ) {
				$selected_name = " ($full_name [rev. $hw_pref-". sprintf("%05d", $hw_dev_id)."-$hw_revision])";
			} else {
				$selected_name = " ($full_name [rev. $hw_revision])";
			}
			my $active = $product->get_active;
			$selected_short_name = $product_ssid->get('product.'.($active+1).'.name');
			$passwd_dialog->destroy;
		} else {
			my $err_dialog = Gtk2::MessageDialog->new(
				$window, 'modal',
				'error',    # message type
				'close',    # set of buttons
				$param_txt
			);
			$err_dialog->run;
			$err_dialog->destroy;
		}
	}else {
		$info_ok = 'info_cancel';
	}

	$passwd_dialog->destroy;

	return $info_ok;
}


sub check_password_dialog{
	my $controll=shift;
	my $password_ok='passw_fail';
	my $passwd_entry = "";

	my $index = $controll->get_active;

	my $passwd_edit = Gtk2::Entry->new();
	$passwd_edit->set_visibility(FALSE);
	$passwd_edit->set_activates_default(TRUE);

	my $passwd_dialog = Gtk2::Dialog->new('Enter password', $window,[qw/modal destroy-with-parent/],'gtk-ok'     => 'accept');
	$passwd_dialog->set_default_response('accept');
	$passwd_dialog->vbox->add(Gtk2::Label->new('Please enter password for target:'));
	$passwd_dialog->vbox->add(Gtk2::Label->new($products[$index]->get_name()));
	$passwd_dialog->vbox->add($passwd_edit);

	$passwd_edit->signal_connect(
		changed => sub {
			$passwd_entry = $passwd_edit->get_text;
		}
	);

	$passwd_dialog->signal_connect(
		response => sub{
			if($_[1] =~ m/accept/){
				my $rev_string = reverse $products[$index]->get_name();
				if ($rev_string ne $passwd_entry){
					my $dialog = Gtk2::MessageDialog->new(
						$window, 'modal',
						'error',     # message type
						'close',    # set of buttons
						"Wrong password..."
					);
					$dialog->run;
					$dialog->destroy;
					$password_ok='passw_fail';
				}else{
					$password_ok='passw_ok';

					my $target = $products[$index]->get_name();
					if ($target ne "none"){
						my $init_file = $products[$index]->get_init_file();
						if ($init_file) {
							if ($init_file ne "") {
								my $cmd_str = "$install_dir$init_file";
								system($cmd_str);
							}
						}
						my $result = enter_prod_info($controll);
						if ($result ne "info_ok") {
							$password_ok='passw_fail';
						}
					}
				}
			}

			if($_[1] =~ m/reject/){
				$password_ok='passw_fail';
			}
		}
	);

	$passwd_dialog->show_all;
	$passwd_dialog->run;
	$passwd_dialog->destroy;

	return $password_ok;
}

my $SELECT_MODE = "manual";
{

	package Migrator;
	use Data::Dumper;
	use Glib qw(FALSE);
	use Gtk2 -init;


	sub new {
		my ( $class, $id, $name, $product_name ) = @_;
		my $self = {};
		$self->{ID}             = $id;
		$self->{_NAME}          = $name;
		$self->{_PRODUCT}		= undef;
		$self->{_PRODUCT_COMBO} = Gtk2::ComboBox->new_text();
		$self->{_PRODUCT_DESC}  = Gtk2::Label->new("Description ");
		$self->{_SERIAL_COMBO}  = Gtk2::ComboBox->new_text();
		$self->{_MAC_LABEL}     = Gtk2::Label->new("xx:xx:xx:xx:xx:xx");
		$self->{_PROGRESS}      = Gtk2::ProgressBar->new();
		$self->{_RESULT_LABEL}  = Gtk2::Label->new('');
		$self->{_RESULT_LABEL}->set_markup('<span foreground="black" size="xx-large"><b>Idle</b></span>');
		$self->{_RESULT_LABEL}->set_size_request(180, 32);
		$self->{_RESULT_LABEL}->set_alignment(0.0, 0.0);
		$self->{_START}         = Gtk2::Button->new_with_label(' Start ');
		$self->{_TEXTVIEW}      = Gtk2::TextView->new();
		$self->{_OUTPUTBUFFER}  = $self->{_TEXTVIEW}->get_buffer();
		$self->{SELECT_MODE}   = 'auto';
		$self->{LAST_SELECTED_TARGET}  = 0;
		$self->{_VIEW}        = undef;
		$self->{_OUTPUTVIEW}  = undef;
		$self->{_INITIALIZED} = 0;
		$self->{_BUSY}        = 0;
		$self->{_CHILD_PID}	  = 0;
		$self->{_PRODUCT_NAME}	  = $product_name;

		$self->{_START_TIME} = 0;
		$self->{_END_TIME}   = 0;

		$self->{PROGRAMMEDMAC} = "";

		bless( $self, $class );
		return $self;
	}


	sub set_auto{
		$SELECT_MODE = 'auto';
	}


	sub set_manual{
		$SELECT_MODE = 'manual';
	}


	sub initialize {
		my $self = shift;
		if ( $self->{_INITIALIZED} == 0 ) {
			$self->set_products(@products);
			$self->set_ttys(@ttys);

			$self->{_START}->set_focus_on_click(FALSE);
			$self->{_START}->signal_connect( 'clicked', \&Migrator::_start, $self );

			my $hbox = Gtk2::HBox->new( FALSE, 5 );
			$hbox->set_border_width(5);

			if ($indsel) {
				$hbox->pack_start( $self->{_PRODUCT_COMBO}, 0, 0, 0 );
			}
			if ($usetty) {
				$hbox->pack_start( $self->{_SERIAL_COMBO},  0, 0, 0 );
			}

			my $product = $self->{_PRODUCT_COMBO}->get_active_text();
			my $p = ::find_product_by_name(\@products, $self->{_PRODUCT_NAME});

			#			if ($p) {
			#				if($p->get_use_barcode()) {
			$hbox->pack_start( $self->{_MAC_LABEL},     0, 0, 0 );

			#				}
			#			}

			$hbox->pack_start( $self->{_PROGRESS},      1, 1, 0 );
			$hbox->pack_start( $self->{_START},         0, 0, 0 );

			my $frame = Gtk2::Frame->new( ' ' . $self->{_NAME} . ' ' );
			$frame->add($hbox);
			$frame->set_border_width(5);
			$self->{_VIEW} = $frame;

			# output view
			$self->{_TEXTVIEW}->set_editable(0);
			$self->{_ENDMARK} =$self->{_OUTPUTBUFFER}->create_mark( 'end', $self->{_OUTPUTBUFFER}->get_end_iter,FALSE );
			$self->{_OUTPUTBUFFER}->signal_connect(
				'insert_text' => \&Migrator::_autoscroll,
				$self
			);

			$self->{_OUTPUTVIEW} = Gtk2::ScrolledWindow->new();
			$self->{_OUTPUTVIEW}->add( $self->{_TEXTVIEW} );

			$self->{_PRODUCT_COMBO}->signal_connect(
				'changed',
				sub{
					if ( $self->{SELECT_MODE} ne 'self'){

						if ($SELECT_MODE eq 'manual'){
							my $passw_result = ::check_password_dialog($self->{_PRODUCT_COMBO});

							if ( $passw_result eq 'passw_ok'){
								$self->{LAST_SELECTED_TARGET}  = $self->{_PRODUCT_COMBO}->get_active;
							}
							if ( $passw_result eq "passw_fail"){
								$self->{SELECT_MODE} = 'self';
								$self->select_product($self->{LAST_SELECTED_TARGET} );
							}
						}else {
							$self->{LAST_SELECTED_TARGET}  = $self->{_PRODUCT_COMBO}->get_active;
						}
					}else{
						$self->{SELECT_MODE} = 'auto';
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
			$cfg->set('slot.'.$self->{ID}.'.product', $self->{_PRODUCT_COMBO}->get_active_text());
		}else {

			# TODO: find a product by given name and activate it
		}
	}


	sub get_view {
		my $self = shift;
		if ( !defined $self->{_VIEW} ) {
			$self->initialize();
		}

		return $self->{_VIEW};
	}


	sub get_outputview {
		my $self = shift;
		if ( !defined $self->{_OUTPUTVIEW} ) {
			$self->initialize();
		}
		return $self->{_OUTPUTVIEW};
	}


	sub append_output {
		my $self = shift;
		my $text = shift;

		$self->{_OUTPUTBUFFER}->insert( $self->{_OUTPUTBUFFER}->get_end_iter, $text );
	}


	sub _autoscroll {
		my $buffer = shift;
		shift;
		shift;
		shift;
		my $self = shift;
		$self->{_TEXTVIEW}->scroll_to_iter( $buffer->get_end_iter, 0.0, 0, 0.0, 0.0 );
	}


	sub _start {
		my $button = shift;
		my $this   = shift;

		$this->start();
		return TRUE;
	}


	sub _progress_timeout {
		my $self = shift;

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
		my $devid   = $self->{_DEVICE_ID};

		my $p = $self->{_PRODUCT};
		$self->{_BUSY} = 1;
		$self->{_CHILD_PID} = $child_pid;

		$self->{_RESULT_LABEL}->set_markup('<span background="darkgrey" foreground="yellow" size="xx-large"><b>Working....</b></span>');
		$self->{_PROGRESS}->modify_bg('normal', $color_running);
		$self->{_PROGRESS}->modify_bg('prelight', $color_running);
		$self->{_PROGRESS}->modify_bg('active', $color_running);
		$self->append_output("\n--------[STARTED: $cmd]\n");
		@controls =
		  ( $self->{_START}, $self->{_PRODUCT_COMBO}, $self->{_SERIAL_COMBO} );
		foreach (@controls) {
			$_->set_sensitive(0);
		}

		my $black = Gtk2::Gdk::Color->new(0,0,0);
		$self->{_PROGRESS}->modify_fg('normal', $black);

		$self->{_TIMER} =Glib::Timeout->add( 200, \&Migrator::_progress_timeout, $self );
		$self->{_START_TIME} = time();
	}


	sub __migration_step {
		my ( $self, $data ) = @_;
		$self->append_output($data);
		if ($data =~ /^=== (\d+) .*$/m) {
			my $progress = $1;
			if ($progress == 100){
				$self->{PROGRAMMEDMAC} = "";
				print("pipe data ->> ".$data." <<- ");
				if ($data =~ /^=== (\d+) (\S{2}\:\S{2}\:\S{2}) Completed with MAC0: (\S{2}\:\S{2}\:\S{2}\:\S{2}\:\S{2}\:\S{2}).*$/m){
					print "MAC found\n";

					$self->{PROGRAMMEDMAC} = " MAC ".$3;#." ".$3." ".$4." ".$5." ".$6." ".$7;

					my $detected_mac = "unknown";
					if ($data =~ /Completed with MAC0: (\S{2}\:\S{2}\:\S{2}\:\S{2}\:\S{2}\:\S{2}).*$/m) {
						$detected_mac = $1;
					}

					$self->{_MAC_LABEL}->set_label($detected_mac);

					$self->{_DONE} = $progress;
				}
			}else{
				$self->{_DONE} = $progress;
			}
		}
	}


	sub __migration_ended {
		my $self   = shift;
		my $status = shift;
		$self->{_END_TIME} = time();
		@controls =
		  ( $self->{_START}, $self->{_PRODUCT_COMBO}, $self->{_SERIAL_COMBO} );
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

		my $red = Gtk2::Gdk::Color->new(0xFFFF,0,0);
		my $green = Gtk2::Gdk::Color->new(0,0x8000,0);

		my $msg = "";
		if ( $status == 0 ) {
			$self->{_RESULT_LABEL}->set_markup('<span background="darkgrey" foreground="green" size="xx-large"><b>PASS</b></span>');
			$self->{_PROGRESS}->modify_bg('normal', $color_pass);
			$self->{_PROGRESS}->modify_bg('prelight', $color_pass);
			$self->{_PROGRESS}->modify_bg('active', $color_pass);
			$msg = "Completed in $duration_str.";
		}else {
			$self->{_RESULT_LABEL}->set_markup('<span background="darkgrey" foreground="red" size="xx-large"><b>FAIL</b></span>');
			$self->{_PROGRESS}->modify_bg('normal', $color_fail);
			$self->{_PROGRESS}->modify_bg('prelight', $color_fail);
			$self->{_PROGRESS}->modify_bg('active', $color_fail);
			$msg = "FAILED with error code $status after $duration_str.";
		}
		$self->{_PROGRESS}->set_text($msg);
		$self->append_output("\n--------[$msg\n");
	}


	sub check_mac_addr {
		my $text = shift;
		$text = substr($text, -$macstr_len);

		if (length($text)<$macstr_len){
			return FALSE;
		}

		if ($text =~ /[^0-9a-fA-F]/){
			return FALSE;
		}else{
			return TRUE;
		}
	}


	sub check_mac_addr_up {
		my $text = shift;

		if (length($text)<$macstr_len){
			return 0;
		}

		if ($text =~ /[^0-9A-F]/){
			return 0;
		}else{
			return 1;
		}
	}


	sub input_barcode {
		my $mac_addr = "";
		my $barcode = "";
		my $mac_check_status = 1;

		my $mac_label = Gtk2::Label->new("------------");

		my $mac_edit = Gtk2::Entry->new();
		$mac_edit->set_visibility(TRUE);
		$mac_edit->set_activates_default(TRUE);


		my $title = 'Waiting for barcode...';

		my $dialog = Gtk2::Dialog->new(
			$title, $window,
			[qw/modal destroy-with-parent/],
			'gtk-ok'     => 'ok',
			'gtk-cancel'     => 'cancel'
		);
		$dialog->set_default_response('ok');
		$dialog->vbox->add(Gtk2::Label->new($title));
		$dialog->vbox->add($mac_label);
		$dialog->vbox->add($mac_edit);

		$mac_edit->signal_connect(
			changed => sub {
				$barcode = $mac_edit->get_text;
			}
		);


		$dialog->signal_connect(
			response => sub{
				if($_[1] =~ m/ok/){

					chomp($barcode);

					if (!check_mac_addr($barcode)){

						my $parent = $window;
						my $dialog = Gtk2::MessageDialog->new(
							$parent, 'modal',
							'error',     # message type
							'close',    # set of buttons
							"MAC address invalid"
						);
						my $response = $dialog->run;
						$dialog->destroy;
						$mac_check_status = 0;
					}

					$mac_addr = substr($barcode, -$macstr_len);
					print "\nmac_addr = $mac_addr\n";
				}

				if($_[1] =~ m/cancel/){
					print "\ncanceled\n";
					$dialog->destroy;
					$mac_check_status = 0;
				}

			}
		);

		$dialog->show_all;
		$dialog->run;
		$dialog->destroy;

		if (!$mac_check_status) {
			return "";
		}

		return $mac_addr;
	}


	sub check_qr_field {
		my ($field, $type, $len) = @_;

		my ($id, $data) = split(/:/,$field);

		my $data_len = length $data;
		if ($id ne $type) {
			return 0;
		}
		if ($data_len != $len) {
			return 0;
		}

		if ($type eq "MAC") {
			return check_mac_addr_up($data);
		}

		if ( $data =~ /^[a-zA-Z0-9\s]{1,$len}$/i ) {
			return 1;
		}

		return 0;
	}


	sub check_qr_code {
		my $text = shift;
		my $mac_len = 6;
		my $pswd_len = 8;
		my $wpa_len = 11;

		my ($MAC, $PSWD, $WPA2) = split(/\n/,$text);

		my $check_result = 0;
		$check_result = check_qr_field($MAC, 'MAC',12);
		if ($check_result == 0) {
			return $check_result;
		}
		$check_result = check_qr_field($PSWD,'PSWD',8);
		if ($check_result == 0) {
			return $check_result;
		}
		$check_result = check_qr_field($WPA2,'WPA2',11);
		if ($check_result == 0) {
			return $check_result;
		}

		return 1;
	}


	sub make_qr_param {
		my $text = shift;

		my ($MAC, $PSWD, $WPA2) = split(/\n/,$text);

		my ($mac_id, $mac_data) = split(/:/,$MAC);
		my ($pswd_id, $pswd_data) = split(/:/,$PSWD);
		my ($wpa2_id, $wpa2_data) = split(/:/,$WPA2);

		return "$mac_data:$pswd_data:$wpa2_data";
	}


	sub input_qrcode {
		my $qrcode = "";
		my $qr_check_status = 1;

		my $mac_val = "";
		my $pswd_val = "";
		my $wpa2_val = "";

		my $qr_edit1 = Gtk2::Entry->new();
		$qr_edit1->set_visibility(TRUE);
		$qr_edit1->set_activates_default(TRUE);
		$qr_edit1->set_has_frame(FALSE);

		my $qr_edit2 = Gtk2::Entry->new();
		$qr_edit2->set_visibility(TRUE);
		$qr_edit2->set_activates_default(TRUE);
		$qr_edit2->set_has_frame(FALSE);

		my $qr_edit3 = Gtk2::Entry->new();
		$qr_edit3->set_visibility(TRUE);
		$qr_edit3->set_activates_default(TRUE);
		$qr_edit3->set_has_frame(FALSE);


		my $title = 'Waiting for QR code...';

		my $frame = Gtk2::Frame->new($title);


		my $dialog = Gtk2::Dialog->new(
			$title, $window,
			[qw/modal destroy-with-parent/],
			'gtk-ok'     => 'ok',
			'gtk-cancel'     => 'cancel'
		);
		$dialog->set_default_response('ok');


		$vbox = Gtk2::VBox->new(FALSE, 0);
		$vbox->add($qr_edit1);
		$vbox->add($qr_edit2);
		$vbox->add($qr_edit3);

		$frame->add($vbox);

		$dialog->vbox->add($frame);

		$qr_edit1->grab_focus;

		$qr_edit1->signal_connect(
			changed => sub {
				my $text_val = $qr_edit1->get_text();
				my ($mac_val_tmp, $pswd_val_tmp, $wpa2_val_tmp) = split(/\n/,$text_val);

				if ($mac_val_tmp ne "") {
					$qr_edit1->set_text($mac_val_tmp);
				}
				$mac_val = $qr_edit1->get_text();

				if ($pswd_val_tmp ne "") {
					$qr_edit2->grab_focus();
					$qr_edit2->set_text($pswd_val_tmp);
				}

				if ($wpa2_val_tmp ne "") {
					$qr_edit3->grab_focus();
					$qr_edit3->set_text($wpa2_val_tmp);
				}
			}
		);

		$qr_edit2->signal_connect(
			changed => sub {
				$pswd_val = $qr_edit2->get_text();
			}
		);

		$qr_edit3->signal_connect(
			changed => sub {
				$wpa2_val = $qr_edit3->get_text();
			}
		);

		$dialog->signal_connect(
			response => sub{
				if($_[1] =~ m/ok/){

					$qrcode="$mac_val\n$pswd_val\n$wpa2_val\n";

					chomp($qrcode);

					if (check_qr_code($qrcode) != 1){

						my $parent = $window;
						my $dialog = Gtk2::MessageDialog->new(
							$parent, 'modal',
							'error',     # message type
							'close',    # set of buttons
							"QR code invalid"
						);
						my $response = $dialog->run;
						$dialog->destroy;
						$qr_check_status = 0;
					}
				}

				if($_[1] =~ m/cancel/){
					$dialog->destroy;
					$qr_check_status = 0;
				}

			}
		);

		$dialog->show_all;
		$dialog->run;
		$dialog->destroy;

		if (!$qr_check_status) {
			return "";
		}

		return $qrcode;
	}


	sub start {
		my $self = shift;

		my $tty     = $self->{_SERIAL_COMBO}->get_active_text();
		my $product = $self->{_PRODUCT_COMBO}->get_active_text();
		my $id      = $self->{ID};

		my $p = ::find_product_by_name(\@products, $product);
		$self->{_PRODUCT} = $p;

		my $mac_addr = "";
		my $barcode = "";

		my $mac_txt_label = "00:00:00:00:00:00";
		my $qr_code = "";

		my $need_barcode = $p->get_use_barcode();
		my $need_qrcode = $p->get_use_qrcode();
		if ($use_barcode_overide != undef) {
			if (($use_barcode_overide == 0) || ($use_barcode_overide == 1 )) {
				$need_barcode = $use_barcode_overide;
			}
		}

		if ($use_qrcode_overide != undef) {
			if (($use_qrcode_overide == 0) || ($use_qrcode_overide == 1 )) {
				$need_qrcode = $use_qrcode_overide;
			}
		}

		if (($need_barcode) or ($need_qrcode)) {
			if ($need_barcode) {
				$mac_addr = input_barcode();
			} elsif ($need_qrcode) {
				$qr_code = input_qrcode();
				if ($qr_code ne "") {
					$qr_code = make_qr_param($qr_code);
				}
				$mac_addr = substr($qr_code, 0, $macstr_len);
			}
			if ($mac_addr eq "") {
				return FALSE;
			}

			$mac_txt_label = substr($mac_addr,0,2).":".substr($mac_addr,2,2).":".substr($mac_addr,4,2).":".substr($mac_addr,6,2).":".substr($mac_addr,8,2).":".substr($mac_addr,10,2);

			$self->{_MAC_LABEL}->set_label($mac_txt_label);
		}


		#
		# ID is used for IP address generation in production script
		# so we should be very careful with it, we should support as
		# many serial ports as possible
		#
		if ( $tty =~ /^ttyUSB(\d+)$/ ) {
			$id = $1;
		}elsif ( $tty =~ /^ttyS(\d+)$/ ) {
			$id = $1 + 50;
		}else {
			$id += 100;
		}
		$self->{_DEVICE_ID} = $id;


		my ($sec,$min,$hour,$mday,$mon,$year, $wday,$yday,$isdst) = localtime time;
		$year += 1900;
		$mon += 1;

		my $target_name = $p->get_name();
		$target_name =~ s/\//\-/g;

		my $directory = $log_directory.'/'.$target_name;

		if (not -e $directory) {
			system "mkdir ".$directory;
		}

		my $temp_file = ''.$directory.'/'.$sec.$min.$hour.rand(200).'.log';

		system "stty -F /dev/$tty speed 115200";

		my @scr_params = split(/ /,$p->get_script_params());

		my $cmd = $p->get_script();

		my $bom_rev = "";
		if ($p->get_use_fullbom()) { #split bom into two variables (required on 32 bit system)
			$bom_rev = $hw_revision + ($hw_dev_id << 8);
			$bom_rev = "$bom_rev $hw_pref";
		}else {
			$bom_rev = "$hw_revision";
		}

		my $bom_string = "$hw_pref-$hw_dev_id-$hw_revision";

		#		tty target idx pass bomrev ssid keys mac srvip

		foreach (@scr_params) {
			given ($_) {
				when('tty') {$cmd.= ' '.$tty}
				when('target') {$cmd.= ' '.$p->get_name()}
				when('idx') {$cmd.= ' '.$id}
				when('passwd') {$cmd.= ' '.$pass_phrase}
				when('bomrev') {$cmd.= ' '.$bom_rev}
				when('ssid') {$cmd.= ' '.lc($selected_product)}
				when('keys') {$cmd.= ' '.$log_directory."/keys"}
				when('dfs') {$cmd.= ' '.'1'}
				when('mac') {$cmd.= ' '.$mac_txt_label}
				when('qrcode') {$cmd.= ' '.$qr_code;}
				when('srvip') {$cmd.= ' '.$host_ip}
				when('devip') {$cmd.= ' '.$target_ip}
				when('model_string') {$cmd.= ' '.$model_string}
				when('bom_string') {$cmd.= ' '.$bom_string}
			}
		}

		print "".$cmd."\n";

		::log_debug('Opening pipe to \'' . $cmd . '\'');
		my $child_pid = open my $pipe, "$cmd |";
		$self->__migration_started($child_pid, $cmd);

		Glib::IO->add_watch(
			fileno $pipe,
			[ 'in', 'hup' ],
			sub {
				my ( $fd, $condition ) = @_;
				if ( $condition >= 'in' ) {
					my $data;
					my $nread = sysread( $pipe, $data, 160 );

					system 'echo -n "'.$data.'" >> '.$temp_file;
					$self->__migration_step($data);
				}
				if ( $condition >= 'hup' ) {
					my $data;

					while (sysread( $pipe, $data, 160 )){
						system 'echo -n "'.$data.'" >> '.$temp_file;
						$self->__migration_step($data);
					}
					close $pipe;
					$self->__migration_ended($?);

					while ($log_file_locked) #wait for log file unlock
					{
					}
					$log_file_locked = TRUE;

					my $prefix = lc $selected_short_name;
					$prefix =~ s/ /_/g;
					my $log_file = ''.$directory.'/' . $prefix ."-".$year.'-'.$mon.'-'.$mday.'.log';

					print "log file - $log_file\n";

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
			$message ="\n There are jobs in progress -\nAre you sure you want to exit?";
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
	my $response = $dialog->run;
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
	my $info;

	foreach (@products) {

		my $p = "\n" . uc($_->get_name()) . ': ' . $_->get_firmware_version();
		if ( $_->get_name() ne "none" ){
			$info .= $p."\n";
			my $name = $_->get_name();

			my @files = </tftpboot/$name*fw.bin>;
			foreach my $file (@files) {

				my ($buf, $data, $n);

				open FILE, $file or next;

				my @fw_name = split('/',$file);

				$info .= $fw_name[2];

				if (($n = read FILE, $data, 80) != 0) {

					my $first = substr($data, 0, 1);
					$first =~ s/[\x00-\x08\x0B-\x1F\x7F-\xFF]//g;

					if ($first ne "") {
						$data =~ s/[\x00-\x08\x0B-\x1F\x7F-\xFF]//g;
						$info .= " - ".$data;
					}

				}

				$info .= "\n";
				close FILE;
			}
		}
	}


	my $textbuffer = Gtk2::TextBuffer->new();
	$textbuffer->set_text($info);

	my $textview = Gtk2::TextView->new_with_buffer($textbuffer);

	my $dialog = Gtk2::MessageDialog->new_with_markup(
		$parent,
		'modal',
		'info',    # message type
		'ok',      # which set of buttons?
		"<b>Factory $_VERSION</b>\n(c) 2006 - 2014 Ubiquiti Networks, Inc."
	);

	my $frame = Gtk2::Frame->new(' Contains firmwares ');
	$frame->add($textview,);
	$frame->set_border_width(10);

	$dialog->vbox->add($frame);

	$dialog->signal_connect(response => sub { $_[0]->destroy });

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


sub create_controls {
	my $hbox = Gtk2::HBox->new( FALSE, 5 );
	$hbox->set_border_width(5);


	my $auth = FALSE;
	$hbox->set_border_width(5);
	my $selection = 'manual';

	my $l = Gtk2::Label->new("Product (for all slots): ");
	my $p = Gtk2::ComboBox->new_text();
	my $inf = Gtk2::Label->new("Flavor: ");
	my $d = Gtk2::Label->new("PD ");

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
	$script = $products[0]->get_script();

	foreach (@migrators) {
		$_->set_auto;
		$_->select_product(0);
		$_->set_manual;
	}
	$cfg->set('common.product', $p->get_active_text);

	$p->signal_connect(
		'changed',
		sub {
			if ($selection eq 'manual'){
				$selected_name = "";
				my $passw_result = &check_password_dialog($p);
				if ( $passw_result eq 'passw_ok'){
					my $index = $p->get_active;
					$d->set_text($products[$index]->get_description().$selected_name);
					$script = $products[$index]->get_script();

					print "$script \n";

					foreach (@migrators) {
						my $slot = $_->get_view();
						$contents->remove($slot);
					}
					my $i = 0;
					for ($i = $output_tabs->get_n_pages(); $i >= 0; $i--) {
						$output_tabs->remove_page($i);
					}
					$window->show_all;

					print "$portcnt\n";
					for ( $i = 0 ; $i < $portcnt ; ++$i ) {
						my $name = 'Slot ' . ( $i + 1 );
						my $migrator = Migrator->new( $i, $name, $p->get_active_text );
						push @migrators, $migrator;
						my $slot = $migrator->get_view();
						$contents->pack_start( $slot, 0, 0, 0 );
						$output_tabs->append_page( $migrator->get_outputview(), $name );
					}
					$window->show_all;

					my @serials = ::collect_serials;

					foreach (@migrators) {
						$_->set_auto;
						$_->select_product($index);
						$_->set_manual;
						$_->set_ttys(@serials);
					}
					$cfg->set('common.product', $p->get_active_text);
					$last_selected_target = $index;
					$window->show_all;
				}
				if ( $passw_result eq "passw_fail"){
					$selection  ='auto';
					$p->set_active($last_selected_target);
					$selection = 'manual';

				}
			}else{
				$selection = 'manual';
			}

		}
	);


	$hbox->pack_start( $l, 0, 0, 0 );
	$hbox->pack_start( $p, 0, 0, 0 );
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
	my @lines = `ls -ls /dev/disk/by-id| grep usb-`;

	my $device;

	#searching for usb storage mount point
	foreach my $line (@lines) {

		my @dev = split('/',$line);
		$device = ''.$dev[-1];
		my $procMountFile = '/proc/mounts';

		# Open the proc mount file
		open(FILE,"$procMountFile");
		while (<FILE>){
			my $line = "$_";

			if (grep { /$device* /} $line){
				my @tags = split(' ',$line);
				if ($tags[1] && ($tags[1] ne "/cdrom" ) ){
					$log_directory = $tags[1];
					print "Found storage at ".$log_directory."\n";
					close(FILE);
					return 1;
				}
			}
		}
		close(FILE);
	}
	print "No USB storage found";
	return 0;
}


my $initializer;


sub initialize {
	my $msg = ' Initializing production environment - please wait...';

	my $parent = $window;
	my $dialog =Gtk2::MessageDialog->new( $parent, 'modal', 'info', 'none', $msg );

	open my $pipe, "$setup_script |";
	Glib::IO->add_watch(
		fileno $pipe,
		['hup'],
		sub {
			my ( $fd, $condition ) = @_;
			if ( $condition >= 'hup' ) {
				close $pipe;
				$dialog->response(0);
				return FALSE;
			}
			return TRUE;
		}
	);

	$dialog->run();
	$dialog->destroy;

	if (!find_usb_storage()){
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

	if ($usetty==1) {
		my @serials = collect_serials;
		foreach (@migrators) {
			$_->set_ttys(@serials);
		}
	}

	$initialized = TRUE;
	Glib::Source->remove($initializer);
	return FALSE;
}


sub default_products {
	my @list;
	my $product = Product->new(1, 'none');
	$product->set_description('No product');
	push @list, $product;
	return @list;
}


sub load_cfg {
	my $product;
	my @list;

	my $pcfg = Configuration->new();

	$product = Product->new($0, "none");
	$product->set_description("No product");
	$product->set_script("none");
	push @list, $product;


	# TODO: add support for product loading from USB flash
	if ($pcfg->load($products_file)) {
		$portcnt = $pcfg->get('portcnt');
		$appname = $pcfg->get('appname');
		$usetty = $pcfg->get('usetty');
		$indsel = $pcfg->get('indsel');

		for (my $i = 1; $i < 10; $i++) {
			my $name = $pcfg->get('product.'.$i.'.name');
			last if (!defined $name);

			my $desc = $pcfg->get('product.'.$i.'.description');
			my $scr = $pcfg->get('product.'.$i.'.script');
			my $scr_par = $pcfg->get('product.'.$i.'.script_params');
			my $req_barcode = $pcfg->get('product.'.$i.'.barcode');
			my $req_qrcode = $pcfg->get('product.'.$i.'.qrcode');
			my $req_full_bom = $pcfg->get( 'product.' . $i . '.fullbom' );
			my $ssid_file = $pcfg->get( 'product.' . $i . '.ssid_file' );

			if ($ssid_file) {

				if ($ssid_file ne "") {
					$product_ssid_file = $ssid_file;
				}
			}
			my $init_file = $pcfg->get( 'product.' . $i . '.init_file' );
			$product = Product->new($i, $name);
			$product->set_description($desc);
			$product->set_script($scr);
			$product->set_script_params($scr_par);
			$product->set_req_barcode($req_barcode);
			$product->set_req_qrcode($req_qrcode);
			$product->set_req_fullbom($req_full_bom);
			$product->set_init_file($init_file);

			push @list, $product;
		}
	} else {
		push @list, default_products();
	}

	return @list;
}


sub parse_params {
	if ( @ARGV > 0 ) {
		$host_ip = $ARGV[0];
		print "Got option Host IP: $host_ip\n";

	}
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

push @products, load_cfg();

parse_params();

my $menubar     = create_menubar();
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

$window->set_title($appname.'[' . $_VERSION . '  ]');
$window->modify_bg('normal', $greyl);
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

