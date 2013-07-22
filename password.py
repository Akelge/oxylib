# -*- coding: utf8
"""

 Password generation class

 $Id$

"""

"""
TODO
Implement dovecot CRAM-MD5 in pure python
"""

import crypt
import hashlib
import random
from subprocess import Popen, PIPE

salted_algo_salt_len = 4
printableChars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# All available schemas (v2.x)
# CRYPT - Unix crypt
# MD5-CRYPT - Unix MD5 enrypted password
# SHA SHA1 SHA256 SHA512 - SHA
# SMD5 - Salted MD5
# SSHA SSHA256 SSHA512 - Salted SHA: SSHA(pw, salt)=SHA(pw+salt)
# PLAIN CLEARTEXT - Synonyms
# CRAM-MD5 - Hardest one: by now we use dovecotpw/doveadm external auth
# MD5 HMAC-MD5 DIGEST-MD5 LDAP-MD5 - MD5, various encoding
# PLAIN-MD5 - Plain
# LANMAN NTLM OTP SKEY RPA - Legacy algorithms
# SHA256-CRYPT SHA512-CRYPT - Unix SHA encrypted password
# RANDOM-PLAIN # added by us returns a random password in PLAIN
# NULL # added by us for pubowner/arcowner
# EXT # added by us for external_auth users (LDAP)


