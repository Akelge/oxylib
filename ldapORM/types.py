import datetime as dt
import logging

# log = logging.getLogger(__name__)
log = logging.getLogger('ldapORM.types')

# Attributes
############

class LDAPAttribute(object):
    """
    An LDAP Attribute.
    This is the basic class, can be scalar or list
    To define a custom type:
        1) Derive from this class
        2) Implement _toPython method
    Example:
        class Prefix(LDAPAttribute):

            def _toPython(self, value):
                return "PREFIX: %s" % value
    """
    list = False

    def __init__(self, name=None, list=False):
        """
        multi: True | False - can have multiple values?
        """
        self.name = name
        self.list = list

    def __str__(self): return str(self.name)
    def __repr__(self): return "<%s('%s')>" % (self.__class__.__name__, self.name)

    def _toPython(self, value):
        """
        Placeholder for type caster, can be overridden in derived types
        This function must convert a single value to the python type we want,
        it will be applied to the value of the field for "scalar" fields
        (list=False), to any value of list for "list" types (list=True)
        """
        return value

    def toPython(self, value):
        """
        Cast a generic value to a specific type:
            1) convert list to scalar if not multi
            2) call type specific caster _cast

        Remember: this function ALWAYS receive a list as value!!!
            
        """
        # log.debug('convert %s' % value)
        if not self.list and type(value)==list:
            # Reduce a list to a scalar
            # log.debug('not list -> converting %s to scalar' % value)
            value = value[0]

        if type(value) == list:
            # Apply specific _toPython to any value of list
            value = map(self._toPython, value)
        else:
            # Apply specific _toPython to value
            value = self._toPython(value)
        return value

# Attribute type extensions
# Custom types
###########################

class String(LDAPAttribute): pass

class Integer(LDAPAttribute):
    """
    Integer LDAP attribute.
    """

    def _toPython(self, value):
        return int(value)

class Float(LDAPAttribute):
    """
    Integer LDAP attribute.
    """

    def _toPython(self, value):
        return float(value)

class Boolean(LDAPAttribute):
    """
    Boolean LDAP attribute.
    'TRUE' or any True python value is True, else False
    """

    def _toPython(self, value):
        return (value == 'TRUE' or value == True)

class Set(LDAPAttribute):
    """
    Set LDAP attribute.
    Has a list of possible values, raise Exception if value is outside set
    """

    def __init__(self, name=None, list=False, set=[]):
        super(Set, self).__init__(name, list=list)
        self.set = set

    def _toPython(self, value):
        if not len(self.set): return value
        if not value in self.set:
            raise Exception("Wrong value: %s not in %s" % (value, self.set))
        return value

class Datetime(LDAPAttribute):
    """
    Datetime LDAP attribute
    Convert an LDAP date (20130417153059Z) to a datetime
    """

    def _toPython(self, value):
        # log.debug('converting %s to datetime' % value)
        if value:
            return dt.datetime.strptime(value, "%Y%m%d%H%M%SZ")
        else:
            return None

class Relation(LDAPAttribute):
    """
    Relation to another LDAPObject class.
    Usage:
        Relation('refname', cls, filter)
    """

    def __init__(self, refname, objclass, ldapFilter, list=False):
        super(Relation, self).__init__(name=refname, list=list)
        self.objclass = objclass
        self.ldapFilter = ldapFilter
