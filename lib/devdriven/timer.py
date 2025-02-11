from datetime import datetime
from .util import datetime_diff_sec, now_utc


class Timer:
    tick_n: int
    elapsed_total: float
    elapsed_tick: float
    elasped_avg: float
    elapsed_avg_running: float
    running: bool
    paused: bool
    started_at: datetime | None
    stopped_at: datetime | None
    paused_at: datetime | None
    resumed_at: datetime | None
    tick_t0: datetime | None
    tick_t1: datetime | None
    tick_t1_prev: datetime | None

    def __init__(self):
        self.tick_n = 0
        self.elapsed_total = self.elapsed_tick = 0
        self.elapsed_avg = self.elapsed_avg_running = 0
        self.running = self.paused = False
        self.started_at = self.stopped_at = None
        self.paused_at = self.resumed_at = None
        self.tick_t0 = self.tick_t1 = self.tick_t1_prev = None

    def start(self):
        self.running = True
        self.paused = False
        self.started_at = self._now()
        self.stopped_at = None

    def stop(self):
        self.stopped_at = self._now()
        self.running = self.paused = False
        self.tick_t1_prev = None

    def pause(self):
        self.paused = True
        self.paused_at = self._now()
        self.resumed_at = None

    def resume(self):
        self.paused = False
        self.paused_at = None
        self.resumed_at = self._now()
        self.tick_t1_prev = self.resumed_at

    def tick(self, now: datetime | None = None):
        if self.paused:
            return
        self.tick_t0 = self.tick_t1
        self.tick_end(now=now)

    def tick_begin(self, now: datetime | None = None):
        if self.paused:
            return
        now = now or self._now()
        self.tick_t1_prev = self.tick_t1 or now
        self.tick_t0 = now
        self.tick_n += 1

    def tick_end(self, now: datetime | None = None, elapsed: float = 0.0):
        if self.paused:
            return
        now = now or self._now()
        elapsed = elapsed or datetime_diff_sec(now, self.tick_t0)
        self.tick_t1_prev = self.tick_t1
        self.tick_t1 = now
        self.tick_elapsed(elapsed)

    def tick_elapsed(self, elapsed: float):
        self.elapsed_tick = elapsed
        self.elapsed_total += elapsed
        self.elapsed_avg = self.elapsed_total / (self.tick_n or 1)
        self.elapsed_avg_running = ((self.elapsed_avg_running or elapsed) + elapsed) / 2

    def _now(self) -> datetime:
        return now_utc()
