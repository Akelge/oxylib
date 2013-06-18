# -*- coding: utf-8 -*-
"""
SQL Plus class

Add some shortcut and utilities to SQLAlchemy declarative_base object

Must be imported in <app>/lib/base.py

$Id$
"""

from sqlalchemy import MetaData, schema, types, orm, sql, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.properties import CompositeProperty
from sqlalchemy.ext.declarative import declared_attr

from oxylib.Money import MoneyInterface, CurrencyInterface

from oxylib.pylons.formatter import Formatter, json

Session = scoped_session(sessionmaker())
session = Session

metadata=MetaData()

def init_oxylib(pySession, pyMetadata):
    """
    Append a call to this function at the end of init_model
    (PROJECT/model/meta.py or PROJECT/model/__init__.py) to set Session in oxylib equal
    to Session in PROJECT
    Must receive Session and Metadata (eventually use Base.metadata)
    """
    global Session, metadata, engine

    metadata=pyMetadata
    Session=pySession
    engine=Session.bind.engine


class SQLError(Exception):
    pass

# ###########################################################################################################

class SQLPlus(object):
    """
    Class with utilities to work on tables with integer PK called 'id'
    """

    def __int__(self): return int(self.id)
    def __repr__(self): return "<%s(%s)>" % (self.__class__.__name__, self.id)
    def __lt__(self, other): return int(self.id) <  int(other.id)
    def __le__(self, other): return int(self.id) <= int(other.id)
    def __eq__(self, other):
        if other != None:
            return self.id == other.id
        else:
            return False

    # SQL Shortcuts

    @classmethod
    def all(cls, order_by='id', filter=None):
        """
        Shortcut. Return all records from a table, ordered by id, as default
        Filter is a list of conditions
        """
        query=Session.query(cls)
        if filter: query.filter(and_(*filter))
        if order_by: query=query.order_by(getattr(cls, order_by))
        return query.all()

    @classmethod
    def get(cls, id):
        """
        Shortcut. Get a record by id
        """
        item = Session.query(cls).get(id)
        if item:
            return Session.query(cls).get(id)
        else:
            return None
            # raise SQLError()

    @classmethod
    def get_by(cls, field, value):
        """
        Shortcut. Get a record by a specific field value
        """
        return Session.query(cls).filter(getattr(cls, field) == value).first()

    def update(self, field, value):
        """
        Shortcut to update a field value
        """
        setattr(self, field, value)
    ##

    # Metadata quick access

    @classmethod
    def table(cls):
        return cls.__table__

    @classmethod
    def columns(cls):
        return cls.__table__.c

    @classmethod
    def column(cls, col):
        return cls.columns().get(col, None)

    ##

    # Converters and formatters

    @property
    def dict(self):
        """
        Shortcut
        """
        return self.toDict()

    def toDict(self):
        """
        Convert a record to a python dict, using table fields as keys
        Used by oxylib.pylons.formatter.Formatter

        Any custom type, any custom class should have a method "toDict" that
        returns a string-serialized representation.
        This repr should be a string, for simple types, a dict for complex one
        """
        import copy

        retDict={}
        props = copy.copy(self.__mapper__._props)
        # Clean composite columns, delete all columns that compose those
        for (k,v) in props.items():
            if isinstance(v, orm.properties.CompositeProperty):
                for col in props[k].columns:
                    props.pop(col.name)

        for (k,v) in props.items():
            val = getattr(self, k)
            if type(val) in [types.Time, types.Date, types.DateTime]:
                    retDict[k]=val.isoformat()
            elif hasattr(val, 'toDict') and val:
                retDict[k] = val.toDict() # toDict has to be implemented for complex values
            else:
                retDict[k]=val
        return retDict

    # Create from dict/JSON
    @classmethod
    def fromDict(cls, dict):
        obj = cls()
        for k,v in dict.items():
            if hasattr(obj, k):
                setattr(obj, k, obj.column(k).type.python_type(v))
        return obj

    # Formatting
    def format(self, fmt='json'):
        """
        Return formatter object
        """
        return Formatter(self, fmt)

    @property
    def json(self): return Formatter(self).toJSON()

    @property
    def csv(self): return Formatter(self).toCSV()
    ##

