"""
CUBE standard library
@brief Model utils

$Id
"""
__headUrl__ = '$HeadURL$'

__all__ = ['typeDate', 'typeTime', 'typeDateTime']

from oxylib.DateTime import Date, DateTime, Time
# from oxylib.sqlalchemy.plus import Money
from sqlalchemy import types


class typeDate(types.TypeDecorator):

    impl = types.Date

    def get_col_spec(self):
        return "DATE"

    @property
    def python_type(self):
        return Date

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return value.toUTC().formatISO(offset=False, part='date')
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return Date(value)
        return process


class typeDateTime(types.TypeDecorator):

    impl = types.DateTime

    def get_col_spec(self):
        return "TIMESTAMP"

    @property
    def python_type(self):
        return DateTime

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return value.toUTC().formatISO(offset=False)
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return DateTime(value)
        return process


class typeTime(types.TypeDecorator):

    impl = types.DateTime

    def get_col_spec(self):
        return "TIME"

    @property
    def python_type(self):
        return Time

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return value.formatISO()
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None:
                return None
            return Time(value)
        return process
