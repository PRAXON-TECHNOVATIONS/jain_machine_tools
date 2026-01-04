// Copyright (c) 2025, Jain Machine Tools and contributors
// For license information, please see license.txt

let formio_instance = null;

frappe.ui.form.on('Brand Motor Configuration', {
	refresh: function(frm) {
		// Load Form.io library (will auto-initialize when loaded)
		load_formio_library(frm);

		// Render preview when form loads
		render_preview(frm);
	},

	parameters_on_form_rendered: function(frm) {
		// Re-initialize Form.io when parameters change
		setTimeout(() => {
			if (window.Formio) {
				init_formio(frm);
			}
		}, 300);
	},

	values_json: function(frm) {
		// Update preview when values_json changes
		render_preview(frm);
	}
});

frappe.ui.form.on('Supplier Parameter Selection', {
	parameters_remove: function(frm) {
		// Re-initialize Form.io when row is removed
		setTimeout(() => {
			if (window.Formio) {
				init_formio(frm);
			}
		}, 300);
	}
});

function init_formio(frm) {

	// Only initialize if Form.io library is loaded
	if (!window.Formio) {
		console.warn('Form.io library not yet loaded');
		return;
	}

	// Get the HTML field wrapper
	const wrapper = frm.fields_dict.formio_container.$wrapper;
	if (!wrapper) {
		console.error('Form.io container field not found');
		return;
	}

	// Get all parameters
	const parameters = (frm.doc.parameters || []);

	if (parameters.length === 0) {
		wrapper.html('<div class="alert alert-info">Please add parameters in the Parameters table to configure values.</div>');
		return;
	}

	// Clear wrapper and show loading
	wrapper.html('<div class="text-center" style="padding: 40px;"><i class="fa fa-spinner fa-spin fa-2x"></i><p class="text-muted">Loading form...</p></div>');

	// Get Form.io schema from server
	frm.call({
		method: 'get_formio_schema',
		doc: frm.doc,
		callback: function(r) {
			if (r.message) {
				render_formio(frm, wrapper, r.message);
			} else {
				console.error('No schema returned from server');
				wrapper.html('<div class="alert alert-danger">Failed to load form schema. Please check console for errors.</div>');
			}
		},
		error: function(err) {
			console.error('Error fetching schema:', err);
			wrapper.html('<div class="alert alert-danger">Error loading form. Please check console for details.</div>');
		}
	});
}

function load_formio_library(frm) {
	// Check if Form.io is already loaded
	if (window.Formio) {
		// Initialize immediately if already loaded
		setTimeout(() => init_formio(frm), 100);
		return;
	}


	// Load Form.io JS
	if (!document.querySelector('script[src*="formio.full.min.js"]')) {
		const script = document.createElement('script');
		script.src = 'https://cdn.form.io/formiojs/formio.full.min.js';
		script.onload = function() {
			// Initialize form after library loads
			setTimeout(() => init_formio(frm), 100);
		};
		script.onerror = function() {
			console.error('Failed to load Form.io library from CDN');
			frappe.msgprint({
				title: 'Error',
				indicator: 'red',
				message: 'Failed to load Form.io library. Please check your internet connection.'
			});
		};
		document.head.appendChild(script);
	}
}


