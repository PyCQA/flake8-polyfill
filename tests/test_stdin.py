"""Tests for polyfill's stdin monkey patching."""
import pep8
import pycodestyle

import pytest

from flake8_polyfill import stdin
from flake8_polyfill import version


def test_modules_dict():
    """Verify that it works the way we expect."""
    assert len(stdin.modules['pep8']) == 1
    assert stdin.modules['pep8'] == [pep8]
    assert len(stdin.modules['pycodestyle']) == 1
    assert stdin.modules['pycodestyle'] == [pycodestyle]
    assert len(stdin.modules['all']) == 2
    assert stdin.modules['all'] == [pep8, pycodestyle]


@pytest.fixture
def pep8_mod(request):
    """Fixture to replace pep8's default stdin_get_value."""
    original_stdin_get_value = pep8.stdin_get_value

    def replace():
        pep8.stdin_get_value = original_stdin_get_value

    request.addfinalizer(replace)
    return pep8


@pytest.fixture
def pycodestyle_mod(request):
    """Fixture to replace pycodestyle's default stdin_get_value."""
    original_stdin_get_value = pycodestyle.stdin_get_value

    def replace():
        pycodestyle.stdin_get_value = original_stdin_get_value

    request.addfinalizer(replace)
    return pycodestyle


# NOTE(sigmavirus24): These are weak tests but *shrug* I'm not sure of a
# better way to test these.
def test_monkey_patch_all(pep8_mod, pycodestyle_mod):
    """Verify we monkey patch everything."""
    stdin.monkey_patch('all')
    assert pep8_mod.stdin_get_value is pycodestyle_mod.stdin_get_value


@pytest.mark.skipif(
    (2, 5) < version.version_info < (2, 7),
    reason='They are the same on everything less than 2.6.'
)
def test_monkey_patch_pep8(pep8_mod):
    """Verify we monkey patch pep8 only."""
    stdin.monkey_patch('pep8')
    assert pep8_mod.stdin_get_value is not pycodestyle.stdin_get_value


@pytest.mark.skipif(
    version.version_info < (2, 6),
    reason='They are the same on everything less than 2.6.'
)
def test_monkey_patch_pycodestyle(pycodestyle_mod):
    """Verify we monkey patch pycodestyle only."""
    stdin.monkey_patch('pycodestyle')
    assert pep8.stdin_get_value is not pycodestyle_mod.stdin_get_value


@pytest.mark.skipif(
    version.version_info < (3, 0) or version.version_info > (4, 0),
    reason='Requires Flake8 3.x'
)
def test_uses_flake8_util_stdin(pep8_mod, pycodestyle_mod):
    """Verify we monkey-patch using internal flake8 functions."""
    import flake8.utils

    stdin.monkey_patch('all')
    assert pep8_mod.stdin_get_value is flake8.utils.stdin_get_value
    assert pycodestyle_mod.stdin_get_value is flake8.utils.stdin_get_value
