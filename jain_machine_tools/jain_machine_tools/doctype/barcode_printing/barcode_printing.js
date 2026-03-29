// Copyright (c) 2025, Praxon Technovation and contributors
// For license information, please see license.txt

frappe.ui.form.on("Barcode Printing", {
	refresh(frm) {
		// Set query for record field to filter Stock Entry by purpose
		frm.set_query('record', function() {
			if (frm.doc.type === 'Stock Entry') {
				return {
					query: 'jain_machine_tools.api.barcode_printing_filters.get_stock_entry_repack'
				};
			}
			// No filter for other doctypes like Purchase Receipt
			return {};
		});
	},

	type(frm) {
		// Clear record field when type changes
		frm.set_value('record', '');

		// Re-apply query filter
		frm.set_query('record', function() {
			if (frm.doc.type === 'Stock Entry') {
				return {
					query: 'jain_machine_tools.api.barcode_printing_filters.get_stock_entry_repack'
				};
			}
			return {};
		});
	},

	record(frm) {
		frm.clear_table('table_hjbk');
		frm.refresh_field('table_hjbk');
	},

	get_serial_no(frm) {
		// Validate required fields
		if (!frm.doc.type) {
			frappe.msgprint(__('Please select a Type first'));
			return;
		}

		if (!frm.doc.record) {
			frappe.msgprint(__('Please select a Record first'));
			return;
		}

		// Fetch item rows from the selected document's child table.
		frappe.call({
			method: 'jain_machine_tools.jain_machine_tools.doctype.barcode_printing.barcode_printing.get_serial_numbers',
			args: {
				record: frm.doc.record,
				doctype_name: frm.doc.type
			},
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					// Clear existing rows in table
					frm.clear_table('table_hjbk');

					// Add serial numbers to the child table
					r.message.forEach(function(row) {
						let child = frm.add_child('table_hjbk');
						child.item_code = row.item_code;
						child.serial_no = row.serial_no;
						if (row.vendor_manufacturing_date) {
							child.vendor_manufacturing_date = row.vendor_manufacturing_date;
						}
						if (row.warranty_expiry_date) {
							child.warranty_expiry_date = row.warranty_expiry_date;
						}
					});

					// Refresh the child table
					frm.refresh_field('table_hjbk');

					frappe.show_alert({
						message: __('Loaded {0} row(s)', [r.message.length]),
						indicator: 'green'
					}, 5);
				} else {
					frappe.msgprint(__('No serial numbers found in the selected record'));
				}
			}
		});
	}
});

frappe.ui.form.on("Barcode Printing Table", {
	vendor_manufacturing_date(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row.vendor_manufacturing_date) {
			return;
		}

		// Keep expiry exactly 12 months after manufacturing date.
		frappe.model.set_value(
			cdt,
			cdn,
			'warranty_expiry_date',
			frappe.datetime.add_months(row.vendor_manufacturing_date, 12)
		);
	}
});
