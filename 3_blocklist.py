#!/usr/bin/python
# -*- coding: utf-8 -*-

#CREATE TABLE IF NOT EXISTS `GeoLite2-Country-Locations-en` (
#  `geoname_id` int(11) NOT NULL,
#  `locale_code` varchar(5) DEFAULT NULL,
#  `continent_code` varchar(5) DEFAULT NULL,
#  `country_iso_code` varchar(5) DEFAULT NULL,
#  `continent_name` varchar(64) DEFAULT NULL,
#  `country_name` varchar(64) DEFAULT NULL,
#  `is_in_european_union` tinyint(4) DEFAULT NULL
#) ENGINE=InnoDB DEFAULT CHARSET=latin1;
#
#CREATE TABLE IF NOT EXISTS `GeoLite2-Country-Blocks-IPv4` (
#  `geoname_id` int(11) NOT NULL,
#  `network` varchar(20) DEFAULT NULL,
#  `registered_country_geoname_id` int(11) DEFAULT NULL,
#  `represented_country_geoname_id` int(11) DEFAULT NULL,
#  `is_anonymous_proxy` tinyint(4) DEFAULT NULL,
#  `is_satellite_provider` tinyint(4) DEFAULT NULL
#) ENGINE=InnoDB DEFAULT CHARSET=latin1;
# Database:
#CREATE DATABASE blocklist;
#        USE blocklist;
#
#CREATE TABLE blocklist (
#        ip CHAR(15) NOT NULL
#        );
#
import sys
reload(sys)
sys.setdefaultencoding('UTF8')

execfile('config.inc.py')


import csv
import MySQLdb as mdb
con = mdb.connect(host=sql['host'], user=sql['user'], passwd=sql['password'], db=sql['db'], charset='utf8');
cursor = con.cursor(mdb.cursors.DictCursor)

import requests
link = "http://lists.blocklist.de/lists/all.txt"
r = requests.get(link)

sql = ["DELETE FROM `blocklist`"]
csv_reader = csv.reader(r.text.splitlines(), delimiter=',')
for row in csv_reader:
  sql.append("INSERT INTO `blocklist` SET `ip`='%s'"%(row[0]) )

print "Inserting into database..."
for i in range(len(sql)):
  cursor.execute(sql[i])
  if i%500 == 0:
    con.commit()
con.commit()




