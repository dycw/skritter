from click import command
from click import option

from skritter import loop


@command()
@option("--init", default=5, type=int)
@option("--test", default=3.0, type=float)
@option("--review", default=3.0, type=float)
def main(*, init: int, test: float, review: float) -> None:
    loop(init=init, test=test, review=review)


if __name__ == "__main__":
    main()
