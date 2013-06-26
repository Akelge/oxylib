Pylons AAA Module

Inspired by RADIUS, uses AV Pairs, couples of key/values (i.e. a Python
dictionary), to talk with plugins.

It is possible to extend AAA methods writing plugins, def's that receive as
input a dictionary (avPairs) and return back an altered dictionary. Plugins
are tried in the order defined in configuration.

Standard fields, that an AuthenticatedUser SHOULD always have are:
     username: ditto
     password: ditto
     realname: the real name (optional)
     gid: id of the main group (optional)
     key: a unique key, user for checking validity of session
     login_time: time of last login
     last_check: time of last key validity check
     isAuthenticated: True of False
     perms: a dictionary with groupname as key and an array of perms (strings)
     as values

Plugins can add other fields, if it is required for a particular auth method
or for a particular application

ACTION or AUTHENTICATION PHASES

This module follows AAA (Authenticatin/Authorization/Accounting) phases, with
some slight modification:

1) Authentication phase is split in two parts:
    1.a) auth: credentials (username/password) are checked against a
    DB to verify they match. If they match isAuthenticated is set to True and
    a unique key is issued.

    1.b) check: if the user has already been authenticated (isAuthenticated ==
    True) and a unique key has been issued, next checks MUST only check key
    validity. Any next request WILL pass the key to the check plugin and it is
    plugin's work to verify if it is valid yet.
    This solution has been adopted to interact with Cookies in web
    applications: the key is suitable to be set as Cookie value.

2) Authorization phase SHOULD set perms dictionary. perms dict is made like:
    {
        'group1': ['perm1', 'perm2'],
        'group2': ['perm2', 'perm3']
    }

    groupN and permN are strings that are checked by authorize() decorator.
    If there is a single group (i.e. we must check only perms), it is advised
    to use "DEFAULT" as group name.

3) Accounting phase is split in two, too:
    3.a) startAcct: this plugin MUST record start of authentication, setting
    last_login in user.avPairs (if not already set by other plugins) and
    SHOULD record start of session in its own way, plus recording Unique Key
    if it has a check method.

    3.b) stopAcct: this plugin MUST delete last_login in user.avPairs (if not
    already deleted by other plugins) and SHOULD record end of session in its
    own way.

This implies that if auth plugin is implemented for a method check plugin must
be implemented too, the same for startAcct/stopAcct.

Example:
In [2]: user=auth.AuthenticatedUser(username=u'test', password=u'test123')
In [3]: user.avPairs
Out[3]: 
{'isAuthenticated': True,
 'key': 'd446f75ce0852ffafb2dfc3e6c8b80e02115f093',
 'last_check': <DateTime('2010-05-28T15:20:30 UTC')>,
 'login_time': <DateTime('2010-05-28T15:20:30 UTC')>,
 'password': u'test123',
 'realname': u'Test User',
 'username': u'test'}

In this example 'user' object of type AuthenticatedUser is created and, first,
username and password are set, then, after calling auth, authz and acct
plugins, the dictionary is complete. Note that 'realname', 'login_time' and
'last_check' have been added by the plugins.


PLUGINS
Plugins name should be <action>_<method> with:
     action: one of auth, check, authz, startAcct, stopAcct (logout)
     method: name of the method used (plain, DB, LDAP)
 
For example:

     def auth_sqlalchemy(avPairs):
         pass
     def check_sqlalchemy(avPairs):
         pass
     def authz_sqlalchemy(avPairs):
         pass
     def startAcct_sqlalchemy(avPairs):
         pass
     def stopAcct_sqlalchemy(avPairs):
         pass
     def stopAcct_plain(avPairs):
         pass

They need to be registered, before being user, using classmethod AuthenticatedUser.register_plugin(fn)
For example:
     def auth_test(avPairs):
         avPairs.isAuthenticated=True
         return avPairs
     AuthenticatedUser.register_plugin(auth_test)

In the .ini file we MUST write the list of methods that we should use:

    oxylib.auth = True ; App supports authentication via this lib
    oxylib.auth.nopermok = True ; User with NO PERMS is authorized, if there
                                 ; is no clause
    oxylib.auth.modules = sqlalchemy,plain ; List of methods App should use
 
If a method does not have a plugin registered for an action, it is skipped and a Warning is raised.

It is possible to add, in the .ini file, othe configuration parts for auth
methods:

    oxylib.auth.sqlalchemy.userModel = model.User
    oxylib.auth.sqlalchemy.key_ttl = 3600

