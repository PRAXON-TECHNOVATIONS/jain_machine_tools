# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

# ─── Monkey Patch: Suppress India Compliance GST Mismatch Validation ──────────
from india_compliance.gst_india.overrides.transaction import ItemGSTDetails

_original_update = ItemGSTDetails.update

def _patched_update(self, doc):
	if doc.doctype in ("Purchase Receipt", "Purchase Invoice"):
		self.doc = doc
		if not self.doc.get("items"):
			return
		self.get_item_defaults()
		self.set_tax_amount_precisions(doc.doctype)
		if self.dont_recompute_tax_is_set():
			self.set_item_code_wise_tax_details()
			self.update_tax_details_by_item_code()
		else:
			self.set_item_name_wise_tax_details()
		# validate_item_gst_details() intentionally skipped for Purchase Receipt
		return

	_original_update(self, doc)

ItemGSTDetails.update = _patched_update
# ─────────────────────────────────────────────────────────────────────────────


class CustomPurchaseTaxesAndTotals(calculate_taxes_and_totals):
	"""
	Custom override to add handling charges calculation to Purchase Order Item
	"""

	def calculate_item_values(self):
		"""
		Override to add handling charges calculation after discount.
		Sequence: price_list_rate → margin → discount → handling_charges → rate

		Fix: ERPNext only recalculates item.rate from price_list_rate when item.rate
		is falsy (taxes_and_totals.py: `if not item.rate`). Pre-setting item.rate
		causes discounts to be silently skipped. Clear item.rate first so ERPNext
		always applies price_list_rate + discount correctly.
		"""
		for item in self.doc.get("items"):
			if item.price_list_rate:
				item.rate = 0

		super(CustomPurchaseTaxesAndTotals, self).calculate_item_values()

		for item in self.doc.get("items"):
			item.base_rate_before_handling_charges = flt(item.rate)

		for item in self.doc.get("items"):
			self.calculate_handling_charges(item)

	def calculate_handling_charges(self, item):
		"""
		Calculate handling charges and update item rate and amount

		Calculation flow:
		1. Get rate after discount (stored in base_rate_before_handling_charges)
		2. Calculate handling charges based on type (Percentage or Amount)
		3. Add handling charges to rate
		4. Recalculate amount = rate * qty
		"""
		# Get custom fields
		handling_charges_type = item.get("handling_charges_type")
		handling_charges_percentage = flt(item.get("handling_charges_percentage"))
		handling_charges_amount = flt(item.get("handling_charges_amount"))

		# Get the rate before handling charges (stored in persistent field)
		rate_before_handling = flt(item.get("base_rate_before_handling_charges") or item.rate)

		if rate_before_handling <= 0:
			return

		# Calculate handling charges value
		handling_value = 0

		# Only calculate if type is selected AND value is greater than 0
		if handling_charges_type == "Percentage" and handling_charges_percentage > 0:
			# Calculate as percentage of rate after discount
			handling_value = rate_before_handling * (handling_charges_percentage / 100.0)

		elif handling_charges_type == "Amount" and handling_charges_amount > 0:
			# Use fixed amount
			handling_value = handling_charges_amount

		item.handling_charges_value = flt(handling_value * item.qty, item.precision("handling_charges_value"))

		# Always recalculate from base rate (even if handling_value is 0)
		# This ensures removal of handling charges works correctly when set to 0
		item.rate = flt(rate_before_handling + handling_value, item.precision("rate"))

		# Recalculate amounts with updated rate
		item.net_rate = item.rate
		item.amount = flt(item.rate * item.qty, item.precision("amount"))
		item.net_amount = item.amount

		# Update base currency values
		item.base_rate = flt(item.rate * self.doc.conversion_rate, item.precision("base_rate"))
		item.base_net_rate = item.base_rate
		item.base_amount = flt(item.amount * self.doc.conversion_rate, item.precision("base_amount"))
		item.base_net_amount = item.base_amount

		# Update taxable_value for India Compliance GST calculation
		# This ensures GST is calculated on the rate WITH handling charges
		item.taxable_value = item.base_net_amount


