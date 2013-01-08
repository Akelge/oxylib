"""
 Copyright Andrea Mistrali 2012

 AAA Module
 Inspired by RADIUS, users AV Pairs, i.e. a dictionary.
 Base Plugins and Sample implementations

 $Id$

"""
from pylons import config
from oxylib.utils import getException
from oxylib.DateTime import DateTime

from auth import AuthenticatedUser
from auth import getConfig, ckey
from paste.util.import_string import eval_import

import logging

def now():
    return DateTime() 

log = logging.getLogger(__name__)

##############
# SQLALCHEMY #
##############
def auth_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
    """
    model = eval_import(getConfig('sqlalchemy.model'))
    userModel=eval(getConfig('sqlalchemy.userModel'))
    query=model.meta.Session.query(userModel).filter(userModel.username == avPairs.username).filter(userModel.external_auth==False)
    user=query.filter(userModel.password==avPairs.password).first()
    if user:
        avPairs.authenticated=True
        avPairs.realname=user.realname
    else:
        raise Exception("Invalid credentials")
    return avPairs

AuthenticatedUser.register_plugin(auth_sqlalchemy)

def authz_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
        config['oxylib.auth.sqlalchemy.ugpModel']
    """
    model = eval_import(getConfig('sqlalchemy.model'))
    userModel=eval(getConfig('sqlalchemy.userModel'))
    ugpModel=eval(getConfig('sqlalchemy.ugpModel'))
    avPairs.perms={}

    log.debug('trying to authorize user %s', avPairs.username)
    try:
        user=model.meta.Session.query(userModel).filter(userModel.username == avPairs.username).first()
    except Exception, e:
        log.debug('Exception %s', e)
        return {}
    log.debug('got user %r', user)
    if user:
        ugp=model.meta.Session.query(ugpModel).filter(ugpModel.user == user).all()
        log.debug('got ugp %r', ugp)
        for gp in ugp:
            glabel=str(gp.group)
            plabel=str(gp.perm)
            if avPairs.perms.has_key(glabel):
                avPairs.perms[glabel].append(plabel)
            else:
                avPairs.perms[glabel]=[plabel]


    return avPairs

AuthenticatedUser.register_plugin(authz_sqlalchemy)

def startAcct_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
    """
    model = eval_import(getConfig('sqlalchemy.model'))
    userModel=eval(getConfig('sqlalchemy.userModel'))
    user=model.meta.Session.query(userModel).filter(userModel.username==avPairs.username).first()
    # user.login_time=now()
    # log.debug('update login time of %s to %s', user, user.login_time)
    model.meta.Session.commit()
    # avPairs.login_time=user.login_time
    return avPairs

AuthenticatedUser.register_plugin(startAcct_sqlalchemy)

def stopAcct_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
    """
    model = eval_import(getConfig('sqlalchemy.model'))
    userModel=eval(getConfig('sqlalchemy.userModel'))
    user=model.meta.Session.query(userModel).filter(userModel.username==avPairs.username).first()
    # user.login_time=None
    model.meta.Session.commit()
    # avPairs.login_time=user.login_time
    # avPairs.authenticated=False
    return avPairs

AuthenticatedUser.register_plugin(stopAcct_sqlalchemy)

#################
# Opendirectory #
#################
import ldap
def auth_opendirectory(avPairs):
    """
    For authentication we use authenticated bindings, i.e. we log in LDAP server
    using user name and password. This is sufficient

    Since we are on OpenDirectory (Apple LDAP implementation) we already kwow user and group
    bases, we simply need to know last part (domain part)
    """
    username='uid=%s,cn=users,%s' % (avPairs.username, getConfig('opendirectory.baseDN'))
    c = ldap.initialize(getConfig('opendirectory.url'))
    try:
        # c.bind_s(getConfig('uid=%s,cn=users,dc=cube,dc=lan') % avPairs.username, avPairs.password)
        c.bind_s(username, avPairs.password)
    except ldap.INVALID_CREDENTIALS:
        raise Exception('Invalid credentials')
    except ldap.SERVER_DOWN:
        raise Exception('LDAP server unreachable')
    except ldap.INVALID_DN_SYNTAX:
        raise Exception('Invalid DN syntax')
    except:
        (e,v) = getException()
        raise v
    # Let's get primary GID and GECOS
    filter='(uid=%s)' % (avPairs.username)
    attrs=['gidNumber', 'cn']
    base_dn='cn=users,%s' % getConfig('opendirectory.baseDN')
    l=c.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    # result is like
    # [('uid=user,cn=users,dc=example,dc=com', {'gidNumber': ['5000'], 'cn': ['xxx']})]
    #
    primaryGID=l[0][1]['gidNumber'][0]
    avPairs.gid=int(primaryGID)
    avPairs.realname=l[0][1]['cn'][0]

    avPairs.authenticated=True
    return avPairs

