from itertools import cycle
from logging import basicConfig
from logging import getLogger
from logging import INFO
from sys import stdout
from time import sleep

from click import command
from click import option
from pynput.keyboard import Controller
from pynput.keyboard import Key
from pynput.mouse import Events


basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="{asctime}: {msg}",
    level=INFO,
    stream=stdout,
    style="{",
)
LOGGER = getLogger(__file__)
LOGGER.setLevel(INFO)
KEYBOARD = Controller()


@command()
@option("--init", default=5, type=int)
@option("--step", default=3.0, type=float)
def main(
    *,
    init: int,
    step: float,
) -> None:
    LOGGER.info("Initializing...")
    sleep(init)

    LOGGER.info("Running...")
    for key in cycle([Key.enter, "3"]):
        LOGGER.info("Waiting for events")
        with Events() as events:
            if isinstance(events.get(timeout=step), Events.Click):
                LOGGER.info("Stopping")
                return
        KEYBOARD.press(key)
        KEYBOARD.release(key)


if __name__ == "__main__":
    main()
