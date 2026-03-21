// Copyright (c) 2026, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.query_reports["Material Transfer Tracking Report"] = {
	"filters": [
		{
			fieldname: "source_warehouse",
			label: "Source Warehouse",
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "destination_warehouse",
			label: "Destination Warehouse",
			fieldtype: "Link",
			options: "Warehouse",
		}
	]
};
