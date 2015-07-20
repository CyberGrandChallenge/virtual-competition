% TI-CLIENT(1) Cyber Grand Challenge Manuals
% Tim <tim@0x90labs.com>
% April 18, 2015

# NAME

ti-client - API compatable synthetic CFE team interface client, part of Virtual Competition.

# SYNOPSIS

ti-client [-h] [--hostname HOSTNAME] [--port PORT] [--debug] [--log LOG] [--user USER] [--password PASSWORD] [--team TEAM]

# DESCRIPTION

ti-client is an interactive example client implementation to exercise the team interface provided to a CRS

ti-client interacts with (and depends on) a ti-server found on a socket specified by HOSTNAME:PORT, similarly, if ti-rotate has not completed a round, data that ti-client expects will not yet have been populated to ti-server directories

WARNING: Virtual Competition for finals in DARPA's Cyber Grand Challenge is for use in verifying the API capability with the competition framework. Data created by the virtual competition is synthetic in nature and is only intended to be used to test the API compatibility of competitor's CRSs.

# ARGUMENTS

none

# OPTIONS

-h, --help
:  show this help message and exit

--hostname *HOSTNAME*
:  Specify hostname of TI server (default: localhost)

--port *PORT*
:  Specify TCP port (default: 1996)

--debug
:  Enable debugging (default: False)

--log *LOG*
:  Specify Log filename (default: None)

--username *USER*
:  Specify username (default: vagrant)

--password *PASSWORD*
:  Specify password associated with user (default: vagrant)

--team *TEAM*
:  Specify Team Number (default: 1)


# EXAMPLE USES

* start ti-client connecting to host 1.1.1.1 with user cgc and password jhkf3uf

  ti-client --hostname localhost --debug --user cgc --password jhkf3uf

* start ti-client with default options

  ti-client

* once ti-client is started, retreive score information (note: > is part of the interactive prompt, not a shell redirect)

  ti-client> scoreboard 

* once ti-client is started, get a list of available commands (note: > is part of the interactive prompt, not a shell redirect)

  ti-client> help

# COPYRIGHT

Under 17 U.S.C S 105 US Government Works are not subject to domestic copyright protection.

# SEE ALSO
ti-server(1) ti-rotate(1)

For more information relating to DARPA's Cyber Grand Challenge, please visit <http://www.darpa.mil/cybergrandchallenge/>