class Password(object):

    basicSchemas = ['PLAIN', 'RANDOM-PLAIN', 'MD5', 'SHA256', 'EXT']  # 'CRAM-MD5'

    @classmethod
    def parse(cls, password):
        if password.startswith('{'):  # Is it already 'full'?
            schema, password = password.replace('{', '').split('}')
        else:
            schema = 'PLAIN'

        npwd = cls()
        npwd._password = password
        npwd._schema = schema
        npwd._schemaMethod = schema.lower().replace('-', '_')

        return npwd

    @classmethod
    def randchar(cls, count=8):
        return ''.join([random.choice(printableChars) for x in xrange(count)])

    @classmethod
    def schemas(cls):
        fn = lambda x: x.replace('_crypt_', '').replace('_', '-').upper()
        return tuple(map(fn, cls._py_algos()))

    @classmethod
    def _py_algos(cls):
        return tuple([x for x in cls.__dict__.keys() if x.startswith('_crypt_')])

    def __init__(self, password='', schema='PLAIN', optional=None):
        self.optional = optional

        self._schema = 'PLAIN'
        self._schemaMethod = 'plain'

        self.password = password
        self.schema = schema.upper()

    def __repr__(self):
        return r"<%s(password='%s', schema='%s')>" % (self.__class__.__name__, self.password, self.schema)

    def __str__(self):
        return self.full

    @property
    def full(self):
        return "{%s}%s" % (self.schema, self.password)

    @property
    def schema(self):
        return "%s" % self._schema

    @schema.setter
    def schema(self, schema):
        """
        Schema changing.
        If schema is the same do nothing,
        we can only go from 'PLAIN' to encrypted ones
        """

        self._schemaMethod = schema.lower().replace('-', '_')  # Lower case, no dash, for method calling

        if self._schema == schema:
            return

        if 'PLAIN' in self._schema:
            self._schema = schema
            self.password = self.password
        else:
            raise AssertionError("Cannot change schema from '%s' to '%s'" %
                                (self._schema, schema))

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, pw):
        self._password = self.encrypt(pw, optional=self.optional)

    def check(self, plainpassword):
        """
        Given a plain text password check if it the same,
        re-encrypting it, if possible.
        """
        try:
            return self.__getattribute__("_check_%s" %
                                         self._schemaMethod)(plainpassword,
                                                             optional=self.optional)
        except AttributeError:
            testpw = Password(plainpassword, schema=self.schema,
                              optional=self.optional)
            return (testpw.full == self.full)

    equal = check

    ###################
    # Encryption part #
    ###################
    def encrypt(self, pw, optional=None):
        """
        generic encrypt function.
        Call appropriate _crypto_ algo
        """
        try:
            return self.__getattribute__("_crypt_%s" % self._schemaMethod)(pw, optional=self.optional)
        except AttributeError, e:
            raise AttributeError("_crypt_%s error: %s" % (self._schemaMethod, e))
            # return self._dovecotpw(pw, optional=self.optional)

    """
    Standard signature of crypt method
    def _crypt_schema(self, pw, optional):
        return pw_encrypted_in_schema

    """
    def _b64encode(self, string):
        return string.encode('base64').rstrip()

    def _b64decode(self, string):
        return string.decode('base64')

    def _dovecotpw(self, pw, optional=None):
        """
        generic fallback, use dovecot utility
        """
        cmdArgsV1 = ['dovecotpw', '-s', self.schema, '-p', self.password]
        cmdArgsV2 = ['doveadm', 'pw', '-s', self.schema, '-p', self.password]
        try:
            proc = Popen(cmdArgsV2, stdout=PIPE, stderr=PIPE)
        except OSError:
            proc = Popen(cmdArgsV1, stdout=PIPE, stderr=PIPE)
        proc.wait()

        if proc.returncode > 0:
            raise AttributeError("Error: %s" % proc.stderr.read().rstrip())
        else:
            hashed = proc.stdout.read().rstrip()
            return hashed.split('}')[-1]

    # Helper algos
    def _crypt_cram_md5(self, pw, optional=None):
        return self._dovecotpw(pw, optional)

    # Pure python algos

    def _crypt_null(self, pw, optional=None):
        return '**NONE**'

    def _crypt_ext(self, pw, optional=None):
        """
        External authentication: authentication is not handled by DB
        We must return NULL as password
        """
        return None

    def _crypt_plain(self, pw, optional=None):
        return pw

    _crypt_cleartext = _crypt_plain

    def _crypt_random_plain(self, pw, optional=8):
        """
        optional: length of password
        """
        self.schema = 'PLAIN'
        if not optional:
                optional = 8
        return self.randchar(optional)

    def _crypt_crypt(self, pw, optional=None, salt=None):
        if salt is None:
            salt = self.randchar()
        return crypt.crypt(pw, salt)

    def _crypt_digest_md5(self, pw, optional=None):
        """
        optional: username@realm
        """

        if optional and optional.index('@'):
            (user, realm) = optional.split('@')
        else:
            raise AssertionError('DIGEST-MD5 need username@realm optional parameter')
        return hashlib.md5("%s:%s:%s" % (user, realm, pw)).hexdigest()

    def _crypt_sha(self, pw, optional=None):
        return self._b64encode(hashlib.sha1(pw).digest())

    _crypt_sha1 = _crypt_sha

    def _crypt_sha256(self, pw, optional=None):
        return self._b64encode(hashlib.sha256(pw).digest())

    def _crypt_sha512(self, pw, optional=None):
        return self._b64encode(hashlib.sha512(pw).digest())

    def _crypt_ldap_md5(self, pw, optional=None):
        return self._b64encode(hashlib.md5(pw).digest())

    def _crypt_plain_md5(self, pw, optional=None):
        return hashlib.md5(pw).hexdigest()

    def _salted_ssha(self, pw, optional=None, salt=None, bits=1):
        """
        Salted ssha, remember that
        sshaN(pw, salt) = shaN(pass+salt)+salt
        with N=1,256,512
        """

        sha = hashlib.new('sha%d' % bits, pw)
        if not salt:
            salt = self.randchar(count=salted_algo_salt_len)

        sha.update(salt)
        return self._b64encode(sha.digest() + salt)

    def _crypt_ssha(self, pw, optional=None, salt=None):
        return self._salted_ssha(pw, optional, bits=1)

    def _crypt_ssha256(self, pw, optional=None, salt=None):
        return self._salted_ssha(pw, optional, bits=256)

    def _crypt_ssha512(self, pw, optional=None, salt=None):
        return self._salted_ssha(pw, optional, bits=512)

    def _crypt_smd5(self, pw, optional=None):
        md = hashlib.md5(pw)
        salt = self.randchar(count=salted_algo_salt_len)
        md.update(salt)

        return (md.digest() + salt).encode('base64').rstrip()

    def _crypt_md5_crypt(self, pw, optional=None, salt=None):
        """
        Used to be called MD5 in versions <= 1.0.rc16 of dovecot
        It is Unix md5+crypt password schema, used in passwd/shadow file
        """

        magic = '$1$'
        passwd = pw
        if salt is None:
            salt = self.randchar(count=9)
        m = hashlib.md5(passwd + magic + salt)

        # /* Then just as many characters of the MD5(pw,salt,pw) */
        mixin = hashlib.md5(passwd + salt + passwd).digest()
        for i in range(0, len(passwd)):
            m.update(mixin[i % 16])

        # /* Then something really weird... */
        # Also really broken, as far as I can tell.  -m
        i = len(passwd)
        while i:
            if i & 1:
                m.update('\x00')
            else:
                m.update(passwd[0])
            i >>= 1

        final = m.digest()

        # /* and now, just to make sure things don't run too fast */
        for i in range(1000):
            m2 = hashlib.md5('')
            if i & 1:
                m2.update(passwd)
            else:
                m2.update(final)

            if i % 3:
                m2.update(salt)

            if i % 7:
                m2.update(passwd)

            if i & 1:
                m2.update(final)
            else:
                m2.update(passwd)

            final = m2.digest()

        # This is the bit that uses to64() in the original code.

        itoa64 = './%s' % printableChars

        rearranged = ''
        for a, b, c in ((0, 6, 12), (1, 7, 13), (2, 8, 14), (3, 9, 15), (4, 10, 5)):
            v = ord(final[a]) << 16 | ord(final[b]) << 8 | ord(final[c])
            for i in range(4):
                rearranged += itoa64[v & 0x3f]
                v >>= 6

        v = ord(final[11])
        for i in range(2):
            rearranged += itoa64[v & 0x3f]
            v >>= 6

        return magic + salt + '$' + rearranged

    _crypt_md5 = _crypt_md5_crypt  # Retrocompatibility with dovecot version <= 1.0.rc16

    ####################
    # Check algorithms #
    ####################
    def _get_salt(self):
        cryptpw = self._b64decode(self.password)
        saltLen = len(cryptpw) - salted_algo_salt_len
        return cryptpw[saltLen:]

    def _check_crypt(self, pw, optional=None):
        salt = self.password[:8]
        return (self.password == crypt.crypt(pw, salt))

    def _check_salted(self, pw, optional=None, bits=1):
        checkPw = self._salted_ssha(pw, optional, salt=self._get_salt(),
                                    bits=bits)
        return (self.password == checkPw)

    def _check_ssha(self, pw, optional=None):
        return self._check_salted(pw, optional, bits=1)

    def _check_ssha256(self, pw, optional=None):
        return self._check_salted(pw, optional, bits=256)

    def _check_ssha512(self, pw, optional=None):
        return self._check_salted(pw, optional, bits=512)

    def _check_smd5(self, pw, optional=None):
        md = hashlib.md5(pw)
        salt = self._get_salt()
        md.update(salt)

        return (self.password == self._b64encode(md.digest() +
                                                 salt))

    def _check_md5_crypt(self, pw, optional=None):
        salt = self.password[3:12]
        cryptPw = self._crypt_md5_crypt(pw, optional=None, salt=salt)
        return (self.password == cryptPw)

    _check_md5 = _check_md5_crypt  # Retrocompatibility with dovecot version <= 1.0.rc16

if __name__ == '__main__':
    for s in Password.schemas():
        optional = None

        if s == 'CRAM-MD5':
            continue

        if s == 'DIGEST-MD5':
            optional = 'test@example.com'

        print "test", s, ":",
        p1 = Password('test123', schema=s, optional=optional)

        if p1.schema != 'PLAIN':
            checkPw = 'test123'
        else:
            checkPw = p1.password

        if not p1.check(checkPw):
            print "failed"
        else:
            print "ok"