def custom_calculate_taxes_and_totals(doc):
	"""
	Custom function to use our CustomPurchaseTaxesAndTotals class
	"""
	CustomPurchaseTaxesAndTotals(doc)


# Validation hooks
def validate_purchase_order(doc, method=None):
	"""
	Hook for Purchase Order validation
	Replaces standard taxes_and_totals calculation with custom one
	"""
	# Use custom calculation class
	custom_calculate_taxes_and_totals(doc)


def validate_purchase_invoice(doc, method=None):
	"""
	Hook for Purchase Invoice validation
	"""
	custom_calculate_taxes_and_totals(doc)
	validate_purchase_invoice_against_po(doc)


def validate_purchase_receipt(doc, method=None):
	"""
	Hook for Purchase Receipt validation
	"""
	custom_calculate_taxes_and_totals(doc)
	validate_purchase_receipt_against_po(doc)


def validate_purchase_invoice_against_po(doc):
	"""
	Allow Purchase Invoice qty/rate to be less than Purchase Order, but never more.
	Also ensures cumulative Purchase Invoice qty across multiple submitted invoices
	never exceeds the linked Purchase Order item qty.
	"""
	mismatches = []
	po_detail_names = list({row.po_detail for row in doc.get("items", []) if row.get("po_detail")})
	po_item_map = _get_po_item_map_with_billed_qty(po_detail_names, doc.name)
	current_invoice_qty_by_po_detail = {}

	for row in doc.get("items", []):
		if not row.get("po_detail"):
			continue

		po_item = po_item_map.get(row.po_detail)
		if not po_item:
			continue

		invoice_qty = _get_row_stock_qty(row)
		po_qty = flt(po_item.get("stock_qty") or po_item.get("qty"))
		invoice_rate = flt(row.get("rate"))
		po_rate = flt(po_item.get("rate"))
		item_code = _format_item_code(row)

		if invoice_qty - po_qty > 1e-9:
			mismatches.append(
				_("{0}: current qty {1}, remaining qty {2}").format(item_code, invoice_qty, po_qty)
			)

		if invoice_rate - po_rate > 1e-9:
			mismatches.append(
				_("{0}: current rate {1}, allowed rate {2}").format(item_code, invoice_rate, po_rate)
			)

		current_invoice_qty_by_po_detail.setdefault(
			row.po_detail,
			{"item_code": item_code, "current_qty": 0.0},
		)
		current_invoice_qty_by_po_detail[row.po_detail]["current_qty"] += invoice_qty

	for po_detail, qty_data in current_invoice_qty_by_po_detail.items():
		po_item = po_item_map.get(po_detail)
		if not po_item:
			continue

		po_qty = flt(po_item.get("stock_qty") or po_item.get("qty"))
		already_billed_qty = flt(po_item.get("already_billed_qty"))
		current_qty = flt(qty_data.get("current_qty"))
		remaining_qty = flt(po_qty - already_billed_qty)

		if current_qty - remaining_qty > 1e-9:
			mismatches.append(
				_("{0}: current qty {1}, remaining qty {2}").format(
					qty_data.get("item_code"),
					current_qty,
					max(remaining_qty, 0),
				)
			)

	if mismatches:
		frappe.throw(
			_(
				"PO limit exceeded.<br><br>{0}"
			).format("<br>".join(mismatches))
		)


