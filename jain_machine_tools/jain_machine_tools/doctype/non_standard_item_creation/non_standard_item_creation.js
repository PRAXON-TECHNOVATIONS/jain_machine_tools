// Copyright (c) 2025, Jain Machine Tools and contributors
// For license information, please see license.txt

frappe.ui.form.on('Non Standard Item Creation', {
	onload: function (frm) {
		// Initialize parameter options storage
		if (!frm.parameter_options) {
			frm.parameter_options = {};
		}

		// Set up grid events to restore options
		setup_grid_events(frm);

	},

	refresh: function (frm) {
		// Load brand configuration data when form loads
		if (frm.doc.brand) {
			load_brand_configuration(frm);
		}

		// Load base price
		if (frm.doc.base_item && frm.doc.brand) {
			fetch_base_price(frm)
		}

		// Restore options from onload data
		setTimeout(function () {
			restore_options_from_onload(frm);
		}, 300);

		// Refresh price logs HTML if document is saved
		if (frm.doc.name && !frm.is_new()) {
			refresh_price_logs(frm);
		}
	},

	brand: function (frm) {
		// Reload brand configuration when brand changes
		if (frm.doc.brand) {
			load_brand_configuration(frm);
		}
	},

	base_item: function (frm) {
		// When base item changes, brand will auto-fetch
		// We need to wait for brand to be set before loading config
		setTimeout(function () {
			if (frm.doc.brand) {
				load_brand_configuration(frm);
			}
		}, 500);
	}
});

function setup_grid_events(frm) {
	// Hook into grid refresh to restore options
	if (frm.fields_dict.parameters && frm.fields_dict.parameters.grid) {
		const grid = frm.fields_dict.parameters.grid;

		// Override grid refresh to restore options
		const original_refresh = grid.refresh.bind(grid);
		grid.refresh = function () {
			original_refresh();
			setTimeout(function () {
				restore_options_from_onload(frm);
			}, 100);
		};
	}
}

function restore_options_from_onload(frm) {
	if (!frm.doc.parameters || !frm.doc.__onload || !frm.doc.__onload.row_data) {
		return;
	}

	const row_data = frm.doc.__onload.row_data;

	frm.doc.parameters.forEach(function (row) {
		if (!row.name || !row_data[row.name]) return;

		const data = row_data[row.name];
		const grid_row = frm.fields_dict.parameters.grid.grid_rows_by_docname[row.name];

		if (grid_row) {
			// Find the selected_value field in the row's docfields and update it
			grid_row.docfields.forEach(function (df) {
				if (df.fieldname === 'selected_value') {
					df.options = data.options;
				}
			});

			// Refresh this specific row
			grid_row.refresh();
		}
	});
}

frappe.ui.form.on('Non Standard Item Parameter', {
	parameter: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (!row.parameter || !frm.doc.brand) {
			return;
		}

		// Load parameter values and options dynamically
		load_parameter_options(frm, row);
	},

	selected_value: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (!row.selected_value || !row.name) {
			return;
		}

		// Update pricing based on selected value using onload data
		update_pricing_from_onload(frm, row);
	}
});

function load_brand_configuration(frm) {
	if (!frm.doc.brand) {
		return;
	}

	// Fetch Brand Motor Configuration
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Brand Motor Configuration',
			filters: {
				brand: frm.doc.brand,
				is_active: 1
			},
			fields: ['name', 'values_json'],
			limit: 1
		},
		callback: function (r) {
			if (r.message && r.message.length > 0) {
				frm.brand_config = r.message[0];

				// Parse values_json
				if (frm.brand_config.values_json) {
					try {
						frm.brand_values = JSON.parse(frm.brand_config.values_json);
					} catch (e) {
						console.error('Error parsing brand configuration:', e);
						frm.brand_values = {};
					}
				}

				// Refresh child table to update filters
				frm.refresh_field('parameters');
			} else {
				frappe.msgprint(__('No active Brand Motor Configuration found for {0}', [frm.doc.brand]));
				frm.brand_config = null;
				frm.brand_values = {};
			}
		}
	});
}

function fetch_base_price(frm) {
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: "Item Price",
			filters: {
				item_name: frm.doc.base_item,
				brand: frm.doc.brand
			},
			fields: ['price_list_rate'],
			limit: 1
		},
		callback: function (r) {
			if (r.message && r.message.length > 0) {
				frm.doc.base_price = r.message[0].price_list_rate
				frm.refresh_field("base_price")
			}
		}
	})
}


