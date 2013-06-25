"""
\package oxylib.salog.handlers
\details Oxylib standard library - SQLAlchemy Logging handlers

$Id$
"""
__headUrl__  = '$HeadURL$'

from sqlalchemy import schema, types, orm
from sqlalchemy.ext.declarative import declarative_base
import logging
from datetime import datetime
from pylons import session, request, response
from paste.util.import_string import eval_import

class SAHandler(logging.Handler):
    """
    \brief Logging handler that logs on a DB via SQLAlchemy ORM
    \param model (\c str) application ORM model 
    \param tablename (\c str) name of the table that would contain log records. Defaults to 'logs'
    \param sessKey (\c str) session key that contains Username. Defaults to 'oxylib.auth.user'
    \param level (\c str) level of logging. Defaults to logging.NOTSET (0)

    Usage example:
        \code
        [handler_salog]
        class = oxylib.salog.SAHandler
        args = ('PROJECTNAME.model',)
        level = NOTSET
        \endcode

    """
    def __init__(self, model,
            tablename="logs",
            level=logging.NOTSET):

        logging.Handler.__init__(self, level)
        # grow model with our class
        if isinstance(model, (str, unicode)):
            model = eval_import(model)

        self.tablename = tablename

        if not hasattr(model, '_salogging'):
            model._salogging = True
            self.model = self.update_model(model)
            self.meta = self.model.meta

# SQLAlchemy part
    def update_model(self, model):
        metadata = model.Base.metadata

        class SALog(object):
            pass

        log_table = schema.Table(
                self.tablename,
                metadata,
                schema.Column("id", types.Integer, primary_key=True),
                schema.Column("date", types.TIMESTAMP, default=datetime.now),
                ## Name of the logger that emitted record.
                schema.Column("name", types.Unicode(256)),
                ## Name of the source file of origin.
                schema.Column("filename", types.Unicode(256)),
                ## Line number in the source file of origin.
                schema.Column("lineno", types.Integer),
                ## Name of the function of origin.
                schema.Column("func", types.Unicode(128)),
                ## Numerical level of logging \see logging.getlevelName
                schema.Column("level", types.Integer, default=logging.NOTSET),
                ## Username: anonymous if we do not require authentication
                ## None if called from controller
                schema.Column("user", types.Unicode(128), default=None),
                ## IP address, gotten from environment
                schema.Column("addr", types.Unicode(15), default=None),
                schema.Column("msg", types.Unicode(1024), default=u"--MARK--")
                )

        orm.mapper(
                SALog,
                log_table,
                )

        model.SALog = SALog
        model.SALog.__table__ = log_table
        model.SALog.__tablename__ = str(log_table)
        return model

# Logging part
    def setLevel(self, level=logging.NOTSET):
        self.level=level

    def emit(self, record):
        # We do not log sqlalchemy queries to not exceed recursion limit
        if record.name.startswith('sqlalchemy.engine'):
            return

        SArecord=self.model.SALog()

        SArecord.date = datetime.fromtimestamp(record.created)
        SArecord.name = u"%s" % record.name
        SArecord.filename = u"%s" % record.filename
        SArecord.lineno = "%d" % record.lineno
        SArecord.func = u"%s" % record.funcName
        SArecord.level = record.levelno
        SArecord.msg = u'%s' % record.getMessage()

# We want to log username only in controllers via session (or environment)
# so we try to get it from session, else we log the fact that there is no SESSION
        try:
            if request.environ.has_key('REMOTE_USER'):
                SArecord.user=u"%s" % request.environ.get('REMOTE_USER')
        except:
            # Let's leave user value to None
            pass

        try:
            SArecord.addr=u"%s" % request.environ.get('REMOTE_ADDR')
        except:
            # Let's leave addr value to None
            pass

        self.meta.Session.add(SArecord)
        try:
            self.meta.Session.commit()
        except:
            self.meta.Session.rollback()

