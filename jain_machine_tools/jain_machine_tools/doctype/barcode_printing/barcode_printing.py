# Copyright (c) 2025, Praxon Technovation and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import base64
from io import BytesIO


class BarcodePrinting(Document):
	def on_submit(self):
		"""Update barcode status and mark serial numbers as generated when submitted"""
		# Mark all serial numbers in this barcode printing as barcode_generated
		mark_serial_numbers_as_generated(self.name, checked=True)

		# Update barcode status in Purchase Receipt Item or Stock Entry Detail
		if self.type == "Purchase Receipt":
			update_barcode_status_purchase_receipt(self.record, self.item_code)
		elif self.type == "Stock Entry":
			update_barcode_status_stock_entry(self.record, self.item_code)

	def on_cancel(self):
		"""Unmark serial numbers when barcode printing is cancelled"""
		# Unmark all serial numbers in this barcode printing
		mark_serial_numbers_as_generated(self.name, checked=False)

		# Update barcode status in Purchase Receipt Item or Stock Entry Detail
		if self.type == "Purchase Receipt":
			update_barcode_status_purchase_receipt(self.record, self.item_code)
		elif self.type == "Stock Entry":
			update_barcode_status_stock_entry(self.record, self.item_code)


def get_barcode_image(serial_no, barcode_type="Code128"):
	"""
	Generate barcode image as base64 data URI.

	Args:
		serial_no: Serial number to encode
		barcode_type: Type of barcode (default: Code128)

	Returns:
		Base64 encoded image data URI
	"""
	try:
		import barcode
		from barcode.writer import ImageWriter

		# Get barcode class
		barcode_class = barcode.get_barcode_class(barcode_type)

		# Create barcode with image writer and better options
		barcode_instance = barcode_class(str(serial_no), writer=ImageWriter())

		# Generate barcode to BytesIO buffer with optimized settings
		buffer = BytesIO()
		barcode_instance.write(buffer, options={
			'module_height': 10.0,  # Height of barcode bars in mm (reduced for 10 per page)
			'module_width': 0.20,   # Width of narrowest bar in mm (slightly reduced)
			'quiet_zone': 2.5,      # White space around barcode (reduced)
			'font_size': 0,         # Don't render text below barcode (we'll show it separately)
			'text_distance': 1.0,
			'background': 'white',
			'foreground': 'black',
			'write_text': False,    # Disable text rendering in barcode
			'dpi': 300,             # High DPI for better quality
		})

		# Get image data and encode as base64
		buffer.seek(0)
		image_data = base64.b64encode(buffer.read()).decode('utf-8')

		return f"data:image/png;base64,{image_data}"

	except Exception as e:
		frappe.log_error(f"Error generating barcode: {str(e)}", "Barcode Generation Error")
		return ""


@frappe.whitelist()
def get_serial_numbers(record, item_code, doctype_name=None):
	"""
	Fetch serial numbers from Stock Entry Detail or Purchase Receipt Item for the given item_code.

	Args:
		record: Stock Entry or Purchase Receipt name
		item_code: Item code to filter
		doctype_name: Type of document (Stock Entry or Purchase Receipt)

	Returns:
		List of serial numbers
	"""
	if not record or not item_code:
		frappe.throw("Please select a record and item code")

	# Determine doctype if not provided
	if not doctype_name:
		# Try to detect doctype from record name pattern or query
		doc = frappe.get_doc("Barcode Printing", {"record": record})
		doctype_name = doc.type if doc else "Stock Entry"

	if doctype_name == "Stock Entry":
		return get_serial_numbers_from_stock_entry(record, item_code)
	elif doctype_name == "Purchase Receipt":
		return get_serial_numbers_from_purchase_receipt(record, item_code)
	else:
		frappe.throw(f"Unsupported document type: {doctype_name}")


