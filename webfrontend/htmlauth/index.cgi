#!/usr/bin/perl

use LoxBerry::Web;
use CGI;
#require "$lbpbindir/libs/LoxBerry/JSON/JSONIO.pm";

my $cfgfile = "$lbpconfigdir/mqtt.json";

my $cgi = CGI->new;
my $q = $cgi->Vars;

my %pids;

my $template;

if( $q->{ajax} ) {
	
	## Handle all ajax requests 
	
	require JSON;
	my %response;
	ajax_header();
	if( $q->{ajax} eq "getpids" ) {
		pids();
		$response{pids} = \%pids;
		print JSON::encode_json(\%response);
	}
	if( $q->{ajax} eq "restartgateway" ) {
		pkill('mqttgateway.pl');
		`cd $lbpbindir ; $lbpbindir/mqttgateway.pl > /dev/null 2>&1 &`;
		pids();
		$response{pids} = \%pids;
		print JSON::encode_json(\%response);
	}
	if( $q->{ajax} eq "relayed_topics" ) {
		my $datafile = "/dev/shm/mqttgateway_topics.json";
		print LoxBerry::System::read_file($datafile);
	}
	exit;

} else {
	
	## Normal request (not ajax)
	
	# Init template
	
	$template = HTML::Template->new(
		filename => "$lbptemplatedir/mqtt.html",
		global_vars => 1,
		loop_context_vars => 1,
		die_on_bad_params => 0,
	);
	
	
	# Push json config to template
	
	my $cfgfilecontent = LoxBerry::System::read_file($cfgfile);
	$cfgfilecontent =~ s/[\r\n]//g;
	$template->param('JSONCONFIG', $cfgfilecontent);
	
	
	# Switch between forms
	
	if( !$q->{form} or $q->{form} eq "settings" ) {
		$navbar{10}{active} = 1;
		$template->param("FORM_SETTINGS", 1);
		settings_form(); 
	}
	elsif ( $q->{form} eq "subscriptions" ) {
		$navbar{20}{active} = 1;
		$template->param("FORM_SUBSCRIPTIONS", 1);
		subscriptions_form();
	}
	elsif ( $q->{form} eq "conversions" ) {
		$navbar{30}{active} = 1;
		$template->param("FORM_CONVERSIONS", 1);
		conversions_form();
	}
	elsif ( $q->{form} eq "topics" ) {
		$navbar{40}{active} = 1;
		$template->param("FORM_TOPICS", 1);
		$template->param("FORM_DISABLE_BUTTONS", 1);
		$template->param("FORM_DISABLE_JS", 1);
		topics_form();
	}
	elsif ( $q->{form} eq "logs" ) {
		$navbar{90}{active} = 1;
		$template->param("FORM_LOGS", 1);
		$template->param("FORM_DISABLE_BUTTONS", 1);
		$template->param("FORM_DISABLE_JS", 1);
		logs_form();
	}
}

print_form();

exit;

######################################################################
# Print Form
######################################################################
sub print_form
{
	my $plugintitle = "MQTT Gateway v" . LoxBerry::System::pluginversion();
	my $helplink = "https://www.loxwiki.eu/x/S4ZYAg";
	my $helptemplate = "help.html";
	
	our %navbar;
	$navbar{10}{Name} = "Settings";
	$navbar{10}{URL} = 'index.cgi';
 
 	$navbar{20}{Name} = "Subscriptions";
	$navbar{20}{URL} = 'index.cgi?form=subscriptions';
 
	$navbar{30}{Name} = "Conversions";
	$navbar{30}{URL} = 'index.cgi?form=conversions';
 
 	$navbar{40}{Name} = "Incoming overview";
	$navbar{40}{URL} = 'index.cgi?form=topics';
 
	$navbar{90}{Name} = "Logfiles";
	$navbar{90}{URL} = 'index.cgi?form=logs';
		
	LoxBerry::Web::lbheader($plugintitle, $helplink, $helptemplate);

	print $template->output();

	LoxBerry::Web::lbfooter();


}


