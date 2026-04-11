# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe


SOURCE_COLLECTION_PLAN_FIELD = "custom_collection__plan"
TARGET_COLLECTION_PLAN_FIELD = "custom_collection_plan_details"
COLLECTION_PLAN_DOCTYPE = "Collection Plan Details"
SYSTEM_CHILD_FIELDS = {
	"name",
	"parent",
	"parentfield",
	"parenttype",
	"idx",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"docstatus",
	"doctype",
}


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False, args=None):
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice as erpnext_make_sales_invoice

	doc = erpnext_make_sales_invoice(
		source_name,
		target_doc=target_doc,
		ignore_permissions=ignore_permissions,
		args=args,
	)
	_copy_collection_plan_rows(source_name, doc)
	return doc


def _copy_collection_plan_rows(source_name, target_doc):
	source_doc = frappe.get_doc("Sales Order", source_name)

	if not source_doc.meta.has_field(SOURCE_COLLECTION_PLAN_FIELD):
		return

	if not target_doc.meta.has_field(TARGET_COLLECTION_PLAN_FIELD):
		return

	target_doc.set(TARGET_COLLECTION_PLAN_FIELD, [])

	for row in source_doc.get(SOURCE_COLLECTION_PLAN_FIELD) or []:
		target_doc.append(
			TARGET_COLLECTION_PLAN_FIELD,
			{
				fieldname: row.get(fieldname)
				for fieldname in _get_collection_plan_fieldnames()
			},
		)


def _get_collection_plan_fieldnames():
	return [
		df.fieldname
		for df in frappe.get_meta(COLLECTION_PLAN_DOCTYPE).fields
		if df.fieldname and df.fieldname not in SYSTEM_CHILD_FIELDS
	]
