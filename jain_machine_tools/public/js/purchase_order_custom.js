// Custom Purchase Order handlers
frappe.ui.form.on('Purchase Order', {
	refresh: function(frm) {
		// Initialize custom grid icons
		if (jain_machine_tools && jain_machine_tools.grid_custom_icons) {
			jain_machine_tools.grid_custom_icons.setup(frm);
		}
	},

	items_add: function(frm, cdt, cdn) {
		// Re-initialize icons when new row is added
		setTimeout(() => {
			if (jain_machine_tools && jain_machine_tools.grid_custom_icons) {
				jain_machine_tools.grid_custom_icons.setup(frm);
			}
		}, 100);
	}
});

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
