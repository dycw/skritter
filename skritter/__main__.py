from click import command
from click import option

from skritter import loop


DEFAULT_INIT = 5.0
DEFAULT_TEST = 2.0
DEFAULT_REVIEW = 4.0


@command()
@option("--init", default=DEFAULT_INIT, type=float)
@option("--test", default=DEFAULT_TEST, type=float)
@option("--review", default=DEFAULT_REVIEW, type=float)
def main(*, init: float, test: float, review: float) -> None:
    loop(init=init, test=test, review=review)


if __name__ == "__main__":
    main()
