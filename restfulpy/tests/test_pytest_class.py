import pytest


# TODO: This line should be uncommented when the TestCase class is moved into
# the testing sub-package
#from restfulpy.testing import TestCase

#
#@pytest.fixture()
#def setup_teardown():
#
#
#@pytest.mark.usefixtures(setup_teardown)


class TestCase:
    pass


class TestFoo(TestCase):
    _setup_call_count = 0
    _teardown_call_count = 0

    @classmethod
    def setup_class(cls):
        cls._setup_call_count += 1

    @classmethod
    def teardown_class(cls):
        cls._teardown_call_count += 1

    def test_setup_teardown_first(self):
        assert self._setup_call_count == 1
        assert self._teardown_call_count == 0

    @pytest.mark.last
    def test_setup_teardown_second(self):
        """ The reason of this test case is to ensure the setup and teardown
        methods was called exactly once
        """
        assert self._setup_call_count == 1
        assert self._teardown_call_count == 0


def test_last():
    assert TestFoo._teardown_call_count == 1