SESSION

After successfull login an object of type AuthenticatedUser is written in the session.
After logout the session is cleared of AuthenticatedUser.

MIDDLEWARE
It is necessary to add a middleware layer to app, to intercept 401 and 403
errors raised by authorize(). Example:

    from oxylib.auth.middleware import OxylibAuthMiddleware

Remember to load Authentication Middleware before SessionMiddleWare!!!

Then, if we want to use standard library base_plugins we should add:

    from oxylib.auth.base_plugins import *

Instead,if we wrote our custom plugins we should add:

    from PROJECT.lib.auth import *

or something similar

    def make_app(global_conf, full_stack=True, static_files=True, **app_conf):
        # Configure the Pylons environment
        config = load_environment(global_conf, app_conf)

        # The Pylons WSGI app
        app = PylonsApp(config=config)

        app = OxylibAuthMiddleware(app, config)

        [snip]

        return app


EXAMPLES

Here is a complete example using sqlalchemy:

from oxylib.auth import AuthenticatedUser
from oxylib.auth import getConfig

# SQLALCHEMY
def auth_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
    """
    userModel=eval(getConfig('sqlalchemy.userModel'))
    query=meta.Session.query(userModel).filter(userModel.username == avPairs.username)
    user=query.filter(userModel.password==avPairs.password).first()
    if user:
        user.key=avPairs.key
        user.last_action=DateTime.DateTime()
        meta.Session.commit()
        avPairs.isAuthenticated=True
        avPairs.last_check=user.last_action
        avPairs.realname=user.realname
    else:
        avPairs.isAuthenticated=False
        raise('Invalid credentials')
    return avPairs

AuthenticatedUser.register_plugin(auth_sqlalchemy)

def check_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
    """
    userModel=eval(getConfig('sqlalchemy.userModel'))
    user=meta.Session.query(userModel).filter(userModel.key==avPairs.key).first()
    if user:
        if int(user.last_action) > int(DateTime.DateTime())-int(config['oxylib.auth.keyttl']):
            user.last_action=DateTime.DateTime()
            user.login_time=user.last_login
            meta.Session.commit()
            avPairs.isAuthenticated=True
            avPairs.last_check=user.last_action
            avPairs.realname=user.realname
    else:
        avPairs.isAuthenticated=False
        raise('Invalid credentials')
    return avPairs

AuthenticatedUser.register_plugin(check_sqlalchemy)


def authz_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
        config['oxylib.auth.sqlalchemy.ugpModel']
    """
    userModel=eval(getConfig('sqlalchemy.userModel'))
    ugpModel=eval(getConfig('sqlalchemy.ugpModel'))
    avPairs.perms={}

    user=meta.Session.query(userModel).filter(userModel.username == avPairs.username).first()
    if user:
        ugp=meta.Session.query(ugpModel).filter(ugpModel.user == user).all()
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
    userModel=eval(getConfig('sqlalchemy.userModel'))
    user=meta.Session.query(userModel).filter(userModel.username==avPairs.username).first()
    user.last_login=DateTime.DateTime()
    meta.Session.commit()

    avPairs.login_time=user.last_login
    return avPairs

AuthenticatedUser.register_plugin(startAcct_sqlalchemy)

def stopAcct_sqlalchemy(avPairs):
    """
    use
        config['oxylib.auth.sqlalchemy.userModel']
    """
    userModel=eval(getConfig('sqlalchemy.userModel'))
    user=meta.Session.query(userModel).filter(userModel.username==avPairs.username).first()
    user.login_time=None
    user.key=AuthenticatedUser.uuid()
    meta.Session.commit()

    avPairs.login_time=None
    avPairs.isAuthenticated=False
    return avPairs

AuthenticatedUser.register_plugin(stopAcct_sqlalchemy)


Here is the relevant excerpt from development.ini:

# AAA
# Authentication, Authorization, Accounting
oxylib.auth.authentication_modules = mod1, mod2
oxylib.auth.authorization_modules = mod1, mod2
oxylib.auth.accounting_modules = mod1, mod2
oxylib.auth.sqlalchemy.userModel = model.User
oxylib.auth.sqlalchemy.ugpModel = model.UGP
oxylib.auth.sqlalchemy.keyttl = 3600

/* vim: set ts=4 sw=4 tw=78 ft= : */
