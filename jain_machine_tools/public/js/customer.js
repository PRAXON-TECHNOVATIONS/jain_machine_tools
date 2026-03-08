frappe.ui.form.on('Customer', {
    onload: function(frm) {

        frm.set_query("custom_rm", function() {
            return {
                filters: {
                    designation: "Relationship Manager"
                }
            };
        });

        frm.set_query("custom_sales_coordinator", function() {
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

frappe.ui.form.on('Customer', {
    after_save: function(frm) {

        let employees = [];

        if (frm.doc.custom_rm) {
            employees.push(frm.doc.custom_rm);
        }

        if (frm.doc.custom_sales_coordinator) {
            employees.push(frm.doc.custom_sales_coordinator);
        }

        frappe.call({
            method: "jain_machine_tools.api.customer_assignment.link_assign_to",
            args: {
                name: frm.doc.name,
                description: frm.doc.customer_name,
                employees: employees,
                doctype: "Customer"
            }
        });

    }
});