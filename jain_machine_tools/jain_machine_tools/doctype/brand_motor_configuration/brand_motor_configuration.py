# Copyright (c) 2025, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document


class BrandMotorConfiguration(Document):
	def validate(self):
		"""Validate Brand configuration"""
		# Ensure Brand is unique
		if not self.is_new():
			existing = frappe.db.get_value(
				"Brand Motor Configuration",
				{"brand": self.brand, "name": ["!=", self.name]},
				"name"
			)
			if existing:
				frappe.throw(f"Configuration already exists for brand {self.brand}: {existing}")

	def get_selected_parameters(self):
		"""Get list of all parameters for Form.io schema generation"""
		parameters = []
		for row in self.parameters:
			# Skip rows without a parameter selected
			if not row.parameter:
				continue

			param_doc = frappe.get_doc("Motor Parameter Master", row.parameter)
			parameters.append({
				"name": param_doc.name,
				"code": param_doc.parameter_code,
				"description": param_doc.description,
				"category": param_doc.category or "Other",
				"pricing_type": row.pricing_type or "Percentage",
				"frame_size_dependent": row.frame_size_dependent,
				"motor_type_dependent": row.motor_type_dependent
			})
		return parameters

	@frappe.whitelist()
	def get_formio_schema(self):
		"""Generate Form.io schema based on selected parameters with category panels"""
		selected_params = self.get_selected_parameters()

		if not selected_params:
			return {"components": []}

		# Group parameters by category
		from collections import defaultdict
		categories = defaultdict(list)

		for param in selected_params:
			category = param.get("category", "Other")
			categories[category].append(param)

		# Build category tabs
		tab_components = []

		for category, params in sorted(categories.items()):
			# Build parameter panels for this category
			parameter_panels = []

			for param in params:
				# Create a panel for each parameter
				panel_components = []

				# Parameter description
				panel_components.append({
					"type": "htmlelement",
					"tag": "p",
					"content": param.get("description", ""),
					"className": "text-muted"
				})

				# Always create datagrid with "Add Another"
				# Fields are conditionally added based on dependencies
				datagrid_components = []

				# Conditionally add motor type field
				if param.get("motor_type_dependent"):
					datagrid_components.append({
						"type": "select",
						"label": "Motor Type",
						"key": "motor_type",
						"data": {
							"values": [
								{"label": "FLP", "value": "FLP"},
								{"label": "Non-FLP", "value": "Non-FLP"}
							]
						},
						"validate": {
							"required": True
						},
						"placeholder": "Select motor type"
					})

				# Conditionally add frame size field
				if param.get("frame_size_dependent"):
					datagrid_components.append({
						"type": "number",
						"label": "Frame Size",
						"key": "frame_size",
						"validate": {
							"required": True,
							"min": 63,
							"max": 500
						},
						"placeholder": "Enter frame size (e.g., 63, 71, 80...)"
					})

				# Always add value and pricing fields
				datagrid_components.append({
					"type": "textfield",
					"label": "Value",
					"key": "value"
				})
				datagrid_components.append(self._get_pricing_field(param, "price"))

				# Add the datagrid
				panel_components.append({
					"type": "datagrid",
					"label": "Configuration Values",
					"key": f"{param['code']}_values",
					"components": datagrid_components
				})

				# Add parameter panel
				parameter_panels.append({
					"type": "panel",
					"title": param["name"],
					"collapsible": True,
					"collapsed": False,
					"key": f"{param['code']}_panel",
					"components": panel_components
				})

			# Create tab for this category
			tab_components.append({
				"label": category,
				"key": f"tab_{category.lower().replace(' ', '_')}",
				"components": parameter_panels
			})

		# Return tabs container
		return {
			"components": [{
				"type": "tabs",
				"label": "Parameter Configuration",
				"key": "parameter_tabs",
				"components": tab_components,
				"input": False,
				"tableView": False
			}]
		}

	def _get_pricing_field(self, param, key):
		"""Generate pricing field based on pricing_type"""
		pricing_type = param.get("pricing_type", "Percentage")

		if pricing_type == "Percentage":
			return {
				"type": "number",
				"label": "Percentage (%)",
				"key": key,
				"suffix": "%",
				"decimalLimit": 2,
				"delimiter": False
			}
		elif pricing_type == "Fixed Amount":
			return {
				"type": "number",
				"label": "Fixed Amount (INR)",
				"key": key,
				"prefix": "₹",
				"decimalLimit": 2,
				"delimiter": True
			}
		else:  # Both
			return {
				"type": "columns",
				"columns": [
					{
						"components": [{
							"type": "number",
							"label": "Percentage (%)",
							"key": f"{key}_pct",
							"suffix": "%",
							"decimalLimit": 2,
							"delimiter": False
						}],
						"width": 6
					},
					{
						"components": [{
							"type": "number",
							"label": "Fixed Amount (INR)",
							"key": f"{key}_amt",
							"prefix": "₹",
							"decimalLimit": 2,
							"delimiter": True
						}],
						"width": 6
					}
				]
			}

	@frappe.whitelist()
	def save_formio_data(self, formio_data):
		"""Save Form.io submission data to JSON field"""
		if isinstance(formio_data, str):
			formio_data = json.loads(formio_data)

		self.values_json = json.dumps(formio_data, indent=2)
		self.save()

		return {"success": True, "message": "Configuration saved successfully"}
