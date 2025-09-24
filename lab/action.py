import pdb
pdb.set_trace()
from abc import ABC, abstractmethod

Duration = float

class Action(ABC):
    def __init__(self):
        super().__init__()
        self._fired = False

    @property
    def fired(self):
        return self._fired

    def reset(self):
        pass

    def __call__(self, dt: Duration):
        return self.tick(dt)

    @abstractmethod
    def tick(self, dt: Duration):
        pass

    def fire(self):
        self._fired = True

    def __or__(self, other):
        return Sequence([self, other])

class Exec(Action):
    def tick(self, dt: Duration):
        self.fire()

    def fire(self):
        super().fire()
        return self.execute()

    @abstractmethod
    def execute(self):
        pass

class Timed(Action):
    def __init__(self, duration: Duration, action: Action):
        super().__init__()
        self._action = action
        self._duration = duration
        self._remaining = self._elapsed = None
        self.reset()

    def reset(self):
        self._remaining = self._initial_duration
        self._elapsed = 0

    @property
    def duration(self):
        return self._duration

    @property
    def remaining(self):
        return self._remaining

    @property
    def is_complete(self):
        return self.remaining <= 0

    def tick(self, dt: Duration):
        is_complete, remaining_dt, applied_dt, = self.apply_tick(dt)
        if is_complete:
            self.action.tick(remaining_dt)

    def apply_tick(self, dt: Duration): # is_complete, remaining_dt, applied_dt
        assert dt >= 0
        if dt == 0:
            return True, 0, 0
        if dt < self._remaining:
            self._remaining -= dt
            self._elapsed += dt
            return False, 0, dt
        applied_dt = self._remaining
        remaining_dt = dt - self._remaining
        self._remaining = 0
        self._elapsed += applied_dt
        return False, remaining_dt, applied_dt

class Composite(Action):
    def __init__(self, actions):
        super().__init__()
        self.initial_actions = actions
        self.actions = self.current = None
        self.reset()

    def advance(self):
        if self.actions:
            self.current = self.actions.pop(0)
        else:
            self.current = None
        return self.current

    def reset(self):
        super().reset()
        self.actions = [ action.copy() for action in self.initial_actions]
        self.current = self.actions.first

###########################################################

class Sequence(Composite):
    def __init__(self, actions):
        super().__init__(actions)

    def tick(self, dt: Duration):
        complete, applied_dt, remaining_dt = False, 0, remaining_dt, dt
        while self.current and remaining_dt > 0:
            complete, applied_dt, remaining_dt = self.apply_tick(self.current)
            if complete:
                self.advance()

class Wait(Timed):
    pass

class Func(Exec):
    def __init__(self, callable, *args, **kwargs):
        super().__init__()
        self.callable, self.args, self.kwargs = callable, args, kwargs
        self.reset()

    def execute(self):
        return self.callable(*self.args, **self.kwargs)

class Method(Exec):
    def __init__(self, target, method, *args, **kwargs):
        super().__init__()
        self.target, self.method, self.args, self.kwargs = target, method, args, kwargs
        self.reset()

    def execute(self):
        return getattr(self.target, self.method)(*self.args, **self.kwargs)

class Forever(Composite):
    def __init__(self, action: Action):
        super().__init__([action])

    def tick(self, dt: Duration):
        self.current.tick(dt)
        if not self.current:
            self.reset()

########################################

tick = 0.1
action = Func(lambda: print("hello"))
action(tick)

breakpoint()