def get_serial_numbers_from_stock_entry(record, item_code):
	"""
	Fetch serial numbers from Stock Entry Detail for the given item_code.
	Excludes serial numbers that already have barcode_generated = 1.

	Args:
		record: Stock Entry name
		item_code: Item code to filter

	Returns:
		List of serial numbers
	"""
	# Get Stock Entry Detail items with serial numbers
	items = frappe.db.sql("""
		SELECT
			sed.item_code,
			sed.serial_and_batch_bundle,
			sed.t_warehouse
		FROM `tabStock Entry Detail` sed
		WHERE
			sed.parent = %(record)s
			AND sed.item_code = %(item_code)s
			AND sed.t_warehouse IS NOT NULL
			AND sed.t_warehouse != ''
	""", {
		'record': record,
		'item_code': item_code
	}, as_dict=True)

	if not items:
		frappe.throw(f"No items found with target warehouse for Item: {item_code} in {record}")

	serial_numbers = []

	# Get serial numbers from serial_and_batch_bundle
	for item in items:
		if item.serial_and_batch_bundle:
			# Get serial numbers from Serial and Batch Bundle
			# Exclude serial numbers that already have barcode_generated = 1
			bundle_entries = frappe.db.sql("""
				SELECT sbe.serial_no
				FROM `tabSerial and Batch Entry` sbe
				INNER JOIN `tabSerial No` sn ON sn.name = sbe.serial_no
				WHERE sbe.parent = %(bundle)s
				AND sbe.serial_no IS NOT NULL
				AND sbe.serial_no != ''
				AND (sn.barcode_generated IS NULL OR sn.barcode_generated = 0)
				ORDER BY sbe.idx
			""", {
				'bundle': item.serial_and_batch_bundle
			}, as_dict=True)

			for entry in bundle_entries:
				serial_numbers.append({
					'item_code': item.item_code,
					'serial_no': entry.serial_no
				})

	return serial_numbers


def get_serial_numbers_from_purchase_receipt(record, item_code):
	"""
	Fetch serial numbers from Purchase Receipt Item for the given item_code.
	Excludes serial numbers that already have barcode_generated = 1.

	Args:
		record: Purchase Receipt name
		item_code: Item code to filter

	Returns:
		List of serial numbers
	"""
	# Get Purchase Receipt Item with serial numbers
	items = frappe.db.sql("""
		SELECT
			pri.item_code,
			pri.serial_and_batch_bundle
		FROM `tabPurchase Receipt Item` pri
		WHERE
			pri.parent = %(record)s
			AND pri.item_code = %(item_code)s
			AND pri.serial_and_batch_bundle IS NOT NULL
			AND pri.serial_and_batch_bundle != ''
	""", {
		'record': record,
		'item_code': item_code
	}, as_dict=True)

	if not items:
		frappe.throw(f"No items found with serial numbers for Item: {item_code} in {record}")

	serial_numbers = []

	# Get serial numbers from serial_and_batch_bundle
	for item in items:
		if item.serial_and_batch_bundle:
			# Get serial numbers from Serial and Batch Bundle
			# Exclude serial numbers that already have barcode_generated = 1
			bundle_entries = frappe.db.sql("""
				SELECT sbe.serial_no
				FROM `tabSerial and Batch Entry` sbe
				INNER JOIN `tabSerial No` sn ON sn.name = sbe.serial_no
				WHERE sbe.parent = %(bundle)s
				AND sbe.serial_no IS NOT NULL
				AND sbe.serial_no != ''
				AND (sn.barcode_generated IS NULL OR sn.barcode_generated = 0)
				ORDER BY sbe.idx
			""", {
				'bundle': item.serial_and_batch_bundle
			}, as_dict=True)

			for entry in bundle_entries:
				serial_numbers.append({
					'item_code': item.item_code,
					'serial_no': entry.serial_no
				})

	return serial_numbers


def update_barcode_status_purchase_receipt(purchase_receipt, item_code):
	"""
	Update barcode status for a specific item in Purchase Receipt.
	Checks all submitted Barcode Printing records and determines if status should be:
	- Pending: No barcode printing records
	- Partial: Some serial numbers have barcodes printed
	- Completed: All serial numbers have barcodes printed

	Args:
		purchase_receipt: Purchase Receipt name
		item_code: Item code to update status for
	"""
	# Get all serial numbers for this item in the Purchase Receipt
	pr_serial_numbers = get_all_serial_numbers_for_item_pr(purchase_receipt, item_code)

	if not pr_serial_numbers:
		return

	# Get all serial numbers that have been printed (from all submitted Barcode Printing records)
	printed_serial_numbers = get_printed_serial_numbers_pr(purchase_receipt, item_code)

	# Determine status
	if not printed_serial_numbers:
		status = "Pending"
	elif len(printed_serial_numbers) >= len(pr_serial_numbers):
		status = "Completed"
	else:
		status = "Partial"

	# Update the barcode_status in Purchase Receipt Item
	frappe.db.sql("""
		UPDATE `tabPurchase Receipt Item`
		SET barcode_status = %(status)s
		WHERE parent = %(purchase_receipt)s
		AND item_code = %(item_code)s
	""", {
		'status': status,
		'purchase_receipt': purchase_receipt,
		'item_code': item_code
	})

	frappe.db.commit()


