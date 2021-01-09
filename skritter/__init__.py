from enum import auto
from enum import Enum
from itertools import cycle
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep
from timeit import default_timer
from typing import Any
from typing import List

from pynput.keyboard import Controller
from pynput.keyboard import Key
from pynput.mouse import Events
from tqdm import tqdm


basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="{asctime}: {msg}",
    level=INFO,
    stream=stdout,
    style="{",
)
LOGGER = getLogger(__name__)


def loop(
    *,
    init: int,
    test: float,
    review: float,
) -> None:
    LOGGER.info("Initializing... (please go to https://skritter.com/study)")
    step = 0.01
    for _ in tqdm(range(int(init / step))):
        sleep(step)

    LOGGER.info("Running...")
    press_and_release_three()
    for phase in cycle(Phase):
        if phase is Phase.test:
            sleep(test)
            press_and_release(Key.enter)
        elif phase is Phase.review:
            events = collect_mouse_events(review)
            clicks = sum(isinstance(e, Events.Click) for e in events)
            if clicks == 0:
                press_and_release_three()
            elif clicks == 1:
                LOGGER.info("Marking as forgot...")
                press_and_release("1")
            else:
                LOGGER.info("Ending session...")
                return
        else:
            raise ValueError(f"Invalid phase: {phase}")


class Phase(Enum):
    test = auto()
    review = auto()


def press_and_release(key: Any) -> None:
    keyboard = Controller()
    keyboard.press(key)
    keyboard.release(key)


def press_and_release_three() -> None:
    press_and_release("3")


def collect_mouse_events(duration: float) -> List[Events]:
    start = default_timer()
    end = start + duration
    events: List[Events] = []
    while (dur := end - default_timer()) > 0.0:
        with Events() as evs:
            if (ev := evs.get(timeout=dur)) is not None:
                events.append(ev)
    return events


__version__ = "0.0.4"
