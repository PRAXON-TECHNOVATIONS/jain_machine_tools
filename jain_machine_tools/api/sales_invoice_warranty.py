# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, add_months, add_years, getdate


def update_serial_warranty_on_submit(doc, method=None):
	"""
	Hook triggered when Sales Invoice is submitted.
	Updates warranty_expiry_date for all serial numbers in THIS Sales Invoice only,
	based on item warranty configuration.

	Args:
		doc: Sales Invoice document
		method: Hook method (on_submit)
	"""
	# Only process if Sales Invoice updates stock
	if not doc.update_stock:
		return

	if not doc.items:
		return

	for item in doc.items:
		# Skip if item doesn't have serial and batch bundle
		# This ensures we only update serial numbers that are in THIS Sales Invoice
		if not item.serial_and_batch_bundle:
			continue

		# Get item warranty configuration
		item_doc = frappe.get_cached_doc("Item", item.item_code)

		# Skip if item doesn't have serial_no enabled or warranty fields not configured
		if not item_doc.has_serial_no:
			continue

		# All warranty fields must be configured
		if not item_doc.warranty_start_from or not item_doc.company_warranty_period or not item_doc.warranty_uom:
			continue

		# Only process if warranty starts from Sales Invoice Posting Date
		if item_doc.warranty_start_from != "Sales Invoice Posting Date":
			continue

		# Calculate warranty expiry date
		warranty_expiry = calculate_warranty_expiry_date(
			doc.posting_date,
			item_doc.warranty_start_from,
			item_doc.company_warranty_period,
			item_doc.warranty_uom
		)

		if not warranty_expiry:
			continue

		# Get all serial numbers from THIS item's bundle
		# This ensures we only update serial numbers sold in THIS Sales Invoice
		serial_numbers = get_serial_numbers_from_bundle(item.serial_and_batch_bundle)

		# Update warranty expiry date for each serial number in this Sales Invoice
		for serial_no in serial_numbers:
			update_serial_warranty_date(serial_no, warranty_expiry)


def calculate_warranty_expiry_date(posting_date, warranty_start_from, warranty_period, warranty_uom):
	"""
	Calculate warranty expiry date based on warranty configuration.

	Args:
		posting_date: Sales Invoice posting date
		warranty_start_from: "Sales Invoice Posting Date" or "Delivery Note Posting Date"
		warranty_period: Number of warranty periods (int)
		warranty_uom: "Days", "Months", or "Years"

	Returns:
		Date: Calculated warranty expiry date
	"""
	if warranty_start_from != "Sales Invoice Posting Date":
		# Currently only supporting Sales Invoice Posting Date
		# Delivery Note Posting Date can be added later if needed
		return None

	start_date = getdate(posting_date)

	if warranty_uom == "Days":
		expiry_date = add_days(start_date, warranty_period)
	elif warranty_uom == "Months":
		expiry_date = add_months(start_date, warranty_period)
	elif warranty_uom == "Years":
		expiry_date = add_years(start_date, warranty_period)
	else:
		frappe.log_error(
			f"Invalid warranty UOM: {warranty_uom}",
			"Warranty Calculation Error"
		)
		return None

	return expiry_date


def get_serial_numbers_from_bundle(bundle_name):
	"""
	Get all serial numbers from a Serial and Batch Bundle.

	Args:
		bundle_name: Name of the Serial and Batch Bundle

	Returns:
		List: List of serial number names
	"""
	serial_numbers = frappe.db.sql("""
		SELECT serial_no
		FROM `tabSerial and Batch Entry`
		WHERE parent = %(bundle)s
			AND serial_no IS NOT NULL
			AND serial_no != ''
		ORDER BY idx
	""", {'bundle': bundle_name}, as_dict=True)

	return [entry.serial_no for entry in serial_numbers]


def update_serial_warranty_date(serial_no, warranty_expiry_date):
	"""
	Update warranty_expiry_date for a serial number.
	Uses the standard ERPNext warranty_expiry_date field.

	Args:
		serial_no: Serial number name
		warranty_expiry_date: Date to set as warranty expiry
	"""
	try:
		# Update the standard warranty_expiry_date field
		frappe.db.set_value(
			"Serial No",
			serial_no,
			"warranty_expiry_date",
			warranty_expiry_date,
			update_modified=False
		)

		frappe.logger().info(
			f"Updated warranty expiry date for Serial No {serial_no} to {warranty_expiry_date}"
		)
	except Exception as e:
		frappe.log_error(
			f"Failed to update warranty for Serial No {serial_no}: {str(e)}",
			"Serial Warranty Update Error"
		)