########################################################################
# Settings Form 
########################################################################
sub settings_form
{

	my $mslist_select_html = LoxBerry::Web::mslist_select_html( FORMID => 'Main.msno', LABEL => 'Miniserver to relay to' );
	$template->param('mslist_select_html', $mslist_select_html);

}

########################################################################
# Subscriptions Form 
########################################################################
sub subscriptions_form
{

	# Nothing in here, everything JS

}

########################################################################
# Conversions Form 
########################################################################
sub conversions_form
{

	# Nothing in here, everything JS

}

########################################################################
# Topics Form 
########################################################################
sub topics_form
{

	require "$lbpbindir/libs/LoxBerry/JSON/JSONIO.pm";
	require POSIX;
	
	my $datafile = "/dev/shm/mqttgateway_topics.json";
	my $relayjsonobj = LoxBerry::JSON::JSONIO->new();
	my $relayjson = $relayjsonobj->open(filename => $datafile);
	
	
	# HTTP
	my $http_table, $http_count = 0;
	$http_table .= qq { <table class="topics_table"> };
	$http_table .= qq { <tr> };
	$http_table .= qq { <th>Miniserver Virtual Input</th> };
	$http_table .= qq { <th>Last value</th> };
	$http_table .= qq { <th>Last submission</th> };
	$http_table .= qq { </tr> };
	
	foreach my $topic (sort keys %{$relayjson->{http}}) {
		$http_count++;
		$http_table .= qq { <tr> };
		$http_table .= qq { <td>$topic</td> };
		$http_table .= qq { <td>$relayjson->{http}{$topic}{message}</td> };
		$http_table .= qq { <td> } . POSIX::strftime('%d.%m.%Y %H:%M:%S', localtime($relayjson->{http}{$topic}{timestamp})) . qq { </td> };
		$http_table .= qq { </tr> };
	}
	$http_table .= qq { </table> };
	
	$template->param("http_table", $http_table);
	$template->param("http_count", $http_count);
	
	
	# UDP
	my $udp_table, $udp_count = 0;
	$udp_table .= qq { <table class="topics_table"> };
	$udp_table .= qq { <tr> };
	$udp_table .= qq { <th>Miniserver UDP</th> };
	#$udp_table .= qq { <th>Last value</th> };
	$udp_table .= qq { <th>Last submission</th> };
	$udp_table .= qq { </tr> };
	
	foreach my $topic (sort keys %{$relayjson->{udp}}) {
		$udp_count++;
		$udp_table .= qq { <tr> };
		$udp_table .= qq { <td>MQTT: $topic=$relayjson->{udp}{$topic}{message}</td> };
		# $udp_table .= qq { <td>$relayjson->{udp}{$topic}{message}</td> };
		$udp_table .= qq { <td> } . POSIX::strftime('%d.%m.%Y %H:%M:%S', localtime($relayjson->{udp}{$topic}{timestamp})) . qq { </td> };
		$udp_table .= qq { </tr> };
	}
	$udp_table .= qq { </table> };
	
	$template->param("udp_table", $udp_table);
	$template->param("udp_count", $udp_count);
	
	
}


########################################################################
# Logs Form 
########################################################################
sub logs_form
{

	$template->param('loglist_html', loglist_html());

}



######################################################################
# AJAX functions
######################################################################

sub pids 
{
	
	$pids{'mqttgateway'} = trim(`pgrep mqttgateway.pl`) ;
	$pids{'mosquitto'} = trim(`pgrep mosquitto`) ;

}	

sub pkill 
{
	my ($process) = @_;
	return `pkill --signal SIGTERM $process`;

}	
	
sub ajax_header
{
	print $cgi->header(
			-type => 'application/json',
			-charset => 'utf-8',
			-status => '200 OK',
	);	
}	
	
	
