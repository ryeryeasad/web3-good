
import os
import sys
import time
import logging
from uuid import uuid4
from flask import jsonify, request

from . import Operate, Status
from .status_code import STATUS


class CommonHandler(object):
    log = logging.getLogger("web3.web.status")

    def __init__(self, center):
        self.cache_time = time.time()
        self.center = center
        self.sql_conn = self.get_sql_conn()

    def get_sql_conn(self):
        sql_conn = self.center.sql_conn
        if not sql_conn:
            sql_conn = self.center.reconnect_sql()
            self.log.debug("sql reconnected {}".format(sql_conn))
        return sql_conn

    def get_current(self):
        try:
            # data = Broker.query.all()
            users, orders, total_trade_amount, total_fee = self.sql_conn.get_current_detail()
        except Exception as e:
            self.log.error(e)
            # self.center.es_conn.create_log(index_name=self.center.config['elasticsearch'].get('ERR_IDX'), id=uuid4().__str__(), body={
            #     "file": __file__,
            #     "line": sys._getframe().f_lineno,
            #     "function": getattr(self.get_broker_list, '__name__'),
            #     "timestamp": int(time.time() * 1000),
            #     "operator": "",
            #     "operator_ip": "0.0.0.0",
            #     "message": "{}".format(e)
            # })
            return jsonify(data=None, code=STATUS.DB_QUERY_ERROR, success=False, message="查询失败"), 200

        result = {
            'users': users,
            'orders': orders,
            'total_trade_amount': total_trade_amount,
            'total_fee': total_fee,
            'withdraw_status': self.center.withdraw_status,
            'robot_status': self.center.robot_status
        }
        return jsonify(data=result, code=STATUS.SUCCESS, success=True, message="SUCCESS")

    # 获取操作类型列表
    # @common_blueprint.route('/operate', methods=['GET'])
    def get_operate_list(self):
        result = list()
        for k in Operate:
            result.append({
                "id": k,
                "name": Operate[k]
            })
        return jsonify(code=STATUS.SUCCESS, success=True, message="SUCCESS", total=len(result), data=result), 200

    # 获取状态类型列表
    # @common_blueprint.route('/status', methods=['GET'])
    def get_status_list(self):
        return jsonify(code=STATUS.SUCCESS, success=True, message="SUCCESS", data=Status), 200

    # 提现暂停
    # @common_blueprint.route('/stop_withdraw', methods=['POST'])
    def withdraw_control(self):
        params = request.form.to_dict()
        self.log.debug(params['flag'], type(params['flag']))
        flag = int(params['flag'])
        if flag != self.center.withdraw_status:
            self.center.withdraw_status = flag
            self.center.redis_conn.set_key('withdraw_status', flag)
            return jsonify(code=STATUS.SUCCESS, success=True, message="SUCCESS", data=None)
        else:
            return jsonify(code=STATUS.PARAM_COMMON_ERROR, success=False, message="请勿重复操作，状态一致", data=None)

    # 暂停机器人
    # @common_blueprint.route('/robot_control', methods=['POST'])
    def robot_control(self):
        params = request.form.to_dict()
        self.log.debug(params['flag'], type(params['flag']))
        flag = int(params['flag'])
        if flag != self.center.robot_status:
            self.center.robot_status = flag
            self.center.redis_conn.set_key('robot_status', flag)
            return jsonify(code=STATUS.SUCCESS, success=True, message="SUCCESS", data=None)
        else:
            return jsonify(code=STATUS.PARAM_COMMON_ERROR, success=False, message="请勿重复操作，状态一致", data=None)



