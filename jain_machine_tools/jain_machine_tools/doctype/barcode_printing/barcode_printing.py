# Copyright (c) 2025, Praxon Technovation and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import base64
from io import BytesIO


class BarcodePrinting(Document):
	pass


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
			'module_height': 12.0,  # Height of barcode bars in mm
			'module_width': 0.25,   # Width of narrowest bar in mm
			'quiet_zone': 3.0,      # White space around barcode
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
def get_serial_numbers(record, item_code):
	"""
	Fetch serial numbers from Stock Entry Detail for the given item_code.

	Args:
		record: Stock Entry name
		item_code: Item code to filter

	Returns:
		List of serial numbers
	"""
	if not record or not item_code:
		frappe.throw("Please select a record and item code")

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
			bundle_entries = frappe.db.sql("""
				SELECT serial_no
				FROM `tabSerial and Batch Entry`
				WHERE parent = %(bundle)s
				AND serial_no IS NOT NULL
				AND serial_no != ''
				ORDER BY idx
			""", {
				'bundle': item.serial_and_batch_bundle
			}, as_dict=True)

			for entry in bundle_entries:
				serial_numbers.append({
					'item_code': item.item_code,
					'serial_no': entry.serial_no
				})

	return serial_numbers
