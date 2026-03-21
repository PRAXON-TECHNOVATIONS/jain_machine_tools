frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        frm.set_value('update_stock', 1);
    },
    refresh: function(frm) {
        if (!frm.doc.update_stock) {
            frm.set_value('update_stock', 1);
        }
    }
});