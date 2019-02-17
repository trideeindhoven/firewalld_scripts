#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import MySQLdb as mdb
import netaddr
import subprocess
from pprint import pprint

execfile('config.inc.py')


def is_systemd():
  import os.path
  if os.path.isfile("/etc/systemd"):
    return True
  else:
    return False

def ipset_find_set_info(set):
  '''
  Return information about the set
  '''

  cmd = '{0} list -t {1}'.format(ipsetcommand, set)
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  (output, err) = p.communicate()

  if err:
    # Set doesn't exist return false
    return False

  setinfo = {}
  _tmp = output.split('\n')
  for item in _tmp:
    # Only split if item has a colon
    if ':' in item:
      key, value = item.split(':', 1)
      setinfo[key] = value[1:]
    return setinfo
  return false

def ipset_create(name,type,size,maxelem):

  subprocess.call([ipsetcommand, "create",name,type,"hashsize",str(size),"maxelem",str(maxelem)])

def ipset_flush(name):
  subprocess.call([ipsetcommand, "-F",name])

def ipset_add_item(cidr,set):
  subprocess.call([ipsetcommand, "add",set,cidr])

def ipset_restore(rules):
  p = subprocess.Popen([ipsetcommand, 'restore', '-exist'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
  stdout = p.communicate(input=rules)[0]


def firewall_add_rule(input):
  print "firewall_add_rule"
  #system(.' --direct --add-rule ipv4 filter GEOIP 0 -m set --match-set geoip_'..' src -j LOG --log-prefix "firewall - '..' Country Drop "');
  action=[firewallcommand,"--direct","--add-rule","ipv4","filter",input['chain']]

  if input['position'] == "insert":
    action.append("0")
  else:
    action.append("1")

  if 'set' in input:
    action.append("-m")
    action.append("set")
    action.append("--match-set")
    action.append(str(input['set']))
    action.append("src")

  if 'multiport' in input:
    action.append("-m")
    action.append("multiport")
    action.append("-p")
    action.append("tcp")
    action.append("--dports")
    action.append(str(input['multiport']))

  if 'port' in input:
    action.append("-m")
    action.append(input['protocol'])
    action.append("-p")
    action.append(input['protocol'])
    action.append("--dport")
    action.append(str(input['port']))

  action.append("-j")
  action.append(input['action'])

  print action
  subprocess.call(action)


 
def firewall_flush_chain(chain):
  subprocess.call([firewallcommand, "--direct","--remove-rules","ipv4","filter",chain])
  #system(.' --direct --remove-rules ipv4 filter GEOIP');


with open('/root/bin/firewall.json') as data_file:   
    data = json.load(data_file)
pprint(data)

con = mdb.connect(host=sql['host'], user=sql['user'], passwd=sql['password'], db=sql['db'], charset='utf8');
cur = con.cursor()

print "Generate ipsets"
countries=[]
for rule in data['whitelist']:
  for country in rule['parameters']['geoip']:
    if country not in countries:
      countries.append(country)
for rule in data['blacklist']:
  for country in rule['parameters']['geoip']:
    if country not in countries:
      countries.append(country)

ipsetrules=""
str_list=[]

for country in countries:
  print country
  setinfo = ipset_find_set_info('geoip_'+country)
  if not setinfo:
    #print "Create ipset geoip_"+country
    ipset_create("geoip_"+country,"hash:net",16000,65536)
  else:
    #print "Flush old geoip_"+country
    ipset_flush("geoip_"+country)
  #print "Generate ipset geoip_"+country
  #with con:

  cur.execute("SELECT `network` FROM `GeoLite2-Country-Locations-en`,`GeoLite2-Country-Blocks-IPv4` where `GeoLite2-Country-Locations-en`.`country_iso_code`=\""+country+'" AND `GeoLite2-Country-Locations-en`.`geoname_id`=`GeoLite2-Country-Blocks-IPv4`.`registered_country_geoname_id`')
  #ci = cur.fetchone()[0]

  #cur.execute("SELECT start, end FROM ip where ci="+str(ci) )
  for i in range(cur.rowcount):
    row = cur.fetchone()
    #print str(netaddr.IPAddress(row[0]))+" - "+str(netaddr.IPAddress(row[1]))
    #for cidr in netaddr.IPRange(row[0],row[1]).cidrs():
    #  #print str(cidr)
    str_list.append("add geoip_%s %s\n"%(country, row[0]) )
    #  #ipset_add_item(str(cidr),"geoip_"+country)

ipsetrules+=''.join(str_list)
ipset_restore(ipsetrules)
ipsetrules=""



firewall_flush_chain("WHITELIST")
firewall_flush_chain("BLACKLIST")
for rule in data['whitelist']:
  if rule['module'] == 'multiport':
    for country in rule['parameters']['geoip']:
      firewall_add_rule({"position":"insert","chain":"WHITELIST","protocol": "tcp", "set":"geoip_"+country, "multiport":rule['parameters']['ports'],"action":"ACCEPT"})
  if rule['module'] == 'udp':
    for country in rule['parameters']['geoip']:
      firewall_add_rule({"position":"insert","chain":"WHITELIST","protocol": "udp", "set":"geoip_"+country, "port":rule['parameters']['ports'],"action":"ACCEPT"})

for rule in data['blacklist']:
  if rule['module'] == 'multiport':
    for country in rule['parameters']['geoip']:
      firewall_add_rule({"position":"insert","chain":"BLACKLIST","protocol": "tcp", "set":"geoip_"+country, "multiport":rule['parameters']['ports'],"action":"DROP"})
  if rule['module'] == 'udp':
    for country in rule['parameters']['geoip']:
      firewall_add_rule({"position":"insert","chain":"BLACKLIST","protocol": "udp", "set":"geoip_"+country, "port":rule['parameters']['ports'],"action":"DROP"})


setinfo = ipset_find_set_info('blocklist')
if not setinfo:
  #print "Create ipset blocklist"
  ipset_create("blocklist","hash:net",16000,65536)
else:
  #print "Flush old blocklist"
  ipset_flush("blocklist")
#print "Generate ipset blocklist"

str_list=[]
with con:
  cur.execute("SELECT ip FROM blocklist")
  for i in range(cur.rowcount):
    row = cur.fetchone()
    str_list.append("add blocklist %s\n" %(row[0]))
    #ipsetrules+="add blocklist "+row[0]+"\n"
ipsetrules+=''.join(str_list)


firewall_add_rule({"position":"insert","chain":"BLACKLIST","set":"blocklist", "action":"DROP"})
con.close()

ipset_restore(ipsetrules)
ipsetrules=""





setinfo = ipset_find_set_info('badips')
if not setinfo:
  #print "Create ipset badips"
  ipset_create("badips","hash:ip",16000,500000)
else:
  #print "Flush old badips"
  ipset_flush("badips")
#print "Generate ipset badips"
str_list=[]
with con:
  cur.execute("SELECT ip FROM badips")
  for i in range(cur.rowcount):
    #print str(i)+" - "+str(cur.rowcount)
    row = cur.fetchone()
    str_list.append("add badips %s\n"%(row[0]))
    #ipsetrules+="add badips "+row[0]+"\n"
    if i % 10000 == 0:
      ipsetrules=''.join(str_list)
      ipset_restore(ipsetrules)
      ipsetrules=""
      str_list=[]

ipsetrules=''.join(str_list)
ipset_restore(ipsetrules)

firewall_add_rule({"position":"insert","chain":"BLACKLIST","set":"badips", "action":"DROP"})
con.close()
ipsetrules=""
str_list=[]






setinfo = ipset_find_set_info('letsencrypt')
if not setinfo:
  ipset_create("letsencrypt","hash:ip",1024,65536)
else:
  ipset_flush("letsencrypt")
str_list=[]
with con:
  cur.execute("SELECT ip FROM letsencrypt")
  for i in range(cur.rowcount):
    row = cur.fetchone()
    str_list.append("add letsencrypt %s\n"%(row[0]))

ipsetrules=''.join(str_list)
ipset_restore(ipsetrules)
firewall_add_rule({"position":"insert","chain":"WHITELIST","protocol": "tcp", "set":"letsencrypt", "multiport":"80,443","action":"ACCEPT"})

con.close()

