// Checkbox row selection, summary bar, and print defaults for Accounts Payable report

frappe.provide("jain_machine_tools.accounts_payable");

jain_machine_tools.accounts_payable = {
	summary_cols: [
		{ fieldname: "invoiced", label: "Invoiced Amount" },
		{ fieldname: "paid", label: "Paid Amount" },
		{ fieldname: "credit_note", label: "Return Amount" },
		{ fieldname: "outstanding", label: "Outstanding Amount" },
	],

	// Fieldnames to pre-tick in the Print / PDF column picker
	default_print_columns: [
		"posting_date",
		"voucher_no",
		"due_date",
		"invoiced",
		"outstanding",
		"age",
	],

	render_summary_bar: function (report) {
		const wrapper = $(report.wrapper || report.page.wrapper);
		if (wrapper.find(".ap-selection-summary").length) return;

		const bar = $(`
			<div class="ap-selection-summary" style="
				display:none;
				padding:10px 16px;
				margin-bottom:10px;
				background:var(--fg-color,#fff);
				border:1px solid var(--border-color,#d1d8dd);
				border-radius:var(--border-radius,6px);
				box-shadow:var(--card-shadow,0 1px 4px rgba(0,0,0,.08));
			">
				<div style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
					<span style="font-weight:600;color:var(--text-color,#1f272e);font-size:12px;text-transform:uppercase;letter-spacing:.5px;">
						Selected Totals
					</span>
					<span class="ap-row-count" style="font-size:11px;color:var(--text-muted,#8d99a6);"></span>
					<div class="ap-summary-values" style="display:flex;gap:24px;flex-wrap:wrap;margin-left:auto;"></div>
				</div>
			</div>
		`);

		const target = wrapper.find(".datatable, .frappe-datatable, .dt-wrapper").first();
		if (target.length) target.before(bar);
		else wrapper.find(".report-wrapper").prepend(bar);
	},

	update_summary: function (report) {
		const wrapper = $(report.wrapper || report.page.wrapper);
		const bar = wrapper.find(".ap-selection-summary");
		if (!bar.length) return;

		const dt = report.datatable;
		if (!dt) return;

		const checked = dt.rowmanager.getCheckedRows();
		if (!checked || checked.length === 0) {
			bar.hide();
			return;
		}

		const col_idx = {};
		(dt.datamanager.getColumns() || []).forEach((col, i) => {
			if (col.fieldname) col_idx[col.fieldname] = i;
			if (col.id) col_idx[col.id] = i;
		});

		const totals = {};
		jain_machine_tools.accounts_payable.summary_cols.forEach((c) => (totals[c.fieldname] = 0));

		checked.forEach((row_idx) => {
			const row = dt.datamanager.getRow(row_idx);
			if (!row) return;
			jain_machine_tools.accounts_payable.summary_cols.forEach(({ fieldname }) => {
				const idx = col_idx[fieldname];
				if (idx === undefined) return;
				const cell = row[idx];
				const val = parseFloat(cell && cell.content);
				if (!isNaN(val)) totals[fieldname] += val;
			});
		});

		const currency = frappe.defaults.get_default("currency") || "INR";
		const fmt = (v) =>
			frappe.format(v, { fieldtype: "Currency", options: currency }, { only_value: false });

		const values_html = jain_machine_tools.accounts_payable.summary_cols
			.map(
				({ fieldname, label }) => `
				<div style="display:flex;flex-direction:column;align-items:flex-end;">
					<span style="font-size:10px;color:var(--text-muted,#8d99a6);text-transform:uppercase;letter-spacing:.5px;">${__(label)}</span>
					<span style="font-size:13px;font-weight:600;color:var(--text-color,#1f272e);">${fmt(totals[fieldname])}</span>
				</div>
			`
			)
			.join(
				`<div style="width:1px;background:var(--border-color,#d1d8dd);align-self:stretch;margin:2px 0;"></div>`
			);

		bar.find(".ap-row-count").text(
			`${checked.length} row${checked.length !== 1 ? "s" : ""} selected`
		);
		bar.find(".ap-summary-values").html(values_html);
		bar.show();
	},

	patch_report_settings: function (report) {
		const s = report.report_settings;
		if (!s || s.__ap_patched) return;
		s.__ap_patched = true;

		const orig_get_datatable_options = s.get_datatable_options;
		const orig_after_render = s.after_datatable_render;

		s.get_datatable_options = function (options) {
			if (orig_get_datatable_options) options = orig_get_datatable_options(options);
			options.checkboxColumn = true;
			const existing_events = options.events || {};
			options.events = Object.assign({}, existing_events, {
				onCheckRow: function () {
					jain_machine_tools.accounts_payable.update_summary(frappe.query_report);
				},
			});
			return options;
		};

		s.after_datatable_render = function (datatable) {
			if (orig_after_render) orig_after_render(datatable);
			const r = frappe.query_report;
			jain_machine_tools.accounts_payable.render_summary_bar(r);
			jain_machine_tools.accounts_payable.update_summary(r);
		};
	},
};

