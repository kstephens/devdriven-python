import datetime
from .runner import Runner


def test_runner():
    sut = TestRunner()

    calls = []

    def callback(runner, now):
        assert isinstance(runner, Runner)
        assert isinstance(now, datetime.datetime)
        calls.append(now)

    sut.callback = callback

    def state():
        state = vars(sut).copy()
        state.pop("clock", None)
        state.pop("clock_tick", None)
        state.pop("callback")
        state.pop("timer")
        return state

    assert state() == {
        "max_runs": 0,
        "n_runs": 0,
        "now": datetime.datetime(1970, 1, 1, 0, 0, 10),
        "poll_seconds": 0.0,
        "running": False,
        "sleep": None,
        "thread": None,
        "thread_wait": 0.5,
    }

    sut.max_runs = 5
    sut.run()
    assert state() == {
        "max_runs": 5,
        "n_runs": 5,
        "now": datetime.datetime(1970, 1, 1, 0, 1, 40),
        "poll_seconds": 0.0,
        "running": False,
        "sleep": None,
        "thread": None,
        "thread_wait": 0.5,
    }

    assert len(calls) == 5
    assert sut.timer.tick_n == 5
    assert sut.timer.elapsed_total == 50
    assert sut.timer.elapsed_tick == 10


class TestRunner(Runner):
    clock = 0
    clock_tick = 10

    def _now(self):
        self.clock += self.clock_tick
        return datetime.datetime.utcfromtimestamp(self.clock)
