from typing import Any, Callable, Iterable, Dict
import time
import random


Attempt = int
OnException = Callable[[Exception, Attempt], bool]


# pylint: disable-next=too-many-arguments,too-many-positional-arguments,too-many-locals
def retry(
    func: Callable,
    args: Iterable[Any] | None = None,
    kwargs: Dict[str, Any] | None = None,
    attempts: int = 10,
    on_exception: OnException | None = None,
    on_failure: OnException | None = None,
    exceptions: tuple = (Exception,),
    wait_min_sec: float = 0.0,
    wait_random_sec: float = 0.0,
    wait_random_factor: float = 1.0,
):
    """
    - Retry iff func(*args, **kwargs) raises an exception in the set of `exceptions` classes
      and `on_exception(exc, ...)` is truthy.
    - Retry at most `attempts` times.
    - If `wait_min_sec` or `wait_random_sec` are non-zero, sleep for a random time between retries.
    - Adjust `wait_random_sec` by `wait_random_factor` after every retry.
    - Return `on_failure(exc, ...)` when all attempts have failed.
    - The last exception is re-raised, by default.
    - `InterruptedError` and `SystemExit` exceptions are passed through.
    """

    def try_again(_exc: Exception, _attempt: Attempt):
        return True

    def fail(exc: Exception, _attempt: Attempt):
        raise exc

    args = tuple(args or [])
    kwargs = dict(kwargs or {})
    on_exc = on_exception or try_again
    on_fail = on_failure or fail
    wait_sec = 0.0
    for attempt in range(attempts):
        try:
            if wait_sec:
                time.sleep(wait_sec)
            return func(*args, **kwargs)
        except (InterruptedError, SystemExit) as exc:
            raise exc
        except exceptions as exc:
            last_exc = exc
            wait_sec = wait_min_sec + wait_random_sec * random.random()
            wait_random_sec *= wait_random_factor
            if not on_exc(exc, attempt):
                break
    return on_fail(last_exc, attempts)
