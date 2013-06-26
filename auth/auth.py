"""
 Copyright Andrea Mistrali 2012

 AAA Module
 Inspired by RADIUS, users AV Pairs, i.e. a dictionary.
 Standard fields are:
     username
     password
     realname
     gid: id of the main group
     login_time: time of last login
     authenticated: True of False
     perms: a dictionary with group name as key and an array of perms (strings) as value

 $Id$

"""

# __all__ = ["BaseUser", "AuthenticatedUser", "login", "logout", "isAuthenticated", "isAuthorized", "authorize"]

import time, hashlib # for _uuid
import re
from pylons import config, request, response, session
from pylons.controllers.util import abort, redirect #TEMPORARY - remove when Middleware works

from paste import httpexceptions
from webob.exc import HTTPForbidden, HTTPUnauthorized, HTTPTemporaryRedirect

from oxylib.utils import sdict, getException # Our Utils
import logging

# from oxylib import DateTime

log = logging.getLogger(__name__)

#
# Internal utilities
#
def warn(message):
    log.debug(message)

def ckey(path):
    __prefix__ = 'oxylib.auth'
    return '%s.%s' % (__prefix__, path)

def getConfig(path, config=config):
    castBoolean={'True': True, 'False': False}

    value=config.get(ckey(path), None)
    if castBoolean.has_key(value):
        value=castBoolean.get(value)
    return value

#
# Session management utilities
#
def sessionLoad():
    return session.get(ckey('user'), BaseUser())

def sessionSave(user, session=session):
    user.password='********' # Hide password
    session[ckey('user')]=user
    session.save()

def sessionClear():
    if session.has_key(ckey('user')):
        del session[ckey('user')]
        session.save()

###
# Start of classes
###

class BaseUser(object):

    _REGISTERED_PLUGINS={}

    @classmethod
    def register_plugin(cls, plugin):
        cls._REGISTERED_PLUGINS[plugin.__name__]=plugin

    def getModules(self, phase, config=config):
        modList=getConfig('%s_modules' % phase, config)

        if modList != None:
            return [mod.strip() for mod in modList.split(',')]
        else:
            warn('no %s method defined' % (phase))
            return []

    def setupModules(self):
        self._AUTHENTICATION_MODULES=self.getModules('authentication')
        self._AUTHORIZATION_MODULES=self.getModules('authorization')
        self._ACCOUNTING_MODULES=self.getModules('accounting')
        self.doAuthentication=(len(self._AUTHENTICATION_MODULES) > 0)
        self.doAuthorization=(len(self._AUTHORIZATION_MODULES) > 0)
        self.doAccounting=(len(self._ACCOUNTING_MODULES) > 0)


    def __init__(self):
        self.username = None
        self.password = None
        self.realname = None
        self.gid = None # Primary Group
        self.login_time = None # Last successfull login time
        self.authenticated = False # Passed authentication
        self.check_authz = False # Passed authorization
        self.perms = sdict() # Perms dictionary {'GROUP': ['perm1', 'perm2']}
        self.errors = []

        self.setupModules()

    def isAuthenticated(self): return self.authenticated

    def isAuthorized(self,clause=None): return isAuthorized(clause=clause,user=self)

    def __repr__(self):
        return r"<%s(username='%s', login_time='%s', authenticated=%s)>" % (self.__class__.__name__,
                self.username,
                self.login_time,
                self.authenticated)

    def __str__(self):
        "username: %s - login_time: %s - AUTH: %s" % (self.username, self.login_time, self.authenticated)

    @property
    def groups(self):
        return self.perms.keys()

    @property
    def roles(self):
        """
        Flat down list of permissions
        """
        roles=[]
        for v in self.perms.values(): roles.extend(v)
        return sorted(set(roles)) # Clean up repetitions
    @property
    def avPairs(self):
        """
        Serialize user properties as a sdict, to be passed to plugins
        """
        d=sdict()
        for k in [key for key in self.__dict__.keys() if not key.startswith('_')]: d[k]=self.__dict__[k]
        d['perms']=self.perms # Add perms
        return d


