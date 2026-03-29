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
        },
        {
            "fieldname": "delivery_planning_schedule",
            "fieldtype": "Link",
            "label": "Select DPS For Print",
            "options": "Delivery Planning Schedule",
            "reqd": 0,
        }
    ],

    after_datatable_render: function(datatable_obj) {
        // Attach click handler on every render (report refresh / filter change)
        $(datatable_obj.wrapper)
            .off("click.jmt_invoice")
            .on("click.jmt_invoice", ".jmt-create-invoice-btn", function() {
                const dps = $(this).data("dps");
                const so  = $(this).data("so");
                jmt_open_sales_invoice(dps, so, $(this));
            })
            .off("click.jmt_print")
            .on("click.jmt_print", ".jmt-print-dps-btn", function() {
                const dps = $(this).data("dps");
                jmt_open_dps_print(dps);
            });
    }
};

function jmt_open_sales_invoice(dps_name, so_name, $btn) {
    $btn.prop("disabled", true).text("Creating...");

    frappe.call({
        method: "jain_machine_tools.jain_machine_tools.report.delivery_planning_schedule_tree_report.delivery_planning_schedule_tree_report.make_sales_invoice",
        args: { dps_name: dps_name },
        callback: function(r) {
            $btn.prop("disabled", false).text("Create Invoice");
            if (!r.message) {
                frappe.msgprint(__("Could not create Sales Invoice."));
                return;
            }
            // Sync unsaved doc into local model and open the form
            frappe.model.sync(r.message);
            frappe.set_route("Form", "Sales Invoice", r.message.name);
        },
        error: function() {
            $btn.prop("disabled", false).text("Create Invoice");
        }
    });
}

function jmt_open_dps_print(dps_name) {
    const url = `/printview?doctype=${encodeURIComponent("Delivery Planning Schedule")}&name=${encodeURIComponent(dps_name)}&trigger_print=1&format=Standard&no_letterhead=0`;
    window.open(url, "_blank");
}
