"""Test that we can import the polyfill module."""


def test_import():
    polyfill = __import__('flake8_polyfill')
    assert polyfill is not None
