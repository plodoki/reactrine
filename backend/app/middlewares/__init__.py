"""Middleware registration package."""

from .request_timing_middleware import register_request_id_and_timing

__all__ = [
    "register_request_id_and_timing",
]
