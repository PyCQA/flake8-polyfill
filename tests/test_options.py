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
multiple_paths = '{},{}'.format(filename, partial_path)
parsed_multiple_paths = [filename, abspath]


@pytest.mark.parametrize('values, parsed_value, expected_value', [
    ({}, filename, filename),
    ({}, partial_path, abspath),
    ({'exclude': filename}, filename, filename),
    ({'exclude': filename}, partial_path, filename),
    ({'exclude': partial_path}, partial_path, abspath),
    ({'exclude': partial_path}, filename, abspath),
    ({'exclude': [filename, partial_path]}, multiple_paths,
        parsed_multiple_paths),
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
# We can only really effectively test the composition with real integration
# tests.
# Testing generate_callback_from's composition separately means we don't need
# to test it when we test the register function. We can just assert it has a
# callback.
@pytest.mark.parametrize(
    'comma_separated_list, normalize_paths, preexisting_callback, values, '
    'parsed_value, expected_value', [
        (True, True, None, {}, multiple_paths, parsed_multiple_paths),
        (True, True, None, {'foo': multiple_paths}, multiple_paths,
            parsed_multiple_paths),
        (True, True, None, {'foo': parsed_multiple_paths}, multiple_paths,
            parsed_multiple_paths),
        (True, True,
            lambda opt, opt_str, v, p: p.values.foo.append('A.py'),
            {}, multiple_paths, parsed_multiple_paths + ['A.py']),
        (True, False,
            lambda opt, opt_str, v, p: p.values.foo.append('A.py'),
            {}, multiple_paths, [filename, partial_path, 'A.py']),
        (False, True,
            lambda opt, opt_str, v, p: setattr(p.values, 'foo',
                                               p.values.foo + '.j2'),
            {}, filename, filename + '.j2'),
        (False, True,
            lambda opt, opt_str, v, p: setattr(p.values, 'foo',
                                               p.values.foo + '.j2'),
            {}, partial_path, abspath + '.j2'),
    ]
)
def test_generate_callback_from_composition(
        comma_separated_list, normalize_paths, preexisting_callback, values,
        parsed_value, expected_value,
):
    """Verify our generate_callback_from composition."""
    dest = 'foo'
    opt_str = '--{}'.format(dest)
    option = optparse.Option(opt_str, dest=dest)
    parser = mock.Mock(values=optparse.Values(values))

    callback = options.generate_callback_from(
        comma_separated_list=comma_separated_list,
        normalize_paths=normalize_paths,
        preexisting_callback=preexisting_callback,
    )

    callback(option, opt_str, parsed_value, parser)
    assert getattr(parser.values, dest) == expected_value


@pytest.fixture
def parser():
    """Provide a pycodestyle-esque OptionParser instance."""
    parser = optparse.OptionParser('flake8')
    parser.config_options = []
    return parser


def test_register_parse_from_config(parser):
    """Verify we append to config_options on registration."""
    options.register(parser, '--select', default='E123,W504',
                     parse_from_config=True)
    assert 'select' in parser.config_options


def test_register_comma_separated_list(parser):
    """Verify we register the comma_separated_callback."""
    options.register(parser, '--select', default='E123,W504',
                     comma_separated_list=True)
    option = parser.get_option('--select')
    assert option.callback is options.comma_separated_callback


def test_register_normalize_paths(parser):
    """Verify we register the normalize_paths_callback."""
    options.register(parser, '--exclude', default='file.py',
                     normalize_paths=True)
    option = parser.get_option('--exclude')
    assert option.callback is options.normalize_paths_callback


def test_register_comma_separated_paths(parser):
    """Verify we register a composed hook."""
    options.register(parser, '--exclude', default='file.py',
                     normalize_paths=True, comma_separated_list=True)
    option = parser.get_option('--exclude')
    assert option.callback is not options.normalize_paths_callback
    assert option.callback is not options.comma_separated_callback
    assert option.callback is not None