def update_barcode_status_stock_entry(stock_entry, item_code):
	"""
	Update barcode status for a specific item in Stock Entry Detail.
	Checks all submitted Barcode Printing records and determines if status should be:
	- Pending: No barcode printing records
	- Partial: Some serial numbers have barcodes printed
	- Completed: All serial numbers have barcodes printed

	Args:
		stock_entry: Stock Entry name
		item_code: Item code to update status for
	"""
	# Get all serial numbers for this item in the Stock Entry
	se_serial_numbers = get_all_serial_numbers_for_item_se(stock_entry, item_code)

	if not se_serial_numbers:
		return

	# Get all serial numbers that have been printed (from all submitted Barcode Printing records)
	printed_serial_numbers = get_printed_serial_numbers_se(stock_entry, item_code)

	# Determine status
	if not printed_serial_numbers:
		status = "Pending"
	elif len(printed_serial_numbers) >= len(se_serial_numbers):
		status = "Completed"
	else:
		status = "Partial"

	# Update the barcode_status in Stock Entry Detail
	frappe.db.sql("""
		UPDATE `tabStock Entry Detail`
		SET barcode_status = %(status)s
		WHERE parent = %(stock_entry)s
		AND item_code = %(item_code)s
		AND t_warehouse IS NOT NULL
		AND t_warehouse != ''
	""", {
		'status': status,
		'stock_entry': stock_entry,
		'item_code': item_code
	})

	frappe.db.commit()


def get_all_serial_numbers_for_item_pr(purchase_receipt, item_code):
	"""
	Get all serial numbers for a specific item in Purchase Receipt.

	Args:
		purchase_receipt: Purchase Receipt name
		item_code: Item code

	Returns:
		Set of serial numbers
	"""
	items = frappe.db.sql("""
		SELECT pri.serial_and_batch_bundle
		FROM `tabPurchase Receipt Item` pri
		WHERE pri.parent = %(purchase_receipt)s
		AND pri.item_code = %(item_code)s
		AND pri.serial_and_batch_bundle IS NOT NULL
		AND pri.serial_and_batch_bundle != ''
	""", {
		'purchase_receipt': purchase_receipt,
		'item_code': item_code
	}, as_dict=True)

	serial_numbers = set()

	for item in items:
		if item.serial_and_batch_bundle:
			bundle_entries = frappe.db.sql("""
				SELECT serial_no
				FROM `tabSerial and Batch Entry`
				WHERE parent = %(bundle)s
				AND serial_no IS NOT NULL
				AND serial_no != ''
			""", {
				'bundle': item.serial_and_batch_bundle
			}, as_dict=True)

			for entry in bundle_entries:
				serial_numbers.add(entry.serial_no)

	return serial_numbers


def get_all_serial_numbers_for_item_se(stock_entry, item_code):
	"""
	Get all serial numbers for a specific item in Stock Entry Detail.

	Args:
		stock_entry: Stock Entry name
		item_code: Item code

	Returns:
		Set of serial numbers
	"""
	items = frappe.db.sql("""
		SELECT sed.serial_and_batch_bundle
		FROM `tabStock Entry Detail` sed
		WHERE sed.parent = %(stock_entry)s
		AND sed.item_code = %(item_code)s
		AND sed.t_warehouse IS NOT NULL
		AND sed.t_warehouse != ''
		AND sed.serial_and_batch_bundle IS NOT NULL
		AND sed.serial_and_batch_bundle != ''
	""", {
		'stock_entry': stock_entry,
		'item_code': item_code
	}, as_dict=True)

	serial_numbers = set()

	for item in items:
		if item.serial_and_batch_bundle:
			bundle_entries = frappe.db.sql("""
				SELECT serial_no
				FROM `tabSerial and Batch Entry`
				WHERE parent = %(bundle)s
				AND serial_no IS NOT NULL
				AND serial_no != ''
			""", {
				'bundle': item.serial_and_batch_bundle
			}, as_dict=True)

			for entry in bundle_entries:
				serial_numbers.add(entry.serial_no)

	return serial_numbers


