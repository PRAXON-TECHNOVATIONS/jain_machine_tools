from collections import defaultdict

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
	validate_delivery_planning_schedule(doc)


def validate_sales_invoice_order_qty(doc):
	"""
	Ensure Sales Invoice item rate does not exceed the linked Sales Order item values.
	(Quantity validation against SO is removed as per new requirements)
	"""
	mismatches = []

	for row in doc.get("items", []):
		if not row.get("so_detail"):
			continue

		so_item = frappe.db.get_value(
			"Sales Order Item",
			row.so_detail,
			["parent", "rate"],
			as_dict=True,
		)

		if not so_item:
			continue

		invoice_rate = flt(row.get("rate"))
		so_rate = flt(so_item.get("rate"))
		item_label = _format_item_label(row)

		if invoice_rate - so_rate >= 0.01:
			mismatches.append(
				_(
					"- {0}: Sales Order Rate = {1}, Sales Invoice Rate = {2}"
				).format(item_label, so_rate, invoice_rate)
			)

	if mismatches:
		frappe.throw(
			_(
				"Sales Invoice cannot have Rate greater than the linked Sales Order.\n\n"
				"Please check these items:\n{0}\n\n"
				"Rule: Sales Invoice Rate may be less than Sales Order, but never more."
			).format("\n".join(mismatches))
		)


def update_delivery_planning_schedule_status(doc, method=None):
	"""
	Update the status of linked Delivery Planning Schedule and its items.
	Triggered on on_submit and on_cancel of Sales Invoice.
	"""
	if not doc.get("delivery_plan_details"):
		return

	dps_names = set()
	for row in doc.delivery_plan_details:
		if row.delivery_planning_schedule:
			dps_names.add(row.delivery_planning_schedule)

	for dps_name in dps_names:
		dps = frappe.get_doc("Delivery Planning Schedule", dps_name)
		_update_dps_status(dps)


def _update_dps_status(dps):
	"""
	Calculate and update status for DPS and its items.
	"""
	# Get already invoiced quantities for this DPS
	invoiced_qty_map = _get_total_invoiced_qty_for_dps(dps.name)

	all_completed = True
	any_completed = False
	any_partial = False

	for item in dps.get("items"):
		invoiced_qty = flt(invoiced_qty_map.get(item.name, 0))
		planned_qty = flt(item.planned_qty)

		if invoiced_qty >= planned_qty - 1e-9:
			item.status = "Completed"
			any_completed = True
		else:
			item.status = "Pending"
			all_completed = False
			if invoiced_qty > 1e-9:
				any_partial = True

		item.db_set("status", item.status, update_modified=False)

	if all_completed:
		overall_status = "Completed"
	elif any_completed or any_partial:
		overall_status = "Partial"
	else:
		overall_status = "Pending"

	dps.db_set("status", overall_status, update_modified=False)


def _get_total_invoiced_qty_for_dps(dps_name):
	"""
	Helper to get total invoiced quantity across all submitted SIs for a DPS.
	"""
	result = frappe.db.sql(
		"""
		SELECT
			sii.delivery_planning_schedule_item,
			SUM(sii.qty) as total_qty
		FROM `tabSales Invoice Delivery Plan` sii
		INNER JOIN `tabSales Invoice` si ON si.name = sii.parent
		WHERE sii.delivery_planning_schedule = %s
			AND si.docstatus = 1
		GROUP BY sii.delivery_planning_schedule_item
		""",
		dps_name,
		as_dict=True
	)
	return {row.delivery_planning_schedule_item: row.total_qty for row in result}


