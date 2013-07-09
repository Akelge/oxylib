"""

 Copyright by Andrea Mistrali <akelge@gmail.com>
 First version: 2013-06-12T10:09 CEST (+0200)

 Synopsis: LDAP O(R)M

 $Id$


TODO:
    Implement caching in connection (if usefull)
    Implement relations between objectClasses

Objects tree
------------
LDAPConnection()
    LAPQuery(LDAPObjClass)
        get(uniqueAttr)
        search(ldapFilter)


LDAPObj()
    LDAPAttribute()
"""

import ldap
import logging

log = logging.getLogger('ldapORM.engine')


# Connection
class LDAPConnection(object):

    def fromPylonsConfig(self, config=None, prefix='ldap'):
        if config:
            ldapURL = config.get('%s.url' % prefix)
            ldapDN = config.get('%s.dn' % prefix)
            ldapSecret = config.get('%s.secret' % prefix)

            return self.bind(ldapURL, ldapDN, ldapSecret)
        else:
            log.error("No valid config")

    # def __init__(self, ldapURL=None, ldapDN=None, ldapSecret=None):
    def bind(self, ldapURL, ldapDN, ldapSecret):
        """
        Bind to LDAP server
        """

        log.debug('Connecting to %s' % ldapURL)
        self.c = ldap.initialize(ldapURL)
        try:
            self.c.bind_s(ldapDN, ldapSecret)
            log.info('Connection established to %s' % ldapURL)
        except ldap.LDAPError, e:
            if type(e.message) == dict and 'desc' in e.message:
                log.warn('Cannot establish connection: %s' % e.message['desc'])
                raise Exception("LDAP error: %s" % e.message['desc'])
            else:
                log.warn('Cannot establish connection: %s' % e)
                raise Exception("LDAP error: %s" % e)

    def query(self, objclass):
        """
        Set up a query object and return it
        """
        return LDAPQuery(self, objclass)

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

    baseDN = ''
    scope = ldap.SCOPE_SUBTREE
    objclass = None

    sorting = False
    sortReverse = False

    def __init__(self, connection, objclass):
        log.debug('Init query')
        self.ldapSession = connection
        self.objclass = objclass
        self.ldapFilter = '(objectClass=%s)' % self.objclass.objectClass

    def __repr__(self):
        return "<%s(%r)>" % (self.__class__.__name__,
                             self.objclass.__name__)

    def _search(self,
                ldapFilter=None,
                attrs=None,
                baseDN=None,
                scope=None,
                attrsonly=0):
        """
        Low level LDAP search
        """

        if ldapFilter is None:
            ldapFilter = self.ldapFilter

        attrs = attrs or self.objclass.attributes()
        baseDN = baseDN or self.baseDN
        scope = scope or self.scope

        log.debug('searching with baseDN: %s, scope: %s, filter: %s, attrs: %s'
                  % (baseDN, scope, self.ldapFilter, attrs))
        try:
            result = self.ldapSession.c.search_s(baseDN,
                                                 scope,
                                                 ldapFilter,
                                                 attrs, attrsonly)

        except Exception, e:
            log.warn('search_s raised %s' % e)
            raise Exception('search_s error: %s' % e)

        log.debug('result: %s' % result)
        return result

    def _map(self, result):
        """
        Map a result on a new object
        """
        (dn, attrs) = result
        resultDict = {'dn': dn}

        if self.objclass.ldapAttributes:
            log.debug('Populating from ldapAttributes')
            for attr in self.objclass.ldapAttributes:
                # attrs is a dict {'ldapAttribute': ldapValue}
                attrVal = attrs.get(attr.name, None)
                # We build a resultDict, with ldapValues casted to python
                resultDict[attr.name] = attr.toPython(attrVal)
        else:
            log.debug('Populating plain')
            for k, v in attrs.items():
                resultDict[k] = v

        retObj = self.objclass(self.ldapSession)  # Create returned object
        retObj._map(resultDict)  # Fill the returned object

        return retObj

    def get(self, uniqueAttr):
        """
        Search an object, given the uniqueAttr, OO mode

        @param uniqueAttr: value of uniqueAttribute to search

        will search for
        (&(objectClass=resultObjectClass)(resultObjectClassUniqueAttr=uniqueAttr))
        """
        ldapFilter = self.objclass._get_filter() % uniqueAttr

        result = self._search(ldapFilter)
        if len(result) > 1:
            raise Exception("more than one result, something went wrong!!")

        if result:
            return self._map(result[0])
        else:
            return None

    def search(self, ldapFilter):
        """
        DEPRECATED: use .filter().all()
        Search ldap for objects matching ldapFilter, OO mode
        @ldapFilter: an LDAP filter

        will search for
        (&(objectClass=resultObjectClass)(ldapFilter))
        """

        log.warn('obsolete .search() ldapORM method')
        return self.filter(ldapFilter).all()

    def count(self):
        """
        Return count of object matching LDAP query
        """
        # ldapFilter = self.objclass._search_filter() % ldapFilter
        result = self._search(attrs=[],
                              attrsonly=1)

        return len(result)

    def first(self):
        """
        Return first object matchin query.
        TODO: Should be better to search, then sort, then map
        """
        return self.all()[0]

    def all(self):
        """
        Return all objects matching objectClass

        will search for
        (objectClass=resultObjectClass)

        """
        # ldapFilter = '(objectClass=%s)' % self.objclass.objectClass
        result = self._search()

        retList = map(lambda r: self._map(r), result)
        if self.sorting:
            retList.sort(key=self.sortKeyFn, reverse=self.sortReverse)
        return retList

    def dn(self, dn):
        """
        Search for a given dn
        """

        baseDN = dn
        scope = ldap.SCOPE_BASE
        ldapFilter = "(objectClass=%s)" % self.objclass.objectClass

        result = self._search(ldapFilter, baseDN=baseDN, scope=scope)

        if result:
            return self._map(result[0])
        else:
            return None

    def filter(self, ldapFilter):
        """
        Build filter
        """

        if not (ldapFilter.startswith('(') and ldapFilter.endswith(')')):
            ldapFilter = '(%s)' % ldapFilter

        self.ldapFilter = '(&(objectClass=%s)%s)' % (self.objclass.objectClass,
                                                     ldapFilter)
        return self

    def sort(self, attribute, reverse=False):
        """
        Sorting.
        Build key Function for sorting and set direction
        """

        self.sorting = True
        self.sortKeyFn = lambda e: e.__getattribute__(attribute)
        self.sortReverse = reverse

        return self

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

    objectClass = None  # Which objectClass distinguish this object
    ldapAttributes = ()
    uniqueAttr = ''
    dn = ''
    ldapSession = None

    def __init__(self, ldapSession=None):
        # self.ldapSession = ldapSession
        pass

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
        d = {'dn': self.dn}
        if self.attributes():
            d.update(dict([(attr, self.__dict__.get(attr, None)) for attr in
                           self.attributes()]))
        else:
            d.update(self.__dict__)
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
