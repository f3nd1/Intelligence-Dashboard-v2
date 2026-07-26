from frappe.tests.utils import FrappeTestCase

from ucc_intelligence.api import get_dashboard_access

# Full rule coverage (union/default/fail-open/role-leak regression, 20
# scenarios) lives in tools/test_ucc_intelligence_access.py, runnable without
# a bench. This is a real-DB smoke test: it proves get_dashboard_access()
# runs against an actual Frappe session and returns the documented shape.


class TestDashboardAccess(FrappeTestCase):
	def test_returns_documented_shape_for_current_user(self):
		result = get_dashboard_access()
		self.assertTrue(result["ok"])
		self.assertIn("workspaces", result)
		self.assertIn("criteria", result)
		for criterion in ("criterion_1", "criterion_2", "criterion_3", "criterion_4",
		                  "criterion_5", "criterion_6", "criterion_7"):
			self.assertIn(criterion, result["criteria"])
		for workspace in ("analytics", "explore", "ask"):
			self.assertIn(workspace, result["workspaces"])
