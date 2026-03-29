# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class DeliveryPlanningSchedule(Document):
	def validate(self):
		self.validate_sales_order()
		self.validate_item_totals()

	def validate_sales_order(self):
		if not self.sales_order:
			frappe.throw(_("Please select a Sales Order before saving Delivery Planning Schedule."))

		sales_order = frappe.get_doc("Sales Order", self.sales_order)
		if sales_order.docstatus != 1:
			frappe.throw(_("Sales Order {0} must be submitted before making a Delivery Planning Schedule.").format(
				frappe.get_desk_link("Sales Order", sales_order.name)
			))

		self.company = sales_order.company
		self.customer = sales_order.customer

		if not self.schedule_date:
			self.schedule_date = nowdate()

	def validate_item_totals(self):
		if not self.get("items"):
			return

		sales_order = frappe.get_doc("Sales Order", self.sales_order)
		so_qty_map = _build_sales_order_qty_map(sales_order.get("items"))
		current_qty_map = _build_current_schedule_qty_map(self.get("items"))
		already_planned_qty_map = _get_planned_qty_map(self.sales_order, exclude_schedule=self.name)

		mismatches = []
		for so_item_name in sorted(set(so_qty_map) | set(current_qty_map) | set(already_planned_qty_map)):
			so_qty = flt(so_qty_map.get(so_item_name))
			current_qty = flt(current_qty_map.get(so_item_name))
			already_planned_qty = flt(already_planned_qty_map.get(so_item_name))
			remaining_qty = so_qty - already_planned_qty

			if current_qty - remaining_qty > 1e-9:
				mismatches.append(
					_("{0}: Sales Order Qty {1}, Already Planned Qty {2}, This Schedule Qty {3}").format(
						so_item_name,
						so_qty,
						already_planned_qty,
						current_qty,
					)
				)

		if mismatches:
			frappe.throw(
				_(
					"Delivery Planning Schedule quantities cannot exceed the remaining quantity on the linked Sales Order.\n{0}"
				).format("\n".join(mismatches))
			)


@frappe.whitelist()
def sales_order_query(doctype, txt, searchfield, start, page_len, filters):
	"""
	Only show submitted Sales Orders that do not already have a Delivery Planning Schedule.
	"""
	txt = f"%{txt}%"
	return frappe.db.sql(
		"""
		SELECT so.name, so.customer, so.customer_name
		FROM `tabSales Order` so
		WHERE so.docstatus = 1
			AND so.workflow_state = 'Approved'
			AND (
				so.name LIKE %(txt)s
				OR so.customer_name LIKE %(txt)s
				OR so.customer LIKE %(txt)s
			)
		ORDER BY so.modified DESC
		LIMIT %(start)s, %(page_len)s
		""",
		{"txt": txt, "start": start, "page_len": page_len},
		as_list=True,
	)


@frappe.whitelist()
def get_items_from_sales_order(sales_order):
	"""
	Fetch Sales Order items to seed the Delivery Planning Schedule table.
	"""
	if not sales_order:
		frappe.throw(_("Please select a Sales Order first."))

	so = frappe.get_doc("Sales Order", sales_order)
	if so.docstatus != 1:
		frappe.throw(_("Sales Order {0} must be submitted before fetching items.").format(
			frappe.get_desk_link("Sales Order", so.name)
		))

	already_planned_qty_map = _get_planned_qty_map(so.name)
	default_delivery_date = so.transaction_date or nowdate()
	items = []
	for row in so.get("items", []):
		already_planned_qty = flt(already_planned_qty_map.get(row.name))
		remaining_qty = flt(row.qty) - already_planned_qty
		if remaining_qty <= 0:
			continue

		# Fetch Projected Qty and Actual Qty from Bin
		projected_qty = 0
		actual_qty = 0
		if row.item_code and row.warehouse:
			bin_data = frappe.db.get_value(
				"Bin",
				{"item_code": row.item_code, "warehouse": row.warehouse},
				["projected_qty", "actual_qty"],
				as_dict=True
			) or {}
			projected_qty = bin_data.get("projected_qty", 0)
			actual_qty = bin_data.get("actual_qty", 0)

		items.append(
			{
				"sales_order_item": row.name,
				"item_code": row.item_code,
				"qty_from_so": row.qty,
				"warehouse": row.warehouse,
				"projected_qty": projected_qty,
				"actual_qty": actual_qty,
				"delivery_date": default_delivery_date,
				"planned_qty": remaining_qty,
				"uom": row.uom,
				"description": row.description or row.item_name,
				"already_planned_qty": already_planned_qty,
				"status": "Pending"
			}
		)

	return {
		"sales_order": so.name,
		"company": so.company,
		"customer": so.customer,
		"schedule_date": nowdate(),
		"status": "Pending",
		"items": items,
	}


def _build_sales_order_qty_map(items):
	qty_map = {}
	for row in items or []:
		item_name = row.get("name")
		if not item_name:
			continue
		qty_map[item_name] = flt(qty_map.get(item_name)) + flt(row.get("qty"))
	return qty_map


def _build_current_schedule_qty_map(items):
	qty_map = {}
	for row in items or []:
		so_item = row.get("sales_order_item")
		if not so_item:
			continue
		qty_map[so_item] = flt(qty_map.get(so_item)) + flt(row.get("planned_qty"))
	return qty_map


def _get_planned_qty_map(sales_order, exclude_schedule=None):
	filters = ["dps.sales_order = %s", "dps.docstatus < 2"]
	values = [sales_order]

	if exclude_schedule:
		filters.append("dps.name != %s")
		values.append(exclude_schedule)

	return {
		row.sales_order_item: flt(row.already_planned_qty)
		for row in frappe.db.sql(
			f"""
			SELECT
				dpsi.sales_order_item,
				SUM(dpsi.planned_qty) AS already_planned_qty
			FROM `tabDelivery Planning Schedule Item` dpsi
			INNER JOIN `tabDelivery Planning Schedule` dps
				ON dps.name = dpsi.parent
			WHERE {' AND '.join(filters)}
				AND dpsi.sales_order_item IS NOT NULL
			GROUP BY dpsi.sales_order_item
			""",
			values,
			as_dict=True,
		)
	}
