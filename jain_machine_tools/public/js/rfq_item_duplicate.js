// frappe.ui.form.on("Request for Quotation Item", {
//     item_code(frm, cdt, cdn) {
//         console.log("hello")
//         let row = locals[cdt][cdn];
//         if (!row.item_code) return;
//         let duplicate = frm.doc.items.filter(i => i.item_code === row.item_code);

//         if (duplicate.length > 1) {
//             frappe.msgprint({
//                 title: "Duplicate Item",
//                 indicator: "red",
//                 message: `Item <b>${row.item_code}</b> has been entered multiple times`
//             });
//             frappe.model.set_value(cdt, cdn, "item_code", "");
//         }
//     }
// });
frappe.ui.form.on("Request for Quotation", {
    before_cancel(frm) {
        frappe.validated = false; // stop default cancel

        // Show popup
        frappe.prompt([
            {
                label: 'Cancel Reason',
                fieldname: 'cancel_reason',
                fieldtype: 'Data',
                reqd: 1
            }
        ],
        function(values){
            // Call backend to set field & cancel
            frappe.call({
                method: "jain_machine_tools.api.cancel_rfq.cancel_with_reason",
                args: {
                    docname: frm.doc.name,
                    reason: values.cancel_reason
                },
                callback: function(r) {
                    if(!r.exc){
                        frappe.show_alert("Document Cancelled Successfully!");
                        frm.reload_doc();
                    }
                }
            });
        },
        "Provide Cancel Reason",
        "Cancel");
    }
});