class AuthenticatedUser(BaseUser):

    @classmethod
    def uuid(cls):
        return hashlib.sha1('%f' % time.time()).hexdigest()

    def __init__(self, username=None, password=None, session=session):
        BaseUser.__init__(self)

        if not (username and password):
            raise ValueError, 'Either specify username/password'

        self.username=username
        self.password=password
        self.auth()

        if self.authenticated:
            if self.doAuthorization:
                self.authz()

            if self.doAccounting:
                if (username and password):
                    self.startAcct()

        sessionSave(self, session)

    def _doAuthPlugins(self):
        """
        Do A1 (authentication), returns after first success
        """
        if not self.doAuthentication:
            return False

        for module in self._AUTHENTICATION_MODULES:
            log.debug('Calling module auth_%s', module)
            try:
                self.updateFromPlugin(self._REGISTERED_PLUGINS["auth_%s" % (module)](self.avPairs))
                if self.authenticated: return True
            except KeyError:
                warn("no auth_%s method defined" % (module))
            except:
                (e, v) = getException()
                self.errors.append(('auth', module, str(v)))

    def _doAuthzPlugins(self):
        """
        Do A2 (authorization), merge of all perms
        """
        for module in self._AUTHORIZATION_MODULES:
            log.debug('Calling module authz_%s', module)
            try:
                plugin=self._REGISTERED_PLUGINS["authz_%s" % (module)](self.avPairs)
                log.debug('plugin returned %s', plugin)
                self.updatePerms(plugin)
                self.updateFromPlugin(plugin, filter='perms')
            except KeyError:
                warn("no authz_%s method defined" % (module))
            except:
                (e, v) = getException()
                self.errors.append(('authz', module, str(v)))

    def _doAcctPlugins(self, start=False, stop=False):
        """
        Do A3 (accounting), pass all plugin
        """
        if start:
            for module in self._ACCOUNTING_MODULES:
                log.debug('Calling module acct_%s', module)
                try:
                    self.updateFromPlugin(self._REGISTERED_PLUGINS["startAcct_%s" % (module)](self.avPairs))
                except KeyError:
                    warn("no startAcct_%s method defined" % (module))
                except:
                    (e, v) = getException()
                    self.errors.append(('startAcct', module, str(v)))


        if stop:
            for module in self._ACCOUNTING_MODULES:
                try:
                    self.updateFromPlugin(self._REGISTERED_PLUGINS["stopAcct_%s" % (module)](self.avPairs))
                except KeyError:
                    warn("no stopAcct_%s method defined" % (module))
                except:
                    (e, v) = getException()
                    self.errors.append(('stopAcct', module, str(v)))


            if session.has_key(ckey('user')):
                sessionClear()
                self.authenticated=False


    # Utilities
    def auth(self): self._doAuthPlugins()
    def authz(self): self._doAuthzPlugins()
    def startAcct(self): self._doAcctPlugins(start=True, stop=False)
    def stopAcct(self): self._doAcctPlugins(start=False, stop=True)
    def logout(self): self.stopAcct()


    # Updaters
    def update(self, attr, value): setattr(self, attr, value)

    def updateFromDict(self, avPairs):
        for k,v in avPairs.items():
            if v != None:
                self.update(k, v)

    def updateFromPlugin(self, avPairs, filter=''):
        if avPairs.has_key(filter): avPairs.pop(filter)
        self.updateFromDict(avPairs)

    def updatePerms(self, avPairs):
        perms=avPairs.perms
        for k,v in perms.items():
            if self.perms.has_key(k):
                    self.perms[k].extend(v)
            else:
                self.perms[k]=v
            # Clean up repetitions
            self.perms[k]=sorted(set(self.perms[k]))

#
# Commodities
#
def login(username, password, session=session):
    """
    Check if a username/password is good
    """

    user=AuthenticatedUser(username=username, password=password, session=session)
    return user.isAuthenticated()

def logout():
    """
    Clear the session
    """
    user=sessionLoad()
    if user and user.isAuthenticated():
        user.logout()

#
# Functions used in decorator and as standalone authorizer
#
def isAuthorized(clause=None, user=None):
    if not user:
        user = sessionLoad()
    if not user.isAuthenticated():
        return False
    if not user.doAuthorization:
        return True

    if clause:
        expandedclause = expandPermClause(clause,user.roles,user.perms)
        try:
            return eval(expandedclause)
        except:
            raise Exception, "Invalid clause! - Clause: \"%s\" - Expanded: \"%s\"" % (clause,expandedclause)
    else:
        return len(user.perms) > 0

def isAuthenticated(user=None):
    """
    Facility to return user state from session or cookie
    """
    if not user: user=sessionLoad()
    return user.authenticated == True

#
# Decorator
#
#
# Exceptions
#
class PermissionError(httpexceptions.HTTPClientError):
    """
    Base class from which ``NotAuthenticatedError`` and ``NotAuthorizedError`` 
    are inherited.
    """
    pass

class NotAuthenticated(PermissionError, HTTPUnauthorized):
    """
    Raised when a permission check fails because the user is not authenticated.

    The exception is caught by the ``httpexceptions`` middleware and converted into
    a ``401`` HTTP response which is intercepted by the authentication middleware
    triggering a sign in.
    """
    required_headers = ()
    code = 401
    title = 'Not Authenticated'
    explanation = ('Please, login first')

class NotAuthorized(PermissionError, HTTPForbidden):
    """
    Raised when a permission check fails because the user is not authorized.

    The exception is caught by the ``httpexceptions`` middleware and converted into
    a ``403`` HTTP response which is intercepted by the authentication middleware
    triggering a sign in.
    """
    code = 403
    title = 'Not Authorized'
    explanation = ('Your permissions do not allow access to this resource')

class authorize(object):
    """
    Authenticator decorator
    """
    def __init__(self, clause=None):
        self.clause = clause

    @classmethod
    def before(self, clause=None):
        """
        Method to be called like a def, i.e. in __before__
        """
        if isAuthenticated():
            if isAuthorized(clause=clause):
                    return True
            else:
                raise NotAuthorized()
        else:
            raise NotAuthenticated()

    def __call__(self, fn=None):
        def wrapped_fn(*args, **kw):
            if self.isAuthenticated():
                if self.isAuthorized():
                    if fn:
                        for x in ['pylons','environ','start_response','action','controller']:
                            if kw.has_key(x): del kw[x]
                        return fn(*args, **kw)
                    else:
                        return True
                else:
                    raise NotAuthorized()
            else:
                raise NotAuthenticated()
        return wrapped_fn

    def isAuthenticated(self): return isAuthenticated()
    def isAuthorized(self): return isAuthorized(clause=self.clause)

#
# Misc
#
def expandPermClause(clause,roles,perms):
    """
    expand a permission clause, used in isAuthorized
    """
    g = re.findall(r'\w+[.]\w+',clause)
    if g:
        for el in g:
            group,perm = el.split('.')
            try:
                replace = str(perm in perms[group])
                replace = "True"
            except:
                replace = "False"
            clause = re.sub("%s" % el,replace,clause)

    g = re.findall(r'\w+',clause)
    if g:
        for el in g:
            role = el
            if not role in ['True','False','and','or','not']:
                replace = str(role in roles)
                clause = re.sub("%s" % role,replace,clause)

    return clause

