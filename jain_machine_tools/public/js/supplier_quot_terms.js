frappe.ui.form.on('Supplier Quotation', {
    custom_payment_terms_template: function(frm) {
        if (!frm.doc.custom_payment_terms_template) {
            frm.clear_table("custom_payment_term_details");
            frm.refresh_field("custom_payment_term_details");
            return;
        }

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Payment Terms Template",
                name: frm.doc.custom_payment_terms_template
            },
            callback: function(r) {
                if (!r.message) return;

                let terms = r.message.terms || [];
                frm.clear_table("custom_payment_term_details");
                terms.forEach(row => {
                    let d = frm.add_child("custom_payment_term_details");
                    d.payment_term = row.payment_term;
                    d.description = row.description;
                    d.due_date_based_on = row.due_date_based_on;
                    d.invoice_portion = row.invoice_portion;
                    d.credit_days = row.credit_days;
                    d.credit_months = row.credit_months;
                    d.due_date = row.due_date;
                });

                frm.refresh_field("custom_payment_term_details");
            }
        });
    }
});

// Auto-populate supplier item code in items child table
frappe.ui.form.on('Supplier Quotation Item', {
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.item_code || !frm.doc.supplier) {
            return;
        }

        // Fetch supplier item code from Party Specific Item
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Party Specific Item',
                filters: {
                    party_type: 'Supplier',
                    party: frm.doc.supplier,
                    based_on_value: row.item_code
                },
                fieldname: 'supplier_item_code'
            },
            callback: function(r) {
                if (r.message && r.message.supplier_item_code) {
                    frappe.model.set_value(cdt, cdn, 'custom_supplier_code', r.message.supplier_item_code);
                }
            }
        });
    }
});