function load_parameter_options(frm, row) {
	// Use brand configuration data from onload
	if (!frm.doc.__onload || !frm.doc.__onload.brand_values || !frm.doc.__onload.param_configs) {
		console.log('Brand configuration not loaded');
		return;
	}

	const brand_values = frm.doc.__onload.brand_values;
	const param_configs = frm.doc.__onload.param_configs;

	// Get parameter configuration
	const param_config = param_configs[row.parameter];
	if (!param_config || !param_config.parameter_code) {
		console.log('Parameter config not found for:', row.parameter);
		return;
	}

	// Get available values from brand configuration
	const values_key = param_config.parameter_code + '_values';
	const available_values = brand_values[values_key];

	if (!available_values || !Array.isArray(available_values)) {
		console.log('No values found for parameter:', row.parameter);
		return;
	}

	// Filter values based on motor type and frame size
	let filtered_values = [];
	let filtered_values_with_pricing = [];

	available_values.forEach(function (val_obj) {
		if (!val_obj.value) return;

		let include = true;

		// Filter by motor type
		if (param_config.motor_type_dependent && val_obj.motor_type) {
			const expected_type = frm.doc.is_flameproof_flp ? 'FLP' : 'Non-FLP';
			if (val_obj.motor_type !== expected_type) {
				include = false;
			}
		}

		// Filter by frame size
		if (param_config.frame_size_dependent && val_obj.frame_size) {
			if (frm.doc.frame_size && val_obj.frame_size != frm.doc.frame_size) {
				include = false;
			}
		}

		if (include && filtered_values.indexOf(val_obj.value) === -1) {
			filtered_values.push(val_obj.value);
			filtered_values_with_pricing.push(val_obj);
		}
	});

	if (filtered_values.length === 0) {
		console.log('No matching values after filtering');
		return;
	}

	const options_string = filtered_values.join('\n');

	// Initialize row_data if not exists
	if (!frm.doc.__onload.row_data) {
		frm.doc.__onload.row_data = {};
	}

	// Store data for this row
	frm.doc.__onload.row_data[row.name] = {
		options: options_string,
		values: filtered_values_with_pricing,
		config: {
			motor_type_dependent: param_config.motor_type_dependent,
			frame_size_dependent: param_config.frame_size_dependent,
			pricing_type: param_config.pricing_type
		}
	};

	// Update the select field options for this specific row only
	const grid_row = frm.fields_dict.parameters.grid.grid_rows_by_docname[row.name];
	if (grid_row) {
		// Find the selected_value field in the row's docfields and update it
		grid_row.docfields.forEach(function (df) {
			if (df.fieldname === 'selected_value') {
				df.options = options_string;
			}
		});

		// Refresh this specific row
		grid_row.refresh();
	}
}

function update_pricing_from_onload(frm, row) {
	if (!frm.doc.__onload || !frm.doc.__onload.row_data || !row.name) {
		return;
	}

	const row_data = frm.doc.__onload.row_data[row.name];
	if (!row_data || !row_data.values || !row_data.config) {
		return;
	}

	// Find the matching value object
	let matching_value = null;

	for (let val_obj of row_data.values) {
		if (val_obj.value === row.selected_value) {
			matching_value = val_obj;
			break;
		}
	}

	if (!matching_value) {
		return;
	}

	// Update pricing fields based on pricing_type
	const pricing_type = row_data.config.pricing_type || 'Percentage';

	frappe.model.set_value(row.doctype, row.name, 'pricing_type', pricing_type);

	if (pricing_type === 'Percentage') {
		frappe.model.set_value(row.doctype, row.name, 'price_percentage', matching_value.price || 0);
		frappe.model.set_value(row.doctype, row.name, 'price_amount', null);
	} else if (pricing_type === 'Fixed Amount') {
		frappe.model.set_value(row.doctype, row.name, 'price_amount', matching_value.price || 0);
		frappe.model.set_value(row.doctype, row.name, 'price_percentage', null);
	} else if (pricing_type === 'Both') {
		frappe.model.set_value(row.doctype, row.name, 'price_percentage', matching_value.price_pct || 0);
		frappe.model.set_value(row.doctype, row.name, 'price_amount', matching_value.price_amt || 0);
	}
}

function refresh_price_logs(frm) {
	// Call server to regenerate price logs HTML
	frappe.call({
		method: 'jain_machine_tools.jain_machine_tools.doctype.non_standard_item_creation.non_standard_item_creation.get_price_logs_html',
		args: {
			docname: frm.doc.name
		},
		callback: function(r) {
			if (r.message) {
				// Update the HTML field with fresh data
				frm.set_df_property('price_log_html', 'options', r.message);
				frm.refresh_field('price_log_html');
			}
		}
	});
}