# ###########################################################################################################
# # Currency and Money class using SQLAlchemy backend


class CurrencySQLAlchemy(SQLPlus, CurrencyInterface):
    """
    Implementation of oxylib.Money.CurrencyInterface using SQLAlchemy as backend
    Can be extended, actually to define tablename

    >>> class Currency(CurrencySQLAlchemy): pass
    >>> c = Currency()
    >>> c.label = 'USD'
    >>> c.symbol = '$'
    >>> c.html = '$'
    >>> print c
    $
    """

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = schema.Column(types.Integer, schema.Sequence('%s_seq_id' % __tablename__, optional=True), primary_key=True)
    label = schema.Column(types.Unicode(3), nullable=False, unique=True, default=u'')
    symbol = schema.Column(types.Unicode(1), nullable=False, default=u'¤')
    html = schema.Column(types.Unicode, nullable=False, default=u'&curren;')

    @classmethod
    def currencies(cls): return cls.all()

    @classmethod
    def byId(cls, id): return Session.query(cls).get(id)
    @classmethod
    def byLabel(cls, label): return cls.get_by('label', label)
    @classmethod
    def bySymbol(cls, symbol): return cls.get_by('symbol', symbol)

class MoneySQLAlchemy(MoneyInterface):
    """
    Implementation of oxylib.Money.MoneyInterface using SQLAlchemy as backend
    To be used for custom type definition

    >>> class Currency(CurrencySQLAlchemy): pass
    >>> c = Currency()
    >>> c.label = 'USD'
    >>> c.symbol = '$'
    >>> c.html = '$'
    >>> class Money(MoneySQLAlchemy): __currencyclass__ = Currency

    >>> m = Money(100, c)
    >>> print m
    100.00 $
    >>> from oxylib.locale import Locale
    >>> print m.html(locale=Locale('it_IT'))
    100,00 $
    """
    __currencyclass__ = CurrencySQLAlchemy

    def __composite_values__(self):
        return (self.amount, self.currency_id)
    @property
    def widgetFormat(self):
        return "%.2f,%d" % (self.amount, self.currency_id)

def compositeMoney(field, cls, default=None):
    """
    Function to create a composite, a pair of fields to contain Money values
    """
    default_amount = default_currency_id = {}
    if default:
        default_amount = {'server_default':str(default.__composite_values__()[0])}
        default_currency_id = {'server_default':str(default.__composite_values__()[1])}
    return orm.composite(cls,
            schema.Column('%s_amount' % field, types.Numeric, **default_amount),
            schema.Column('%s_currency_id' % field, types.Integer,
                schema.ForeignKey('%s.id' % cls.__currencyclass__.__tablename__),
                **default_currency_id),
            comparator_factory=MoneyComparator)

class MoneyComparator(CompositeProperty.Comparator):
    def __commontest(self, other):
        return self.__clause_element__().clauses[1] == other.__composite_values__()[1]

    def __lt__(self, other):
        return sql.and_(
                *[self.__clause_element__().clauses[0] < other.__composite_values__()[0],
                    self.__commontest(other)])
    def __le__(self, other):
        return sql.and_(
                *[self.__clause_element__().clauses[0] <= other.__composite_values__()[0],
                    self.__commontest(other)])
    def __ge__(self, other):
        return sql.and_(
                *[self.__clause_element__().clauses[0] >= other.__composite_values__()[0],
                    self.__commontest(other)])
    def __gt__(self, other):
        return sql.and_(
                *[self.__clause_element__().clauses[0] > other.__composite_values__()[0],
                    self.__commontest(other)])



if __name__ == "__main__":
    import doctest
    doctest.testmod()
