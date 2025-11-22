#!/usr/bin/env python3
# vim: set tw=0

import requests
import json
import subprocess
import pprint

debug = False

api_key_file = '.apikey'
overrides_file = '/etc/unbound/unbound.conf.d/host_overrides.conf'
opnsense_url = 'https://opnsense.example.com'

api_key = {}

try:
    with open(api_key_file, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('key='):
                api_key['key'] = line.split('=', 1)[1]
            elif line.startswith('secret='):
                api_key['secret'] = line.split('=', 1)[1]
    # Ensure we found both key and secret
    if 'key' not in api_key or 'secret' not in api_key:
        raise ValueError("Both the key and secret must be in the file")

except FileNotFoundError:
    print(f"Error: The API key file {file_path} does not exist")
except Exception as e:
    print(f"Error: {e}")


if debug:
    pprint.pprint(api_key)

endpoint = '/api/unbound/settings/get'
# Join the url and enpoint, with a / between
endpointurl = '/'.join(part.strip('/') for part in (opnsense_url, endpoint))

if debug:
    print(f"Url: {endpointurl}")

r = requests.get(endpointurl,
                 auth=(api_key['key'], api_key['secret']))

if debug:
    pprint.pprint(r)

settings = ""

if r.status_code == 200:
    settings = json.loads(r.text)

    if debug:
        pprint.pprint(settings)

else:
    raise Exception("Connection / Authentication issue, response received")

outfile = '''server:
local-zone: "example.com" transparent

# Localhost
local-data-ptr: "127.0.0.1 localhost"
local-data: "localhost A 127.0.0.1"
local-data: "localhost.example.com A 127.0.0.1"
local-data-ptr: "::1 localhost"
local-data: "localhost AAAA ::1"
local-data: "localhost.example.com AAAA ::1"

# From OPNSense overrides
'''

ptrs = ['127.0.0.1', '::1']

for hostid in settings['unbound']['hosts']['host']:
    # !!!! enabled is a string but selected is an int !!!!
    if settings['unbound']['hosts']['host'][hostid]['enabled'] != '1' or settings['unbound']['hosts']['host'][hostid]['rr']['MX']['selected'] == 1:
        continue;

    # Only add PTR records once.
    if settings['unbound']['hosts']['host'][hostid]['server'] not in ptrs:
        ptrline = 'local-data-ptr: "' + settings['unbound']['hosts']['host'][hostid]['server'] + ' ' + settings['unbound']['hosts']['host'][hostid]['hostname'] + '.' + settings['unbound']['hosts']['host'][hostid]['domain'] + "\"\n"
        ptrs.append(settings['unbound']['hosts']['host'][hostid]['server'])
    else:
        ptrline = ''

    dataline = 'local-data: "' + settings['unbound']['hosts']['host'][hostid]['hostname'] + '.' + settings['unbound']['hosts']['host'][hostid]['domain'] + ' ' + settings['unbound']['hosts']['host'][hostid]['ttl'] + ' IN '
    if settings['unbound']['hosts']['host'][hostid]['rr']['A']['selected'] == 1:
        dataline += 'A '
    else:
        dataline += 'AAAA '
    dataline += settings['unbound']['hosts']['host'][hostid]['server'] + "\"\n"

    outfile += ptrline + dataline

    for aliasid in settings['unbound']['aliases']['alias']:
        # !!!! enabled is a string but selected is an int !!!!
        if settings['unbound']['aliases']['alias'][aliasid]['enabled'] != '1' or settings['unbound']['aliases']['alias'][aliasid]['host'][hostid]['selected'] != 1:
            continue;

        aliasdataline += 'local-data: "' + settings['unbound']['aliases']['alias'][aliasid]['hostname'] + '.' + settings['unbound']['aliases']['alias'][aliasid]['domain'] + ' ' + settings['unbound']['hosts']['host'][hostid]['ttl'] + ' IN '
        if settings['unbound']['hosts']['host'][hostid]['rr']['A']['selected'] == 1:
            aliasdataline += 'A '
        else:
            aliasdataline += 'AAAA '
        aliasdataline += settings['unbound']['hosts']['host'][hostid]['server'] + "\"\n"

        outfile += aliasdataline

if debug:
    print(outfile)

with open(overrides_file, 'w') as oridefile:
    oridefile.write(outfile)

subprocess.run(['sudo', 'systemctl', 'reload', 'unbound'])
