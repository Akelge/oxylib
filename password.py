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
import hmac
import hashlib
import random
from subprocess import Popen, PIPE
import os

salted_algo_salt_len = 4
printableChars='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

# All available schemas (v2.x)
# CRYPT - Unix crypt
# MD5-CRYPT - Unix MD5 enrypted password
# SHA SHA1 SHA256 SHA512 - SHA
# SMD5 - Salted MD5
# SSHA SSHA256 SSHA512 - Salted SHA: SSHA(pw, salt)=SHA(pw+salt)
# PLAIN CLEARTEXT - Synonyms
# CRAM-MD5 - Hardest one: by now we use dovecotpw/doveadm external auth
# MD5 HMAC-MD5 DIGEST-MD5 LDAP-MD5 - MD5, various encoding
# PLAIN-MD4 PLAIN-MD5 - Plain 
# LANMAN NTLM OTP SKEY RPA - Legacy algorithms
# SHA256-CRYPT SHA512-CRYPT - Unix SHA encrypted password
# RANDOM-PLAIN # added by us returns a random password in PLAIN
# NULL # added by us for pubowner/arcowner
# EXT # added by us for external_auth users (LDAP)

class Password(object):

    basicSchemas=['PLAIN', 'RANDOM-PLAIN', 'MD5', 'SHA256', 'EXT'] # 'CRAM-MD5'

    @classmethod
    def randchar(cls, count):
        return ''.join([random.choice(printableChars) for x in xrange(count)])

    @classmethod
    def schemas(cls):
        fn=lambda x: x.replace('_crypt_', '').replace('_', '-').upper()
        return tuple(map(fn, cls._py_algos()))

    @classmethod
    def _py_algos(cls):
        return tuple([x for x in cls.__dict__.keys() if x.startswith('_crypt_')])

    def __init__(self, password, schema='PLAIN', optional=None):
        self.optional=optional

        self._schema='PLAIN'
        self._schemaMethod='plain'
        self.password=password
        self.schema=schema.upper()

    def __repr__(self):
        return r"<%s(password='%s', schema='%s')>" % (self.__class__.__name__, self.password, self.schema)

    def __str__(self):
        return self.full

    @property
    def full(self):
        return "{%s}%s" % (self.schema, self.password)

    # @property
    def get_schema(self):
        return "%s" % self._schema

    # @schema.setter
    def set_schema(self, schema):

        self._schemaMethod=schema.lower().replace('-', '_') # Lower case, no dash, for method calling

        if self._schema==schema:
            return

        if 'PLAIN' in self._schema:
            self._schema=schema
            self.password=self.password
        else:
            raise AssertionError, r"Cannot change schema from '%s' to '%s'" % (self._schema, schema)
    schema=property(get_schema, set_schema)

    # @property
    def get_password(self):
        return self._password

    # @password.setter
    def set_password(self, pw):
        self._password=self.encrypt(pw, optional=self.optional)
    password=property(get_password, set_password)


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
    def _b64encode(string):
        return string.encode('base64').rstrip()

    def _b64decode(string):
        return string.decode('base64')

    def _dovecotpw(self, pw, optional):
        """
        generic fallback, use dovecot utility
        """
        cmdArgsV1=['dovecotpw', '-s', self.schema, '-p', self.password]
        cmdArgsV2=['doveadm', 'pw', '-s', self.schema, '-p', self.password]
        try:
            proc=Popen(cmdArgsV2, stdout=PIPE, stderr=PIPE)
        except OSError, e:
            proc=Popen(cmdArgsV1, stdout=PIPE, stderr=PIPE)
        proc.wait()

        if proc.returncode > 0:
            raise AttributeError, "Error: %s" % proc.stderr.read().rstrip()
        else:
            hashed=proc.stdout.read().rstrip()
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
        self.schema='PLAIN'
        if not optional: optional=8
        return self.randchar(optional)

    def _crypt_crypt(self, pw, optional=None):
        return crypt.crypt(pw, self.randchar())

    def _crypt_digest_md5(self, pw, optional=None):
        """
        optional: username@realm
        """

        if optional and optional.index('@'):
            (user, realm) = optional.split('@')
        else:
            raise AssertionError, 'DIGEST-MD5 need username@realm optional parameter'
        return hashlib.md5("%s:%s:%s" % (user,realm,pw)).hexdigest()

   
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

        sha=hashlib.new('sha%d' % bits, pw)
        if not salt:
            salt=self.randchar(count=salted_algo_salt_len)
        sha.update(salt)
        return (sha.digest() + salt).encode('base64').rstrip()

    def _crypt_ssha(self, pw, optional=None, salt=None):
        return self._salted_ssha(pw, optional, bits=1)

    def _crypt_ssha256(self, pw, optional=None, salt=None):
        return self._salted_ssha(pw, optional, bits=256)

    def _crypt_ssha512(self, pw, optional=None, salt=None):
        return self._salted_ssha(pw, optional, bits=512)

    def _crypt_smd5(self, pw, optional=None):
        md=hashlib.md5(pw)
        salt=self.randchar(count=salted_algo_salt_len)
        md.update(salt)

        return (md.digest() + salt).encode('base64').rstrip()

    def _crypt_md5_crypt(self, pw, optional=None):
        """
        Used to be called MD5 in versions <= 1.0.rc16 of dovecot
        It is Unix md5+crypt password schema, used in passwd/shadow file
        """

        magic='$1$'
        passwd=pw
        salt=self.randchar(count=9)
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
                rearranged += itoa64[v & 0x3f]; v >>= 6

        v = ord(final[11])
        for i in range(2):
            rearranged += itoa64[v & 0x3f]; v >>= 6

        return magic + salt + '$' + rearranged

    _crypt_md5 = _crypt_md5_crypt # Retrocompatibility with dovecot version <= 1.0.rc16
