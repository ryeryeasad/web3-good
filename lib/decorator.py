import datetime
import time
import logging
from functools import wraps

logger = logging.getLogger("triple.Decorator")
BASIC_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
chlr = logging.StreamHandler() # 输出到控制台的handler
chlr.setFormatter(formatter)
chlr.setLevel('DEBUG')  # 也可以不设置，不设置就默认用logger的level
logger.addHandler(chlr)


def time_cost(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.debug("Function <%s> begins." % f.__name__)
        result = f(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.debug("Function <%s> took %d ms to finish." % (f.__name__, elapsed))
        return result
    return wrapper


def tries(num=3):
    def _try(fun):
        @wraps(fun)
        def wrapper(*args, **kwds):
            i = 0
            while i < int(num):
                try:
                    result = fun(*args, **kwds)
                    return result
                except Exception as e:
                    i += 1
                    logger.debug("the {} try".format(i + 1))
                    if i >= num:
                        raise e
        return wrapper
    return _try


def class_route(methods=['GET']):
    def _route(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            func.provide_automatic_options = False
            func.methods = methods.append('OPTIONS')  # ['GET', 'OPTIONS']
            result = func(self, *args, **kwargs)
            return result
        return wrapper
    return _route