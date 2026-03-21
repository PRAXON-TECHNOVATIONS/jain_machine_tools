

import frappe
from frappe import _
from frappe.utils import nowdate

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data


def get_columns(filters):
	return [
		{"label": _("Freight Charges"), "fieldname": "freight_charges", "fieldtype": "Link", "options": "Freight Charges", "width": 150},
		{"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 180},
		{"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
		{"label": _("Supplier"), "fieldname": "supplier_name", "fieldtype": "Link", "options": "Supplier", "width": 300},
		{"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 200},
		{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Data", "width": 170},
	] 
	
def get_data(filters):
	if not filters:
		filters = {}  
	
	data= []
	conditions = ""
	
	if filters.get("sales_invoice"):
		conditions += " AND si.name = %(sales_invoice)s"
	
	if filters.get("supplier"):
		conditions += " AND fcd.supplier_name = %(supplier)s"

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s"
  
	sales_invoice = frappe.db.sql(f""" 
					SELECT 
						fc.name as freight_charges,
						fcd.sales_invoice as sales_invoice,
						si.posting_date ,
						fcd.supplier_name,
						fcd.type,
						fcd.amount
					FROM `tabFreight Charges` fc
					LEFT JOIN `tabFreight Charges Details` fcd ON fcd.parent = fc.name
					LEFT JOIN `tabSales Invoice` si ON fcd.sales_invoice = si.name
					WHERE 1=1
					{conditions}
					""",filters, as_dict=True)
	
	last_fc = None
	for row in sales_invoice:
		if row.freight_charges != last_fc:
			data.append({
				'indent': 0,
				'freight_charges': row.freight_charges,
			})
			last_fc = row.freight_charges
   
		data.append({
				'indent': 1,
				'freight_charges' : '',
				'sales_invoice' : row.sales_invoice,
				'posting_date' : row.posting_date,
				'supplier_name' : row.supplier_name,
				'type' : row.type,
				'amount' : row.amount,
			}
		)
	
	return data
	