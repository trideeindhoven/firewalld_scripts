#!/usr/bin/python3
# -*- coding: utf-8 -*-

import csv
import subprocess
import requests
#import tarfile
import io
import os
import sys
from zipfile import ZipFile
import netaddr
from pprint import pprint

maxMindLicenseKey = 'etGRN5sJYW7LZsLx'
url = 'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-Country-CSV&license_key=%s&suffix=zip'%(maxMindLicenseKey)
locations_file='GeoLite2-Country-Locations-en.csv'
database_file ='GeoLite2-Country-Blocks-IPv4.csv'
ipsetcommand='/usr/sbin/ipset'
sudocommand='/usr/bin/sudo'
firewallcmdcommand='/usr/bin/firewall-cmd'
geochain='GEOIP'
ipsetwhitelist='ipwhitelist'
ipsetblacklist='ipblacklist'

print(url)
r = requests.get(url, allow_redirects=True, stream=True)
with ZipFile(io.BytesIO(r.raw.read()), 'r') as zipObj:
   listOfFileNames = zipObj.namelist()
   for fileName in listOfFileNames:
      if fileName.endswith('GeoLite2-Country-Blocks-IPv4.csv'):
          print(fileName)
          #zipObj.extract(fileName, '/tmp/geoip.csv')
          with zipObj.open(fileName) as source:
            with open(os.path.join('/tmp', 'GeoLite2-Country-Blocks-IPv4.csv'), "w") as target:
              for line in source:
                target.write(line.decode())
      if fileName.endswith('GeoLite2-Country-Locations-en.csv'):
          print(fileName)
          #zipObj.extract(fileName, '/tmp/geoip.csv')
          with zipObj.open(fileName) as source:
            with open(os.path.join('/tmp', 'GeoLite2-Country-Locations-en.csv'), "w") as target:
              for line in source:
                target.write(line.decode())


whitelistcountries=['CY', 'GR', 'EE', 'LV', 'SJ', 'MD', 'FI', 'AX', 'MK', 'HU', 'BG', 'PL', 'RO', 'XK', 'PT', 'GI', 'ES', 'MT', 'FO', 'DK', 'IS', 'GB', 'CH', 'SE', 'NL', 'AT', 'BE', 'DE', 'LU', 'IE', 'MC', 'FR', 'AD', 'LI', 'JE', 'IM', 'GG', 'SK', 'CZ', 'NO', 'VA', 'SM', 'IT', 'SI', 'ME', 'HR', 'BA', 'RS', #EU - Baltics
'US', 'CA']
whitelistcountries=['NL', 'BE', 'CH', 'PK']

def ipset_create(name,type,size,maxelem):
  subprocess.call([sudocommand, '-S', '-n',  ipsetcommand, "create",name,type,"hashsize",str(size),"maxelem",str(maxelem)])

def ipset_flush(name):
  subprocess.call([sudocommand, '-S', '-n', ipsetcommand, "-F",name])

def ipset_add_item(cidr,set):
  subprocess.call([sudocommand, '-S', '-n', ipsetcommand, "add",set,cidr])

def ipset_find_set_info(set):
  '''
  Return information about the set
  '''

  cmd = '{0} -S -n {1} list -t {2}'.format(sudocommand, ipsetcommand, set)
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  (output, err) = p.communicate()
  #print(output)

  if err:
    # Set doesn't exist return false
    return False

  setinfo = {}
  _tmp = str(output).split('\n')
  for item in _tmp:
    # Only split if item has a colon
    if ':' in item:
      key, value = item.split(':', 1)
      setinfo[key] = value[1:]
    return setinfo
  return false

setinfo = ipset_find_set_info(ipsetblacklist)
if not setinfo:
  ipset_create(ipsetblacklist,"hash:net",16000,500000)
else:
  ipset_flush(ipsetblacklist)

