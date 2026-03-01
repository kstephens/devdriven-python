from .retry import retry, Attempt


def test_retry():
    assert run_retry(5) == (
        6,
        "None",
        5,
        0,
    )

    assert run_retry(15) == (
        None,
        "Exception('10')",
        10,
        1,
    )

    assert run_retry(5, InterruptedError) == (
        None,
        "InterruptedError('1')",
        0,
        0,
    )


def run_retry(max_tries, exc_class=Exception):
    on_exception_count = on_failure_count = 0
    result, n, exception = None, 0, None

    def on_exception(_exc: Exception, _attempt: Attempt):
        nonlocal on_exception_count
        on_exception_count += 1
        # print(f"on_exception {on_exception_count} {exc!r} {attempt}")
        return True

    def on_failure(exc: Exception, _attempt: Attempt):
        nonlocal on_failure_count
        on_failure_count += 1
        # print(f"on_failure {on_failure_count} {exc!r} {attempt}")
        raise exc

    def func(a, b=3):
        nonlocal n
        assert a == 2
        assert b == 5
        n += 1
        if n <= max_tries:
            raise exc_class(str(n))
        return n

    try:
        result = retry(
            func,
            args=(2,),
            kwargs={"b": 5},
            on_exception=on_exception,
            on_failure=on_failure,
            wait_min_sec=0.01,
            wait_random_sec=0.01,
            wait_random_factor=1.10,
        )
    # pylint: disable-next=broad-exception-caught
    except Exception as exc:
        exception = exc
    return result, repr(exception), on_exception_count, on_failure_count
