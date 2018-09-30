from unittest import TestCase

from rom.shared import is_int


class TestShared(TestCase):
    def test_is_int(self):
        self.assertTrue(is_int(5.6))
        self.assertFalse(is_int("Not an int"))