def validate_delivery_planning_schedule(doc):
	"""
	Validate Sales Invoice item quantities against selected Delivery Planning Schedule rows.
	"""
	sales_order = _get_sales_order_from_invoice(doc)
	if not sales_order:
		return

	selected_plans = doc.get("delivery_plan_details") or []
	available_plans = get_available_delivery_plan_rows(sales_order, sales_invoice=doc.name)

	if not available_plans and not selected_plans:
		return

	if not selected_plans:
		return

	available_plan_map = {
		(row.delivery_planning_schedule_item, row.sales_order_item): row for row in available_plans
	}
	selected_key_counts = defaultdict(int)
	selected_qty_by_so_item = defaultdict(float)

	for row in selected_plans:
		key = (row.get("delivery_planning_schedule_item"), row.get("sales_order_item"))
		selected_key_counts[key] += 1
		if selected_key_counts[key] > 1:
			frappe.throw(
				_("Delivery Plan row {0} is selected multiple times.").format(
					row.get("delivery_planning_schedule_item")
				)
			)

		available_row = available_plan_map.get(key)
		if not available_row:
			frappe.throw(
				_(
					"Selected Delivery Plan row {0} is invalid, belongs to another Sales Order, "
					"or is already fully invoiced."
				).format(row.get("delivery_planning_schedule_item"))
			)

		selected_qty = flt(row.get("qty"))
		if selected_qty <= 0:
			frappe.throw(
				_("Selected Delivery Plan row {0} must have Qty greater than zero.").format(
					row.get("delivery_planning_schedule_item")
				)
			)

		if selected_qty - flt(available_row.available_qty) > 1e-9:
			frappe.throw(
				_(
					"Selected Qty for Delivery Plan row {0} cannot exceed available qty {1}."
				).format(row.get("delivery_planning_schedule_item"), flt(available_row.available_qty))
			)

		selected_qty_by_so_item[row.get("sales_order_item")] += selected_qty

	invoice_qty_map = _build_invoice_qty_map(doc.get("items"))
	item_label_map = _build_item_label_map(doc.get("items"))

	mismatches = []
	for item_name in sorted(set(selected_qty_by_so_item) | set(invoice_qty_map)):
		selected_qty = flt(selected_qty_by_so_item.get(item_name))
		invoice_qty = flt(invoice_qty_map.get(item_name))

		if abs(selected_qty - invoice_qty) > 1e-9:
			item_label = item_label_map.get(item_name) or item_name
			mismatches.append(
				_(
					"- {0}: Delivery Plan Qty = {1}, Sales Invoice Qty = {2}, Difference = {3}"
				).format(
					item_label, selected_qty, invoice_qty, flt(invoice_qty - selected_qty)
				)
			)

	if mismatches:
		frappe.throw(
			_(
				"Delivery Plan qty does not match Sales Invoice qty.\n\n"
				"Please check these items:\n{0}\n\n"
				"Rule: Sales Invoice Qty must exactly match the total Qty selected in Delivery Plans for each item."
			).format("\n".join(mismatches))
		)


def _get_sales_order_from_invoice(doc):
	"""
	Resolve the originating Sales Order from the invoice header or item rows.
	"""
	if doc.get("sales_order"):
		return doc.sales_order

	sales_orders = []
	for row in doc.get("items", []):
		so_item = row.get("so_detail")
		if not so_item:
			continue

		parent = frappe.db.get_value("Sales Order Item", so_item, "parent")
		if parent:
			sales_orders.append(parent)

	if not sales_orders:
		return None

	unique_sales_orders = list(dict.fromkeys(sales_orders))
	if len(unique_sales_orders) > 1:
		frappe.throw(
			_("Sales Invoice contains items from multiple Sales Orders: {0}").format(
				", ".join(unique_sales_orders)
			)
		)

	return unique_sales_orders[0]


def _build_invoice_qty_map(items):
	"""
	Aggregate Sales Invoice quantities by linked Sales Order Item.
	"""
	qty_map = defaultdict(float)

	for row in items or []:
		so_item = row.get("so_detail")
		if not so_item:
			continue

		qty_map[so_item] += flt(row.get("stock_qty") or row.get("qty"))

	return qty_map


