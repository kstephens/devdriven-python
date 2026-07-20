def with_retry(
        func: Callable,
        max_attempts = 10,
        backoff_min_sec = 0.25,
        backoff_sec = 1.0
        backoff_factor = 1.25,
        exception_class = Exception,
        should_retry: Callable | None = None,
        failed_retry: Callable | None = None,
    ) -> Tuple[int, Any]:

    def always_retry(_attempt, _exc):
        return True

    def reraise_failed_retry(_attempt, exc):
        raise exc

    should_retry = should_retry or always_retry
    failed_retry = failed_retry or reraise_failed_retry
    last_exc = None

    for attempt in range(max_attempts):
        try:
            return attempt, func()
        except (KeyboardInterrupt, SystemExit):
            raise exc
        except exception_class as exc:
            last_exc = exc
            if should_retry(attempt, exc):
                    delay = backoff_min_sec + random.random() * backoff_sec
                    backoff_sec = backoff_sec * backoff_factor
                    time.sleep(delay)
            else:
                break
    return failed_retry(attempt, last_exc)

