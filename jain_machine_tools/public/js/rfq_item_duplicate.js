frappe.ui.form.on("Request for Quotation Item", {
    item_code(frm, cdt, cdn) {
        console.log("hello")
        let row = locals[cdt][cdn];
        if (!row.item_code) return;
        let duplicate = frm.doc.items.filter(i => i.item_code === row.item_code);

        if (duplicate.length > 1) {
            frappe.msgprint({
                title: "Duplicate Item",
                indicator: "red",
                message: `Item <b>${row.item_code}</b> has been entered multiple times`
            });
            frappe.model.set_value(cdt, cdn, "item_code", "");
        }
    }
});

frappe.ui.form.on('Request for Quotation', {
    refresh(frm) {
        hide_get_items_from_rfq(frm);
        hide_tools_rfq(frm);
    },
    onload(frm) {
        hide_get_items_from_rfq(frm);
        hide_tools_rfq(frm);
    },
    after_save(frm) {
        hide_get_items_from_rfq(frm);
        hide_tools_rfq(frm);
    }
});

function hide_get_items_from_rfq(frm) {
    setTimeout(() => {
        [
            'Opportunity',
            'Possible Supplier'
        ].forEach(btn => {
            frm.remove_custom_button(btn, 'Get Items From');
        });
    }, 200);
}
function hide_tools_rfq(frm) {
    setTimeout(() => {
        [
            'Get Suppliers',
            'Link to Material Requests',
            'Send Emails to Suppliers',
            'Download PDF'
        ].forEach(btn => {
            frm.remove_custom_button(btn, 'Tools');
        });
    }, 200);
}


frappe.ui.form.on('Request for Quotation', {
    before_cancel(frm) {
        if (!frm.doc.custom_cancel_reason) {
            frappe.validated = false;
            frappe.prompt(
                [
                    {
                        fieldname: 'reason',
                        fieldtype: 'Small Text',
                        label: 'Cancel Reason',
                        reqd: 1
                    }
                ],
                (values) => {
                    frappe.call({
                        method: "jain_machine_tools.api.rfq.cancel_with_reason",
                        args: {
                            docname: frm.doc.name,
                            reason: values.reason
                        },
                        callback: () => {
                            frappe.show_alert({
                                message: __('Request for Quotation Cancelled'),
                                indicator: 'red'
                            });
                            frm.reload_doc();
                        }
                    });
                },
                __('Cancel Request for Quotation'),
                __('Cancel')
            );
        }
    }
});

frappe.ui.form.on('Request for Quotation', {
    refresh(frm) {
        toggle_cancel_reason(frm);
    },
    onload_post_render(frm) {
        toggle_cancel_reason(frm);
    }
});

function toggle_cancel_reason(frm) {
    if (frm.doc.docstatus === 2) {
        frm.set_df_property('custom_cancel_reason', 'hidden', 0);
    } else {
        frm.set_df_property('custom_cancel_reason', 'hidden', 1);
    }
}

