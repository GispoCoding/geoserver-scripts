#!/usr/bin/env python
import argparse
import csv
import math
import pprint
import sys
import xml.etree.ElementTree as ET

"""
Handle logs written by the GeoServer monitor extension

<Requests><Request id="1234">
   <Service>WMS</Service>
   <Version>1.3.0</Version>
   <Operation>GetMap</Operation>
   <SubOperation></SubOperation>
   <Resources>LAYERNAMES</Resources> <!-- Multiple will be comma separated! -->
   <ResourcesProcessingTime>123</ResourcesProcessingTime> <!-- Comma separated! -->
   <LabelsProcessingTime></LabelsProcessingTime>
   <Path>/WORKSPACE/wms</Path>
   <QueryString>FULL_QUERY_STRING_HERE</QueryString>
   <Body>
   
   </Body>
   <HttpMethod>GET</HttpMethod>
   <StartTime>2024-11-05T07:38:20.782Z</StartTime>
   <EndTime>2024-11-05T07:38:21.662Z</EndTime> <!-- Is this needed? See TotalTime -->
   <TotalTime>880</TotalTime> <!-- Milliseconds -->
   <RemoteAddr>12.34.56.78</RemoteAddr>
   <RemoteHost>12-34-56-78.isp.example.com</RemoteHost>
   <Host>HOSTNAME</Host> 
   <RemoteUser>USER</RemoteUser>
   <ResponseStatus>200</ResponseStatus>
   <ResponseLength>8677</ResponseLength>
   <ResponseContentType>text/html; subtype=openlayers3</ResponseContentType>
   <CacheResult></CacheResult>
   <MissReason></MissReason>
   <Failed>false</Failed>
</Request>...
</Requests> <!-- NB. This will be missing if reading the active log file -->
"""

# Add a line to the log dictionary.
def addLogLine(logLines, logObject):
    # We get a thousands separator in the ID. Annoying.
    idx = int(logObject.attrib['id'].replace(".","").replace(",",""))
    logLine = {}
    for field in logObject:
        text = field.text or ""
        logLine[field.tag] = text.strip()
    logLines[idx] = logLine


# Return the desired CSV fields from logLine in an array.
# A falsey logLine returns the field names for a header row
def getCSVline(idx, logLine):
    CSVFields = [ 'StartTime', 'Service', 'Version', 'Operation', 'SubOperation', 'Resources', 'TotalTime', 'ResourcesProcessingTime', 'LabelsProcessingTime', 'Path', 'HttpMethod', 'RemoteAddr', 'Host', 'RemoteUser', 'ResponseStatus', 'ResponseLength', 'ResponseContentType', 'CacheResult', 'MissReason', 'Failed' ]
    if not logLine:
        return ['ID'] + CSVFields

    CSV = [idx]
    for f in CSVFields:
        CSV.append(logLine[f])

    return CSV

# CSV output, a falsey outfile outputs to stdout
def CSVwrite(outfile, logLines):
    with (open(outfile, 'w') if outfile else sys.stdout) as csvfile:
        CSVout = csv.writer(csvfile, delimiter=',',
                            quotechar='\'', quoting=csv.QUOTE_MINIMAL)

        CSVout.writerow(getCSVline(None, None))

        sortedLines = dict(sorted(logLines.items()))
        for idx, line in sortedLines.items():
            CSVout.writerow(getCSVline(idx, line))


def debugPrint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def statsWrite(logLines):
    services = {}
    resources = {}
    users = {}
    
    total =   len(logLines)
    failed =  sum(1 for v in logLines.values() if v['Failed'] == 'true')
    success = sum(1 for v in logLines.values() if v['Failed'] == 'false')
    for l in logLines.values():
        # Count WMS/WFS/etc into services[SERVICE][VERSION][FAILURE_STATUS] dict
        if not l['Service'] in services:
            services[l['Service']] = {}
        if not l['Version'] in services[l['Service']]:
            services[l['Service']][l['Version']] = {'true': 0, 'false': 0}
        services[l['Service']][l['Version']][l['Failed']] += 1

        # Count resources
        res_split = l["Resources"].split(',')
        for r in res_split:
            res = r.strip()
            if not res in resources:
                resources[res] = 0
            resources[res] += 1
        
        # Count users
        if not l['RemoteUser'] in users:
            users[l['RemoteUser']] = 0
        users[l['RemoteUser']] += 1

    w = math.floor(math.log10(total)+2)

    print('Total req: {n:{space}{w}}'.format(n=total, space=' ', w=w))
    print('Failed:    {n:{space}{w}}'.format(n=failed, space=' ', w=w),end='')
    print(f' ({failed/total*100.0:.1f}%)')
    print('Success:   {n:{space}{w}}'.format(n=success, space=' ', w=w), end='')
    print(f' ({success/total*100.0:.1f}%)')
    print("Services ----- ")
    pprint.pp(services) # TODO: prettier print
    print("Users ----- ")
    pprint.pp(users)
    print("Resources ----- ")
    #pprint.pp(resources)
    for name, count in resources.items():
        if name: 
            workspace,layer = name.split(':')
            print(f'{workspace}\t{layer}\t{count}')
            #print(f'{name}\t{count}')
        else:
            print(f'[None]\t[None]\t{count}')
    

    
# ---- Here we go ---
    
logLines = {}

# Initialize parser
argParser = argparse.ArgumentParser()
group = argParser.add_mutually_exclusive_group()
group.add_argument('--csv', help='output log entries as CSV (- for stdout)')
group.add_argument('--stats', help='Statistics on stdout', action="store_true")
argParser.add_argument('--debug', help='Debug output', action="store_true")
argParser.add_argument('files', nargs='*')

# Read arguments from command line
args = argParser.parse_args()
outfile = args.csv

# Read in the input files one by one
for filename in args.files:
    if args.debug:
        debugPrint(f"Processing {filename}") 
    
    # Read in the input files one by one
    with open(filename) as f:
        xmldata = f.read()

    try:
        root = ET.fromstring(xmldata)
    except ET.ParseError:
        # The log file might be open, so try parsing after closing root element
        if args.debug:
            debugPrint(f"   Attempting root element fix for {filename}")
        try:
            root = ET.fromstring(xmldata + '</Requests>')
        except ET.ParseError:
            debugPrint(f"Failed parsing {filename} as XML, skipping.")
            continue

    if root.tag == 'Requests':
        for child in root:
            if child.tag == 'Request':
                # Put the data from XML into an array/dictionary/something
                addLogLine(logLines, child)

if args.csv:
    if args.csv == '-':
        args.csv = None
    CSVwrite(args.csv, logLines)
elif args.stats:
    statsWrite(logLines)
