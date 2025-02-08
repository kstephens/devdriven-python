from typing import Any, Optional, Callable
import sys
from datetime import datetime
import logging
from threading import Thread, Event
from .timer import Timer
from .util import log_exc, now_utc


class Runner:
    """
    Runs a task callback periodically in a separate thread or
    in the main thread, every poll_seconds for self.max_runs runs.
    """

    callback: Callable[[Any, datetime], Any]
    poll_seconds: float
    n_runs: int
    running: bool
    timer: Timer
    now: datetime
    thread: Optional[Thread]
    thread_wait: float
    sleep: Optional[Event]

    def __init__(self) -> None:
        self.callback = lambda runner, now: None
        self.now = self._now()
        self.running = False
        self.n_runs = 0
        self.max_runs = 0
        self.poll_seconds = 0.0
        self.thread = None
        self.thread_wait = 0.5
        self.timer = Timer()
        self.sleep = None

    def spawn(self) -> None:
        """
        Spaws a thread to run the task.
        """
        self.thread = Thread(target=self, name="Runner")
        self.thread.start()

    def run(self) -> None:
        """
        Runs the task callback periodically in a separate thread or in the main thread, every poll_seconds.
        Will run at most max_runs times.
        Sleeps for poll_seconds between runs.
        Can be called multiple times as a polling loop.
        """
        msg = "Runner.run"
        logging.info("%s", f"{msg} : starting")
        self.sleep = None
        self.n_runs = 0
        self.timer.start()
        self.running = True
        while self.running:
            logging.debug("%s", f"{msg} : {self.n_runs} runs : {self.max_runs} max")
            self.step()
            if self.max_runs > 0 and self.n_runs >= self.max_runs:
                self.running = False
            if self.running and self.poll_seconds:
                logging.info("%s", f"{msg} : sleeping : {self.poll_seconds} sec")
                # https://stackoverflow.com/a/42710697
                self.sleep = Event()
                self.sleep.wait(timeout=self.poll_seconds)
        self.timer.stop()
        logging.info("%s", f"{msg} : stopped : {self.n_runs} runs")

    def step(self) -> None:
        msg = "Runner.step"
        try:
            self.now = self._now()
            self.timer.tick_begin(now=self.now)
            self.callback(self, self.now)
        # pylint: disable-next=broad-exception-caught
        except Exception as exc:
            log_exc(exc, sys.exc_info(), msg)
        self.timer.tick_end(now=self._now())
        self.n_runs += 1

    def stop(self) -> None:
        """
        Stops run loop.
        Will wait self.thread_wait seconds for thread to stop, if running in a thread.
        """
        logging.info("%s", "Runner.stop")
        self.running = False
        if self.sleep:
            self.sleep.set()
        if self.thread:
            self.thread.join(self.thread_wait)

    def _now(self):
        return now_utc()

    def __call__(self, *args) -> None:
        self.run()
