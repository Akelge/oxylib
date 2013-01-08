#-*- coding: latin-1 -*-

"""

@brief Oxysoft standard library
Misc utilities module

$Id$
"""
__headUrl__  = '$HeadURL$'

import re
import sys

# Backwards compat
from customtypes import *

def checkIfPylons():
    """
    @brief Check if we are under pylons, looking for request and/or session in pylons module
    @return a tuple (request, session), eventually equal to None
    """
    try:
        from pylons import request, session
        try:
            session['@oxylib_checkIfPylons@']=1
        except TypeError:
            return (False, None, None)
        del (session['@oxylib_checkIfPylons@'])
        return (request, session)
    except ImportError:
        return (False, None, None)
    return (True, request, session)

# *************************************************************************** #

def Property(func):
    """
    Facility to setup a property with setter, getter, deleter and doc
    Usage:
        class bar(object):
            _foo=42

        @Property
        def foo():
            doc="foo property"

            def fget(self):
                return self._foo
            def fset(self, value):
                self._foo=value
            def fdel(self):
                del self._foo
        b=bar()
        b.foo # returns 42
        b.foo=3
        b.foo # returns 3
    """

    return property(**func())


# *************************************************************************** #

def getException():
    """
    @brief Get last exception raised and return a tuple: (name of exception, error message)
    @return Tuple (exceptionName, exceptionMessage)
    """
    (e, m, b) = sys.exc_info()
    if e:
        exception = e.__name__
        value = m
        return (exception, value)
    return (None, None)

