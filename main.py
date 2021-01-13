#!/usr/bin/env python3
from contextlib import suppress
from enum import auto
from enum import Enum
from enum import unique
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from timeit import default_timer
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


DEFAULT_INIT = 2.0
DEFAULT_TEST = 1.5
DEFAULT_REVIEW = 1.5
DEFAULT_FORGOTTEN = 3.0


_CONTROLLER = Controller()
_ENUM_LIKE = TypeVar("_ENUM_LIKE", bound=Enum)
_LOGGER = getLogger(__name__)
_TILDE = KeyCode.from_char("`")
_TQDM_STEP = 0.1


class State(Enum):
    init = auto()
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
class InitAction(Enum):
    pause = Key.esc
    shut_down = "q"


@unique
class TestAction(Enum):
    toggle_pause = Key.esc
    fail_current = Key.ctrl
    fail_previous = Key.shift
    shut_down = "q"


@unique
class ReviewAction(Enum):
    toggle_pause = Key.esc
    fail_current = Key.ctrl
    fail_previous = Key.shift
    shut_down = "q"


@unique
class ForgottenAction(Enum):
    pause = Key.esc
    shut_down = "q"


class FailMsg(Enum):
    current = auto()
    previous = auto()

    def __str__(self) -> str:
        return f"Marking {self.name} as forgotten..."


@command()
@option("--init", default=DEFAULT_INIT, type=float)
@option("--test", default=DEFAULT_TEST, type=float)
@option("--review", default=DEFAULT_REVIEW, type=float)
@option("--forgotten", default=DEFAULT_FORGOTTEN, type=float)
def main(
    *,
    init: float,
    test: float,
    review: float,
    forgotten: float,
) -> None:
    state = State.init
    while (
        state := advance(state, init, test, review, forgotten)
    ) is not State.shut_down:
        pass
    _LOGGER.info("Shutting down...")


def advance(
    state: "State",
    init: float,
    test: float,
    review: float,
    forgotten: float,
) -> "State":
    durations = {
        State.init: init,
        State.test: test,
        State.review: review,
        State.forgotten: forgotten,
    }
    duration = durations.get(state, 60.0)

    if state is State.init:
        init_action = get_action(
            duration=duration,
            state=state,
            actions=InitAction,
        )
        if init_action is None:
            return State.test
        elif init_action is InitAction.pause:
            return pause_test()
        elif init_action is InitAction.shut_down:
            return State.shut_down
        else:
            raise ValueError(f"Invalid action: {init_action}")

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
            return pause_test()
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


def get_action(
    duration: float,
    state: "State",
    actions: Type[_ENUM_LIKE],
) -> Optional[_ENUM_LIKE]:
    for _ in tqdm(
        range(int(duration / _TQDM_STEP)),
        desc=str(state),
        bar_format="{desc} {bar} {percentage:3.0f}%",
    ):
        end = default_timer() + _TQDM_STEP
        while (dur := end - default_timer()) > 0.0:
            with Events() as events:
                event = events.get(timeout=dur)
                if isinstance(event, Events.Press):
                    key = event.key
                    with suppress(StopIteration):
                        try:
                            match = key.char
                        except AttributeError:
                            match = key
                        return next(
                            action
                            for action in actions
                            if action.value == match
                        )
    return None


def fail_previous() -> "State":
    _CONTROLLER.tap(Key.left)
    return fail_current_review()


def fail_current_review() -> "State":
    _CONTROLLER.tap("1")
    _CONTROLLER.tap(Key.left)
    return State.forgotten


def pause_test() -> "State":
    _LOGGER.info("Pausing test...")
    return State.test_paused


def pause_review() -> "State":
    _LOGGER.info("Pausing review...")
    return State.review_paused


if __name__ == "__main__":
    main()
