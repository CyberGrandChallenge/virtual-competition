% TI-ROTATE(1) Cyber Grand Challenge Manuals
% Chris Eagle <cseagle@nps.edu>
% April 18, 2015

# NAME

ti-rotate - CGC CFE round simulator; part of Virtual Competiton.  Meant to populate data that ti-server will make available.

# SYNOPSIS

ti-rotate [-h] --roundlen ROUNDLEN [--debug] [--log LOG] [--cbdir CBDIR] [--webroot WEBROOT] [--team TEAM] [--rounds ROUNDS]

# DESCRIPTION

ti-rotate simlates CFE rounds by creating data for ti-server to make available via the CRS API.  Once started, ti-rotate will continue to simulate rounds every ROUNDLEN seconds until ti-rotate is stopped or ROUNDS is reached.

WARNING: Virtual Competition for finals in DARPA's Cyber Grand Challenge is for use in verifying the API capability with the competition framework. Data created by the virtual competition is synthetic in nature and is only intended to be used to test the API compatibility of competitor's CRSs.

# ARGUMENTS

none

# OPTIONS

-h, --help
:  show this help message and exit

--debug
:  Enable debugging (default: False)

--log *LOG*
:  Log filename (default: None)

--cbdir *CBDIR*
:  Initial CB directory (default: /usr/share/cgc-challenges)

--webroot *WEBROOT*
:  ti-server web root directory (default: ./webroot)

--team *TEAM*
:  Simulate playing as the specified team (0-7) (default: 1)

--rounds *ROUNDS*
:  How many rounds to simulate (default: None)

--roundlen *ROUNDLEN*  
:  Length of a round in seconds (default: None)


# EXAMPLE USES

* start ti-rotate specifying a new round to be simulated every 5 seconds

  ti-rotate --roundlen 5

* start ti-rotate specifying a new round to be simulated every 5 minutes, for 90 rounds, in a tmp directory

  ti-rotate --roundlen 300 --webroot /tmp/simulation/webroot --rounds 90

* start ti-rotate specifying a new round to be simulated every 20 minutes, simulating team 3

  ti-rotate --roundlen 1200 --team 3

# COPYRIGHT

Under 17 U.S.C S 105 US Government Works are not subject to domestic copyright protection.


# SEE ALSO
ti-server(1) ti-client(1)

For more information relating to DARPA's Cyber Grand Challenge, please visit <http://www.darpa.mil/cybergrandchallenge/>
