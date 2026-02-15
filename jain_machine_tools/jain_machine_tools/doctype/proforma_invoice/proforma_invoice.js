// Copyright (c) 2026, Jain Machine Tools and contributors
// For license information, please see license.txt

frappe.ui.form.on('Proforma Invoice', {
	setup: function(frm) {
		// Setup similar to Quotation/Sales Order
		frm.custom_make_buttons = {
			'Sales Order': 'Sales Order'
		};

		frm.set_query("customer", function() {
			return {
				filters: {
					"disabled": 0
				}
			};
		});
	},

	refresh: function(frm) {
		// Initialize custom grid icons if available
		if (jain_machine_tools && jain_machine_tools.grid_custom_icons) {
			jain_machine_tools.grid_custom_icons.setup(frm);
		}

		// Add Sales Order button if submitted and no SO created yet
		if (frm.doc.docstatus === 1 && !frm.doc.sales_order) {
			frm.add_custom_button(__('Sales Order'), function() {
				frappe.model.open_mapped_doc({
					method: "jain_machine_tools.jain_machine_tools.doctype.proforma_invoice.proforma_invoice.make_sales_order",
					frm: frm,
					callback: function(r) {
						// Update Proforma Invoice with Sales Order reference
						if (r.message) {
							frappe.call({
								method: "jain_machine_tools.jain_machine_tools.doctype.proforma_invoice.proforma_invoice.update_proforma_on_sales_order_submit",
								args: {
									proforma_invoice: frm.doc.name,
									sales_order: r.message.name,
									sales_order_date: r.message.transaction_date
								},
								callback: function() {
									frm.reload_doc();
								}
							});
						}
					}
				});
			}, __('Create'));
		}

		// Show Sales Order link if created
		if (frm.doc.sales_order) {
			frm.add_custom_button(__('View Sales Order'), function() {
				frappe.set_route("Form", "Sales Order", frm.doc.sales_order);
			});
		}

		// Show Quotation link if exists
		if (frm.doc.quotation) {
			frm.add_custom_button(__('View Quotation'), function() {
				frappe.set_route("Form", "Quotation", frm.doc.quotation);
			});
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

// Proforma Invoice Item handlers (for handling charges support)
frappe.ui.form.on('Proforma Invoice Item', {
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
