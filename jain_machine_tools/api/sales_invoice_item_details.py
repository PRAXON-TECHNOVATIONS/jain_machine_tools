import json

import frappe
from erpnext.stock.get_item_details import get_item_details as erpnext_get_item_details


@frappe.whitelist()
def get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
	"""
	Keep ERPNext item detail resolution intact, but do not auto-pick FIFO serial numbers
	for Sales Invoice rows. Serial numbers there must come only from manual/barcode entry.
	"""
	result = erpnext_get_item_details(
		args,
		doc=doc,
		for_validate=for_validate,
		overwrite_warehouse=overwrite_warehouse,
	)

	parsed_args = json.loads(args) if isinstance(args, str) else (args or {})
	if parsed_args.get("doctype") == "Sales Invoice" and not parsed_args.get("serial_no"):
		result["serial_no"] = ""

	return result
