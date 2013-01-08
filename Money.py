# -*- coding: utf8 -*-
"""
Oxysoft standard library
Money classes
$Id$
"""

from oxylib.customtypes import sdict
import decimal as dc
from babel import numbers as n

# *************************************************************************** #
# MONEY FOR ALL
# *************************************************************************** #

class CurrencyInterface(object):
    """
    Interface to Currencies. Must be extended for real implementation.
    A Currency object has this structure

        currency.id = 0
        currency.label = 'EUR'
        currency.symbol = '€' # UTF-8
        currency.html = '&html;'

    classmethod currencies must return all defined currencies object
    """

    def __init__(self, id=None, label=None, symbol=None, html=None):
        self.id = id
        self.label = label
        self.symbol = symbol
        self.html = html

    def __repr__(self): return "<%s(%s)>" % (self.__class__.__name__, self.id)
    def __str__(self):
        if isinstance(self.symbol, unicode):
            return self.symbol.encode('utf8')
        else:
            return self.symbol
    def __int__(self): return self.id
    def __eq__(self, other): return self.id == other.id

    def __lt__(self, other):
        """
        It is not possible to compare different currencies
        """
        return False
    __le__ = __lt__

    @classmethod
    def currencies(cls):
        raise NotImplementedError, 'Extend %s and implement this method' % cls.__name__

    @classmethod
    def byId(cls, id):
        """
        Factory
        """
        raise NotImplementedError, 'Extend %s and implement this method' % cls.__name__

    @classmethod
    def byLabel(cls, label):
        raise NotImplementedError, 'Extend %s and implement this method' % cls.__name__

    @classmethod
    def bySymbol(cls, symbol):
        raise NotImplementedError, 'Extend %s and implement this method' % cls.__name__

    def toDict(self):
        return dict(id=self.id, label=self.label,
                symbol=self.symbol,
                html=self.html)

class MoneyInterface(object):
    __roundfactor = dc.Decimal('0.01')
    __currencyclass__ = None

    def __new__(cls, amount=None, currency=None):
        if amount is None and currency is None:
            return None
        else:
            return object.__new__(cls)

    def __init__(self, amount, currency):

        self.__currencyclass__ = self.__class__.__currencyclass__
        self.currency_obj = None # Caching object
        if not self.__currencyclass__:
            raise NotImplementedError, "__currencyclass__ is not defined. Define a complete Currency class"

        """
        Initialize from amount and currency
        Currency can be:
            a Currency object
            an integer (id of currency object)
        """
        self.amount=dc.Decimal(str(amount))

        if isinstance(currency, self.__currencyclass__):
            self.currency_obj = currency
            self.currency_id = currency.id
        elif isinstance(currency, int):
            self.currency_id = currency


    @property
    def currency(self):
        # get currency
        # cache currency object at first call (or when id is changed)
        if not self.currency_obj or self.currency_obj.id <> self.currency_id :
            self.currency_obj = self.__currencyclass__.byId(self.currency_id)
        return self.currency_obj

    @currency.setter
    def currency(self, currency):
        # set currency
        if currency is None:
            self.currency_id = None
        else:
            self.currency_id = currency.id


    def __str__(self): return "%.2f %s" % (self.rounded, self.currency)
    def __repr__(self): return "<Money(amount=%.2f, currency=%s)>" % (self.amount, self.currency.id)

    # Algebra
    def __eq__(self, other): return (self.amount == other.amount) and (self.currency_id == other.currency_id) 

    def __lt__(self, other):
        return (self.amount < other.amount) and (self.currency_id == other.currency_id)
        # if self.currency_id == other.currency_id:
            # return self.amount < other.amount
        # else:
            # raise Exception('It is not possible to compare %s with different currencies' % self.__class__.__name__)

    def __le__(self, other):
        return (self.amount <= other.amount) and (self.currency_id == other.currency_id)
        # if self.currency_id == other.currency_id:
            # return self.amount <= other.amount
        # else:
            # raise Exception('It is not possible to compare %s with different currencies' % self.__class__.__name__)

    def __sub__(self, other):
        if isinstance(other, self.__class__):
            if self.currency_id == other.currency_id:
                return self.__class__(amount = self.amount-other.amount, currency = self.currency)
            else:
                raise Exception('It is not possible to subtract %s with different currencies' % self.__class__.__name__)
        else:
            return self.__class__(amount = self.amount-dc.Decimal(str(other)), currency = self.currency)

    def __rsub__(self, other):
        if isinstance(other, self.__class__):
            if self.currency_id == other.currency_id:
                return self.__class__(amount = other.amount-self.amount, currency = self.currency)
            else:
                raise Exception('It is not possible to subtract %s with different currencies' % self.__class__.__name__)
        else:
            return self.__class__(amount = dc.Decimal(str(other))-self.amount, currency = self.currency)


    def __add__(self, other):
        if isinstance(other, self.__class__):
            if self.currency_id == other.currency_id:
                return self.__class__(amount = self.amount+other.amount,
                        currency = self.currency_obj)
            else:
                raise Exception('It is not possible to sum %s with different currencies' % self.__class__.__name__)
        else:
            return self.__class__(amount = self.amount+other, currency =
                    self.currency_obj)
    __radd__ = __add__

    def __div__(self, div):
        return self.__class__(amount = self.amount/div,
                currency=self.currency_obj)
    def __rdiv__(self, div):
        return self.__class__(amount = div/self.amount,
                currency=self.currency_obj)

    def __mul__(self, mul):
        return self.__class__(amount=self.amount*mul,
                currency=self.currency_obj)
    __rmul__ = __mul__

    @property
    def rounded(self):
        """
        Return amount rounded to correct decimal places
        """
        return self.amount.quantize(self.__class__.__roundfactor)

    # For oxylib.formatter.Formatter
    def toDict(self):
        return dict(amount=float(self.amount), currency=self.currency.toDict())

    def format(self):
        return n.format_currency(self.amount, self.currency.label, u'#,##0.00 ¤')

    def html(self, locale=None):
        if locale:
            return "%s %s" % (n.format_currency(self.rounded, self.currency.label,
                u'#,##0.00', locale=locale), self.currency.html)
        else:
            return "%s %s" % (n.format_currency(self.rounded, self.currency.label,
                u'#,##0.00', locale=locale), self.currency.html)

    # Shortcuts to currency
    # @property
    # def label(self): return self.currency_obj.label
    # @property
    # def symbol(self): return self.currency_obj.symbol
    # @property
    # def html(self): return self.currency_obj.html


