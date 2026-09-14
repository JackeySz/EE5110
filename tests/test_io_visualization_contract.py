"""Placeholders for integration and visualization acceptance tests."""

import pytest


@pytest.mark.skip(reason="event persistence has not landed")
def test_npz_round_trip_preserves_events() -> None:
    pass


@pytest.mark.skip(reason="event-frame accumulation has not landed")
def test_accumulation_window_is_half_open() -> None:
    pass


@pytest.mark.skip(reason="visualization has not landed")
def test_on_is_red_and_off_is_blue_in_bgr() -> None:
    pass
