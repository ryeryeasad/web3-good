import os
import time
import logging
import threading

from flask_jwt_extended import JWTManager
from six.moves import configparser as ConfigParser

from gevent.pywsgi import WSGIServer
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request

from connection import sql
from webapp.view_common import CommonHandler
from webapp.view_order import OrderHandler

from webapp.view_user import UserHandler


class StatusHandler(object):
    log = logging.getLogger("web3.web.status")

    def __init__(self, center):
        self.cache = None
        self.cache_time = time.time()
        self.center = center

    def status(self):
        self.log.debug("View parameter {0}".format(request.args))
        data = {'start time': self.center.start_time}
        self.log.debug("status result {0}".format(data))
        return "SUCCESS"


class WebApp(threading.Thread):
    log = logging.getLogger("web3.web.WebApp")
    # app = Flask(__name__)

    def __init__(self, gear_server=None,
                 gear_port=None, ssl_key=None, ssl_cert=None, ssl_ca=None,
                 static_cache_expiry=3600, connections=None,
                 info=None, static_path=None, authenticators=None,
                 command_socket=None):
        threading.Thread.__init__(self)
        self.listen_address = '0.0.0.0'
        self.url_prefix = ''
        self.listen_port = 8001
        self.start_time = time.time()
        self.read_config()
        self.set_config()
        self.event_loop = None
        self.term = None
        self.tables = list()
        self.app = Flask(__name__)
        self.set_app_config()
        self.jwt = JWTManager(self.app)
        # 初始化数据库连接
        sql_conn = self.configure_sql()
        self.set_sql_connection(sql_conn)
        self.status_handler = StatusHandler(self)
        self.common_handler = CommonHandler(self)
        self.user_handler = UserHandler(self)
        self.order_handler = OrderHandler(self)
        self.add_url()

    def set_config(self):
        if self.config.has_option('webapp', 'listen_address'):
            self.listen_address = self.config.get('webapp', 'listen_address')

        if self.config.has_option('webapp', 'port'):
            self.listen_port = self.config.getint('webapp', 'port')

        if self.config.has_option('webapp', 'url_prefix'):
            self.url_prefix = self.config.get('webapp', 'url_prefix')

    def read_config(self):
        self.config = ConfigParser.ConfigParser()
        locations = ['/etc/triple/triple.conf',
                     '~/triple.conf',
                     '../etc/triple.conf',
                     './etc/triple.conf']
        for fp in locations:
            if os.path.exists(os.path.expanduser(fp)):
                self.config.read(os.path.expanduser(fp))
                return
        raise Exception("Unable to locate config file in %s" % locations)

    def configure_sql(self):
        db_config = self.config['database']
        sql_conn = sql.SQLConnection('mysql', db_config)
        self.log.debug("mysql connection {} connected".format(sql_conn))
        return sql_conn

    def reconnect_sql(self):
        db_config = self.config['database']
        sql_conn = sql.SQLConnection('mysql', db_config)
        self.log.debug("mysql connection {} reconnected".format(sql_conn))
        return sql_conn

    def set_sql_connection(self, sql_conn):
        self.sql_conn = sql_conn

    def get_sql_conn(self):
        sql_conn = self.sql_conn
        if not sql_conn:
            sql_conn = self.reconnect_sql()
            self.log.debug("sql reconnected {}".format(sql_conn))
        return sql_conn

    def set_app_config(self):
        self.log.info("mysql uri {}".format(self.config['database'].get('dburi')))
        self.app.config['SQLALCHEMY_DATABASE_URI'] = self.config['database'].get('dburi')
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
        self.app.config["SQLALCHEMY_POOL_SIZE"] = 10  # 连接池大小
        self.app.config["SQLALCHEMY_POOL_TIMEOUT"] = 5400  # 1.5h 连接池超时时间, mysql的连接超时时间是7200
        self.app.config["SQLALCHEMY_POOL_RECYCLE"] = 3600  # 1.0h 连接池回收连接时间
        self.app.config["SQLALCHEMY_ECHO"] = True  # debug输出
        self.app.config["JWT_SECRET_KEY"] = "web3-entry-" + str(int(time.time())) # debug输出

    def add_url(self):
        """
        添加路由映射， 并在__init__函数中初始化
        """
        self.app.add_url_rule(rule=self.url_prefix + '/', endpoint="status",
                              view_func=self.status_handler.status,
                              methods=('GET',))

        self.app.add_url_rule(rule=self.url_prefix + '/login', endpoint="login",
                              view_func=self.user_handler.login,
                              methods=('POST',))

        self.app.add_url_rule(rule=self.url_prefix + '/protected', endpoint="protected",
                              view_func=self.user_handler.protected,
                              methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/operate', endpoint="operate",
        #                       view_func=self.common_handler.get_operate_list,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/status', endpoint="order_status",
        #                       view_func=self.common_handler.get_status_list,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/current', endpoint="current",
        #                       view_func=self.common_handler.get_current,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/withdraw_control', endpoint="withdraw_control",
        #                       view_func=self.common_handler.withdraw_control,
        #                       methods=('POST',))
        # self.app.add_url_rule(rule=self.url_prefix + '/robot_control', endpoint="robot_control",
        #                       view_func=self.common_handler.robot_control,
        #                       methods=('POST',))
        #
        # # 用户接口
        # self.app.add_url_rule(rule=self.url_prefix + '/users', endpoint="user_get",
        #                       view_func=self.user_handler.get_user_list,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/user/<int:user_id>', endpoint="user_detail",
        #                       view_func=self.user_handler.get_user_detail,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/withdraw_list', endpoint="withdraw_list",
        #                       view_func=self.user_handler.get_withdraw_list,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/withdraw/<string:operation_id>', endpoint="withdraw_confirm",
        #                       view_func=self.user_handler.withdraw_confirm,
        #                       methods=('POST',))
        #
        # # 订单接口
        # self.app.add_url_rule(rule=self.url_prefix + '/orders', endpoint="order_get",
        #                       view_func=self.order_handler.get_order_list,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/order/<string:order_id>', endpoint="order_detail",
        #                       view_func=self.order_handler.get_order_detail,
        #                       methods=('GET',))
        # self.app.add_url_rule(rule=self.url_prefix + '/order/<string:order_id>', endpoint="order_judge",
        #                       view_func=self.order_handler.judge,
        #                       methods=('POST',))

    def apscheduler(self):
        """
        Note: 根据需要启动
        """
        apscheduler = BackgroundScheduler()
        apscheduler.start()

    def web_server(self):
        """
        Note: 可以直接在start函数中启动， 通过gevent方式启动
        https://dormousehole.readthedocs.io/en/latest/deploying/wsgi-standalone.html
        """
        http_server = WSGIServer(listener=(self.listen_address, self.listen_port), application=self.app)
        http_server.base_env['wsgi.multithread'] = True
        http_server.base_env['wsgi.multiprocess'] = True
        http_server.serve_forever()

    def run(self):
        """
        1: gunicorn
        2: uwsgi
        https://dormousehole.readthedocs.io/en/latest/deploying/wsgi-standalone.html
        类视图：https://blog.csdn.net/yuaicsdn/article/details/109235975
        """
        # self.app.run(host=self.listen_address, port=self.listen_port, debug=True)
        self.web_server()

if __name__ == "__main__":
    # app.run(port=8080)
    web3 = WebApp()
    web3.run()