// ---------------------------------------------------------------------------
// Proxy: intercept when ERPNext defines "Accounts Payable" and hook onload
// ---------------------------------------------------------------------------
(function () {
	const _reports = frappe.query_reports;

	if (typeof Proxy !== "undefined") {
		const proxy = new Proxy(_reports, {
			set: function (target, prop, value) {
				target[prop] = value;
				if (prop === "Accounts Payable" && value && !value.__ap_onload_hooked) {
					value.__ap_onload_hooked = true;
					const orig_onload = value.onload;
					value.onload = function (report) {
						if (orig_onload) orig_onload(report);
						jain_machine_tools.accounts_payable.patch_report_settings(report);
					};
				}
				return true;
			},
		});
		frappe.query_reports = proxy;
	} else {
		const interval = setInterval(function () {
			const r = frappe.query_reports["Accounts Payable"];
			if (r && !r.__ap_onload_hooked) {
				clearInterval(interval);
				r.__ap_onload_hooked = true;
				const orig_onload = r.onload;
				r.onload = function (report) {
					if (orig_onload) orig_onload(report);
					jain_machine_tools.accounts_payable.patch_report_settings(report);
				};
			}
		}, 200);
	}
})();

// ---------------------------------------------------------------------------
// Wrap frappe.ui.get_print_settings to auto-set defaults when called from
// the Accounts Payable report (detected via frappe.query_report.report_name)
// ---------------------------------------------------------------------------
(function () {
	const orig = frappe.ui.get_print_settings;
	frappe.ui.get_print_settings = function (pdf, callback, letter_head, pick_columns) {
		const report = frappe.query_report;
		if (report && report.report_name === "Accounts Payable") {
			// Use visible columns if report has run, fall back to all columns,
			// or as last resort use a hardcoded list so the picker always appears.
			if (!pick_columns || !pick_columns.length) {
				const cols = (report.columns || []).filter((c) => !c.hidden);
				pick_columns = cols.length ? cols : [
					{ label: __("Posting Date"), fieldname: "posting_date" },
					{ label: __("Voucher No"), fieldname: "voucher_no" },
					{ label: __("Party"), fieldname: "party" },
					{ label: __("Due Date"), fieldname: "due_date" },
					{ label: __("Invoiced Amount"), fieldname: "invoiced" },
					{ label: __("Paid Amount"), fieldname: "paid" },
					{ label: __("Return Amount"), fieldname: "credit_note" },
					{ label: __("Outstanding Amount"), fieldname: "outstanding" },
					{ label: __("Age (Days)"), fieldname: "age" },
				];
			}
		}

		const dialog = orig(pdf, callback, letter_head, pick_columns);

		if (!report || report.report_name !== "Accounts Payable") return dialog;

		// Mark the desired columns as checked in the MultiCheck options BEFORE
		// they render. We patch make_checkboxes on the field so that every time
		// it builds the checkbox DOM, our defaults come pre-selected. This avoids
		// any timing race with refresh_dependency / set_value promises.
		const defaults = jain_machine_tools.accounts_payable.default_print_columns;
		const field = dialog.get_field("columns");
		if (field) {
			const orig_make = field.make_checkboxes.bind(field);
			field.make_checkboxes = function () {
				(field.options || []).forEach(function (opt) {
					opt.checked = defaults.includes(opt.value);
				});
				orig_make();
			};
		}

		// Tick "Pick Columns" — triggers depends_on → field.refresh() → make_checkboxes()
		dialog.set_value("pick_columns", 1);

		return dialog;
	};
})();
