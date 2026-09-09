from app.schemas import ReviewResponse

reviews_db: dict[str, ReviewResponse] = {}


def save_review(review: ReviewResponse) -> None:
    reviews_db[review.run_id] = review


def get_review(run_id: str) -> ReviewResponse | None:
    return reviews_db.get(run_id)
