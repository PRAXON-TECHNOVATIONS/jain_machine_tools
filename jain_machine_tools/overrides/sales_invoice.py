import frappe
from frappe import _
from frappe.utils import flt

from jain_machine_tools.overrides.quotation import custom_calculate_taxes_and_totals


def validate_sales_invoice(doc, method=None):
	"""
	Hook for Sales Invoice validation.
	"""
	custom_calculate_taxes_and_totals(doc)
	validate_sales_invoice_order_qty(doc)


def validate_sales_invoice_order_qty(doc):
	"""
	Ensure Sales Invoice item qty exactly matches linked Sales Order item qty.
	"""
	for row in doc.get("items", []):
		if not row.get("so_detail"):
			continue

		so_item = frappe.db.get_value(
			"Sales Order Item",
			row.so_detail,
			["parent", "qty", "stock_qty"],
			as_dict=True,
		)

		if not so_item:
			continue

		# Prefer stock_qty to avoid UOM mismatch between SO and SI rows.
		invoice_qty = flt(row.get("stock_qty") or row.get("qty"))
		so_qty = flt(so_item.get("stock_qty") or so_item.get("qty"))

		if abs(invoice_qty - so_qty) > 1e-9:
			frappe.throw(
				_(
					"Row #{0}: Qty must be exactly same as Sales Order Qty. "
					"SO: {1}, Item: {2}, SO Qty: {3}, Invoice Qty: {4}"
				).format(
					row.idx,
					so_item.parent,
					row.item_code,
					so_qty,
					invoice_qty,
				)
			)
