from __future__ import annotations

import frappe

from jain_machine_tools.utils.serial_normalization import (
	normalize_serial_no,
	normalize_serial_no_list,
	normalize_serial_no_multiline,
)


def normalize_serial_doc(doc, method=None):
	normalized_name = normalize_serial_no(doc.name)
	if doc.is_new() and normalized_name:
		doc.name = normalized_name

	if doc.get("serial_no"):
		doc.serial_no = normalized_name or normalize_serial_no(doc.serial_no)


def normalize_item_serial_fields(doc, method=None):
	for row in doc.get("items", []):
		if row.get("serial_no"):
			row.serial_no = normalize_serial_no_multiline(row.serial_no)


def validate_purchase_receipt_serial_conflicts(doc, method=None):
	for row in doc.get("items", []):
		for serial_no in normalize_serial_no_list(row.get("serial_no")):
			existing_item_code = frappe.db.get_value("Serial No", serial_no, "item_code")
			if existing_item_code:
				frappe.throw(
					f"Serial No {serial_no} already exists in system for Item {existing_item_code}."
				)
