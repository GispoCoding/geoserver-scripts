#!/usr/bin/env python

# Compare two GeoServer instances using REST API.
#   - Loaded plugins
#   - Layers
#   - 

import argparse
from dotenv import load_dotenv
import json
import os
import pprint
import requests


# Modules renamed along the way, we should probably ignore them:
# (these are in the core)
RenamedModules = { 'system-environment': 'System Environment',
                   'system-properties':  'System Properties',
                   'GeoServer Web REST': 'GeoServer Web UI REST',
                   'GeoWeb Cache':       'GeoWebCache' }



helptext = "Compare two GeoServer instances, either live or live vs. stored (TODO)"
epilog = "The environment should include variables SERVER_[URL|USER|PASS|TAG]_[1|2].\nTAG variables are optional. When dumping or loading from file, only variables numbered 1 are required."
argparser = argparse.ArgumentParser(description=helptext, epilog=epilog)
argparser.add_argument('-e', '--env', action='store', help='Environment file (defaults to .env)', metavar='ENVFILE', type=argparse.FileType('r'), default='.env')
g = argparser.add_mutually_exclusive_group()
g.add_argument('-d', '--dump', action='store', help='Dump GeoServer state to JSON file', metavar='DUMPFILE', type=argparse.FileType('w'))
g.add_argument('-l', '--load', action='store', help='Use stored GeoServer state for comparison', metavar='DUMPFILE', type=argparse.FileType('r'))
g.add_argument('-v', '--verbose', action='store_true')
conf = argparser.parse_args()
env, dumpfile, loadfile,verbosity = conf.env, conf.dump, conf.load, conf.verbose

if env is not None:
    load_dotenv(stream=env)

GeoServers = [ {"URL": os.getenv('SERVER_URL_1'),
                "user": os.getenv('SERVER_USER_1'),
                "tag": os.getenv('SERVER_TAG_1'),                
                "pass": os.getenv('SERVER_PASS_1') } ]

if dumpfile is None and loadfile is None:
    GeoServers.append( {"URL": os.getenv('SERVER_URL_2'),
                "user": os.getenv('SERVER_USER_2'),
                "tag": os.getenv('SERVER_TAG_2'),               
                "pass": os.getenv('SERVER_PASS_2') } )



# Return a tuple with items unique to A and B
def set_differences(A, B):
    return A.difference(B), B.difference(A)

# Dig through a GeoServer and store the info 
def analyze(G):
    print(f" -- Loading modules for {G['tag']}")
    # Load status = installed modules. Available fields:
    # 2.18: name, href
    response = requests.get(G["URL"] + "/about/status.json", auth=(G["user"], G["pass"]) )
    tmp = response.json()['statuss']['status']
    G["status"] = {item['name']:item for item in tmp}
    if verbosity:
        print(G["status"])
        
    print(f" -- Loading workspaces for {G['tag']}")
    # Load workspaces
    response = requests.get(G["URL"] + "/workspaces.json", auth=(G["user"], G["pass"]) )
    tmp = response.json()['workspaces']['workspace']
    G["workspaces"] = {item['name']:item for item in tmp}
        
    for ws in G["workspaces"].keys():
        response = requests.get(G["URL"] + f"/workspaces/{ws}/layers.json", auth=(G["user"], G["pass"]) )
        #print(response.headers)
        #pprint.pp(response.json())
        tmp = response.json()
        if 'layers' in tmp and 'layer' in tmp['layers']:
            layers = {item['name']:item for item in response.json()['layers']['layer'] }
        else:
            layers = {}
        G["workspaces"][ws]["layers"] = layers
        if verbosity:
            print(ws + " : " + ", ".join(layers))
    return G

print(f"Analyzing GeoServers ...")        
for G in GeoServers:    
    G = analyze(G)

if dumpfile is not None:
    print(" -- Storing status to file")
    GeoServers[0].pop('user')
    GeoServers[0].pop('pass')
    dumpfile.write(json.dumps(GeoServers[0]))
    exit(0)

if loadfile is not None:
    print(" -- Loading stored status from file")
    GeoServers.append(json.load(loadfile))
    
# Comparison time
print(" -- Comparing data")
S1 = set(GeoServers[0]["workspaces"].keys())
S2 = set(GeoServers[1]["workspaces"].keys())

# Unique workspaces
D1,D2 = set_differences(S1, S2)

if len(D1) > 0:
    print(f"[WARN] Workspaces only in {GeoServers[0]['tag']}: ", D1)

if len(D2) > 0:
    print(f"[WARN] Workspaces only in {GeoServers[1]['tag']}: ", D2)    

if (D1,D2) == (set(), set()):    
    print(f'[OK] Workspace lists are identical')

# Check layer lists in common workspaces
I = S1.intersection(S2)
for ws in I:
    S1 = set(GeoServers[0]["workspaces"][ws]["layers"].keys() )
    S2 = set(GeoServers[1]["workspaces"][ws]["layers"].keys() )
    D1, D2 = set_differences(S1, S2)
    if len(D1) > 0:
        print(f"[WARN] Layers only in {GeoServers[0]['tag']} - {ws}: ", D1)

    if len(D2) > 0:
        print(f"[WARN] Layers only in {GeoServers[1]['tag']} - {ws}: ", D2)    

    if (D1,D2) == (set(), set()):    
        print(f'[OK] Workspace {ws} identical')
    


print(" -- Comparing modules")
S1 = set(GeoServers[0]["status"].keys())
S2 = set(GeoServers[1]["status"].keys())

D1,D2 = set_differences(S1, S2)
R = set()

for D in D1.copy():
    if D in RenamedModules.keys():
        D1.discard(D)
        D2.discard(RenamedModules[D])
        R.add(D)
for D in D2.copy():
    if D in RenamedModules.keys():
        D1.discard(RenamedModules[D])
        D2.discard(D)
        R.add(D)

if len(D1) > 0:
    print(f"[WARN] Modules only in {GeoServers[0]['tag']}: ", D1)

if len(D2) > 0:
    print(f"[WARN] Modules only in {GeoServers[1]['tag']}: ", D2)    

if len(R) > 0:
    print(f"[INFO] Renamed modules: ", {k: v for k, v in RenamedModules.items() if k in R} )

if (D1,D2) == (set(), set()):
    print(f'[OK] Module lists are identical')
    

