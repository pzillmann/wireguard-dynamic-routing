#!/usr/bin/env python3

import configparser
import sys
import re
import subprocess
from collections import OrderedDict
from ipaddress import IPv4Network


#rekey ini sections: datastructure
class multidict(OrderedDict):
    _unique = 0   # class variable

    def __setitem__(self, key, val):
        if isinstance(val, dict):
            self._unique += 1
            key += str(self._unique)
        OrderedDict.__setitem__(self, key, val)

if len(sys.argv) != 3:
    print("Usage: ", sys.argv[0], " Interface-Name Wireguard-Config-File", file=sys.stderr)
    print("eg.: ", sys.argv[0], " wg0 /etc/wireguard/wg0.conf", file=sys.stderr)
    exit(1)

interface = sys.argv[1]
configfile = sys.argv[2]

wgRoutingTable = dict()

#read the Kernel's routing table by calling /usr/bin/route -n
routes = str(subprocess.check_output(["route", "-n"]), "utf-8")

#init ini reader for rekeying due to duplicate section names
#section get a unique identifier at the end (ascending integer starting at 1)
config = configparser.ConfigParser(strict=False, dict_type=multidict)

if len(config.read(configfile)) == 0:
    print("No such file: ", configfile, file=sys.stderr)
    exit(2)

routeLines = (routes.split("\n"))[2:]

for line in routeLines:
    #search the routing table for an entry handled by the wireguard interface
    if re.search(r"\s" + interface + "$", line):
        
        #this entry is for the wireguard interface
        entry = re.search(r"^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})", line).groups()
        if len(entry) < 3:
            print("Malformed return of route -n", file=sys.stderr)
            continue

        if entry[1] == "0.0.0.0":
            print("Ignoring L2 Route", file=sys.stderr)
            continue

        if (entry[1] + "/32") not in wgRoutingTable:
            wgRoutingTable[entry[1] + "/32"] = list()
        
        cidr = IPv4Network(entry[0] + "/" + entry[2]).prefixlen
        wgRoutingTable[entry[1] + "/32"].append(entry[0] + "/" + str(cidr))

for section in config.sections():
    if section.startswith("Peer"):
        pubkey = config.get(section, "PublicKey")
        allowed = config.get(section, "AllowedIps")

        for ip in allowed.split(","):
            ipOtherNode = ip.strip()
            if ipOtherNode in wgRoutingTable:
                allowed += ", " + (", ").join(wgRoutingTable[ipOtherNode])

        print("Calling: wg set " + interface + " peer " + pubkey + " allowed-ips " + allowed)
        subprocess.run(["wg", "set", interface, "peer", pubkey, "allowed-ips", allowed])