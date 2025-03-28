#!/usr/bin/env python

# Compare two GeoServer instances using REST API.
#   - Loaded plugins
#   - Layers
#   - 

# Modules renamed along the way, we should probably ignore them:
# (these are in the core)
RenamedModules = { 'system-environment': 'System Environment',
                   'system-properties':  'System Properties',
                   'GeoServer Web REST': 'GeoServer Web UI REST',
                   'GeoWeb Cache':       'GeoWebCache' }

import os
from dotenv import load_dotenv
import requests
import pprint

load_dotenv()

# Return a tuple with items unique to A and B
def set_differences(A, B):
    return A.difference(B), B.difference(A)


GeoServers = [ {"URL": os.getenv('SERVER_URL_1'),
                "user": os.getenv('SERVER_USER_1'),
                "tag": os.getenv('SERVER_TAG_1'),                
                "pass": os.getenv('SERVER_PASS_1') },
               {"URL": os.getenv('SERVER_URL_2'),
                "user": os.getenv('SERVER_USER_2'),
                "tag": os.getenv('SERVER_TAG_2'),               
                "pass": os.getenv('SERVER_PASS_2') }
               ]

print(f"Analyzing GeoServers ...")
for G in GeoServers:
    print(f" -- Loading modules for {G['tag']}")
    # Load status = installed modules. Available fields:
    # 2.18: name, href
    response = requests.get(G["URL"] + "/about/status.json", auth=(G["user"], G["pass"]) )
    tmp = response.json()['statuss']['status']
    G["status"] = {item['name']:item for item in tmp}

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
        
    #pprint.pp(G["workspaces"])
    

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
    