def validate_purchase_receipt_against_po(doc):
	"""
	Allow Purchase Receipt rate to be less than or equal to Purchase Order rate,
	but never greater than the linked Purchase Order item rate.
	"""
	mismatches = []
	po_detail_names = list(
		{
			row.get("purchase_order_item") or row.get("po_detail")
			for row in doc.get("items", [])
			if row.get("purchase_order_item") or row.get("po_detail")
		}
	)
	po_item_map = _get_po_item_map_with_billed_qty(po_detail_names)

	for row in doc.get("items", []):
		po_detail = row.get("purchase_order_item") or row.get("po_detail")
		if not po_detail:
			continue

		po_item = po_item_map.get(po_detail)
		if not po_item:
			continue

		receipt_rate = flt(row.get("rate"))
		po_rate = flt(po_item.get("rate"))
		rate_precision = row.precision("rate") if hasattr(row, "precision") else 2

		if flt(receipt_rate - po_rate, rate_precision) > 0:
			mismatches.append(
				_(
					"Row #{0}: Item {1} has Purchase Receipt Rate = {2} and Purchase Order Rate = {3}. Purchase Receipt Rate cannot be greater than Purchase Order Rate."
				).format(
					row.idx,
					_format_item_code(row),
					frappe.format_value(receipt_rate, {"fieldtype": "Currency", "options": doc.currency}),
					frappe.format_value(po_rate, {"fieldtype": "Currency", "options": doc.currency}),
				)
			)

	if mismatches:
		frappe.throw(mismatches, title=_("Purchase Receipt Rate Validation"), as_list=True)


@frappe.whitelist()
def get_purchase_order_item_invoice_status(po_detail, purchase_invoice=None):
	po_item_map = _get_po_item_map_with_billed_qty([po_detail], purchase_invoice)
	po_item = po_item_map.get(po_detail)

	if not po_item:
		return {}

	po_qty = flt(po_item.get("stock_qty") or po_item.get("qty"))
	already_billed_qty = flt(po_item.get("already_billed_qty"))

	return {
		"po_detail": po_detail,
		"po_qty": po_qty,
		"already_billed_qty": already_billed_qty,
		"remaining_qty": flt(po_qty - already_billed_qty),
		"rate": flt(po_item.get("rate")),
		"purchase_order": po_item.get("parent"),
	}


def _get_po_item_map_with_billed_qty(po_detail_names, exclude_purchase_invoice=None):
	if not po_detail_names:
		return {}

	exclude_clause = ""
	params = {"po_detail_names": tuple(po_detail_names)}

	if exclude_purchase_invoice:
		exclude_clause = "and pii.parent != %(exclude_purchase_invoice)s"
		params["exclude_purchase_invoice"] = exclude_purchase_invoice

	rows = frappe.db.sql(
		f"""
		select
			poi.name,
			poi.parent,
			poi.qty,
			poi.stock_qty,
			poi.rate,
			coalesce(sum(
				case
					when pi.docstatus = 1 then coalesce(pii.stock_qty, pii.qty * coalesce(pii.conversion_factor, 1), pii.qty)
					else 0
				end
			), 0) as already_billed_qty
		from `tabPurchase Order Item` poi
		left join `tabPurchase Invoice Item` pii on pii.po_detail = poi.name
		left join `tabPurchase Invoice` pi on pi.name = pii.parent
		where poi.name in %(po_detail_names)s
			{exclude_clause}
		group by poi.name, poi.parent, poi.qty, poi.stock_qty, poi.rate
		""",
		params,
		as_dict=True,
	)

	return {row.name: row for row in rows}


def _get_row_stock_qty(row):
	return flt(row.get("stock_qty")) or flt(row.get("qty")) * flt(row.get("conversion_factor") or 1)


def _format_item_code(row):
	return row.get("item_code") or _("Row #{0}").format(row.get("idx"))


def on_cancel(doc, method):
	if not doc.items:
		return

	for row in doc.items:
		if row.serial_no:
			serial_list = row.serial_no.split("\n")
			for sn in serial_list:
				if frappe.db.exists("Serial No", sn):
					try:
						frappe.delete_doc("Serial No", sn, force=1)
					except Exception as e:
						frappe.log_error(f"Error deleting Serial No {sn}: {str(e)}")               