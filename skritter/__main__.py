from click import command
from click import option

from skritter import loop


DEFAULT_INIT = 2.0
DEFAULT_TEST = 1.25
DEFAULT_REVIEW = 2.0
DEFAULT_REVIEW_FORGOTTEN = 1.0


@command()
@option("--init", default=DEFAULT_INIT, type=float)
@option("--test", default=DEFAULT_TEST, type=float)
@option("--review", default=DEFAULT_REVIEW, type=float)
@option("--review-forgotten", default=DEFAULT_REVIEW_FORGOTTEN, type=float)
def main(
    *,
    init: float,
    test: float,
    review: float,
    review_forgotten: float,
) -> None:
    loop(
        init=init,
        test=test,
        review=review,
        review_forgotten=review_forgotten,
    )


if __name__ == "__main__":
    main()
