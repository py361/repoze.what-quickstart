# -*- coding: utf-8 -*-
"""
Sample SQLAlchemy-powered model definition for the repoze.what SQL plugin.

This model definition has been taken from a quickstarted TurboGears 2 project,
but it's absolutely independent of TurboGears.

"""

import os
from hashlib import sha1
from datetime import datetime

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import String, Unicode, UnicodeText, Integer, DateTime, \
                             Boolean, Float
from sqlalchemy.orm import relation, backref, synonym

from yourproject.model import DeclarativeBase, metadata


# This is the association table for the many-to-many relationship between
# groups and permissions.
group_permission_table = Table('group_permission', metadata,
    Column('group_id', Integer, ForeignKey('group.group_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('permission_id', Integer, ForeignKey('permission.permission_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships.
user_group_table = Table('user_group', metadata,
    Column('user_id', Integer, ForeignKey('user.user_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('group_id', Integer, ForeignKey('group.group_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)

# auth model

class Group(DeclarativeBase):
    """An ultra-simple group definition."""
    __tablename__ = 'group'

    group_id = Column(Integer, autoincrement=True, primary_key=True)

    group_name = Column(Unicode(16), unique=True)

    users = relation('User', secondary=user_group_table, backref='groups')


class User(DeclarativeBase):
    """
    Reasonably basic User definition. Probably would want additional
    attributes.
    
    """
    __tablename__ = 'user'

    user_id = Column(Integer, autoincrement=True, primary_key=True)
    
    user_name = Column(Unicode(16), unique=True)

    _password = Column('password', Unicode(80))

    def _set_password(self, password):
        """Hash password on the fly."""
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password
        
        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        # Make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode
        # fields
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        self._password = hashed_password

    def _get_password(self):
        """Return the password hashed"""
        return self._password

    password = synonym('_password', descriptor=property(_get_password,
                                                        _set_password))

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool
        
        """
        hashed_pass = sha1()
        hashed_pass.update(password + self.password[:40])
        return self.password[40:] == hashed_pass.hexdigest()


class Permission(DeclarativeBase):
    """A relationship that determines what each Group can do"""
    __tablename__ = 'permission'

    permission_id = Column(Integer, autoincrement=True, primary_key=True)

    permission_name = Column(Unicode(16), unique=True)

    groups = relation(Group, secondary=group_permission_table,
                      backref='permissions')
