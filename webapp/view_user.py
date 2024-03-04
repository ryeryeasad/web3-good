import datetime
import os
import sys
import time
import logging
from uuid import uuid4
from flask import jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from .status_code import STATUS


class UserHandler(object):
    log = logging.getLogger("triple.web.status")

    def __init__(self, center):
        self.cache_time = time.time()
        self.center = center
        self.db_conn = self.get_db_conn()

    def get_db_conn(self):
        db_conn = self.center.sql_conn
        if not db_conn:
            db_conn = self.center.reconnect_db()
            self.log.debug("db reconnected {}".format(db_conn))
        return db_conn

    def login(self):
        username = request.json.get("username", None)
        password = request.json.get("password", None)
        if username != "test" or password != "test":
            return jsonify({"msg": "Bad username or password"}), 401

        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    @jwt_required()
    def protected(self):
        # Access the identity of the current user with get_jwt_identity
        current_user = get_jwt_identity()
        return jsonify(logged_in_as=current_user), 200

    # 获取用户列表
    # @user_blueprint.route('/users', methods=['GET'])
    def get_user_list(self):
        # user = get_user_from_header(request)
        # if user == '' or user is None:
        #     self.log.error("<%s> missing user in header" % sys._getframe().f_code.co_name)
        #     return jsonify(data=None, code=STATUS.PARAM_MISSING_ERROR, success=False,
        #                    message="missing user in header"), 400

        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=20, type=int)
        username = request.args.get(key='username', default=None, type=str)

        kwargs = {
            'username': username,
            'page': page,
            'page_size': page_size,
        }

        try:
            data, total = self.db_conn.get_users(kwargs=kwargs)
        except Exception as e:
            self.log.error(e)
            # self.scheduler.es_conn.create_log(index_name=self.scheduler.config['elasticsearch'].get('ERR_IDX'),
            #                                   id=uuid4().__str__(), body={"message": "{}".format(e)})

            return jsonify(data=[], code=STATUS.DB_QUERY_ERROR, success=False, message="查询失败"), 200

        result = list()
        for user in data:
            user_obj = self.center.pipeline.get_user_by_id(user.id)
            result.append(user_obj.__dict__())
        return jsonify(data=result, page=page, page_size=page_size, total=total, code=STATUS.SUCCESS, success=True,
                       message="SUCCESS"), 200

    # 用户详情
    # @user_blueprint.route('/user/<string:user_id>', methods=['GET'])
    def get_user_detail(self, user_id: int):
        # user = get_user_from_header(request)
        # if user is None:
        #     self.log.error("missing user in header")
        #     return jsonify(data=None, code=STATUS.PARAM_MISSING_ERROR, success=False,
        #                    message="missing user in header"), 400
        try:
            user = self.center.pipeline.get_user_by_id(user_id)

            if user is not None:
                # 查询总共完成了多少笔交易，成功交易的资金量
                result = user.__dict__()
                total_trade_amount, total_fee, finished = self.db_conn.get_total_trade_amount_and_count(user_id)
                result['total_trade_amount'] = total_trade_amount
                result['total_fee'] = total_fee
                result['finished'] = finished
                result['order_list'] = [order.__dict__() for order in user.queue.orders]
                result['cash_operation_list'] = [cash_operation.__dict__() for cash_operation in user.cash_operation_list[::-1]]
                return jsonify(data=result, code=STATUS.SUCCESS, success=True, message="SUCCESS"), 200
            else:
                return jsonify(data=None, code=STATUS.ACCOUNT_MISSING_ERROR, success=False, message="查询账户详情失败，账户不存在或已被删除"), 200
        except Exception as e:
            # self.scheduler.es_conn.create_log(self.scheduler.config['elasticsearch'].get('ERR_IDX'), uuid4().__str__(), body={
            #     "file": __file__,
            #     "line": sys._getframe().f_lineno,
            #     "function": sys._getframe().f_code.co_name,
            #     "timestamp": int(time.time() * 1000),
            #     "operator": user,
            #     "operator_ip": get_req_ip(request),
            #     "message": "{}".format(e)
            # })
            self.log.error(e)
            return jsonify(data=None, code=STATUS.DB_QUERY_ERROR, success=False, message="查询账户详情失败"), 200

    # 获取正在提现列表
    # @common_blueprint.route('/withdraw_list', methods=['GET'])
    def get_withdraw_list(self):
        result = [cash_operation.__dict__() for cash_operation in self.center.pipeline.withdrawal_list]
        return jsonify(data=result, code=STATUS.SUCCESS, success=True, message="SUCCESS")

