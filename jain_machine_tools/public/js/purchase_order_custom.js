// Auto-populate supplier item code in Purchase Order items child table
frappe.ui.form.on('Purchase Order Item', {
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

frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        hide_get_items_from_po(frm);
        hide_tools_po(frm);
    },
    onload(frm) {
        hide_get_items_from_po(frm);
        hide_tools_po(frm);
    },
    after_save(frm) {
        hide_get_items_from_po(frm);
        hide_tools_po(frm);
    }
});

function hide_get_items_from_po(frm) {
    setTimeout(() => {
        [
            'Material Request',
            'Product Bundle'
        ].forEach(btn => {
            frm.remove_custom_button(btn, 'Get Items From');
        });
    }, 200);
}
function hide_tools_po(frm) {
    setTimeout(() => {
        [
            'Update Rate as per Last Purchase',
            'Link to Material Request',
        ].forEach(btn => {
            frm.remove_custom_button(btn, 'Tools');
        });
    }, 200);
}
