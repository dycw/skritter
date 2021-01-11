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
    init: float,
    test: float,
    review: float,
) -> None:
    LOGGER.info("Initializing... (please go to https://skritter.com/study)")
    step = 0.01
    for _ in tqdm(range(int(init / step))):
        sleep(step)

    LOGGER.info("Running...")
    press_3()
    skip_review = False
    for phase in cycle(Phase):
        LOGGER.info(phase)
        if phase is Phase.test:
            if (clicks := count_clicks(test)) == 0:
                press_enter()
            elif clicks == 1:
                log_forgotten()
                press_enter()
                press_1()
                skip_review |= True
            elif clicks == 2:
                return log_end()
        elif phase is Phase.review:
            if skip_review:
                skip_review &= False
            else:
                if (clicks := count_clicks(review)) == 0:
                    press_3()
                elif clicks == 1:
                    log_forgotten()
                    press_1()
                else:
                    return log_end()
        else:
            raise ValueError(f"Invalid phase: {phase}")


class Phase(Enum):
    test = auto()
    review = auto()


def log_end() -> None:
    LOGGER.info("Ending session...")


def log_forgotten() -> None:
    LOGGER.info("Marking as forgotten...")


def press(key: Any) -> None:
    keyboard = Controller()
    keyboard.press(key)
    keyboard.release(key)


def press_enter() -> None:
    press(Key.enter)


def press_1() -> None:
    press("1")


def press_3() -> None:
    press("3")


def count_clicks(duration: float) -> int:
    start = default_timer()
    end = start + duration
    clicks = 0
    while (dur := end - default_timer()) > 0.0:
        with Events() as events:
            event = events.get(timeout=dur)
            if isinstance(event, Events.Click) and event.pressed:
                clicks += 1
    return clicks


__version__ = "0.0.7"
