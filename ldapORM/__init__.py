"""

 Copyright by Andrea Mistrali <akelge@gmail.com>
 First version: 2013-06-12T10:09 CEST (+0200)

 Synopsis: LDAP O(R)M

 $Id$


TODO:
    Implement caching
    Logging levels
    search for 'dn'
    doctests

Objects tree
------------
engine.py
LDAPConnection()
    LAPQuery(LDAPObjClass)
        get(uniqueAttr)
        search(ldapFilter)
    LDAPObj()
types.py
    LDAPAttribute()
"""
__version__ ='1.0'
__author__ ='Andrea Mistrali <akelge@gmail.com>'

import ldap
import logging

log = logging.getLogger(__name__)

from engine import * # Connection, query and result
import types
