import frappe
from frappe import _
from frappe.utils import flt

from erpnext.utilities.transaction_base import TransactionBase


_original_validate_rate_with_reference_doc = TransactionBase.validate_rate_with_reference_doc


def _patched_validate_rate_with_reference_doc(self, ref_details):
	"""
	Allow lower or equal rates on Purchase Receipt / Purchase Invoice / Sales Invoice
	against their source docs.
	Only block when the current rate is greater than the reference rate.
	"""
	if self.doctype not in ("Purchase Receipt", "Purchase Invoice", "Sales Invoice"):
		return _original_validate_rate_with_reference_doc(self, ref_details)

	stop_actions = []
	for ref_dt, ref_dn_field, ref_link_field in ref_details:
		reference_names = [d.get(ref_link_field) for d in self.get("items") if d.get(ref_link_field)]
		reference_details = self.get_reference_details(reference_names, ref_dt + " Item")

		for d in self.get("items"):
			if not d.get(ref_link_field):
				continue

			ref_rate = flt(reference_details.get(d.get(ref_link_field)))
			current_rate = flt(d.rate)

			if current_rate - ref_rate >= 0.01:
				stop_actions.append(
					_(
						"Row #{0}: Entered Rate cannot be greater than {1} rate for {2}. Entered Rate = {3}, PO Reference Rate = {4}"
					).format(d.idx, ref_dt, d.get(ref_dn_field), current_rate, ref_rate)
				)

	if stop_actions:
		frappe.throw(stop_actions, as_list=True)


TransactionBase.validate_rate_with_reference_doc = _patched_validate_rate_with_reference_doc
