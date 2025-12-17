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