import signal
from typing import Callable


def with_timeout(timeout_sec: float, f: Callable) -> Callable:
    "This is suitable only for main thread or subprocess."
    if timeout_sec <= 0:
        return f

    def g(*args, **kwargs):
        def timed_out(*_args):
            raise TimeoutError(f"timeout : {timeout_sec} : in {f.__qualname__}")
        old_handler = signal.signal(signal.SIGALRM, timed_out)
        old_itimer = signal.setitimer(signal.ITIMER_REAL, timeout_sec)
        try:
            return f(*args, **kwargs)
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.setitimer(signal.ITIMER_REAL, *old_itimer)

    return g
