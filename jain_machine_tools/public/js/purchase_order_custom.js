// Custom Purchase Order Item handlers for handling charges
frappe.ui.form.on('Purchase Order Item', {
	item_code: function(frm, cdt, cdn) {
		// Clear handling charges when item changes
		let row = locals[cdt][cdn];
		if (row.item_code) {
			frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
			frappe.model.set_value(cdt, cdn, 'handling_charges_percentage', 0);
			frappe.model.set_value(cdt, cdn, 'handling_charges_amount', 0);
			frappe.model.set_value(cdt, cdn, 'base_rate_before_handling_charges', 0);
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
		calculate_item_handling_charges(frm, cdt, cdn);
	},

	handling_charges_percentage: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// If percentage is set to 0, clear the type
		if (row.handling_charges_percentage === 0 || !row.handling_charges_percentage) {
			frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
		}
		calculate_item_handling_charges(frm, cdt, cdn);
	},

	handling_charges_amount: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		// If amount is set to 0, clear the type
		if (row.handling_charges_amount === 0 || !row.handling_charges_amount) {
			frappe.model.set_value(cdt, cdn, 'handling_charges_type', '');
		}
		calculate_item_handling_charges(frm, cdt, cdn);
	},

	rate: function(frm, cdt, cdn) {
		// When rate changes (from discount/margin calculation), recalculate handling charges
		let row = locals[cdt][cdn];
		if (row.handling_charges_type) {
			setTimeout(() => {
				calculate_item_handling_charges(frm, cdt, cdn);
			}, 100);
		}
	}
});

function calculate_item_handling_charges(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	if (!row.handling_charges_type) {
		// No handling charges, trigger standard calculation
		frm.script_manager.trigger('calculate_taxes_and_totals');
		return;
	}

	// The calculation will be done on the server side via validation hook
	// Just trigger the recalculation
	frm.script_manager.trigger('calculate_taxes_and_totals');
}
