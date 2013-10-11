"""
CUBE standard library
@brief Functions to manage Numbers (Decimal)

$Id$
"""
__headUrl__ = '$HeadURL$'

import babel.numbers as babelnumbers
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING, ROUND_FLOOR  # , ROUND_05UP, ROUND_UP, ROUND_DOWN

##########################################################################

# Some usefull commodities
ZERO = Decimal('0.0')
ONE = Decimal('1.0')
TEN = Decimal('10.0')
TWO = Decimal('2.0')
HUNDRED = Decimal('100.0')

##########################################################################


def formatDecimal(value, locale, decimals=0):
    """
    @brief Format a number (either int or float) in the given locale
    @param value number to format
    @param locale locale
    @param decimals decimal places to use, default (from format_decimal) is 3 places without rounding
    @return formatted number

    BUG:
    algebrically add 10E-12 to value to prevent rounding errors
    """
    format = '###,###'
    if decimals > 0:
        format = '###,###.%s' % ('0' * decimals)

    value += 10**-12 if value > 0 else -10**-11

    return babelnumbers.format_decimal(value, format=format, locale=locale)


def parseDecimal(string, locale):
    """
    @brief Parse a string in the given locale
    @param string string
    @param locale locale
    @return Decimal
    """
    return toDecimal(babelnumbers.parse_decimal(string, locale=locale))


def toDecimal(value):
    """
    @brief Converts a value to Decimal
    @param value a string, int, float or Decimal
    @return Decimal
    """
    if value is None:
        return None
    if type(value) == type(float()):
        return Decimal("%f" % value)
    if type(value) == type(Decimal()):
        return value
    return Decimal(str(value))

##########################################################################


def roundDecimal(value, decimals=0):
    """
    @brief Rounds a Decimal (0-4 -> down, 5-9 -> up)
    @param value a string, int, float or Decimal
    @param decimals digits of decimal part
    @return Decimal
    """
    return toDecimal(value).quantize(ONE / (TEN ** decimals), ROUND_HALF_UP)


def ceilDecimal(value, decimals=0):
    """
    @brief Rounds a Decimal (0-9 -> up)
    @param value Decimal
    @param decimals digits of decimal part
    @return Decimal
    """
    return toDecimal(value).quantize(ONE / (TEN ** decimals), ROUND_CEILING)


def floorDecimal(value, decimals=0):
    """
    @brief Rounds a Decimal (0-9 -> down)
    @param value Decimal
    @param decimals digits of decimal part
    @return Decimal
    """
    return toDecimal(value).quantize(ONE / (TEN ** decimals), ROUND_FLOOR)

##########################################################################


def humanBytes(bytes, locale, reuse=False):

    m = ['B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

    limit = 1024
    r = bytes
    exp = 0

    while(r > limit):
        r = r / 1024.0
        exp += 1

    if reuse:
        return (roundDecimal(r, 3), m[exp])
    else:
        return "%s %s" % (formatDecimal(r, locale, 1), m[exp])
