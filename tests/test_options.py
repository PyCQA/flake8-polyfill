"""Tests for our options submodule."""
import optparse
import os

import mock
import pytest

from flake8_polyfill import options


@pytest.mark.parametrize("value,expected", [
    ("E123,\n\tW234,\n    E206", ["E123", "W234", "E206"]),
    ("E123,W234,E206", ["E123", "W234", "E206"]),
    (["E123", "W234", "E206"], ["E123", "W234", "E206"]),
    (["E123", "\n\tW234", "\n    E206"], ["E123", "W234", "E206"]),
])
def test_parse_comma_separated_list(value, expected):
    """Verify that similar inputs produce identical outputs."""
    assert options.parse_comma_separated_list(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("flake8", "flake8"),
    ("../flake8", os.path.abspath("../flake8")),
    ("flake8/", os.path.abspath("flake8")),
])
def test_normalize_path(value, expected):
    """Verify that we normalize paths provided to the tool."""
    assert options.normalize_path(value) == expected


def test_generate_callback_from_nothing():
    """Assert that do not create a new callback for nothing."""
    callback = options.generate_callback_from(comma_separated_list=False,
                                              normalize_paths=False,
                                              preexisting_callback=None)
    assert callback is None


def test_generate_callback_from_returns_preexisting():
    """Assert we return the original callback.

    If the value isn't comma separated or a path but we have a callback,
    show that we return it unadulterated.
    """
    def preexisting_callback():
        pass
    callback = options.generate_callback_from(
        comma_separated_list=False,
        normalize_paths=False,
        preexisting_callback=preexisting_callback,
    )
    assert callback is preexisting_callback


def test_generate_callback_from_comma_separated_list():
    """Assert we just return the comma-separated callback."""
    callback = options.generate_callback_from(comma_separated_list=True,
                                              normalize_paths=False,
                                              preexisting_callback=None)
    assert callback is options.comma_separated_callback


def test_generate_callback_from_normalize_paths():
    """Assert we just return the noramlize_paths callback."""
    callback = options.generate_callback_from(comma_separated_list=False,
                                              normalize_paths=True,
                                              preexisting_callback=None)
    assert callback is options.normalize_paths_callback


filename = 'file.py'
partial_path = 'path/file.py'
abspath = os.path.abspath('path/file.py')


@pytest.mark.parametrize('values, parsed_value, expected_value', [
    ({}, filename, filename),
    ({}, partial_path, abspath),
    ({'exclude': filename}, filename, filename),
    ({'exclude': filename}, partial_path, filename),
    ({'exclude': partial_path}, partial_path, abspath),
    ({'exclude': partial_path}, filename, abspath),
    ({'exclude': [filename, partial_path]},
        '{},{}'.format(filename, partial_path),
        [filename, abspath]),
])
def test_normalize_paths_callback(values, parsed_value, expected_value):
    """Assert our normalize_paths_callback behaves the right way."""
    dest = 'exclude'
    opt_str = '--exclude'
    option = optparse.Option(opt_str, dest=dest)
    parser = mock.Mock(values=optparse.Values(values))
    options.normalize_paths_callback(option, opt_str, parsed_value, parser)
    assert getattr(parser.values, dest) == expected_value


single_code = 'E123'
parsed_single_code = ['E123']
multi_code = 'E123,E234,W504'
parsed_multi_code = ['E123', 'E234', 'W504']


@pytest.mark.parametrize('values, parsed_value, expected_value', [
    ({}, single_code, parsed_single_code),
    ({}, multi_code, parsed_multi_code),
    ({'select': single_code}, single_code, parsed_single_code),
    ({'select': single_code}, multi_code, parsed_single_code),
    ({'select': multi_code}, multi_code, parsed_multi_code),
    ({'select': multi_code}, single_code, parsed_multi_code),
])
def test_comma_separated_callback(values, parsed_value, expected_value):
    """Assert our comma_separated_callback behaves the right way."""
    dest = 'select'
    opt_str = '--{}'.format(dest)
    option = optparse.Option(opt_str, dest=dest)
    parser = mock.Mock(values=optparse.Values(values))
    options.comma_separated_callback(option, opt_str, parsed_value, parser)
    assert getattr(parser.values, dest) == expected_value


# NOTE(sigmavirus24): Now for the tricky bits