def _build_item_label_map(items):
	"""
	Build user-friendly labels for Sales Order Item references used in error messages.
	"""
	label_map = {}

	for row in items or []:
		so_item = row.get("so_detail")
		if not so_item:
			continue

		item_code = row.get("item_code") or ""
		item_name = row.get("item_name") or row.get("description") or ""
		if item_code and item_name and item_name != item_code:
			label_map[so_item] = f"{item_code} / {item_name}"
		else:
			label_map[so_item] = item_code or item_name or so_item

	return label_map


def _format_item_label(row):
	item_code = row.get("item_code") or ""
	item_name = row.get("item_name") or row.get("description") or ""
	if item_code and item_name and item_name != item_code:
		return f"{item_code} / {item_name}"
	return item_code or item_name or _("Row #{0}").format(row.get("idx"))


def _get_invoiced_qty_by_plan_row(sales_order, exclude_sales_invoice=None):
	"""
	Return already invoiced qty grouped by Delivery Planning Schedule child row.
	"""
	conditions = [
		"si.docstatus = 1",
		"sii.delivery_planning_schedule_item IS NOT NULL",
		"sii.sales_order_item IS NOT NULL",
	]
	values = []

	if exclude_sales_invoice:
		conditions.append("si.name != %s")
		values.append(exclude_sales_invoice)

	conditions.append(
		"""
		EXISTS (
			SELECT 1
			FROM `tabSales Invoice Item` sii_ref
			WHERE sii_ref.parent = si.name
				AND sii_ref.so_detail IN (
					SELECT soi.name
					FROM `tabSales Order Item` soi
					WHERE soi.parent = %s
				)
		)
		"""
	)
	values.append(sales_order)

	return {
		(row.delivery_planning_schedule_item, row.sales_order_item): flt(row.invoiced_qty)
		for row in frappe.db.sql(
			f"""
			SELECT
				sii.delivery_planning_schedule_item,
				sii.sales_order_item,
				SUM(sii.qty) AS invoiced_qty
			FROM `tabSales Invoice Delivery Plan` sii
			INNER JOIN `tabSales Invoice` si
				ON si.name = sii.parent
			WHERE {' AND '.join(conditions)}
			GROUP BY sii.delivery_planning_schedule_item, sii.sales_order_item
			""",
			values,
			as_dict=True,
		)
	}


@frappe.whitelist()
def get_available_delivery_plan_rows(sales_order, sales_invoice=None):
	"""
	Return selectable Delivery Planning Schedule rows for a Sales Order with remaining qty.
	"""
	if not sales_order:
		return []

	invoiced_qty_map = _get_invoiced_qty_by_plan_row(sales_order, exclude_sales_invoice=sales_invoice)

	rows = frappe.db.sql(
		"""
		SELECT
			dps.name AS delivery_planning_schedule,
			dpsi.name AS delivery_planning_schedule_item,
			dpsi.sales_order_item,
			dpsi.item_code,
			dpsi.delivery_date,
			dpsi.planned_qty,
			dpsi.uom
		FROM `tabDelivery Planning Schedule Item` dpsi
		INNER JOIN `tabDelivery Planning Schedule` dps
			ON dps.name = dpsi.parent
		WHERE dps.sales_order = %s
			AND dps.docstatus < 2
			AND dpsi.sales_order_item IS NOT NULL
		ORDER BY dpsi.delivery_date, dps.name, dpsi.idx
		""",
		sales_order,
		as_dict=True,
	)

	available_rows = []
	for row in rows:
		already_invoiced_qty = flt(
			invoiced_qty_map.get((row.delivery_planning_schedule_item, row.sales_order_item))
		)
		available_qty = flt(row.planned_qty) - already_invoiced_qty

		if available_qty <= 1e-9:
			continue

		row.already_invoiced_qty = already_invoiced_qty
		row.available_qty = available_qty
		row.qty = available_qty
		available_rows.append(row)

	return available_rows
