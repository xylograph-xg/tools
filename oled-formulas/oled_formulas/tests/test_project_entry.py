"""Keep the installed panel and existing owner wired to the same implementation."""
import unittest

from browser.api import formula_only__enabled, formula_only__run
from browser.formula_only import control_pilot
from oled_formulas import api


class ProjectEntry(unittest.TestCase):
    def test_legacy_owner_and_control_resolve_to_project(self):
        self.assertIs(formula_only__enabled, api.enabled)
        self.assertIs(formula_only__run, api.run)
        self.assertIs(control_pilot, api.control_pilot)
        self.assertEqual(api.run.__module__, 'oled_formulas.formula_only')
