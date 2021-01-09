from contextlib import contextmanager
from itertools import cycle
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep
from timeit import default_timer
from typing import Iterator
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


@contextmanager
def collect_mouse_events(duration: float) -> Iterator[List[Events]]:
    start = default_timer()
    end = start + duration
    events: List[Events] = []
    while (dur := end - default_timer()) > 0.0:
        with Events() as evs:
            if (ev := evs.get(timeout=dur)) is not None:
                events.append(ev)
    yield events


def loop_until_click(
    *,
    init: int,
    test: int,
    review: int,
) -> None:
    LOGGER.info("Initializing... (please go to https://skritter.com/study)")
    step = 0.01
    for _ in tqdm(range(int(init / step))):
        sleep(step)

    LOGGER.info("Running...")
    keyboard = Controller()
    for key, dur in cycle([(Key.enter, test), ("3", review)]):
        with collect_mouse_events(dur) as events:
            if any(isinstance(event, Events.Click) for event in events):
                LOGGER.info("Mouse clicked; aborting...")
                return
            else:
                keyboard.press(key)
                keyboard.release(key)


__version__ = "0.0.3"
