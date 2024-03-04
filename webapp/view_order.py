import datetime
import json
import os
import sys
import time
import logging
from uuid import uuid4
from flask import jsonify, request

from .status_code import STATUS


class OrderHandler(object):
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

    def format_order(self, order):
        """
        order 数据库对象
        :param order:
        :return:
        """
        chat = self.center.bot.bot.get_chat(order.chat_id)
        if chat:
            title = chat.title
        else:
            title = order.chat_id

        buyer = self.center.pipeline.get_user_by_id(order.buyer_id)
        # buyer_name = ''
        # if buyer:
        #     if buyer.first_name:
        #         buyer_name = str(buyer.first_name)
        #     if buyer.last_name:
        #         buyer_name = buyer_name + ' ' + str(buyer.last_name)
        #     if buyer.username:
        #         buyer_name = buyer_name + ' @' + str(buyer.username)

        seller = self.center.pipeline.get_user_by_id(order.seller_id)
        # seller_name = ''
        # if seller:
        #     if seller.first_name:
        #         seller_name = str(seller.first_name)
        #     if seller.last_name:
        #         seller_name = seller_name + ' ' + str(seller.last_name)
        #     if seller.username:
        #         seller_name = seller_name + ' @' + str(seller.username)

        return {
            'id': order.id,
            "chat_name": title,
            "buyer": buyer.__dict__() if buyer else None,
            "seller": seller.__dict__() if seller else None,
            "buyer_bank": order.buyer_bank,
            "seller_bank": order.seller_bank,
            "buyer_address": order.buyer_address,
            "seller_address": order.seller_address,
            "minute": order.minute,
            "price": order.price,
            "amount": order.amount,
            "fee": order.fee,
            "status": order.status,
            "note": order.note,
            "create_time": order.create_time,
            "update_time": order.update_time,
        }

    # 获取订单列表
    # @order_blueprint.route('/orders', methods=['GET'])
    def get_order_list(self):
        # order = get_order_from_header(request)
        # if order == '' or order is None:
        #     self.log.error("<%s> missing order in header" % sys._getframe().f_code.co_name)
        #     return jsonify(data=None, code=STATUS.PARAM_MISSING_ERROR, success=False,
        #                    message="missing order in header"), 400

        try:
            page = request.args.get('page', default=1, type=int)
            page_size = request.args.get('page_size', default=20, type=int)
            status = request.args.get(key='status', default=None, type=str)
            if status:
                status = status.split(',')

            kwargs = {
                         'status': status,
                         'page': page,
                         'page_size': page_size,
            }
            data, total = self.db_conn.get_orders(kwargs=kwargs)
        except Exception as e:
            self.log.error(e)
            # self.scheduler.es_conn.create_log(index_name=self.scheduler.config['elasticsearch'].get('ERR_IDX'),
            #                                   id=uuid4().__str__(), body={"message": "{}".format(e)})

            return jsonify(data=[], code=STATUS.DB_QUERY_ERROR, success=False, message="查询失败"), 200

        result = list()
        for order in data:
            result.append(self.format_order(order))
        return jsonify(data=result, page=page, page_size=page_size, total=total, code=STATUS.SUCCESS, success=True,
                       message="SUCCESS"), 200

    # 订单详情
    # @order_blueprint.route('/order/<int:order_id>', methods=['GET'])
    def get_order_detail(self, order_id: str):
        # order = get_order_from_header(request)
        # if order is None:
        #     self.log.error("missing order in header")
        #     return jsonify(data=None, code=STATUS.PARAM_MISSING_ERROR, success=False,
        #                    message="missing order in header"), 400
        try:
            order = self.db_conn.get_order_by_id(order_id)

            if order is not None:
                result = self.format_order(order)
                return jsonify(data=result, code=STATUS.SUCCESS, success=True, message="SUCCESS"), 200
            else:
                return jsonify(data=None, code=STATUS.ACCOUNT_MISSING_ERROR, success=False, message="查询订单详情失败，订单不存在或已被删除"), 200
        except Exception as e:
            # self.scheduler.es_conn.create_log(self.scheduler.config['elasticsearch'].get('ERR_IDX'), uuid4().__str__(), body={
            #     "file": __file__,
            #     "line": sys._getframe().f_lineno,
            #     "function": sys._getframe().f_code.co_name,
            #     "timestamp": int(time.time() * 1000),
            #     "operator": order,
            #     "operator_ip": get_req_ip(request),
            #     "message": "{}".format(e)
            # })
            self.log.error(e)
            return jsonify(data=None, code=STATUS.DB_QUERY_ERROR, success=False, message="订单账户详情失败"), 200
    
    # 订单详情
    # @order_blueprint.route('/order/<int:order_id>', methods=['POST'])
    def judge(self, order_id: str):
        """
        post 带
        修改订单状态，需要客服介入的订单状态有 32 或者 2
        需要查看两边证据，如果购买者已付款，那么要将钱款划拨给购买者，订单状态改为4，添加备注，如果购买者没有付款，那么取消订单，该订单移除，状态改为52，添加备注
        :param order_id:
        :return:
        """
        try:
            params = request.form.to_dict()
            order = self.center.pipeline.get_order_by_id(order_id)
            if order is not None:
                # 判断订单的状态是否为2或 32
                if order.status == '2' or order.status == '32':
                    if params['judge'] == 'seller':
                        # 判seller 胜利，那么取消订单，该订单移除，状态改为52，添加备注
                        manage_event = ManageEvent()
                        manage_event.category = 'judge'
                        manage_event.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        manage_event.type = '2'
                        manage_event.order = order
                        self.center.add_event(manage_event)

                    if params['judge'] == 'buyer':
                        # 判 buyer 胜利，那么要将钱款划拨给购买者，订单状态改为4，添加备注
                        manage_event = ManageEvent()
                        manage_event.category = 'judge'
                        manage_event.time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        manage_event.type = '1'
                        manage_event.order = order
                        self.center.add_event(manage_event)

                    return jsonify(data=None, code=STATUS.SUCCESS, success=True, message="SUCCESS"), 200
                else:
                    return jsonify(data=None, code=STATUS.ACCOUNT_MISSING_ERROR, success=False,
                                   message="当前订单状态无法处理"), 200
            else:
                return jsonify(data=None, code=STATUS.ACCOUNT_MISSING_ERROR, success=False,
                               message="查询订单详情失败，订单不存在或已被删除"), 200
        except Exception as e:
            # self.scheduler.es_conn.create_log(self.scheduler.config['elasticsearch'].get('ERR_IDX'), uuid4().__str__(), body={
            #     "file": __file__,
            #     "line": sys._getframe().f_lineno,
            #     "function": sys._getframe().f_code.co_name,
            #     "timestamp": int(time.time() * 1000),
            #     "operator": order,
            #     "operator_ip": get_req_ip(request),
            #     "message": "{}".format(e)
            # })
            self.log.error(e)
            return jsonify(data=None, code=STATUS.DB_QUERY_ERROR, success=False, message="订单处理失败"), 200