# SAMPLE IMPLEMENTATIONS

class CurrencyPlain(CurrencyInterface):
    """
    Sample implementation of CurrencyInterface in memory,
    with some standard defaults

    >>> c1 = CurrencyPlain(1, 'EUR', '€', '&euro;')
    >>> c2 = CurrencyPlain(2, 'USD', '$', '$')
    >>> c3 = CurrencyPlain(3, 'GBP', '£', '&pound;')
    >>> print c1
    €
    >>> c1 == c2
    False
    >>> c1 < c2
    False

    """
    _currencies = []

    def __init__(self, id, label, symbol, html):
        CurrencyInterface.__init__(self, id, label, symbol, html)
        self.__class__._currencies.append(self)

    @classmethod
    def currencies(cls):
        return cls._currencies

    @classmethod
    def byId(cls, id):
        c = [x for x in cls._currencies if x.id == int(id)]
        if c: return c[0]

    @classmethod
    def byLabel(cls, label):
        c = [x for x in cls._currencies if x.label == label]
        if c: return c[0]

    @classmethod
    def bySymbol(cls, symbol):
        c = [x for x in cls._currencies if x.symbol == symbol]
        if c: return c[0]


class MoneyPlain(MoneyInterface):
    """
    Implementation in plain mode of Money

    >>> c1 = CurrencyPlain(1, 'EUR', '€', '&euro;')
    >>> c2 = CurrencyPlain(2, 'USD', '$', '$')

    >>> m1 = MoneyPlain(100, 1)
    >>> print m1
    100.00 €
    >>> m1+10
    <Money(amount=110.00, currency=1)>
    >>> 2*m1
    <Money(amount=200.00, currency=1)>
    >>> m1/2
    <Money(amount=50.00, currency=1)>

    >>> m2 = MoneyPlain(200, 1)
    >>> m1 < m2
    True
    >>> m1 <= m2
    True
    >>> m1 == m2
    False
    >>> m1+m2
    <Money(amount=300.00, currency=1)>

    >>> m3 = MoneyPlain(100, 2) # An other currency
    >>> m1 < m3
    False
    >>> m1 > m3
    False
    >>> m1 == m3
    False

    """
    __currencyclass__ = CurrencyPlain


if __name__ == "__main__":
    import doctest
    doctest.testmod()
