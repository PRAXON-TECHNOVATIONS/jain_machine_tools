# Copyright (c) 2026, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals


class CustomPurchaseTaxesAndTotals(calculate_taxes_and_totals):
	"""
	Custom override to add handling charges calculation to Purchase Order Item
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
		super(CustomPurchaseTaxesAndTotals, self).calculate_item_values()

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


def validate_purchase_receipt(doc, method=None):
	"""
	Hook for Purchase Receipt validation
	"""
	custom_calculate_taxes_and_totals(doc)
