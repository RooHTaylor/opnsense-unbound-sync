# OPNSense to Unbound Overrides Sync

Sync OPNSense Unbound overrides to a seperate Unbound DNS server for redundant DNS.

A Python3 script to use the OPNSense API to get a list of overrides present, and format them into a configuration file for Unbound to use.

This could also be acomplished by using SSH to copy `/var/unbound/host_entries.conf` to the unbound server.
