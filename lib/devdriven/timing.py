"""
Combinators for collecting and logging timing information.
"""

import datetime
import logging
import time
from typing import Any, Callable, Tuple

CapturedException = Tuple[Any, None] | Tuple[None, Exception]


def capture_exception(f: Callable) -> Callable[..., CapturedException]:
    def g(*args, **kwargs):
        try:
            return f(*args, **kwargs), None
        except Exception as e:
            return None, e

    g.__name__ = g.__qualname__ = f"capture_exception({f.__name__})"
    return g


def timing(f: Callable) -> Callable[..., Tuple[Any, float]]:
    def g(*args, **kwargs):
        t0 = time.perf_counter()
        result = f(*args, **kwargs)
        return result, time.perf_counter() - t0

    g.__name__ = g.__qualname__ = f"timing({f.__name__})"
    return g


def with_timing_log(f: Callable) -> Callable:
    f = timing(capture_exception(f))
    msg = f"{f.__name__}"

    def g(*args, **kwargs):
        logging.info("%s", f"{msg} : ...")
        (result, exc), elapsed_sec = f(*args, **kwargs)
        logging.info("%s", f"{msg} : {round(elapsed_sec * 1000, 2)} ms")
        if exc:
            logging.error("%s", f"{msg} : {exc!r}")
            raise exc
        return result

    g.__name__ = g.__qualname__ = f"with_timing_log({f.__name__})"
    return g


def watch(
    f: Callable,
    wait=60,
    n=-1,
    log_result: Callable | None = None,
    log_msg: Callable | None = None,
) -> Callable:
    """
    Combinator: call f(), print result, wait, repeat n times.
    Loops forever if n < 0.
    """
    log_result = log_result or (lambda x: print(repr(x)))
    log_msg = log_msg or print

    def g(*args, **kwargs):
        result = None
        i = 0
        timed_f = timing(f)

        def log(msg):
            log_msg(
                f"### watch : {i:4d} : {datetime.datetime.now().isoformat()} : {f.__name__}{msg}"
            )

        while n < 0 or i < n:
            i += 1
            try:
                log(" : ...")
                result, elapsed_sec = timed_f(*args, **kwargs)
                log_result(result)
                log(f" : {elapsed_sec} sec")
                time.sleep(wait)
            except KeyboardInterrupt as exc:
                raise exc
        return result

    g.__name__ = g.__qualname__ = f"watch({f.__name__})"
    return g
