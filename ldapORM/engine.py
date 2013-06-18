"""

 Copyright by Andrea Mistrali <akelge@gmail.com>
 First version: 2013-06-12T10:09 CEST (+0200)

 Synopsis: LDAP O(R)M

 $Id$


TODO:
    Implement caching

Objects tree
------------
LDAPConnection()
    LAPQuery(LDAPObjClass)
        get(uniqueAttr)
        search(ldapFilter)


LDAPObj()
    LDAPAttribute()
"""

try:
    from pylons import config
    pylonsEnv=True
except:
    pylonsEnv=False

import ldap
import logging

log = logging.getLogger('ldapORM.engine')

# Connection
class LDAPConnection(object):

    @classmethod
    def fromPylonsConfig(cls, prefix='ldap'):
        if pylonsEnv:
            ldapURL = config.get('%s.url' % prefix)
            ldapDN = config.get('%s.dn' % prefix)
            ldapSecret = config.get('%s.secret' % prefix)

            return cls(ldapURL, ldapDN, ldapSecret)
        else:
            print "Not under pylons env!"

    def __init__(self, ldapURL, ldapDN, ldapSecret):
        """
        Bind to LDAP server and prepare query object
        """

        self.c = ldap.initialize(ldapURL)
        try:
            self.c.bind_s(ldapDN, ldapSecret)
            log.info('Connection established to %s' % ldapURL)
        except ldap.LDAPError, e:
            if type(e.message) == dict and e.message.has_key('desc'):
                raise Exception("LDAP error: %s" % e.message['desc'])
            else:
                raise Exception("LDAP error: %s" % e)
            raise Exception(e.message.get('desc'))

        # Add LDAPQuery object
        self.query=LDAPQuery(self)

# Query
class LDAPQuery(object):
    """
    Execute a search on LDAP.
    Usage:
        c = LDAPConnection(url, dn, secret)

        # return a scalar result, an instance of ResultClass, with LDAP
        # Attributes mapped on ResultClass attributes
        c.query(ResultClass).get(uniqueAttr) 

        # return a list of ResultClass instances, with LDAP Attributes mapped
        # on ResultClass attributes
        c.query(ResultClass).search(ldapFilter)

        # Using a differente baseDN
        c.query(ResultClass).baseDN(base).get(uniqueAttr)

        # Changing scope
        c.query(ResultClass).scope(ldap.SCOPE_ONELEVEL).get(uniqueAttr)
    """

    _baseDN=''
    _scope = ldap.SCOPE_SUBTREE

    def __init__(self, connection):
        self._ldapConnection = connection

    def __call__(self, objclass):
        self._baseDN=''
        self._scope = ldap.SCOPE_SUBTREE
        self._objclass=objclass
        return self

    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__, self._objclass)

    def _search(self, ldapFilter, attrs=None, baseDN=None, scope=None):

        attrs = attrs or self._objclass.attributes()
        baseDN = baseDN or self._baseDN
        scope = scope or self._scope

        log.info('searching with baseDN: %s, scope: %s, filter: %s, attrs: %s'
                % (baseDN, scope, ldapFilter, attrs))
        try:
            result = self._ldapConnection.c.search_s(baseDN,
                    scope, ldapFilter, attrs)
        except Exception, e:
            log.info('search_s raised %s' % e)
            raise Exception('search_s error: %s' % e)

        log.debug('result: %s' % result)
        return result

    def _map(self, result):
        """
        Map a result on a new object
        """
        (dn, attrs) =  result
        resultDict = { 'dn': dn }

        for attr in self._objclass.ldapAttributes:
            attrVal = attrs.get(attr.name, None)
            resultDict[attr.name]=attr.toPython(attrVal)

        retObj = self._objclass() # Create returned object
        retObj._map(resultDict) # Fill the returned object

        return retObj

    def scope(self, scope):
        """
        Set scope for searches
        """
        self._scope = scope
        return self

    def baseDN(self, baseDN):
        """
        Set baseDN for searches
        """
        self._baseDN = baseDN
        return self

    def get(self, uniqueAttr):
        """
        Search an object, given the uniqueAttr
        """
        ldapFilter = self._objclass._get_filter() % uniqueAttr

        result = self._search(ldapFilter)
        if len(result)>1:
            raise Exception("more than one result, something went wrong!!")

        if result:
            return self._map(result[0])
        else:
            return None

    def search(self, ldapFilter):
        """
        Search ldap for objects matching ldapFilter
        @ldapFilter: an LDAP filter
        """

        ldapFilter = self._objclass._search_filter() % ldapFilter
        result = self._search(ldapFilter)

        return map(lambda r: self._map(r), result)

    def dn(self, dn):

        baseDN = dn
        scope = ldap.SCOPE_BASE
        ldapFilter = "(objectClass=%s)" % self._objclass.objectClass

        result = self._search(ldapFilter, baseDN=baseDN, scope=scope)

        if result:
            return self._map(result[0])
        else:
            return None



# Result object
class LDAPObject(object):
    """
    Generic class with LDAP generic methods: build filters, map an LDAP result
    on an object

    @objectClass:  objectClass of this kind of Object
    @ldapAttributes: all LDAP Attributes we want to read from LDAP
    uniqueAttr: unique attribute of this object (uid, zimbraId), used for "get"
    queries

    We must derive from this generic class:

        class PosixUser(LDAPObject):
            objectClass='posixAccount'
            ldapAttributes=(LDAPAttribute('uid'),
            LDAPAttribute('userPassword'))
            uniqueAttr='uid'

    """

    objectClass = None # Which objectClass distinguish this object
    ldapAttributes = ()
    uniqueAttr = ''
    dn = ''

    def __str__(self):
        return str(self.dict)

    def __repr__(self):
        return "<%s('%s')>" % (self.__class__.__name__,
                self.__dict__.get(self.uniqueAttr, None))

    def __eq__(self, other):
        return self.__getattribute__(self.uniqueAttr) == other.__getattribute__(other.uniqueAttr)

    @classmethod
    def _get_filter(cls):
        return "(&(objectClass=%s)(%s=%%s))" % (cls.objectClass, cls.uniqueAttr)

    @classmethod
    def _search_filter(cls):
        return "(&(objectClass=%s)%%s)" % (cls.objectClass)

    def _map(self, ldapDict):
        self.__dict__.update(ldapDict)

    @property
    def dict(self):
        """
        Commodity: convert object attrs into dictionary
        """
        d = { 'dn': self.dn }
        d.update(dict([(attr, self.__dict__.get(attr, None)) for attr in
                self.attributes()]))
        return d

    @classmethod
    def attributes(cls):
        """
        tuple, read only
        """
        return tuple([a.name for a in cls.ldapAttributes])

    @classmethod
    def getAttribute(cls, attrname):
        return [a for a in cls if a.name == attrname][0]
