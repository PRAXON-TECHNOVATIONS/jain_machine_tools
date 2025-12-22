frappe.ui.form.on("Material Request Item", {
    item_code(frm, cdt, cdn) {
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
