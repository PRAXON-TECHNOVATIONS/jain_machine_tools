// Copyright (c) 2026, Praxon Technovation and contributors
// For license information, please see license.txt

// frappe.query_reports["Pending Dispatch Orders"] = {
// 	"filters": [

// 	]
// };

frappe.query_reports["Pending Dispatch Orders"] = {
    filters: [
        {
            fieldname: "company",
            label: "Company",
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },
        { fieldname: "customer", label: "Customer", fieldtype: "Link", options: "Customer" },
        { fieldname: "sales_order", label: "Sales Order", fieldtype: "Link", options: "Sales Order" },
        { fieldname: "warehouse", label: "Warehouse", fieldtype: "Link", options: "Warehouse" },
        { fieldname: "from_delivery_date", label: "Delivery Date From", fieldtype: "Date" },
        { fieldname: "to_delivery_date", label: "Delivery Date To", fieldtype: "Date" },
        {
            fieldname: "dispatch_status",
            label: "Dispatch Status",
            fieldtype: "Select",
            options: ["", "Not Dispatched", "Partially Dispatched"]
        },
        {
            fieldname: "overdue_only",
            label: "Overdue Only",
            fieldtype: "Check"
        }
    ],

    tree: true,
    initial_depth: 0,

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        if (column.fieldname === "delivery_percent") {
            let p = data.delivery_percent || 0;
            let color = p === 0 ? "#d9534f" : p < 50 ? "#f0ad4e" : "#ffd500";

            return `
                <div style="min-width:90px;">
                    <div style="background:#eee;border-radius:4px;">
                        <div style="
                            width:${p}%;
                            background:${color};
                            padding:2px 4px;
                            font-size:11px;
                            border-radius:4px;
                            text-align:center;
                            font-weight:bold;">
                            ${p}%
                        </div>
                    </div>
                </div>`;
        }

        if (column.fieldname === "dispatch_status") {
            let color = data.dispatch_status === "Not Dispatched" ? "#d9534f" : "#f0ad4e";
            return `<span style="color:${color};font-weight:bold;">${data.dispatch_status}</span>`;
        }

        if (column.fieldname === "overdue" && data.overdue === "Yes") {
            return `<span style="color:#b30000;font-weight:bold;">Yes</span>`;
        }

        if (column.fieldname === "pending_qty" && data.pending_qty > 0) {
            return `<span style="font-weight:bold;">${value}</span>`;
        }

        return value;
    }
};