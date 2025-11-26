frappe.ui.form.on("Supplier Quotation", {
    validate: function(frm) {

        if (frm.doc.supplier && frm.doc.rfq) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Supplier Quotation",
                    filters: {
                        supplier: frm.doc.supplier,
                        rfq: frm.doc.rfq,
                        name: ["!=", frm.doc.name]   // ignore same doc
                    },
                    fields: ["name"]
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        frappe.throw(
                            "A Supplier Quotation already exists for this Supplier and RFQ.<br><br>" +
                            "<b>Existing SQ:</b> " + r.message[0].name
                        );
                    }
                }
            });
        }
    }
});
