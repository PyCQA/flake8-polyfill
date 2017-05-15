"""Tests for our options submodule."""
import optparse
import os

import mock
import pytest

from flake8_polyfill import options


@pytest.mark.parametrize('value,expected', [
    ('E123,\n\tW234,\n    E206', ['E123', 'W234', 'E206']),
    ('E123,W234,E206', ['E123', 'W234', 'E206']),
    (['E123', 'W234', 'E206'], ['E123', 'W234', 'E206']),
    (['E123', '\n\tW234', '\n    E206'], ['E123', 'W234', 'E206']),
])
def test_parse_comma_separated_list(value, expected):
    """Verify that similar inputs produce identical outputs."""
    assert options.parse_comma_separated_list(value) == expected


@pytest.mark.parametrize('value,expected', [
    ('flake8', 'flake8'),
    ('../flake8', os.path.abspath('../flake8')),
    ('flake8/', os.path.abspath('flake8')),
])
def test_normalize_path(value, expected):
    """Verify that we normalize paths provided to the tool."""
    assert options.normalize_path(value) == expected


@pytest.mark.parametrize('value,expected', [
    ('file.py', 'file.py'),
    ('path/file.py', os.path.abspath('path/file.py')),
    (['file.py', 'path/file.py'],
     ['file.py', os.path.abspath('path/file.py')]),
])
def test_parse_normalized_paths(value, expected):
    """Verify that we handle strings and lists when normalizing paths."""
    assert options.parse_normalized_paths(value) == expected


@pytest.mark.parametrize(
    # NOTE: `defaults` has NO impact, since the callback being called implies
    # that a `value` was specified.
    'comma_separated_list, normalize_paths, defaults, value, expected_value', [
        (True, True, {}, 'val', 'N(C(val))'),
        (True, True, {'foo': 'defaultval'}, 'val', 'N(C(val))'),
        (True, False, {}, 'val', 'C(val)'),
        (True, False, {'foo': 'defaultval'}, 'val', 'C(val)'),
        (False, False, {}, 'val', 'val'),
        (False, False, {'foo': 'defaultval'}, 'val', 'val'),
    ]
)
def test_generate_callback_from_composition(
        comma_separated_list, normalize_paths, defaults,
        value, expected_value,
):
    """Verify our generate_callback_from composition.

    We mock out parse_comma_separated_list and parse_normalized_paths with
    simple string transformations for better readability.
    """
    dest = 'foo'
    opt_str = '--foo'
    option = optparse.Option(opt_str, dest=dest)
    parser = mock.Mock(values=optparse.Values(defaults))

    base_callback = mock.Mock()
    callback = options.generate_callback_from(
        comma_separated_list=comma_separated_list,
        normalize_paths=normalize_paths,
        base_callback=base_callback,
    )

    with mock.patch('flake8_polyfill.options.parse_comma_separated_list') as \
            parse_comma_separated_list, \
            mock.patch('flake8_polyfill.options.parse_normalized_paths') as \
            parse_normalized_paths:

        parse_comma_separated_list.side_effect = lambda v: 'C({})'.format(v)
        parse_normalized_paths.side_effect = lambda v: 'N({})'.format(v)
        callback(option, opt_str, value, parser)

    base_callback.assert_called_with(option, opt_str, expected_value, parser)


def test_store_callback():
    """Verify the default callback behaves like option with action='store'."""
    dest = 'foo'
    opt_str = '--foo'
    option = optparse.Option(opt_str, dest=dest)
    parser = mock.Mock(values=optparse.Values({'foo': 'defaultval'}))
    options.store_callback(option, opt_str, 'val', parser)
    assert parser.values.foo == 'val'


@pytest.fixture
def parser():
    """Provide a pycodestyle-esque OptionParser instance."""
    parser = optparse.OptionParser('flake8')
    parser.config_options = []
    return parser


def test_register_with_store_callback(parser):
    """Verify we handle typical no-custom-callback case (integration test)."""
    options.register(parser, '--foo', default=['path/file.py'], type='string',
                     comma_separated_list=True, normalize_paths=True)
    values, _ = parser.parse_args([])
    assert values.foo == ['path/file.py']  # default is used in its entirety
    values, _ = parser.parse_args(['--foo=file.py,path/file.py'])
    assert values.foo == ['file.py', os.path.abspath('path/file.py')]


def test_register_with_custom_callback(parser):
    """Verify we handle custom callback (integration test)."""
    def custom_callback(option, opt_str, value, parser, *args, **kwargs):
        parser.values.count = len(value)

    options.register(parser, '--foo', type='string', callback=custom_callback,
                     comma_separated_list=True, normalize_paths=True)
    values, _ = parser.parse_args(['--foo=file.py,path/file.py'])
    assert values.count == 2


def test_register_parse_from_config(parser):
    """Verify we append to config_options on registration."""
    options.register(parser, '--select', default='E123,W504',
                     parse_from_config=True)
    assert 'select' in parser.config_options
