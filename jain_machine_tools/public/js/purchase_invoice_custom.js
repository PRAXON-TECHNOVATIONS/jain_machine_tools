// Custom Purchase Invoice Item handlers for handling charges
frappe.ui.form.on('Purchase Invoice', {
	async refresh(frm) {
		if (frm.doc.docstatus !== 0 || !(frm.doc.items || []).length) {
			return;
		}

		let adjusted_rows = 0;

		for (const row of (frm.doc.items || [])) {
			const adjusted = await enforce_po_quantity_limit(frm, row.doctype, row.name, { silent: true });
			if (adjusted) {
				adjusted_rows++;
			}
		}

		if (adjusted_rows) {
			frappe.show_alert({
				message: __('PO balance ke hisaab se {0} item row ki qty adjust ki gayi.', [adjusted_rows]),
				indicator: 'orange'
			});
		}
	}
});

frappe.ui.form.on('Purchase Invoice Item', {
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
	},

	qty: function(frm, cdt, cdn) {
		enforce_po_quantity_limit(frm, cdt, cdn);
	},

	conversion_factor: function(frm, cdt, cdn) {
		enforce_po_quantity_limit(frm, cdt, cdn);
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

async function enforce_po_quantity_limit(frm, cdt, cdn, options = {}) {
	const row = locals[cdt][cdn];

	if (!row || !row.po_detail || !row.qty) {
		return false;
	}

	const response = await frappe.call({
		method: 'jain_machine_tools.overrides.purchase_order.get_purchase_order_item_invoice_status',
		args: {
			po_detail: row.po_detail,
			purchase_invoice: frm.doc.name
		}
	});

	const status = response.message || {};
	if (!status.po_detail) {
		return false;
	}

	const other_rows_stock_qty = (frm.doc.items || [])
		.filter((item) => item.name !== row.name && item.po_detail === row.po_detail)
		.reduce((total, item) => total + get_row_stock_qty(item), 0);

	const allowed_stock_qty = Math.max((status.remaining_qty || 0) - other_rows_stock_qty, 0);
	const row_stock_qty = get_row_stock_qty(row);

	if (row_stock_qty <= allowed_stock_qty + 1e-9) {
		return false;
	}

	const conversion_factor = flt(row.conversion_factor) || 1;
	const allowed_qty = allowed_stock_qty / conversion_factor;

	await frappe.model.set_value(cdt, cdn, 'qty', allowed_qty);

	if (!options.silent) {
		frappe.msgprint(
			__(
				'Row {0}: max allowed qty {1}.',
				[row.idx, allowed_qty]
			)
		);
	}

	return true;
}

function get_row_stock_qty(row) {
	return (flt(row.stock_qty) || (flt(row.qty) * (flt(row.conversion_factor) || 1)));
}

function flt(value) {
	return frappe.utils.flt(value);
}
