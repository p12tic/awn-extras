#!/usr/bin/perl

use Net::DBus;

Xchat::register( "Awn plugin", "0.1", "", "" );

Xchat::EAT_XCHAT;
Xchat::hook_print('Channel Action', \&message);
Xchat::hook_print('Channel Action Hilight', \&message);
Xchat::hook_print('Channel Message', \&message);
Xchat::hook_print('Channel Msg Hilight', \&message);

Xchat::hook_print('Focus Window', \&active);

my $bus = Net::DBus->find;
my $awn = $bus->get_service("com.google.code.Awn");
my $manager = $awn->get_object("/com/google/code/Awn", "com.google.code.Awn");

$i = 0;
$nick = '';

sub active {
	$i = 0;
	eval {
		$manager->SetInfoByName(xchat, "$nick($i)");
	};
	if ($@ =~ /ServiceUnknown/) {
		sleep 10;
		return 0;
	}
}

sub message {
	$nick = $_[0][0];
	$status = Xchat::get_info(win_status);
	if ($status ne "active") {
		$i++;
	}
	else {
		$i = 0;
	}
	eval {
		$manager->SetInfoByName(xchat, "$nick($i)");
	};
	if ($@ =~ /ServiceUnknown/) {
		sleep 10;
		return 0;
	}
}

