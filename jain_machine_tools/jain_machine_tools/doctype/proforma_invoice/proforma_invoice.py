# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from erpnext.controllers.selling_controller import SellingController


class ProformaInvoice(SellingController):
	def calculate_taxes_and_totals(self):
		"""Override to use custom calculation with handling charges support"""
		from jain_machine_tools.overrides.quotation import custom_calculate_taxes_and_totals
		custom_calculate_taxes_and_totals(self)

	def validate(self):
		super().validate()
		self.set_status()

	def before_submit(self):
		self.set_status()

	def on_submit(self):
		self.set_status(update=True)

	def on_cancel(self):
		self.check_sales_order_created()
		self.set_status(update=True)

	def set_status(self, update=False):
		"""Update status based on document state"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.sales_order:
				self.status = "Sales Order Created"
			else:
				self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

		if update:
			self.db_set("status", self.status, update_modified=False)

	def check_sales_order_created(self):
		"""Prevent cancellation if Sales Order has been created"""
		if self.sales_order:
			frappe.throw(
				_("Cannot cancel because Sales Order {0} has been created from this Proforma Invoice").format(
					frappe.get_desk_link("Sales Order", self.sales_order)
				)
			)


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	"""Create Sales Order from Proforma Invoice"""

	def set_missing_values(source, target):
		"""Set missing values in target Sales Order"""
		# Import custom calculation method
		from jain_machine_tools.overrides.quotation import custom_calculate_taxes_and_totals

		target.run_method("set_missing_values")

		# Use custom calculation for handling charges support
		custom_calculate_taxes_and_totals(target)

	def update_item(obj, target, source_parent):
		"""Update item fields during mapping"""
		# Carry forward quotation_item reference if exists
		if hasattr(obj, 'quotation_item') and obj.quotation_item:
			target.quotation_item = obj.quotation_item

	doclist = get_mapped_doc(
		"Proforma Invoice",
		source_name,
		{
			"Proforma Invoice": {
				"doctype": "Sales Order",
				"validation": {"docstatus": ["=", 1]},
				"field_map": {
					"quotation": "quotation"  # Carry forward quotation reference
				}
			},
			"Proforma Invoice Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					"parent": "prevdoc_docname"
				},
				"postprocess": update_item
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"reset_value": True
			},
			"Sales Team": {
				"doctype": "Sales Team",
				"add_if_empty": True
			},
			"Payment Schedule": {
				"doctype": "Payment Schedule",
				"add_if_empty": True
			}
		},
		target_doc,
		set_missing_values
	)

	return doclist


@frappe.whitelist()
def update_proforma_on_sales_order_submit(proforma_invoice, sales_order, sales_order_date):
	"""Update Proforma Invoice when Sales Order is created and saved"""
	if not proforma_invoice:
		return

	doc = frappe.get_doc("Proforma Invoice", proforma_invoice)
	doc.db_set("sales_order", sales_order, update_modified=False)
	doc.db_set("sales_order_date", sales_order_date, update_modified=False)
	doc.db_set("status", "Sales Order Created", update_modified=False)
