import frappe


def on_update(doc, method):
	"""
	Hook triggered when Serial No is updated.
	Updates Purchase Receipt Item and Stock Entry Detail barcode_status when barcode_generated checkbox changes.
	"""
	# Check if barcode_generated field has changed
	if doc.has_value_changed('barcode_generated'):
		update_purchase_receipt_barcode_status(doc.name)
		update_stock_entry_barcode_status(doc.name)


def update_purchase_receipt_barcode_status(serial_no):
	"""
	Find all Purchase Receipts containing this serial number and update their barcode status.

	Args:
		serial_no: Serial No name
	"""
	# Find which Purchase Receipt(s) contain this serial number
	purchase_receipts = frappe.db.sql("""
		SELECT DISTINCT
			pri.parent as purchase_receipt,
			pri.item_code
		FROM `tabPurchase Receipt Item` pri
		INNER JOIN `tabSerial and Batch Entry` sbe ON sbe.parent = pri.serial_and_batch_bundle
		WHERE sbe.serial_no = %(serial_no)s
		AND pri.docstatus < 2
	""", {
		'serial_no': serial_no
	}, as_dict=True)

	# Update barcode status for each Purchase Receipt + item combination
	for pr in purchase_receipts:
		from jain_machine_tools.jain_machine_tools.doctype.barcode_printing.barcode_printing import update_barcode_status_purchase_receipt
		update_barcode_status_purchase_receipt(pr.purchase_receipt, pr.item_code)


def update_stock_entry_barcode_status(serial_no):
	"""
	Find all Stock Entries containing this serial number and update their barcode status.

	Args:
		serial_no: Serial No name
	"""
	# Find which Stock Entry(s) contain this serial number
	stock_entries = frappe.db.sql("""
		SELECT DISTINCT
			sed.parent as stock_entry,
			sed.item_code
		FROM `tabStock Entry Detail` sed
		INNER JOIN `tabSerial and Batch Entry` sbe ON sbe.parent = sed.serial_and_batch_bundle
		WHERE sbe.serial_no = %(serial_no)s
		AND sed.t_warehouse IS NOT NULL
		AND sed.t_warehouse != ''
		AND sed.docstatus < 2
	""", {
		'serial_no': serial_no
	}, as_dict=True)

	# Update barcode status for each Stock Entry + item combination
	for se in stock_entries:
		from jain_machine_tools.jain_machine_tools.doctype.barcode_printing.barcode_printing import update_barcode_status_stock_entry
		update_barcode_status_stock_entry(se.stock_entry, se.item_code)
