// Copyright (c) 2026, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.query_reports["Collection Plan Report"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "sales_invoice",
			label: __("Sales Invoice"),
			fieldtype: "Link",
			options: "Sales Invoice",
		},
		{
			fieldname: "from_date",
			label: __("Plan From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("Plan To Date"),
			fieldtype: "Date",
		}
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (!data || column.fieldname !== "status") {
			return value;
		}

		const color_map = {
			Collected: "green",
			Partial: "orange",
			Overdue: "red",
			Pending: "blue",
		};

		const color = color_map[data.status] || "gray";
		return `<span style="font-weight: 600; color: ${color};">${value}</span>`;
	},
};
