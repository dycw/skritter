from time import sleep

from click import command
from click import option
from pynput.keyboard import Controller
from pynput.keyboard import Key
from tqdm import tqdm


KEYBOARD = Controller()
INIT_STEP = 0.1


def _make_tqdm(*, total: int, step: float, desc: str) -> tqdm:
    return tqdm(range(int(total / step)), desc=desc)


@command()
@option("--init", default=10, type=int)
@option("--duration", default=60 * 60, type=int)
@option("--step", default=3.0, type=float)
def main(
    *,
    init: int,
    duration: int,
    step: float,
) -> None:
    for _ in _make_tqdm(
        total=init,
        step=INIT_STEP,
        desc="Initializing",
    ):
        sleep(INIT_STEP)

    for _ in _make_tqdm(
        total=duration,
        step=step,
        desc="Running",
    ):
        KEYBOARD.press(Key.enter)
        KEYBOARD.release(Key.enter)
        sleep(step)


if __name__ == "__main__":
    main()
