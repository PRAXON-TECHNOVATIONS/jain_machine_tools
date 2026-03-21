// Copyright (c) 2026, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.query_reports["Freight Charges"] = {
	"filters": [
		{
            fieldname: "sales_invoice",
            label: __("Sales Invoice"),
            fieldtype: "Link",
            options: "Sales Invoice",
        },
		{
            fieldname: "supplier",
            label: __("Supplier"),
            fieldtype: "Link",
            options: "Supplier",
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
        },
	],
	formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        if (data.indent === 0) {
            value = `<b>${value}</b>`;
        }
        
        return value;
    },
};