def get_printed_serial_numbers_pr(purchase_receipt, item_code):
	"""
	Get all serial numbers that have barcode_generated=1 for a specific item in Purchase Receipt.
	Checks the actual barcode_generated field on Serial No instead of barcode printing records.

	Args:
		purchase_receipt: Purchase Receipt name
		item_code: Item code

	Returns:
		Set of serial numbers that have barcode_generated=1
	"""
	# Get all serial numbers for this item in Purchase Receipt that have barcode_generated=1
	serial_numbers = frappe.db.sql("""
		SELECT DISTINCT sbe.serial_no
		FROM `tabPurchase Receipt Item` pri
		INNER JOIN `tabSerial and Batch Entry` sbe ON sbe.parent = pri.serial_and_batch_bundle
		INNER JOIN `tabSerial No` sn ON sn.name = sbe.serial_no
		WHERE pri.parent = %(purchase_receipt)s
		AND pri.item_code = %(item_code)s
		AND pri.serial_and_batch_bundle IS NOT NULL
		AND pri.serial_and_batch_bundle != ''
		AND sbe.serial_no IS NOT NULL
		AND sbe.serial_no != ''
		AND sn.barcode_generated = 1
	""", {
		'purchase_receipt': purchase_receipt,
		'item_code': item_code
	}, as_dict=True)

	printed_serial_numbers = set()
	for entry in serial_numbers:
		printed_serial_numbers.add(entry.serial_no)

	return printed_serial_numbers


def mark_serial_numbers_as_generated(barcode_printing_name, checked=True):
	"""
	Mark or unmark serial numbers as barcode_generated and update vendor warranty dates.

	Args:
		barcode_printing_name: Barcode Printing document name
		checked: True to mark as generated, False to unmark
	"""
	# Get all serial numbers from the Barcode Printing Table with warranty dates
	serial_entries = frappe.db.sql("""
		SELECT serial_no, vendor_manufacturing_date, warranty_expiry_date
		FROM `tabBarcode Printing Table`
		WHERE parent = %(parent)s
		AND serial_no IS NOT NULL
		AND serial_no != ''
	""", {
		'parent': barcode_printing_name
	}, as_dict=True)

	# Update each serial number
	for entry in serial_entries:
		if checked:
			# When marking as generated, update barcode_generated flag and vendor warranty dates
			frappe.db.set_value('Serial No', entry.serial_no, {
				'barcode_generated': 1,
				'vendor_manufacturing_date': entry.vendor_manufacturing_date,
				'vendor_warranty_expiry_date': entry.warranty_expiry_date
			}, update_modified=False)
		else:
			# When unmarking (on cancel), only unset the barcode_generated flag
			# Keep the warranty dates as they were set
			frappe.db.set_value('Serial No', entry.serial_no, 'barcode_generated', 0, update_modified=False)

	frappe.db.commit()


def get_printed_serial_numbers_se(stock_entry, item_code):
	"""
	Get all serial numbers that have barcode_generated=1 for a specific item in Stock Entry.
	Checks the actual barcode_generated field on Serial No instead of barcode printing records.

	Args:
		stock_entry: Stock Entry name
		item_code: Item code

	Returns:
		Set of serial numbers that have barcode_generated=1
	"""
	# Get all serial numbers for this item in Stock Entry that have barcode_generated=1
	serial_numbers = frappe.db.sql("""
		SELECT DISTINCT sbe.serial_no
		FROM `tabStock Entry Detail` sed
		INNER JOIN `tabSerial and Batch Entry` sbe ON sbe.parent = sed.serial_and_batch_bundle
		INNER JOIN `tabSerial No` sn ON sn.name = sbe.serial_no
		WHERE sed.parent = %(stock_entry)s
		AND sed.item_code = %(item_code)s
		AND sed.t_warehouse IS NOT NULL
		AND sed.t_warehouse != ''
		AND sed.serial_and_batch_bundle IS NOT NULL
		AND sed.serial_and_batch_bundle != ''
		AND sbe.serial_no IS NOT NULL
		AND sbe.serial_no != ''
		AND sn.barcode_generated = 1
	""", {
		'stock_entry': stock_entry,
		'item_code': item_code
	}, as_dict=True)

	printed_serial_numbers = set()
	for entry in serial_numbers:
		printed_serial_numbers.add(entry.serial_no)

	return printed_serial_numbers