AuthenticatedUser.register_plugin(auth_opendirectory)

def authz_opendirectory(avPairs):
    """
    For authorization we should get Primary Group name, then all other groups the user
    belongs to.
    Since we are on OpenDirectory (Apple LDAP implementation) we already kwow user and group
    bases, we simply need to know last part (domain part)
    """
    username='uid=%s,cn=users,%s' % (avPairs.username, getConfig('opendirectory.baseDN'))
    c = ldap.initialize(getConfig('opendirectory.url'))
    try:
        c.bind_s(username, avPairs.password)
    except ldap.INVALID_CREDENTIALS:
        raise Exception('Invalid credentials')
    except ldap.SERVER_DOWN:
        raise Exception('LDAP server unreachable')
    except ldap.INVALID_DN_SYNTAX:
        raise Exception('Invalid DN syntax')
    except:
        (e,v) = getException()
        raise v

    # Let's get primary GID and GECOS
    # filter='(uid=%s)' % (avPairs.username)
    # attrs=['gidNumber', 'cn']
    # base_dn='cn=users,%s' % getConfig('opendirectory.baseDN')
    # l=c.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    # # result is like
    # # [('uid=user,cn=users,dc=example,dc=com', {'gidNumber': ['5000'], 'cn': ['xxx']})]
    # #
    # primaryGID=l[0][1]['gidNumber'][0]
    # avPairs.gid=int(primaryGID)
    # avPairs.realname=l[0][1]['cn'][0]

    ## Get primary GROUP ##
    # First we get the Primary GID
      # Then we get Primary Group cn
    filter='(gidNumber=%d)' % int(avPairs.gid)
    attrs=['cn']
    base_dn='cn=groups,%s' % getConfig('opendirectory.baseDN')

    l=c.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    #
    # [('cn=group0,cn=groups,dc=example,dc=com', {'cn': ['group0']})]
    #
    avPairs.perms['DEFAULT']=[l[0][1]['cn'][0]]
    
    # Get Additional groups
    filter='(memberUid=%s)' % avPairs.username

    l=c.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)
    # Results are like this
    # [('cn=group1,cn=groups,dc=example,dc=com', {'cn': ['group1']}),
    #  ('cn=group2,cn=groups,dc=example,dc=com', {'cn': ['group2']}),
    #  ('cn=group3,cn=groups,dc=example,dc=com', {'cn': ['group3']}),
    #  ('cn=group4,cn=groups,dc=example,dc=com', {'cn': ['group4']}),
    #  ('cn=group5,cn=groups,dc=example,dc=com', {'cn': ['group5']}),
    #  ('cn=group6,cn=groups,dc=example,dc=com', {'cn': ['group6']})]
    
    avPairs.perms['DEFAULT'].extend([g[1]['cn'][0] for g in l])
    return avPairs

AuthenticatedUser.register_plugin(authz_opendirectory)

##############################
# Plain text accounting file #
##############################
import os
def startAcct_plain(avPairs):
    avPairs.login_time=now()
    wtmpFormat="%(username)-8s %(login_time)-10s\n"
    wtmp=open(getConfig('plain.filename'), 'a+')
    wtmp.write(wtmpFormat % avPairs)
    wtmp.close()
    return avPairs

AuthenticatedUser.register_plugin(startAcct_plain)

def stopAcct_plain(avPairs):
    oldfile=getConfig('plain.filename')
    newfile="%s.tmp" % getConfig('plain.filename')
    wtmpFormat="%(username)-8s %(login_time)-10s\n"
    wtmp=open(oldfile, 'r+')
    wtmpNew=open(newfile, 'w+')
    for line in wtmp:
        if line != wtmpFormat % avPairs:
            wtmpNew.write(line)
    wtmp.close()
    wtmpNew.close()
    os.rename(newfile, oldfile)
    avPairs.login_time=None
    avPairs.authenticated=None
    return avPairs

AuthenticatedUser.register_plugin(stopAcct_plain)


