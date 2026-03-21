# Copyright (c) 2026, Praxon Technovation and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, msgprint
from frappe.utils import get_link_to_form


class FreightCharges(Document):
	
	def validate(self):
		seen = set()

		for row in self.freight_charges_details:
			key = (row.sales_invoice, row.type)

			if key in seen:
				frappe.throw(
					_("Duplicate entry found for Sales Invoice {0} with Type {1}")
					.format(row.sales_invoice, row.type)
				)

			seen.add(key)

			existing = frappe.db.sql("""
				SELECT fc.name
				FROM `tabFreight Charges Details` fcd
				INNER JOIN `tabFreight Charges` fc
					ON fc.name = fcd.parent
				WHERE
					fcd.sales_invoice = %s
					AND fcd.type = %s
					AND fc.name != %s
					AND fc.docstatus != 2
				LIMIT 1
			""", (row.sales_invoice, row.type, self.name), as_dict=True)
   
			if existing:
				fc_name = existing[0].name
				fc_link = get_link_to_form("Freight Charges", fc_name)

				frappe.throw(
					_("Sales Invoice with Type {0} already exists in {1}")
					.format(row.type, fc_link)
				)




@frappe.whitelist()
def get_sales_invoice(start_date, to_date):
	if not start_date or not to_date:
		frappe.throw(_("Please set From Date and To Date"))

	sales_invoice = frappe.db.sql("""
		SELECT
			si.name as sales_invoice
		FROM
			`tabSales Invoice` si
		WHERE
			si.docstatus = 1
			AND si.posting_date BETWEEN %(start_date)s AND %(to_date)s
		ORDER BY
			si.posting_date ASC
	""", {
		'start_date': start_date,
		'to_date': to_date,
	}, as_dict=True)

	frappe.msgprint(_("Found {0} Sales Invoice in the date range").format(len(sales_invoice)))

	return {
		'sales_invoice': [
			{
				'sales_invoice': si.sales_invoice,
			}
			for si in sales_invoice
		]
	}