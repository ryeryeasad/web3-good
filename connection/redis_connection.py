#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @Time     : 2022/7/14 17:09 
# @Author   : 0xJohsnon
# @File     : redis_connection.py
# @Usage    :
import json
import logging
import sys
from six.moves import configparser as ConfigParser

import redis
from six.moves import queue as Queue
from triple.connection import BaseConnection


class RedisConnection(BaseConnection):
    driver_name = 'redis'
    log = logging.getLogger("triple.RedisConnection")

    def __init__(self, connection_name, connection_config):
        super(RedisConnection, self).__init__(connection_name,
                                              connection_config)
        if 'server' not in self.connection_config:
            raise Exception('server is required for redis connections in '
                            '%s' % self.connection_name)
        self.server = self.connection_config.get('server')
        self.port = int(self.connection_config.get('port', 6379))
        self.password = self.connection_config.get('password')
        self.db = self.connection_config.get('db', 0)
        self.watch_key = self.connection_config.get('watch_key').split(',')
        self.time_out = int(self.connection_config.get('timeout'))
        self.connection_pool = self.get_pool()
        self.client = self.get_client()
        self.event_queue = Queue.Queue()
        self.watcher_thread = dict()
        self.redis_connector = None
        # self.clear_serial()

    def get_pool(self):
        kwargs = {
            'host': self.server,
            'port': self.port,
            'password': self.password,
            'decode_responses': True,
            'retry_on_timeout': 3,
            'max_connections': 50,  # 默认2^31
            'db': self.db
        }
        pool = redis.ConnectionPool(**kwargs)
        return pool

    def get_client(self):
        conn = redis.Redis(connection_pool=self.connection_pool)
        return conn

    def add_event(self, data):
        return self.event_queue.put(data)

    def get_event(self):
        return self.event_queue.get()

    def event_done(self):
        self.event_queue.task_done()

    def get_key(self, key):
        try:
            client = self.get_client()
            result = client.get(key)
        except Exception as e:
            self.log.error('%s failed. error: %s' % (sys._getframe().f_code.co_name, e))
            raise e
        else:
            return result

    def set_key(self, key, data):
        """
        :param key:
        :param data:
        :return:
        """
        try:
            client = self.get_client()
            result = client.set(key, data)
        except Exception as e:
            # 写报错日志到es和本地，以及发邮件给相关人员
            self.log.error('%s failed. key: %s. data: %s. error: %s. ' % (sys._getframe().f_code.co_name, key, data, e))
        else:
            self.log.info(
                '%s success. key: %s. data: %s ' % (sys._getframe().f_code.co_name, key, data))

    def get_flag(self, key):
        """
        :param key: key
        :return:
        """
        try:
            client = self.get_client()
            result = client.get(key)
        except Exception as e:
            # 写报错日志到es和本地，以及发邮件给相关人员
            self.log.error('%s failed. key: %s. error: %s. ' % (sys._getframe().f_code.co_name, key, e))
        else:
            return result

    def incr_count(self, key):
        try:
            client = self.get_client()
            result = client.incr(key)
        except Exception as e:
            self.log.error('%s failed. error: %s' % (sys._getframe().f_code.co_name, e))
            raise e
        else:
            if result:
                return result
            else:
                return result

    def set_response(self, serial, data):
        """
        :param serial: 序列号
        :param data: {
                        code = None   # 错误码
                        message = None
                        result = None
                        data = None
                }
        :return:
        """
        try:
            client = self.get_client()
            result = client.lpush(serial, json.dumps(data))
        except Exception as e:
            # 写报错日志到es和本地，以及发邮件给相关人员
            self.log.error(
                '%s failed. serial: %s. data: %s. error: %s. ' % (sys._getframe().f_code.co_name, serial, data, e))
        else:
            self.log.info(
                '%s success. serial: %s. data: %s ' % (sys._getframe().f_code.co_name, serial, data))

    def get_response(self, serial):
        """
        :param serial: 序列号
        :return:
        """
        try:
            client = self.get_client()
            result = client.brpop(serial, self.time_out)
            self.log.info(
                '%s success. serial: %s. data: %s ' % (sys._getframe().f_code.co_name, serial, result))
        except Exception as e:
            # 写报错日志到es和本地，以及发邮件给相关人员
            self.log.error('%s failed. data: %s. error: %s. ' % (sys._getframe().f_code.co_name, serial, e))
            raise e
        else:
            if result:
                return json.loads(result[1])
            else:
                return result

    def set_flag(self, key, data):
        """
        :param key: key
        :param data: 时间
        :return:
        """
        try:
            client = self.get_client()
            result = client.set(key, data)
        except Exception as e:
            # 写报错日志到es和本地，以及发邮件给相关人员
            self.log.error('%s failed. key: %s. data: %s. error: %s. ' % (sys._getframe().f_code.co_name, key, data, e))
        else:
            self.log.info(
                '%s success. key: %s. data: %s ' % (sys._getframe().f_code.co_name, key, data))

    def on_load(self):
        self.log.debug("Starting Redis Conncetion/Watchers")
        self._start_watcher_thread()
        self._start_redis_connector()

    def on_stop(self):
        self.log.debug("Stopping Redis Conncetion/Watchers")
        self._stop_watcher_thread()
        self._stop_event_connector()

    def clear_serial(self):
        try:
            client = self.get_client()
            keys = client.keys()
            for key in keys:
                if key.find('-') != -1:
                    client.delete(key)
        except Exception as e:
            # 写报错日志到es和本地，以及发邮件给相关人员
            self.log.error('%s failed. error: %s. ' % (sys._getframe().f_code.co_name, e))
            raise e


def redis_connection_test():
    config = ConfigParser.ConfigParser()
    config.read('../../etc/triple.conf')

    redis_connection = RedisConnection('connection', config['redis'])

    # block_number = redis_connection.get_key('block_number')
    # print(block_number)
    redis_connection.set_key('stop', True)
    stop = redis_connection.get_key('stop')
    print(type(stop), stop)
    if stop:
        print(123)
    else:
        print(213)
    # redis_connection.on_load()
    # while True:
    #     time.sleep(1)
    #     event = redis_connection.get_event()
    #     print('get event %s' % event)


if __name__ == '__main__':
    redis_connection_test()
