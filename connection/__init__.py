#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time     : 2022/7/14 15:55 
# @Author   : 0xJohsnon
# @File     : __init__.py.py
# @Usage    :

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseConnection(object):
    """
    Base class for connections.
    """

    def __init__(self, connection_name, connection_config):
        self.connection_name = connection_name
        self.connection_config = connection_config
        self.center = None

    def on_load(self):
        pass

    def on_stop(self):
        pass

    def register_center(self, center):
        self.center = center

    def register_use(self, what, instance):
        self.attached_to[what].append(instance)

    def maintain_cache(self, relevant):
        """
        Make cache  reserved for future
        """