function render_formio(frm, wrapper, schema) {

	// Parse existing values if any
	let existing_data = {};
	if (frm.doc.values_json) {
		try {
			existing_data = JSON.parse(frm.doc.values_json);
		} catch (e) {
			console.error('Error parsing values_json:', e);
		}
	}

	// Add submit button to schema if not present
	if (!schema.components) {
		schema.components = [];
	}

	// Add a submit button at the end
	schema.components.push({
		type: 'button',
		label: 'Save Configuration',
		key: 'submit',
		action: 'submit',
		theme: 'primary',
		size: 'md'
	});

	// Clear wrapper and create form container div
	const formContainer = document.createElement('div');
	wrapper.html('');
	wrapper.append(formContainer);

	// Create Form.io instance using the pattern from reference code

	Formio.createForm(formContainer, schema, {
		buttonSettings: {
			showCancel: false,
			showSubmit: false
		},
		language: 'en'
	}).then(function(form) {
		formio_instance = form;

		// Load existing data using submission pattern
		form.submission = { data: existing_data };

		// Fix input-group wrapping issue with inline styles
		setTimeout(function() {
			const inputGroups = formContainer.querySelectorAll('.input-group');
			inputGroups.forEach(function(group) {
				group.style.flexWrap = 'nowrap';
				group.style.display = 'flex';
			});

			// Prevent tab navigation from changing URL
			const tabLinks = formContainer.querySelectorAll('.nav-tabs a, .nav-link');
			tabLinks.forEach(function(link) {
				link.addEventListener('click', function(e) {
					e.preventDefault();
					e.stopPropagation();

					// Get the tab index from href or data attribute
					const href = link.getAttribute('href');
					if (href && href.startsWith('#')) {
						// Find the tab pane
						const tabPane = formContainer.querySelector(href);
						if (tabPane) {
							// Hide all tab panes
							formContainer.querySelectorAll('.tab-pane').forEach(function(pane) {
								pane.classList.remove('active', 'show');
							});
							// Remove active from all tabs
							formContainer.querySelectorAll('.nav-link').forEach(function(navLink) {
								navLink.classList.remove('active');
							});
							// Show clicked tab
							tabPane.classList.add('active', 'show');
							link.classList.add('active');
						}
					}
					return false;
				});
			});
		}, 100);

		// Handle form submission
		form.on('submit', function(submission) {

			// Save to backend
			frm.call({
				method: 'save_formio_data',
				doc: frm.doc,
				args: {
					formio_data: submission.data
				},
				callback: function(r) {
					if (r.message && r.message.success) {
						frappe.show_alert({
							message: r.message.message,
							indicator: 'green'
						});

						// Update the JSON field
						frm.set_value('values_json', JSON.stringify(submission.data, null, 2));

						// Update preview after saving
						setTimeout(function() {
							render_preview(frm);
						}, 500);
					} else {
						frappe.msgprint({
							title: 'Error',
							indicator: 'red',
							message: r.message ? r.message.message : 'Failed to save configuration'
						});
					}
				},
				error: function(err) {
					console.error('Error saving configuration:', err);
					frappe.msgprint({
						title: 'Error',
						indicator: 'red',
						message: 'Failed to save configuration. Please check console for details.'
					});
				}
			});
		});

		// Handle form changes
		form.on('change', function({ data }) {
		});

	}).catch(function(error) {
		console.error('Error creating Form.io form:', error);
		wrapper.html('<div class="alert alert-danger"><strong>Error loading form:</strong> ' + error.message + '<br><br>Please check the console for more details.</div>');
	});
}