def ipset_restore(rules):
  cmd = '{0} -S -n {1}'.format(sudocommand, ipsetcommand)
  p = subprocess.Popen([sudocommand, '-S', '-n', ipsetcommand, 'restore', '-exist'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
  stdout = p.communicate(input=rules.encode('UTF8'))[0]


locations={}
with open(os.path.join('/tmp', locations_file) ) as csvfile:
  readCSV = csv.reader(csvfile, delimiter=',')
  for row in readCSV:
    if row[0] == 'geoname_id' or row[4] == '':
      continue
    locations[row[0]] = row[4].upper()

for country in whitelistcountries:
    ipList=[]
    with open(os.path.join('/tmp', database_file) ) as csvfile:
      readCSV = csv.reader(csvfile, delimiter=',')
      for row in readCSV:
          if row[0] == 'network':
              continue
          if row[1] in locations:
              if locations[row[1]] == country:
                  ipList.append(netaddr.IPNetwork(row[0]) )

    str_list=[]
    for net in netaddr.cidr_merge(ipList):
        str_list.append("add geoip_%s %s\n"%(country, net) )

    setinfo = ipset_find_set_info('geoip_%s'%(country) )
    if not setinfo:
      ipset_create('geoip_%s'%(country),"hash:net",16000,500000)
    else:
      ipset_flush('geoip_%s'%(country))
    ipsetrules=''.join(str_list)
    ipset_restore(ipsetrules)

##iptablescommand -I geochain -m set --match-set <ipmset> src -j <blocktype>
#subprocess.call([sudocommand, iptablescommand, "-t", "raw", "-F","IPSETS"])
#subprocess.call([sudocommand, iptablescommand, "-t", "filter", "-F","IPSETS"])
#subprocess.call([sudocommand, iptablescommand, "-t", "raw", "-I","IPSETS", "-m", "set", "--match-set", ipsetblacklist, "src", "-j", "DROP"])
#subprocess.call([sudocommand, iptablescommand, "-t", "filter", "-A","IPSETS", "-m", "set", "--match-set", ipsetwhitelist, "src", "-j", "ACCEPT"])
#subprocess.call([sudocommand, iptablescommand, "-t", "raw", "-A","IPSETS", "-j", "RETURN"])
#subprocess.call([sudocommand, iptablescommand, "-t", "filter", "-A","IPSETS", "-j", "RETURN"])

subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-chain", "ipv4", "raw", "IPSETS"])
subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--remove-rules", "ipv4", "raw", "IPSETS"])
subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-rule", "ipv4", "raw", "PREROUTING", "0", "-j", "IPSETS"])
subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-rule", "ipv4", "raw", "IPSETS", "0", "-m", "set", "--match-set", "ipblacklist", "src", "-j", "DROP"])
#subprocess.call([sudocommand, firewallcmdcommand, "--direct", "--add-rule", "ipv4", "raw", "IPSETS", "0", "-m", "set", "--match-set", "ipwhitelist", "src", "-j", "ACCEPT"])

subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-chain", "ipv4", "filter", "IPSETS"])
subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--remove-rules", "ipv4", "filter", "IPSETS"])
for c in whitelistcountries:
  subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-rule", "ipv4", "filter", "IPSETS", "0", "-p", "udp", "-m", "set", "--match-set", "geoip_%s"%(c), "src", "-m", "multiport", "--dports", "5080,9000:10999", "-j", "ACCEPT"])
  subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-rule", "ipv4", "filter", "IPSETS", "0", "-p", "tcp", "-m", "set", "--match-set", "geoip_%s"%(c), "src", "-m", "multiport", "--dports", "80,443,5080", "-j", "ACCEPT"])

subprocess.call([sudocommand, '-S', '-n', firewallcmdcommand, "--direct", "--add-rule", "ipv4", "filter", "INPUT_direct", "0", "-j", "IPSETS"])

r = requests.get('http://www.voipbl.org/update/')
str_list=[]
for ip in r.text.split("\n"):
  if ip.startswith('# TOTAL'):
    continue

  if ip != '':
    str_list.append("add %s %s\n"%(ipsetblacklist, ip) )

ipsetrules=''.join(str_list)
ipset_restore(ipsetrules)
#print(ipsetrules)
