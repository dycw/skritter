#!/usr/bin/env python3
from collections import defaultdict
from contextlib import suppress
from enum import auto
from enum import Enum
from itertools import cycle
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep
from timeit import default_timer
from typing import Iterator, Optional, List, Callable, Dict, Iterable, Tuple

from click import command
from click import option
from more_itertools import peekable
from pynput.keyboard import Controller
from pynput.keyboard import Events
from pynput.keyboard import Key
from tqdm import tqdm


basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="{asctime}: {msg}",
    level=INFO,
    stream=stdout,
    style="{",
)


DEFAULT_INIT = 2.0
DEFAULT_TEST = 1.5
DEFAULT_CHECK_ANSWER = 1.5
DEFAULT_REVIEW_FORGOTTEN = 3.0
DEFAULT_PAUSE = 1.


_CONTROLLER = Controller()
_LOGGER = getLogger(__name__)
_TQDM_STEP = 0.1


class Msg(Enum):
    current = auto()
    previous = auto()
    pause = auto()

    def __str__(self) -> str:
        if self in {Msg.current, Msg.previous}:
            return f"Marking {self.name} as forgotten..."
        elif self is Msg.pause:
            return 'Pausing...'
        else:
            raise ValueError(f"Invalid message: {self}")


class Phase(Enum):
    test = auto()
    review = auto()


class State(Enum):
    initializing = auto()
    testing = auto()
    reviewing = auto()
    confirming = auto()
    pausing = auto()
    shutting_down = auto()


    def __str__(self) -> str:
        max_len = max(len(state) for state in State if state.name)
        template = f"{{:{max_len}}}"
        return template.format(self.name.title())





def advance(
        state: "State",
        pre_pause:Optional["State"],
        init :float,
        test: float,
        check_answer:float,
        check_forgotten:float,
        pause:float,
)->Tuple["State", Optional["State"]]:
    if state is State.initializing:
        tqdm_sleep(dur=init, state=state)
        return State.testing, pre_pause
    elif state is State.testing:
        if (outcome := get_outcome(dur=test, state=state)) is Outcome.test_and_check_success:
            _CONTROLLER.tap("3")
            _CONTROLLER.tap(Key.enter)
            return State.reviewing, None
        elif outcome is Outcome.test_review_fail_current:
            _LOGGER.info(Msg.current)
            _CONTROLLER.tap(Key.enter)
            _CONTROLLER.tap("1")
            return fail_previous(check_forgotten)
        elif outcome is Outcome.test_review_fail_previous:
            _LOGGER.info(Msg.previous)
            return fail_previous(check_forgotten)
        elif outcome is Outcome.test_review_pause:
            _LOGGER.info(Msg.pause)
            return State.pausing, state
        elif outcome is Outcome.terminate:
            _LOGGER.info('Shutting down...')
            return State.shutting_down, None
        else:
            raise ValueError("Invalid outcome")
    if  state is State.pausing:
        key = get_key(keys={'`', Key.esc}, dur=pause, state=State.pausing)
        if key is None:
            return State.pausing, pre_pause
        elif key == '`':
            return pre_pause, None
        elif key is Key.esc:
            return State.shutting_down, None
        else:
            raise ValueError(f"Invalid key: {key}")
    else:
            phases = peekable(cycle(Phase))
            for phase in phases:
                if phase is Phase.test:
                    status = get_status(dur=test, state=Desc.test)
                elif phase is Phase.review:
                    status = get_status(dur=check_answer, state=Desc.review)
                else:
                    raise ValueError(f"Invalid phase: {phase}")
                if (phase is Phase.test) and (status is Status.test_and_check_success):
                    _CONTROLLER.tap("3")
                    _CONTROLLER.tap(Key.enter)
                elif (phase is Phase.test) and (status is Status.test_review_fail_current):
                    _LOGGER.info(str(Msg.current))
                    _CONTROLLER.tap(Key.enter)
                    _CONTROLLER.tap("1")
                    fail_previous(check_forgotten, phases)
                elif (phase is Phase.review) and (status is Status.test_and_check_success):
                    _CONTROLLER.tap("3")
                elif (phase is Phase.review) and (status is Status.test_review_fail_current):
                    _LOGGER.info("Marking current as forgotten...")
                    fail_current(forgotten=check_forgotten, phases=phases)
                elif status is Status.test_review_fail_previous:
                    _LOGGER.info(str(Msg.previous))
                    fail_previous(forgotten=check_forgotten, phases=phases)
                elif status is Status.terminate:
                    _LOGGER.info("Terminating program...")
                    return
                else:
                    raise ValueError(f"Invalid phase/status: {phase}, {status}")

            if state is State.testing:
                pass

            else:
                raise ValueError(f"Invalid state: {state}")


