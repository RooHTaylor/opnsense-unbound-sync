#/usr/bin/env python3

import requests
import json
import pprint

debug = True

api_key_file = '.apikey'
opnsense_url = 'https://opn.m.h.sawknerd.net'

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

response = ""

if r.status_code == 200:
    response = json.loads(r.text)

    if debug:
        pprint.pprint(response)

else:
    print('Connection / Authentication issue, response received:')
    print(r.text)