function render_preview(frm) {
	// Access the HTML field wrapper
	const preview_container = frm.fields_dict.preview_html.$wrapper;

	if (!preview_container) {
		console.log('Preview container not found, waiting for DOM...');
		// Try again after a delay
		setTimeout(function() {
			render_preview(frm);
		}, 1000);
		return;
	}

	// Parse values_json
	let data = {};
	if (!frm.doc.values_json) {
		preview_container.html('<div style="text-align: center; padding: 60px; color: #888;"><i class="fa fa-inbox fa-4x" style="margin-bottom: 20px; opacity: 0.3;"></i><h3>Nothing to Preview</h3><p>Please configure parameters in the "Parameter Values" tab first.</p></div>');
		return;
	}

	try {
		data = JSON.parse(frm.doc.values_json);
	} catch (e) {
		console.error('Error parsing values_json:', e);
		preview_container.html('<div class="alert alert-warning">Invalid configuration data. Please reconfigure parameters in the "Parameter Values" tab.</div>');
		return;
	}

	// Get parameter details from the parameters table
	const param_map = {};
	(frm.doc.parameters || []).forEach(function(row) {
		param_map[row.parameter_code] = {
			name: row.parameter,
			frame_size_dependent: row.frame_size_dependent,
			motor_type_dependent: row.motor_type_dependent,
			pricing_type: row.pricing_type || 'Percentage'
		};
	});

	// Build HTML preview
	let html = '<div style="padding: 20px;">';
	html += '<style>';
	html += '.config-preview { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }';
	html += '.config-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; margin-bottom: 0; }';
	html += '.config-section { background: #f8f9fa; border: 1px solid #dee2e6; border-top: none; padding: 15px; margin-bottom: 20px; }';
	html += '.config-section:last-child { border-radius: 0 0 8px 8px; }';
	html += '.param-card { background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }';
	html += '.param-title { font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 12px; border-bottom: 2px solid #667eea; padding-bottom: 8px; }';
	html += '.value-table { width: 100%; border-collapse: collapse; margin-top: 10px; }';
	html += '.value-table th { background: #f1f3f5; padding: 10px; text-align: left; font-weight: 600; font-size: 13px; color: #495057; border: 1px solid #dee2e6; }';
	html += '.value-table td { padding: 10px; border: 1px solid #dee2e6; font-size: 13px; }';
	html += '.value-table tbody tr:hover { background: #f8f9fa; }';
	html += '.badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; }';
	html += '.badge-percentage { background: #e3f2fd; color: #1976d2; }';
	html += '.badge-fixed { background: #f3e5f5; color: #7b1fa2; }';
	html += '.badge-both { background: #fff3e0; color: #f57c00; }';
	html += '.empty-state { text-align: center; padding: 40px; color: #6c757d; }';
	html += '</style>';

	html += '<div class="config-preview">';
	html += '<div class="config-header">';
	html += `<h3 style="margin: 0; font-size: 24px;">⚙️ Motor Configuration Summary</h3>`;
	html += `<p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 14px;">Brand: ${frm.doc.brand || 'Not Set'}</p>`;
	html += '</div>';

	html += '<div class="config-section">';

	let param_count = 0;

	// Iterate through data and organize by parameter
	for (let key in data) {
		if (data.hasOwnProperty(key) && key !== 'submit') {
			// Extract parameter code from key (e.g., "VF_values" -> "VF")
			const param_code = key.replace('_values', '').replace('_value', '').replace('_price', '').replace('_panel', '');

			// Skip if we've already processed this parameter or if it's a pricing-only key
			if (key.endsWith('_price') || key.endsWith('_panel') || key.includes('_pct') || key.includes('_amt')) continue;

			const param_info = param_map[param_code];
			if (!param_info) continue;

			const value = data[key];
			param_count++;

			html += '<div class="param-card">';
			html += `<div class="param-title">${param_info.name}`;

			// Add pricing type badge
			if (param_info.pricing_type === 'Percentage') {
				html += ' <span class="badge badge-percentage">% Pricing</span>';
			} else if (param_info.pricing_type === 'Fixed Amount') {
				html += ' <span class="badge badge-fixed">₹ Fixed</span>';
			} else {
				html += ' <span class="badge badge-both">% + ₹ Both</span>';
			}

			html += '</div>';

			// Check if it's an array (frame size/motor type dependent)
			if (Array.isArray(value) && value.length > 0) {
				html += '<table class="value-table">';
				html += '<thead><tr>';
				if (param_info.motor_type_dependent) {
					html += '<th>Motor Type</th>';
				}
				if (param_info.frame_size_dependent) {
					html += '<th>Frame Size</th>';
				}
				html += '<th>Value</th>';

				if (param_info.pricing_type === 'Percentage') {
					html += '<th>Percentage (%)</th>';
				} else if (param_info.pricing_type === 'Fixed Amount') {
					html += '<th>Price (₹)</th>';
				} else {
					html += '<th>Percentage (%)</th><th>Fixed Amount (₹)</th>';
				}

				html += '</tr></thead><tbody>';

				value.forEach(function(row) {
					html += '<tr>';
					if (param_info.motor_type_dependent && row.motor_type) {
						html += `<td><span style="padding: 2px 8px; background: #e3f2fd; border-radius: 4px; font-weight: 500;">${row.motor_type}</span></td>`;
					}
					if (param_info.frame_size_dependent && row.frame_size) {
						html += `<td><strong>${row.frame_size}</strong></td>`;
					}
					html += `<td>${row.value || '-'}</td>`;

					if (param_info.pricing_type === 'Percentage') {
						html += `<td>${row.price || '-'}%</td>`;
					} else if (param_info.pricing_type === 'Fixed Amount') {
						html += `<td>₹${row.price || '-'}</td>`;
					} else {
						html += `<td>${row.price_pct || '-'}%</td>`;
						html += `<td>₹${row.price_amt || '-'}</td>`;
					}

					html += '</tr>';
				});

				html += '</tbody></table>';
			} else {
				// Single value (non-frame size dependent)
				html += '<table class="value-table">';
				html += '<thead><tr><th>Value</th>';

				if (param_info.pricing_type === 'Percentage') {
					html += '<th>Percentage (%)</th>';
				} else if (param_info.pricing_type === 'Fixed Amount') {
					html += '<th>Price (₹)</th>';
				} else {
					html += '<th>Percentage (%)</th><th>Fixed Amount (₹)</th>';
				}

				html += '</tr></thead><tbody><tr>';
				html += `<td>${value || data[param_code + '_value'] || '-'}</td>`;

				if (param_info.pricing_type === 'Percentage') {
					html += `<td>${data[param_code + '_price'] || '-'}%</td>`;
				} else if (param_info.pricing_type === 'Fixed Amount') {
					html += `<td>₹${data[param_code + '_price'] || '-'}</td>`;
				} else {
					html += `<td>${data[param_code + '_price_pct'] || '-'}%</td>`;
					html += `<td>₹${data[param_code + '_price_amt'] || '-'}</td>`;
				}

				html += '</tr></tbody></table>';
			}

			html += '</div>';
		}
	}

	if (param_count === 0) {
		html += '<div class="empty-state">';
		html += '<i class="fa fa-inbox fa-3x" style="color: #dee2e6; margin-bottom: 15px;"></i>';
		html += '<p>No configuration data found.</p>';
		html += '</div>';
	}

	html += '</div>'; // config-section
	html += '</div>'; // config-preview
	html += '</div>';

	preview_container.html(html);
}
