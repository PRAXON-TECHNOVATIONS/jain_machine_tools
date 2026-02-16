# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


class CustomTaxesAndTotals(calculate_taxes_and_totals):
	"""
	Custom override to add handling charges calculation to Quotation Item
	"""

	def calculate_item_values(self):
		"""
		Override to add handling charges calculation after discount
		Sequence: price_list_rate → margin → discount → handling_charges → rate
		"""
		# First, temporarily remove handling charges from rate if they exist
		# This ensures parent calculation works with the base rate
		for item in self.doc.get("items"):
			handling_charges_type = item.get("handling_charges_type")
			base_rate_stored = flt(item.get("base_rate_before_handling_charges"))

			# If base rate is stored, always restore it before calculation
			# This handles both: active handling charges AND when type is cleared to 0
			if base_rate_stored > 0:
				item.rate = base_rate_stored
				item.amount = flt(item.rate * item.qty, item.precision("amount"))

		# Call parent method (handles margin and discount)
		super(CustomTaxesAndTotals, self).calculate_item_values()

		# Store rate before handling charges for each item
		for item in self.doc.get("items"):
			handling_charges_type = item.get("handling_charges_type")
			base_rate_stored = flt(item.get("base_rate_before_handling_charges"))

			# Determine if we should update the stored base rate
			should_update_base = False

			if not base_rate_stored:
				# First time or field is empty - store the rate
				should_update_base = True
			elif not handling_charges_type:
				# No handling charges configured - update base rate
				# This allows manual rate changes to work properly
				should_update_base = True

			# Update the base rate if needed
			if should_update_base:
				item.base_rate_before_handling_charges = flt(item.rate)

		# Now apply handling charges to each item
		for item in self.doc.get("items"):
			self.calculate_handling_charges(item)

	def calculate_handling_charges(self, item):
		"""
		Calculate handling charges and update item rate and amount

		Calculation flow:
		1. Get rate after discount (stored in _rate_before_handling_charges)
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

	def calculate_totals(self):
		"""
		Override to handle missing 'category' attribute in Sales Taxes and Charges
		This is a compatibility fix for different ERPNext versions
		"""
		try:
			# Try the parent method first
			super(CustomTaxesAndTotals, self).calculate_totals()
		except AttributeError as e:
			# If 'category' attribute is missing, handle manually
			if "'category'" in str(e) or "category" in str(e):
				# Safe calculation without category attribute
				from frappe.utils import flt

				self.doc.grand_total = flt(self.doc.get("grand_total_export") or self.doc.net_total)
				self.doc.grand_total += flt(self.doc.get("total_taxes_and_charges"))

				self.doc.base_grand_total = flt(self.doc.grand_total * self.doc.conversion_rate, self.doc.precision("base_grand_total"))

				# Round if needed
				if self.doc.get("is_rounded_total_disabled"):
					self.doc.rounded_total = self.doc.grand_total
					self.doc.base_rounded_total = self.doc.base_grand_total
				else:
					from erpnext import get_default_cost_center
					self.doc.rounded_total = round(self.doc.grand_total)
					self.doc.base_rounded_total = round(self.doc.base_grand_total)
					self.doc.rounding_adjustment = flt(self.doc.rounded_total - self.doc.grand_total, self.doc.precision("rounding_adjustment"))
					self.doc.base_rounding_adjustment = flt(self.doc.base_rounded_total - self.doc.base_grand_total, self.doc.precision("base_rounding_adjustment"))
			else:
				# Re-raise if it's a different AttributeError
				raise


def custom_calculate_taxes_and_totals(doc):
	"""
	Custom function to use our CustomTaxesAndTotals class
	"""
	CustomTaxesAndTotals(doc)


def patch_insert_item_price():
	"""
	Monkey patch ERPNext's insert_item_price function to prevent creation for Non-Standard items
	This is called after migrate to override the function at runtime
	"""
	import erpnext.stock.get_item_details as item_details_module

	# Store the original function
	if not hasattr(item_details_module, '_original_insert_item_price'):
		item_details_module._original_insert_item_price = item_details_module.insert_item_price

	# Replace with our custom function
	item_details_module.insert_item_price = custom_insert_item_price


def custom_insert_item_price(args):
	"""
	Override ERPNext's insert_item_price to prevent creation for Non-Standard items
	This function is called from get_item_details when auto-insert is enabled
	"""
	# Check if this is a non-standard item first
	if args.get("item_code"):
		is_non_standard = frappe.get_cached_value("Item", args.item_code, "is_non_standard")

		if is_non_standard:
			# Silently skip - don't create Item Price for Non-Standard items
			# They have unique pricing per customer/quotation
			return

	# If not non-standard, execute the original ERPNext logic
	_insert_item_price_for_standard_items(args)


def _insert_item_price_for_standard_items(args):
	"""
	Original ERPNext insert_item_price logic for standard items only
	"""
	from frappe.utils import flt
	from erpnext.stock.get_item_details import _get_stock_uom_rate

	if (
		not args.price_list
		or not args.rate
		or args.get("is_internal_supplier")
		or args.get("is_internal_customer")
	):
		return

	stock_settings = frappe.get_cached_doc("Stock Settings")

	if (
		not frappe.db.get_value("Price List", args.price_list, "currency", cache=True) == args.currency
		or not stock_settings.auto_insert_price_list_rate_if_missing
		or not frappe.has_permission("Item Price", "write")
	):
		return

	item_price = frappe.db.get_value(
		"Item Price",
		{
			"item_code": args.item_code,
			"price_list": args.price_list,
			"currency": args.currency,
			"uom": args.stock_uom,
		},
		["name", "price_list_rate"],
		as_dict=1,
	)

	update_based_on_price_list_rate = stock_settings.update_price_list_based_on == "Price List Rate"

	if item_price and item_price.name:
		if not stock_settings.update_existing_price_list_rate:
			return

		rate_to_consider = flt(args.price_list_rate) if update_based_on_price_list_rate else flt(args.rate)
		price_list_rate = _get_stock_uom_rate(rate_to_consider, args)

		if not price_list_rate or item_price.price_list_rate == price_list_rate:
			return

		frappe.db.set_value("Item Price", item_price.name, "price_list_rate", price_list_rate)
		frappe.msgprint(
			_("Item Price updated for {0} in Price List {1}").format(args.item_code, args.price_list),
			alert=True,
		)
	else:
		rate_to_consider = (
			(flt(args.price_list_rate) or flt(args.rate))
			if update_based_on_price_list_rate
			else flt(args.rate)
		)
		price_list_rate = _get_stock_uom_rate(rate_to_consider, args)

		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"price_list": args.price_list,
				"item_code": args.item_code,
				"currency": args.currency,
				"price_list_rate": price_list_rate,
				"uom": args.stock_uom,
			}
		)
		item_price.insert()
		frappe.msgprint(
			_("Item Priceeeeeee added for {0} in Price List {1}").format(args.item_code, args.price_list),
			alert=True,
		)


# Validation hooks
def validate_quotation(doc, method=None):
	"""
	Hook for Quotation validation
	Replaces standard taxes_and_totals calculation with custom one
	"""
	# Use custom calculation class
	custom_calculate_taxes_and_totals(doc)


def validate_sales_order(doc, method=None):
	"""
	Hook for Sales Order validation
	"""
	custom_calculate_taxes_and_totals(doc)


def validate_sales_invoice(doc, method=None):
	"""
	Hook for Sales Invoice validation
	"""
	custom_calculate_taxes_and_totals(doc)


def validate_delivery_note(doc, method=None):
	"""
	Hook for Delivery Note validation
	"""
	custom_calculate_taxes_and_totals(doc)


def validate_proforma_invoice(doc, method=None):
	"""
	Hook for Proforma Invoice validation
	"""
	custom_calculate_taxes_and_totals(doc)


# ========================================
# Mapping Functions
# ========================================

@frappe.whitelist()
def make_proforma_invoice(source_name, target_doc=None):
	"""
	Create Proforma Invoice from Quotation
	Replaces direct Quotation → Sales Order flow
	"""
	return _make_proforma_invoice(source_name, target_doc)


def _make_proforma_invoice(source_name, target_doc=None):
	"""
	Internal implementation for creating Proforma Invoice from Quotation
	Follows ERPNext pattern similar to make_sales_order
	"""
	from frappe.model.mapper import get_mapped_doc

	def set_missing_values(source, target):
		"""Set missing values in target Proforma Invoice"""
		# Store quotation reference
		target.quotation = source.name

		# Map customer from quotation's party_name if quotation_to is Customer
		if source.quotation_to == "Customer" and source.party_name:
			target.customer = source.party_name
			target.customer_name = source.customer_name or frappe.get_cached_value("Customer", source.party_name, "customer_name")

		# Set missing values using ERPNext standard methods
		target.run_method("set_missing_values")

		# Use custom calculation instead of standard ERPNext method
		custom_calculate_taxes_and_totals(target)

	def update_item(obj, target, source_parent):
		"""Update item fields during mapping"""
		# Set prevdoc_doctype for proper linking
		target.prevdoc_doctype = "Quotation"

	doclist = get_mapped_doc(
		"Quotation",
		source_name,
		{
			"Quotation": {
				"doctype": "Proforma Invoice",
				"validation": {"docstatus": ["=", 1]}  # Only submitted quotations
			},
			"Quotation Item": {
				"doctype": "Proforma Invoice Item",
				"field_map": {
					"parent": "prevdoc_docname",  # Store quotation name in prevdoc_docname
					"name": "quotation_item"  # Store quotation item row reference
				},
				"postprocess": update_item
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"reset_value": True  # Recalculate taxes
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
