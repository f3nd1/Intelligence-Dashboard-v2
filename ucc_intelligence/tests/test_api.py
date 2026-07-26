import frappe
from frappe.tests.utils import FrappeTestCase

from ucc_intelligence.api import health_check


class TestHealthCheck(FrappeTestCase):
	def test_health_check_returns_ok(self):
		result = health_check()
		self.assertTrue(result["ok"])
		self.assertEqual(result["app"], "ucc_intelligence")
		self.assertEqual(result["user"], frappe.session.user)
