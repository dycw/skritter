#!/usr/bin/env python3
from contextlib import suppress
from enum import auto
from enum import Enum
from enum import unique
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep
from timeit import default_timer
from typing import Iterator
from typing import Optional
from typing import Type
from typing import TypeVar

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


DEFAULT_TEST = 1.5
DEFAULT_REVIEW = 1.5
DEFAULT_FORGOTTEN = 3.0


_CONTROLLER = Controller()
_ENUM_LIKE = TypeVar("_ENUM_LIKE", bound=Enum)
_LOGGER = getLogger(__name__)
_TILDE = KeyCode.from_char("`")
_TQDM_STEP = 0.1


class State(Enum):
    pre_start = auto()
    test = auto()
    test_paused = auto()
    review = auto()
    review_paused = auto()
    forgotten = auto()
    shut_down = auto()

    def __str__(self) -> str:
        max_len = max(len(state.name) for state in State)
        template = f"{{:{max_len}}}"
        return template.format(self.name.title())


@unique
class PreStartAction(Enum):
    unpause = Key.esc
    shut_down = KeyCode.from_char("q")


@unique
class TestAction(Enum):
    toggle_pause = Key.esc
    fail_current = Key.ctrl
    fail_previous = Key.shift
    shut_down = KeyCode.from_char("q")


@unique
class ReviewAction(Enum):
    toggle_pause = Key.esc
    fail_current = Key.ctrl
    fail_previous = Key.shift
    shut_down = KeyCode.from_char("q")


@unique
class ForgottenAction(Enum):
    pause = Key.esc
    shut_down = KeyCode.from_char("q")


class FailMsg(Enum):
    current = auto()
    previous = auto()

    def __str__(self) -> str:
        return f"Marking {self.name} as forgotten..."


@command()
@option("--test", default=DEFAULT_TEST, type=float)
@option("--review", default=DEFAULT_REVIEW, type=float)
@option("--forgotten", default=DEFAULT_FORGOTTEN, type=float)
def main(
    *,
    test: float,
    review: float,
    forgotten: float,
) -> None:
    state = State.pre_start
    while (
        state := advance(state, test, review, forgotten)
    ) is not State.shut_down:
        pass
    _LOGGER.info("Shutting down...")


def advance(
    state: "State",
    test: float,
    review: float,
    forgotten: float,
) -> "State":
    durations = {
        State.test: test,
        State.review: review,
        State.forgotten: forgotten,
    }
    duration = durations.get(state, 60.0)

    if state is State.pre_start:
        pre_start_action = get_action(
            duration=duration,
            state=state,
            actions=PreStartAction,
        )
        if pre_start_action is None:
            return state
        elif pre_start_action is PreStartAction.unpause:
            _LOGGER.info("Starting tests...")
            return State.test
        elif pre_start_action is PreStartAction.shut_down:
            return State.shut_down
        else:
            raise ValueError(f"Invalid action: {pre_start_action}")

    elif state in {State.test, State.test_paused}:
        test_action = get_action(
            duration=duration,
            state=state,
            actions=TestAction,
        )
        if (state is State.test) and (test_action is None):
            _CONTROLLER.tap("3")
            _CONTROLLER.tap(Key.enter)
            return State.review
        elif (state is State.test) and (test_action is TestAction.toggle_pause):
            _LOGGER.info("Pausing test...")
            return State.test_paused
        elif (state is State.test_paused) and (test_action is None):
            return State.test_paused
        elif (state is State.test_paused) and (
            test_action is TestAction.toggle_pause
        ):
            _LOGGER.info("Unpausing test...")
            return State.test
        elif test_action is TestAction.fail_current:
            _LOGGER.info(FailMsg.current)
            _CONTROLLER.tap("1")
            return fail_previous()
        elif test_action is TestAction.fail_previous:
            _LOGGER.info(FailMsg.previous)
            return fail_previous()
        elif test_action is TestAction.shut_down:
            return State.shut_down
        else:
            raise ValueError(f"Invalid state/action: {state}/{test_action}")

    elif state in {State.review, State.review_paused}:
        review_action = get_action(
            duration=duration,
            state=state,
            actions=ReviewAction,
        )
        if (state is State.review) and (review_action is None):
            _CONTROLLER.tap("3")
            return State.test
        elif (state is State.review) and (
            review_action is ReviewAction.toggle_pause
        ):
            return pause_review()
        elif (state is State.review_paused) and (review_action is None):
            return State.review_paused
        elif (state is State.review_paused) and (
            review_action is ReviewAction.toggle_pause
        ):
            _LOGGER.info("Unpausing review...")
            return State.review
        elif review_action is ReviewAction.fail_current:
            _LOGGER.info(FailMsg.current)
            return fail_current_review()
        elif review_action is ReviewAction.fail_previous:
            _LOGGER.info(FailMsg.previous)
            return fail_previous()
        elif review_action is ReviewAction.shut_down:
            return State.shut_down
        else:
            raise ValueError(f"Invalid state/action: {state}, {review_action}")

    elif state is State.forgotten:
        forgotten_action = get_action(
            duration=duration,
            state=state,
            actions=ForgottenAction,
        )
        if forgotten_action is None:
            _CONTROLLER.tap(Key.right)
            return State.test
        elif forgotten_action is ForgottenAction.pause:
            return pause_review()
        elif forgotten_action is ForgottenAction.shut_down:
            return State.shut_down
        else:
            raise ValueError(f"Invalid action: {forgotten_action}")

    else:
        raise ValueError(f"Invalid state: {state}")


def tqdm_sleep(duration: float, state: "State") -> None:
    for _ in tqdm_duration(duration=duration, state=state):
        sleep(_TQDM_STEP)


def tqdm_duration(duration: float, state: "State") -> Iterator[None]:
    for _ in tqdm(range(int(duration / _TQDM_STEP)), desc=str(state)):
        yield None


def get_action(
    duration: float,
    state: "State",
    actions: Type[_ENUM_LIKE],
) -> Optional[_ENUM_LIKE]:
    for _ in tqdm_duration(duration=duration, state=state):
        end = default_timer() + _TQDM_STEP
        while (dur := end - default_timer()) > 0.0:
            with Events() as events:
                event = events.get(timeout=dur)
                if isinstance(event, Events.Press):
                    key = event.key
                    with suppress(StopIteration):
                        try:
                            char = key.char
                        except AttributeError:
                            return next(
                                action
                                for action in actions
                                if action.value is key
                            )
                        else:
                            return next(
                                action
                                for action in actions
                                if getattr(action.value, "char", None) == char
                            )

    return None


def fail_previous() -> "State":
    _CONTROLLER.tap(Key.left)
    return fail_current_review()


def fail_current_review() -> "State":
    _CONTROLLER.tap("1")
    _CONTROLLER.tap(Key.left)
    return State.forgotten


def pause_review() -> "State":
    _LOGGER.info("Pausing review...")
    return State.review_paused


if __name__ == "__main__":
    main()
