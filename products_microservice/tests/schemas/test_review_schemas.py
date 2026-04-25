from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewRead


def test_review_create_rating_must_be_1_to_5() -> None:
    pid = uuid4()
    assert ReviewCreate(product_id=pid, text="Nice", rating=1).rating == 1
    assert ReviewCreate(product_id=pid, text="Nice", rating=5).rating == 5

    with pytest.raises(ValidationError):
        ReviewCreate(product_id=pid, text="Nice", rating=0)
    with pytest.raises(ValidationError):
        ReviewCreate(product_id=pid, text="Nice", rating=6)


def test_review_create_text_length() -> None:
    pid = uuid4()

    long_ok = "x" * 2000
    assert ReviewCreate(product_id=pid, text=long_ok, rating=3).text == long_ok

    too_long = "x" * 2001
    with pytest.raises(ValidationError):
        ReviewCreate(product_id=pid, text=too_long, rating=3)

    with pytest.raises(ValidationError):
        ReviewCreate(product_id=pid, text="", rating=3)


def test_review_read_round_trips() -> None:
    rid = uuid4()
    pid = uuid4()
    payload = {
        "id": rid,
        "product_id": pid,
        "text": "Great bulb",
        "rating": 5,
        "created_at": datetime(2026, 4, 25, 12, 0, tzinfo=timezone.utc),
        "created_by": None,
        "edited_at": None,
        "edited_by": None,
    }
    read = ReviewRead.model_validate(payload)
    assert read.id == rid
    assert read.product_id == pid
    assert read.rating == 5
    assert read.created_by is None
    assert read.edited_by is None

    listing = ReviewListResponse(data=[read])
    assert listing.data[0].id == rid