class Desc(Enum):
    initial = auto()
    test = auto()
    review = auto()
    confirm = auto()
    sleep =auto()

    def __str__(self) -> str:
        max_len = max(len(desc.ing) for desc in Desc)
        template = f"{{:{max_len}}}"
        return template.format(self.ing)

    @property
    def ing(self) -> str:
        return self.name.title() + "ing"

class Outcome(Enum):
    test_and_check_success = auto()
    test_review_fail_current = auto()
    test_review_fail_previous = auto()
    test_review_pause = auto()
    test_review_unpause = auto()

    paused_continue = auto()
    paused_to_unpaused = auto()
    terminate = auto()

@command()
@option("--init", default=DEFAULT_INIT, type=float)
@option("--test", default=DEFAULT_TEST, type=float)
@option("--check-answer", default=DEFAULT_CHECK_ANSWER, type=float)
@option("--review-forgotten", default=DEFAULT_REVIEW_FORGOTTEN, type=float)
@option("--pause", default=DEFAULT_PAUSE, type=float)
def main(
    *,
    init: float,
    test: float,
    check_answer: float,
    review_forgotten: float,
        pause: float
) -> None:
    tqdm_sleep(dur=init, state=State.initializing)

    state = State.initializing
    pre_pause = None
    while    True:
        if state is State.shutting_down:
            _LOGGER.info("Shutting down...")
            return
        else:
            state, pre_pause = advance(state, pre_pause, init=init, test=test,
                                       check_answer=check_answer,
    review_forgotten=review_forgotten,
                                       pause=pause)

def tqdm_sleep(dur: float, state: "State") -> None:
    for _ in tqdm_dur(dur=dur, state=state):
        sleep(_TQDM_STEP)


def tqdm_dur(dur: float, state: "State") -> Iterator[None]:
    for _ in tqdm(range(int(dur / _TQDM_STEP)), desc=str(state)):
        yield None


def get_key(keys: Iterable[Key], dur: float, state: "State", ) ->Optional[Key]:
    keys = set(keys)
    for _ in tqdm_dur(dur=dur, state=state):
        end = default_timer() + _TQDM_STEP
        while (loop_dur := end - default_timer()) > 0.0:
            with Events() as events:
                event = events.get(timeout=loop_dur)
                if isinstance(event, Events.Press) and ((key := event.key) in keys):
                    return key
    return None





def get_outcome(dur:float, state: "State")->Outcome:
    if state is State.initializing:
        mapping = {'`': Outcome.paused_to_unpaused}
        default = Outcome
    if state in {State.testing, State.shutting_down}:
        mapping = {
            Key.ctrl: Outcome.test_review_fail_current,
            Key.shift: Outcome.test_review_fail_previous,
            '`': Outcome.test_review_pause,
        }
        default = Outcome.test_and_check_success
    elif state is State.pausing:
        mapping = {'`': Outcome.paused_to_unpaused}
        default = Outcome.paused_continue
    else:
        raise ValueError(f'Invalid state: {state}')
    for _ in tqdm_dur(dur=dur, state=state):
        end = default_timer() + _TQDM_STEP
        while (loop_dur := end - default_timer()) > 0.0:
            with Events() as events:
                event = events.get(timeout=loop_dur)
                if isinstance(event, Events.Press):
                    key = event.key
                    try:
                        return mapping[key]
                    except KeyError:
                        if key is Key.esc:
                            return Outcome.terminate
    return default

def fail_previous(forgotten: float) -> Tuple["State",Optional['State']]:
    _CONTROLLER.tap(Key.left)
    return fail_current(forgotten)


def fail_current(forgotten: float) -> Tuple["State", Optional['State']]:
    _CONTROLLER.tap("1")
    _CONTROLLER.tap(Key.left)
    return State.confirming, None
    # tqdm_sleep(dur=forgotten, state=Desc.confirm)
    # _CONTROLLER.tap(Key.right)
    # while phases.peek() is not Phase.test:
    #     next(phases)


if __name__ == "__main__":
    main()
