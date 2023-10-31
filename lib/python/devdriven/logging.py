import json
import logging
import sys
from devdriven.to_dict import to_dict

# https://docs.python.org/3.9/library/logging.html#formatter-objects
# https://docs.python.org/3.9/library/logging.html#logging.LogRecord


# ???: subclass logging.Formatter so Formmatter(fmt, datafmt) are honored.
class JsonFormatter:  # (logging.Formatter):
    # pylint: disable=too-many-arguments
    def __init__(self, static_data=None, message_prefix=None,
                 data_key=None, encode=None,
                 message_size_limit=1024, json_size_limit=2048):
        self.static_data = static_data if static_data else {}
        self.message_prefix = message_prefix if message_prefix else ''
        self.encode = encode if encode else to_dict
        self.data_key = data_key
        self.message_separator = ' | '
        self.message_size_limit = message_size_limit
        self.json_size_limit = json_size_limit

    def format(self, record):
        # print(repr(vars(record)))
        data = {
            'level': record.levelname,
            'timestamp': record.created,
            'pid': record.process,
            'thread': record.threadName,
            'message': '',
        }
        record_data = {}
        record_args = []
        if isinstance(record.msg, dict):
            self.process_record_arg(record.msg, record_data, record_args)
        else:
            record_args.append(record.msg)
        for arg in record.args:
            self.process_record_arg(arg, record_data, record_args)
        if self.data_key:
            data[self.data_key] = record_data
        else:
            data.update(record_data)
        msg = record_args.pop(0) if record_args else ''
        if record_args:
            try:
                msg = msg % tuple(record_args)
            except TypeError as _e:
                # TypeError('not enough arguments for format string')
                # TypeError: not all arguments converted during string formatting
                record_args = [str(elem) for elem in record_args]
                msg += self.message_separator + self.message_separator.join(record_args)
        data['message'] = trim_message(msg, self.message_size_limit)
        data.update(self.static_data)
        json_body = json.dumps(self.encode(data), separators=(',', ':'))
        record.msg = self.message_prefix + trim_message(json_body, self.json_size_limit)
        record.args = []
        return record.msg

    def process_record_arg(self, arg, record_data, record_args):
        if isinstance(arg, dict):
            record_data.update(arg)
        else:
            record_args.append(arg)


def trim_message(msg, max_len, suffix='...'):
    if len(msg) >= max_len:
        return msg[0:(max_len - len(suffix))] + suffix
    return msg

def setup_logging():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def numeric_level(loglevel):
    if isinstance(loglevel, int):
        level_num = loglevel
    else:
        level_num = getattr(logging, str(loglevel).upper(), None)
    if not isinstance(level_num, int):
        raise ValueError(f'Invalid log level: {loglevel}')
    return level_num

def configure_logging(logger_options, formatter_options=None):
    # See https://docs.python.org/3/howto/logging.html
    level_number = numeric_level(logger_options.get('log_level', 'INFO'))
    logger = logging.getLogger()
    logger.setLevel(level_number)
    if not formatter_options:
        formatter_options = {}
    for handler in logger.handlers:
        handler.setFormatter(JsonFormatter(**formatter_options))
    return logger
