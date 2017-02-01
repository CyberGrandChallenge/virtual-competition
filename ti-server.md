% TI-SERVER(1) Cyber Grand Challenge Manuals
% Chris Eagle <cseagle@nps.edu>
% April 18, 2015

# NAME

ti-server - API compatible synthetic CFE team interface server, part of Virtual Competition.


# SYNOPSIS

ti-server [-h] [--debug] [--team TEAM] [--port PORT] [--daemonize] [--cbdir CBDIR] [--username USERNAME] [--password PASSWORD] [--webroot WEBROOT]

# DESCRIPTION

ti-server makes CFE data available to a CRS.  As part of Virtual competition, ti-server serves synthetic data created by ti-rotate.

WARNING: Virtual Competition for finals in DARPA's Cyber Grand Challenge is for use in verifying the API capability with the competition framework. Data created by the virtual competition is synthetic in nature and is only intended to be used to test the API compatibility of competitor's CRSs.

# ARGUMENTS

none

# OPTIONS

-h, --help
:  show this help message and exit

--debug
:  Enable debugging (default: False)

--team *TEAM*
:  Run as the server for the specified team (default: 1)

--port *PORT*
:  TCP Port to listen (default: 1996)

--daemonize
:  Run as a daemon (default: False)

--cbdir *CBDIR*
:  Initial CB directory (default: /usr/share/cgc-challenges)

--username *USERNAME*
:  Username for client to use (default: vagrant)

--password *PASSWORD*
:  Password for client to use (default: vagrant)

--webroot *WEBROOT*
:  ti-server web root directory (default: ./webroot)

--max_ids *SIZE*
:  Specify max size of a IDS rule

--max_pov *SIZE*
:  Specify max size of a POV

--max_rcb *SIZE*
:  Specify max size of a RCB

# EXAMPLE USES
TBD

# COPYRIGHT

Under 17 U.S.C S 105 US Government Works are not subject to domestic copyright protection.

# SEE ALSO
ti-rotate(1) ti-client(1)

For more information relating to DARPA's Cyber Grand Challenge, please visit <http://www.darpa.mil/cybergrandchallenge/>
