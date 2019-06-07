# Wireguard Dynamic Routing

This project parses the Kernel's routing table and calls the `wg` tool for every relevant rules.
You can create the Kernel's routing table via any dynamic routing protocol, eg. via OSPF using bird.

### Requirements:

* python3
* net-tools (for the route executable)
* wireguard-tools

### Using:

call `./wg-dynroute.py wg0 /path/to/wireguard-interface-config.conf`

Important:
In the Wireguard Interface Config File every peer needs to have at least one Allowed IP specified. That IP is matched with the `via` fields in the routing table. It should be the peer's internal IP address with an /32 netmask.

You can specify multiple addresses in the Allowed IPs field. The script respects that.

This tool does not respect route metrics. So for now this works only for routes with no duplicates!

### Licence:
This tool is licensed unter the MIT licence