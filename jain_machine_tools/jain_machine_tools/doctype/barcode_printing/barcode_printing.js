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

		// Set query for item_code field to filter by t_warehouse or serial_no
		frm.set_query('item_code', function() {
			if (frm.doc.record && frm.doc.type === 'Stock Entry') {
				return {
					query: 'jain_machine_tools.api.barcode_printing_filters.get_items_with_t_warehouse',
					filters: {
						'stock_entry': frm.doc.record
					}
				};
			} else if (frm.doc.record && frm.doc.type === 'Purchase Receipt') {
				return {
					query: 'jain_machine_tools.api.barcode_printing_filters.get_items_with_serial_no',
					filters: {
						'purchase_receipt': frm.doc.record
					}
				};
			}
			return {};
		});
	},

	type(frm) {
		// Clear record field when type changes
		frm.set_value('record', '');
		frm.set_value('item_code', '');

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
		// Clear item_code when record changes
		frm.set_value('item_code', '');

		// Set query for item_code based on selected record
		frm.set_query('item_code', function() {
			if (frm.doc.record && frm.doc.type === 'Stock Entry') {
				return {
					query: 'jain_machine_tools.api.barcode_printing_filters.get_items_with_t_warehouse',
					filters: {
						'stock_entry': frm.doc.record
					}
				};
			} else if (frm.doc.record && frm.doc.type === 'Purchase Receipt') {
				return {
					query: 'jain_machine_tools.api.barcode_printing_filters.get_items_with_serial_no',
					filters: {
						'purchase_receipt': frm.doc.record
					}
				};
			}
			return {};
		});
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

		if (!frm.doc.item_code) {
			frappe.msgprint(__('Please select an Item Code first'));
			return;
		}

		// Fetch serial numbers from the Stock Entry or Purchase Receipt
		frappe.call({
			method: 'jain_machine_tools.jain_machine_tools.doctype.barcode_printing.barcode_printing.get_serial_numbers',
			args: {
				record: frm.doc.record,
				item_code: frm.doc.item_code,
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
					});

					// Refresh the child table
					frm.refresh_field('table_hjbk');

					frappe.show_alert({
						message: __('Loaded {0} serial number(s)', [r.message.length]),
						indicator: 'green'
					}, 5);
				} else {
					frappe.msgprint(__('No serial numbers found for this item in the selected record'));
				}
			}
		});
	}
});
