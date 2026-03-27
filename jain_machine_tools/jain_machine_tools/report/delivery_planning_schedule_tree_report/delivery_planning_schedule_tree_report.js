// Copyright (c) 2026, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.query_reports["Delivery Planning Schedule Tree Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "fieldtype": "Date",
            "label": "From Date",
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "fieldtype": "Date",
            "label": "To Date",
            "reqd": 0
        },
        {
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "label": "Sales Order",
            "options": "Sales Order",
            "reqd": 0
        }
    ]
};
