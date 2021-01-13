#!/usr/bin/env python3
from dataclasses import dataclass
from dataclasses import replace
from enum import auto
from enum import Enum
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep
from timeit import default_timer
from typing import Iterator
from typing import Optional

from click import command
from click import option
from pynput.keyboard import Controller
from pynput.keyboard import Events
from pynput.keyboard import Key
from pynput.keyboard import KeyCode
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
DEFAULT_REVIEW = 1.5
DEFAULT_FORGOTTEN = 3.0
DEFAULT_PAUSE = 1.0


_CONTROLLER = Controller()
_LOGGER = getLogger(__name__)
_TILDE = KeyCode.from_char("`")
_TQDM_STEP = 0.1


class State(Enum):
    initialize = auto()
    test = auto()
    review = auto()
    forgotten = auto()
    paused = auto()
    shut_down = auto()

    def __str__(self) -> str:
        max_len = max(len(state.name) for state in State)
        template = f"{{:{max_len}}}"
        return template.format(self.name.title())


@dataclass
class States:
    curr: "State"
    pre_pause: Optional["State"] = None


class Action(Enum):
    test_success = auto()
    test_fail_current = auto()
    fail_previous = auto()
    pause = auto()
    review_success = auto()
    review_fail_current = auto()
    finish_forgotten = auto()
    continue_pause = auto()
    unpause = auto()
    shut_down = auto()


class FailMsg(Enum):
    current = auto()
    previous = auto()

    def __str__(self) -> str:
        return f"Marking {self.name} as forgotten..."


def advance(
    states: "States",
    test: float,
    review: float,
    forgotten: float,
    pause: float,
) -> "States":
    if (
        action := get_action(states.curr, test, review, forgotten, pause)
    ) is Action.test_success:
        _CONTROLLER.tap("3")
        _CONTROLLER.tap(Key.enter)
        return States(curr=State.review)
    elif action is Action.test_fail_current:
        _LOGGER.info(FailMsg.current)
        _CONTROLLER.tap("1")
        return States(curr=fail_previous())
    elif action is Action.fail_previous:
        _LOGGER.info(FailMsg.previous)
        return States(curr=fail_previous())
    elif action is Action.pause:
        _LOGGER.info("Pausing...")
        return States(curr=State.paused, pre_pause=states.curr)
    elif action is Action.review_success:
        _CONTROLLER.tap("3")
        return States(curr=State.test)
    elif action is Action.review_fail_current:
        _LOGGER.info(FailMsg.current)
        return States(curr=fail_current_review())
    elif action is Action.finish_forgotten:
        _CONTROLLER.tap(Key.right)
        return States(curr=State.test)
    elif action is Action.continue_pause:
        return replace(states, curr=State.paused)
    elif action is Action.unpause:
        _LOGGER.info("Unpausing...")
        if (pre_pause := states.pre_pause) is None:
            raise ValueError(f"Invalid pre-pause state: {pre_pause}")
        else:
            return States(curr=pre_pause)
    elif action is Action.shut_down:
        return States(curr=State.shut_down)
    else:
        raise ValueError(f"Invalid action: {action}")


@command()
@option("--init", default=DEFAULT_INIT, type=float)
@option("--test", default=DEFAULT_TEST, type=float)
@option("--review", default=DEFAULT_REVIEW, type=float)
@option("--forgotten", default=DEFAULT_FORGOTTEN, type=float)
@option("--pause", default=DEFAULT_PAUSE, type=float)
def main(
    *,
    init: float,
    test: float,
    review: float,
    forgotten: float,
    pause: float,
) -> None:
    tqdm_sleep(duration=init, state=State.initialize)
    states = States(curr=State.test)
    while True:
        if states.curr is State.shut_down:
            _LOGGER.info("Shutting down...")
            break
        else:
            states = advance(
                states,
                test,
                review,
                forgotten,
                pause,
            )


def tqdm_sleep(duration: float, state: "State") -> None:
    for _ in tqdm_duration(duration=duration, state=state):
        sleep(_TQDM_STEP)


def tqdm_duration(duration: float, state: "State") -> Iterator[None]:
    for _ in tqdm(range(int(duration / _TQDM_STEP)), desc=str(state)):
        yield None


def get_action(
    state: "State",
    test: float,
    review: float,
    forgotten: float,
    pause: float,
) -> Action:
    if state is State.test:
        duration = test
        mapping = {
            Key.ctrl: Action.test_fail_current,
            Key.shift: Action.fail_previous,
            _TILDE: Action.pause,
        }
        default = Action.test_success
    elif state is State.review:
        duration = review
        mapping = {
            Key.ctrl: Action.review_fail_current,
            Key.shift: Action.fail_previous,
            _TILDE: Action.pause,
        }
        default = Action.review_success
    elif state is State.forgotten:
        duration = forgotten
        mapping = {_TILDE: Action.pause}
        default = Action.finish_forgotten
    elif state is State.paused:
        duration = pause
        mapping = {_TILDE: Action.unpause}
        default = Action.continue_pause
    else:
        raise ValueError(f"Invalid state: {state}")
    for _ in tqdm_duration(duration=duration, state=state):
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
                            return Action.shut_down
    return default


def fail_previous() -> "State":
    _CONTROLLER.tap(Key.left)
    return fail_current_review()


def fail_current_review() -> "State":
    _CONTROLLER.tap("1")
    _CONTROLLER.tap(Key.left)
    return State.forgotten


if __name__ == "__main__":
    main()
