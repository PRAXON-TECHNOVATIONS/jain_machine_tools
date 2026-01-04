// Custom Sales Order handlers
frappe.ui.form.on('Sales Order', {
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

// Custom Sales Order Item handlers for handling charges
frappe.ui.form.on('Sales Order Item', {
	item_code: function(frm, cdt, cdn) {
		// Clear handling charges when item changes
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
			frappe.model.set_value(cdt, cdn, 'handling_charges_percentage', 0);
			frappe.model.set_value(cdt, cdn, 'handling_charges_amount', 0);
		}
	},

	handling_charges_type: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		// Clear the other field when type changes
		if (row.handling_charges_type === 'Percentage') {
			frappe.model.set_value(cdt, cdn, 'handling_charges_amount', 0);
		} else if (row.handling_charges_type === 'Amount') {
			frappe.model.set_value(cdt, cdn, 'handling_charges_percentage', 0);
		} else {
			// Clear both if no type selected
			frappe.model.set_value(cdt, cdn, 'handling_charges_percentage', 0);
			frappe.model.set_value(cdt, cdn, 'handling_charges_amount', 0);
		}

		// Trigger recalculation
		frm.script_manager.trigger('calculate_taxes_and_totals');
	},

	handling_charges_percentage: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// If percentage is set to 0, clear the type
		if (row.handling_charges_percentage === 0 || !row.handling_charges_percentage) {
			frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
		}
		frm.script_manager.trigger('calculate_taxes_and_totals');
	},

	handling_charges_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// If amount is set to 0, clear the type
		if (row.handling_charges_amount === 0 || !row.handling_charges_amount) {
			frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
		}
		frm.script_manager.trigger('calculate_taxes_and_totals');
	}
});
