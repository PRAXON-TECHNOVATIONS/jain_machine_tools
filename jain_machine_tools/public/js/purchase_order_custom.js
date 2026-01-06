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
    },

    item_code: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    price_list_rate: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    custom_non_standard_percentage: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    custom_discount_percent: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    custom_extra_non_standard_amount: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    custom_handling_percentage: function(frm, cdt, cdn) { calculate_row(frm, cdt, cdn); },
    
    // Standard/Non-Standard change toggles the visblity
    custom_is_non_standard: function(frm, cdt, cdn) {
        calculate_row(frm, cdt, cdn);
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
        frm.remove_custom_button('Update Items');
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


var calculate_row = function(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if (!row.item_code) return;

    // Get Values
    let list_price = flt(row.price_list_rate);
    let is_non_standard = row.custom_is_non_standard;
    
    let ns_percent = flt(row.custom_non_standard_percentage);
    let discount_percent = flt(row.custom_discount_percent);
    let extra_ns_amt = flt(row.custom_extra_non_standard_amount);
    let handling_percent = flt(row.custom_handling_percentage);

    let discount_price = 0.0;
    let absolute_ns_price = 0.0;
    let final_rate = 0.0;

    if (is_non_standard) {
        // Non-Standard Logic
        let val_after_ns_percent = list_price + (list_price * (ns_percent / 100));
        
        let discount_amount = val_after_ns_percent * (discount_percent / 100);
        discount_price = val_after_ns_percent - discount_amount;

        absolute_ns_price = discount_price + extra_ns_amt;

        let handling_amount = absolute_ns_price * (handling_percent / 100);
        final_rate = absolute_ns_price + handling_amount;        
    } else {
        // Standard Logic
        let discount_amount = list_price * (discount_percent / 100);
        discount_price = list_price - discount_amount;
        
        let handling_amount = discount_price * (handling_percent / 100);
        final_rate = discount_price + handling_amount;
        
        absolute_ns_price = 0; 
    }

    frappe.model.set_value(cdt, cdn, 'custom_discount_price', discount_price);
    frappe.model.set_value(cdt, cdn, 'custom_absolute_ns_price', absolute_ns_price);
    frappe.model.set_value(cdt, cdn, 'rate', final_rate);
};