// Copyright (c) 2026, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.ui.form.on("Freight Charges", {
    get_sales_invoice: function (frm) {
        if (!frm.doc.start_date || !frm.doc.to_date) {
            frappe.msgprint(__('Please set From Delivery Date and To Delivery Date'));
            return;
        }

        frappe.call({
            method: 'jain_machine_tools.jain_machine_tools.doctype.freight_charges.freight_charges.get_sales_invoice',
            args: {
                start_date: frm.doc.start_date,
                to_date: frm.doc.to_date,
            },
            callback: function (r) {

                if (r.message && r.message.sales_invoice) {

                    let existing_rows = frm.doc.freight_charges_details || [];
                    let added_count = 0;

                    r.message.sales_invoice.forEach(function (si) {

                        let duplicate = existing_rows.find(row =>
                            row.sales_invoice === si.sales_invoice &&
                            (row.type === "Transport to Customer" || row.type === "Transport to Warehouse")
                        );

                        if (duplicate) {
                            frappe.msgprint(
                                __("Skipped duplicate Sales Invoice {0}", [si.sales_invoice])
                            );
                            return;
                        }

                        let row = frappe.model.add_child(
                            frm.doc,
                            'Freight Charges Details',
                            'freight_charges_details'
                        );

                        row.sales_invoice = si.sales_invoice;
                        added_count++;
                    });

                    frm.refresh_field('freight_charges_details');

                    frappe.show_alert({
                        message: __('{0} Sales Invoice Added', [added_count]),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    setup: function(frm) {

        frm.set_query('supplier_name', 'freight_charges_details', function() {
            return {
                filters: {
                    is_transporter: 1
                }
            };
        });

    }
});