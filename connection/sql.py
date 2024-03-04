# Copyright @JiangZhen
# Build sql connection

import logging
import sys
import time
from copy import deepcopy

from sqlalchemy import and_, or_, not_, func, desc
import voluptuous as v
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# from webapp import ADMIN_USERS, ACCOUNT_TYPE_REAL, ACCOUNT_TYPE_SIMULATION
from lib.decorator import tries

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = sa.Column(sa.BIGINT, primary_key=True, nullable=False)
    is_bot = sa.Column(sa.Boolean, nullable=False, default=False, comment='是否是机器人')  #
    first_name = sa.Column(sa.String(255), default='', nullable=False, comment='首')
    last_name = sa.Column(sa.String(255), default='', nullable=True, comment='名称')
    username = sa.Column(sa.String(255), default='', nullable=True, comment='用户名')          # String	Optional. User's or bot's username
    language_code = sa.Column(sa.String(255), default='', nullable=True, comment='语言代码')   # String	Optional. IETF language tag of the user's language
    can_join_groups = sa.Column(sa.Boolean, nullable=True, default=False, comment='是否可以被邀请入群')  #
    can_read_all_group_messages = sa.Column(sa.Boolean, nullable=True, default=False, comment='是否可以读所有信息')  #
    supports_inline_queries = sa.Column(sa.Boolean, nullable=True, default=False, comment='支持请求')  #
    private_chat_id = sa.Column(sa.BIGINT, nullable=True, comment="单独聊天对话ID")
    balance = sa.Column(sa.BIGINT, nullable=False, default=0)
    freeze = sa.Column(sa.BIGINT, nullable=False, default=0)
    address = sa.Column(sa.String(255), default='', nullable=True, comment='钱包地址')
    status = sa.Column(sa.String(10), nullable=False, comment="账户状态  1：正常状态 2：无法操作")
    is_deleted = sa.Column(sa.Boolean, default=False, comment="删除标志")
    create_time = sa.Column(sa.Integer, default=int(time.time()))
    update_time = sa.Column(sa.Integer, default=int(time.time()))


class SQLConnection(object):
    driver_name = 'sql'
    log = logging.getLogger("web3.SQLConnection")

    def __init__(self, connection_name, connection_config):

        self.dburi = None
        self.engine = None
        self.connection = None
        self.tables_established = False
        self.connection_config = connection_config
        try:
            self.dburi = self.connection_config.get('dburi')
            self.engine = sa.create_engine(self.dburi, pool_recycle=3600, pool_size=int(self.connection_config.get('pool_size')), max_overflow=int(self.connection_config.get('max_overflow')))
            Base.metadata.create_all(self.engine)
            self.tables_established = True
        except sa.exc.NoSuchModuleError:
            self.log.exception(
                "The required module for the dburi dialect isn't available. "
                "SQL connection %s will be unavailable." % connection_name)
        except sa.exc.OperationalError:
            self.log.exception(
                "Unable to connect to the database or establish the required "
                "tables. Reporter %s is disabled" % self)

    @tries(num=3)
    def get_users(self, kwargs=None):
        """

        :param kwargs: {
                            username:
                            page:
                            page_size:

                        }
        :return:
        """
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        users = list()
        try:
            query = session.query(User).filter(User.is_deleted == 0).order_by(User.create_time.desc())
            if kwargs:
                if 'username' in kwargs and kwargs['username'] is not None:
                    query = query.filter(User.username == kwargs['username'])

                if 'page_size' in kwargs and 'page' in kwargs:
                    users = query.order_by(User.create_time.desc()).limit(kwargs['page_size']).offset(
                        (kwargs['page'] - 1) * kwargs['page_size'])
                    # accounts = query.order_by((desc(Account.create_time)))
                    # accounts = query.all()
                    total = query.count()
                    # self.log.debug("Accounts from db query {}".format(accounts))
                else:
                    users = query.all()
                    total = query.count()
            else:
                users = query.all()
                total = len(users)
            self.log.debug("Users from db {}".format(users))
        except Exception as _err:
            self.log.debug("Get users from db failed {}".format(str(_err)))
            session.close()
            raise _err
        finally:
            session.close()
        return users, total

    @tries(num=3)
    def get_user_by_id(self, user_id):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        user = None
        try:
            account = session.query(User).filter(User.id == user_id).first()
            self.log.debug("Account from db {}".format(account))
        except Exception as _err:
            self.log.debug("Get account from db failed {}".format(str(_err)))
            session.close()
            raise _err
        finally:
            session.close()
        return user

    @tries(num=3)
    def add_user(self, data):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        try:
            user = User(**data)
            session.add(user)
            session.commit()
            self.log.debug("Add user success")
        except Exception as _err:
            self.log.debug("Add user failed {0}".format(str(_err)))
            session.close()
            raise _err
        finally:
            session.close()

    @tries(num=3)
    def update_user(self, user_id, data):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        data = deepcopy(data)
        data["update_time"] = int(time.time())
        try:
            session.query(User).filter(User.id == user_id).update(data, synchronize_session=False)
            session.commit()
            self.log.debug("Update user for {0} success".format(user_id))
        except Exception as _err:
            self.log.debug("Update user for {0} failed {1}".format(user_id, str(_err)))
            session.close()
            raise _err
        else:
            return True
        finally:
            session.close()

    @tries(num=3)
    def delete_user_by_id(self, user_id):
        DBSession = sessionmaker(bind=self.engine)
        session = DBSession()
        ret = False
        try:
            # session.query(Account).filter(Account.id == account_id).delete()
            session.query(User).filter(User.id == user_id).update({"is_deleted": 1}, synchronize_session=False)
            session.commit()
            deleted = session.query(User).filter(User.id == user_id)
            if deleted and deleted[0].is_deleted == 1:
                ret = True
                self.log.debug("Delete user success")
            else:
                self.log.debug("Delete user failed")
        except Exception as _err:
            self.log.debug("Delete account failed {0}".format(str(_err)))
            session.close()
            raise _err
        finally:
            session.close()
        return ret


def get_schema():
    sql_connection = v.Any(str, v.Schema(dict))
    return sql_connection

def test_sql():
    db_config = {
        'driver': 'sql',
        'dburi': 'mysql+pymysql://root:root@8.210.56.186/web3',
        'pool_size': 30,
        'max_overflow': 100
    }
    sql_conn = SQLConnection('mysql', db_config)

    result = sql_conn.get_current_detail()
    print(result)
    # t1, t2, t3 = sql_conn.get_total_trade_amount_and_winning_count('50faacc4-125e-440b-83d0-c44a10c6b23a')
    # print(t1, t2, t3)

if __name__ == '__main__':
    test_sql()