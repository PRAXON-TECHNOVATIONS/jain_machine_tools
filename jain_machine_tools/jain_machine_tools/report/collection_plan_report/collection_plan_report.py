# Copyright (c) 2026, Praxon Technovation and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	report_summary = get_report_summary(data)
	return columns, data, None, None, report_summary


def get_columns():
	return [
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 180,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Voucher ID"),
			"fieldname": "voucher_id",
			"fieldtype": "Link",
			"options": "Sales Invoice",
			"width": 180,
		},
		{
			"label": _("Invoice Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Due Date"),
			"fieldname": "due_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Due Amount"),
			"fieldname": "due_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Collection Plan Date"),
			"fieldname": "collection_plan_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": _("Collection Amount"),
			"fieldname": "collection_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Actual Collection Date"),
			"fieldname": "actual_collection_date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"label": _("Actual Collection Amount"),
			"fieldname": "actual_collection_amount",
			"fieldtype": "Currency",
			"width": 160,
		},
		{
			"label": _("Payment Entry"),
			"fieldname": "payment_entries",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100,
		},
	]


def get_data(filters):
	conditions = [
		"si.docstatus = 1",
		"cpd.parenttype = 'Sales Invoice'",
		"cpd.parentfield = 'custom_collection_plan_details'",
	]
	params = {}

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		params["company"] = filters.company

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		params["customer"] = filters.customer

	if filters.get("sales_invoice"):
		conditions.append("si.name = %(sales_invoice)s")
		params["sales_invoice"] = filters.sales_invoice

	if filters.get("from_date"):
		conditions.append("cpd.collection_date >= %(from_date)s")
		params["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("cpd.collection_date <= %(to_date)s")
		params["to_date"] = filters.to_date

	data = frappe.db.sql(
		f"""
		SELECT
			si.customer AS customer,
			si.customer_name AS customer_name,
			si.name AS voucher_id,
			si.posting_date AS posting_date,
			si.due_date AS due_date,
			si.outstanding_amount AS due_amount,
			cpd.collection_date AS collection_plan_date,
			cpd.amount AS collection_amount,
			pe.actual_collection_date AS actual_collection_date,
			pe.actual_collection_amount AS actual_collection_amount,
			pe.payment_entries AS payment_entries
		FROM `tabSales Invoice` si
		INNER JOIN `tabCollection Plan Details` cpd
			ON cpd.parent = si.name
		LEFT JOIN (
			SELECT
				per.reference_name AS sales_invoice,
				MAX(pe.posting_date) AS actual_collection_date,
				SUM(per.allocated_amount) AS actual_collection_amount,
				GROUP_CONCAT(DISTINCT pe.name ORDER BY pe.posting_date SEPARATOR ', ') AS payment_entries
			FROM `tabPayment Entry Reference` per
			INNER JOIN `tabPayment Entry` pe
				ON pe.name = per.parent
			WHERE
				per.reference_doctype = 'Sales Invoice'
				AND pe.docstatus = 1
			GROUP BY per.reference_name
		) pe
			ON pe.sales_invoice = si.name
		WHERE {" AND ".join(conditions)}
		ORDER BY cpd.collection_date ASC, si.posting_date DESC, si.name DESC, cpd.idx ASC
		""",
		params,
		as_dict=True,
	)

	for row in data:
		row.actual_collection_amount = flt(row.actual_collection_amount)
		row.collection_amount = flt(row.collection_amount)
		row.due_amount = flt(row.due_amount)
		row.status = get_status(row)

	return data


def get_status(row):
	actual_amount = flt(row.actual_collection_amount)
	planned_amount = flt(row.collection_amount)
	plan_date = row.get("collection_plan_date")

	if actual_amount >= planned_amount and planned_amount > 0:
		return "Collected"

	if 0 < actual_amount < planned_amount:
		return "Partial"

	if plan_date and getdate(plan_date) < getdate(today()):
		return "Overdue"

	return "Pending"


def get_report_summary(data):
	if not data:
		return []

	invoice_totals = {}
	for row in data:
		invoice_totals.setdefault(
			row.get("voucher_id"),
			{
				"due_amount": flt(row.get("due_amount")),
				"actual_collection_amount": flt(row.get("actual_collection_amount")),
			},
		)

	total_due = sum(row["due_amount"] for row in invoice_totals.values())
	total_planned = sum(flt(row.get("collection_amount")) for row in data)
	total_actual = sum(row["actual_collection_amount"] for row in invoice_totals.values())

	return [
		{
			"value": total_due,
			"label": _("Total Due Amount"),
			"indicator": "Red",
			"datatype": "Currency",
		},
		{
			"value": total_planned,
			"label": _("Total Planned Collection"),
			"indicator": "Orange",
			"datatype": "Currency",
		},
		{
			"value": total_actual,
			"label": _("Total Actual Collection"),
			"indicator": "Green",
			"datatype": "Currency",
		},
	]
