import datetime
from .timer import Timer


def test_timer():
    sut = TestTimer()

    def state():
        state = vars(sut).copy()
        state.pop("clock", None)
        state.pop("clock_tick", None)
        return state

    assert state() == {
        "elapsed_avg": 0,
        "elapsed_avg_running": 0,
        "elapsed_tick": 0,
        "elapsed_total": 0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": False,
        "started_at": None,
        "stopped_at": None,
        "tick_n": 0,
        "tick_t0": None,
        "tick_t1": None,
        "tick_t1_prev": None,
    }

    sut.start()
    assert state() == {
        "elapsed_avg": 0,
        "elapsed_avg_running": 0,
        "elapsed_tick": 0,
        "elapsed_total": 0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": True,
        "started_at": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "stopped_at": None,
        "tick_n": 0,
        "tick_t0": None,
        "tick_t1": None,
        "tick_t1_prev": None,
    }

    sut.tick_begin()
    assert state() == {
        "elapsed_avg": 0,
        "elapsed_avg_running": 0,
        "elapsed_tick": 0,
        "elapsed_total": 0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": True,
        "started_at": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "stopped_at": None,
        "tick_n": 1,
        "tick_t0": datetime.datetime(1970, 1, 1, 0, 0, 20),
        "tick_t1": None,
        "tick_t1_prev": datetime.datetime(1970, 1, 1, 0, 0, 20),
    }

    sut.tick_end()
    assert state() == {
        "elapsed_avg": 10.0,
        "elapsed_avg_running": 10.0,
        "elapsed_tick": 10.0,
        "elapsed_total": 10.0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": True,
        "started_at": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "stopped_at": None,
        "tick_n": 1,
        "tick_t0": datetime.datetime(1970, 1, 1, 0, 0, 20),
        "tick_t1": datetime.datetime(1970, 1, 1, 0, 0, 30),
        "tick_t1_prev": None,
    }

    sut.clock_tick = 5
    sut.tick()
    assert state() == {
        "elapsed_avg": 15.0,
        "elapsed_avg_running": 7.5,
        "elapsed_tick": 5.0,
        "elapsed_total": 15.0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": True,
        "started_at": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "stopped_at": None,
        "tick_n": 1,
        "tick_t0": datetime.datetime(1970, 1, 1, 0, 0, 30),
        "tick_t1": datetime.datetime(1970, 1, 1, 0, 0, 35),
        "tick_t1_prev": datetime.datetime(1970, 1, 1, 0, 0, 30),
    }

    sut.tick()
    assert state() == {
        "elapsed_avg": 20.0,
        "elapsed_avg_running": 6.25,
        "elapsed_tick": 5.0,
        "elapsed_total": 20.0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": True,
        "started_at": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "stopped_at": None,
        "tick_n": 1,
        "tick_t0": datetime.datetime(1970, 1, 1, 0, 0, 35),
        "tick_t1": datetime.datetime(1970, 1, 1, 0, 0, 40),
        "tick_t1_prev": datetime.datetime(1970, 1, 1, 0, 0, 35),
    }

    sut.tick()
    assert state() == {
        "elapsed_avg": 25.0,
        "elapsed_avg_running": 5.625,
        "elapsed_tick": 5.0,
        "elapsed_total": 25.0,
        "paused": False,
        "paused_at": None,
        "resumed_at": None,
        "running": True,
        "started_at": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "stopped_at": None,
        "tick_n": 1,
        "tick_t0": datetime.datetime(1970, 1, 1, 0, 0, 40),
        "tick_t1": datetime.datetime(1970, 1, 1, 0, 0, 45),
        "tick_t1_prev": datetime.datetime(1970, 1, 1, 0, 0, 40),
    }


class TestTimer(Timer):
    clock = 0
    clock_tick = 10

    def _now(self):
        self.clock += self.clock_tick
        return datetime.datetime.utcfromtimestamp(self.clock)
