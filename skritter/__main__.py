from click import command
from click import option

from skritter import loop_until_click


@command()
@option("--init", default=5, type=int)
@option("--test", default=3, type=int)
@option("--review", default=3, type=int)
def main(*, init: int, test: int, review: int) -> None:
    loop_until_click(init=init, test=test, review=review)


if __name__ == "__main__":
    main()
