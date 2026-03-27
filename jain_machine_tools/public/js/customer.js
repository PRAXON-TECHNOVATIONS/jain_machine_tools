frappe.ui.form.on('Customer', {
    onload: function (frm) {

        frm.set_query("custom_rm", function () {
            return {
                filters: {
                    designation: ["in", ["Relationship Manager", "Sales Head"]]
                }
            };
        });

        frm.set_query("custom_sales_coordinator", function () {
            return {
                filters: {
                    designation: "Sales Coordinator"
                }
            };
        });

    },
    gstin(frm) {
        if (!frm.doc.gstin) return;

        frm.set_value({
            pan: "",
            tax_id: "",
        });

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Customer",
                filters: [
                    ["gstin", "=", frm.doc.gstin],
                    ["name", "!=", frm.doc.name]
                ],
                fields: ["name"],
                limit_page_length: 1
            },
            callback(r) {
                if (r.message && r.message.length) {
                    frappe.msgprint({
                        title: __("Duplicate GSTIN"),
                        indicator: "red",
                        message: __(
                            "Duplicate GSTIN already exists in Customer <b>{0}</b>. You cannot use this GSTIN.",
                            [r.message[0].name]
                        )
                    });

                    frm.set_value("gstin", "");
                }
            }
        });
    }
});
