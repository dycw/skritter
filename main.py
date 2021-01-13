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


DEFAULT_INIT = 2.0
DEFAULT_TEST = 1.25
DEFAULT_REVIEW = 2.0
DEFAULT_FORGOTTEN = 1.0


_CONTROLLER = Controller()
_DEFAULT_TQDM_STEP = 0.1
_LOGGER = getLogger(__name__)


def loop(
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
        if status is Status.success:
            _CONTROLLER.tap(Key.enter)
        elif status is Status.fail_current:
            _LOGGER.info("Marking current as forgotten...")
            if phase is Phase.test:
                _CONTROLLER.tap(Key.enter)
                forget_previous(forgotten, phases)
            elif phase is Phase.review:
                forget_previous(forgotten, phases)
            else:
                raise ValueError(f"Invalid phase: {phase}")
        elif status is Status.fail_previous:
            _LOGGER.info("Marking previous as forgotten...")
            forget_previous(forgotten, phases)
        elif status is Status.terminate:
            _LOGGER.info("Terminating program...")
            return
        else:
            raise ValueError(f"Invalid status: {status}")


def tqdm_sleep(dur: float, desc: str) -> None:
    for _ in tqdm_range(dur=dur, desc=desc):
        sleep(_DEFAULT_TQDM_STEP)


def tqdm_range(dur: float, desc: str) -> Iterator[None]:
    for _ in tqdm(range(int(dur / _DEFAULT_TQDM_STEP)), desc=desc):
        yield None


class Phase(Enum):
    test = auto()
    review = auto()


def get_status(dur: float, desc: str) -> "Status":
    total = int(dur / _DEFAULT_TQDM_STEP)
    for _ in tqdm(range(total), desc=desc):
        end = default_timer() + dur
        while (loop_dur := end - default_timer()) > 0.0:
            with Events() as events:
                event = events.get(timeout=loop_dur)
                if isinstance(event, Events.Release):
                    if event.key is Key.ctrl:
                        return Status.fail_current
                    elif event is Key.shift:
                        return Status.fail_previous
                elif isinstance(event, Events.Press) and (event.key is Key.esc):
                    return Status.terminate
    return Status.success


class Status(Enum):
    success = auto()
    fail_current = auto()
    fail_previous = auto()
    terminate = auto()


def forget_previous(
    forgotten: float,
    phases: peekable,
) -> None:

    _CONTROLLER.tap(Key.left)
    _CONTROLLER.tap("1")
    _CONTROLLER.tap(Key.left)
    tqdm_sleep(dur=forgotten, desc="Reviewing forgotten...")
    _CONTROLLER.tap(Key.right)
    while phases.peek() is not Phase.test:
        next(phases)


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
    loop(
        init=init,
        test=test,
        review=review,
        forgotten=forgotten,
    )


if __name__ == "__main__":
    main()
