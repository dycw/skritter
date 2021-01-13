#!/usr/bin/env python3
from enum import auto
from enum import Enum
from itertools import cycle
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep
from timeit import default_timer
from typing import Iterator

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


# DEFAULT_INIT = 2.0
# DEFAULT_TEST = 1.25
# DEFAULT_REVIEW = 2.0
# DEFAULT_FORGOTTEN = 1.0
DEFAULT_INIT = 5.0
DEFAULT_TEST = 5.0
DEFAULT_REVIEW = 5.0
DEFAULT_FORGOTTEN = 5.0


_CONTROLLER = Controller()
_LOGGER = getLogger(__name__)
_MARKING_TEMPLATE = "Marking {0} as forgotten..."
_MARKING_CURRENT = _MARKING_TEMPLATE.format("current")
_TQDM_STEP = 0.1


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
    tqdm_sleep(dur=init, desc="Initializing")
    phases = peekable(cycle(Phase))
    for phase in phases:
        if phase is Phase.test:
            status = get_status(dur=test, desc="Testing")
        elif phase is Phase.review:
            status = get_status(dur=review, desc="Reviewing")
        else:
            raise ValueError(f"Invalid phase: {phase}")
        if (phase is Phase.test) and (status is Status.success):
            _CONTROLLER.tap("3")
            _CONTROLLER.tap(Key.enter)
        elif (phase is Phase.test) and (status is Status.fail_current):
            _LOGGER.info("Marking current as forgotten...")
            _CONTROLLER.tap(Key.enter)
            _CONTROLLER.tap("1")
            fail_previous(forgotten, phases)
        elif (phase is Phase.review) and (status is Status.success):
            _CONTROLLER.tap("3")
        elif (phase is Phase.review) and (status is Status.fail_current):
            _LOGGER.info("Marking current as forgotten...")
            fail_current(forgotten=forgotten, phases=phases)
        elif status is Status.fail_previous:
            _LOGGER.info(_MARKING_TEMPLATE.format("previous"))
            fail_previous(forgotten=forgotten, phases=phases)
        elif status is Status.terminate:
            _LOGGER.info("Terminating program...")
            return
        else:
            raise ValueError(f"Invalid phase/status: {phase}, {status}")


def tqdm_sleep(dur: float, desc: str) -> None:
    for _ in tqdm_dur(dur=dur, desc=desc):
        sleep(_TQDM_STEP)


def tqdm_dur(dur: float, desc: str) -> Iterator[None]:
    for _ in tqdm(range(int(dur / _TQDM_STEP)), desc=desc):
        yield None


class Phase(Enum):
    test = auto()
    review = auto()


def get_status(dur: float, desc: str) -> "Status":
    for _ in tqdm_dur(dur=dur, desc=desc):
        end = default_timer() + _TQDM_STEP
        while (loop_dur := end - default_timer()) > 0.0:
            with Events() as events:
                event = events.get(timeout=loop_dur)
                if isinstance(event, Events.Press):
                    if event.key == Key.ctrl:
                        return Status.fail_current
                    elif event == Key.shift:
                        return Status.fail_previous
                    elif event.key == Key.esc:
                        return Status.terminate
    return Status.success


class Status(Enum):
    success = auto()
    fail_current = auto()
    fail_previous = auto()
    terminate = auto()


def fail_previous(
    forgotten: float,
    phases: peekable,
) -> None:
    _CONTROLLER.tap(Key.left)
    fail_current(forgotten=forgotten, phases=phases)


def fail_current(forgotten: float, phases: peekable) -> None:
    _CONTROLLER.tap("1")
    _CONTROLLER.tap(Key.left)
    tqdm_sleep(dur=forgotten, desc="Confirming")
    _CONTROLLER.tap(Key.right)
    while phases.peek() is not Phase.test:
        next(phases)


if __name__ == "__main__":
    main()
