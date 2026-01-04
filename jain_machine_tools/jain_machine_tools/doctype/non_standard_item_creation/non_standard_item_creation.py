# Copyright (c) 2025, Jain Machine Tools and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class NonStandardItemCreation(Document):

    # ---------------------------------------------------------
    # ONLOAD (UNCHANGED – UI SUPPORT + PRICE LOGS HTML)
    # ---------------------------------------------------------
    def onload(self):
        # Render price logs HTML
        self.render_price_logs_html()

        # Original onload logic
        """Store brand configuration data for JavaScript access"""
        if not self.brand:
            return

        brand_config = frappe.db.get_value(
            "Brand Motor Configuration",
            {"brand": self.brand, "is_active": 1},
            ["name", "values_json"],
            as_dict=True,
        )

        if not brand_config or not brand_config.values_json:
            return

        try:
            brand_values = json.loads(brand_config.values_json)
        except Exception:
            return

        param_configs = frappe.get_all(
            "Supplier Parameter Selection",
            filters={"parent": brand_config.name},
            fields=[
                "parameter",
                "parameter_code",
                "motor_type_dependent",
                "frame_size_dependent",
                "pricing_type",
            ],
        )

        self.set_onload("brand_values", brand_values)
        self.set_onload("param_configs", {p.parameter: p for p in param_configs})

        if not self.parameters:
            return

        row_data = {}
        param_config_map = {p.parameter: p for p in param_configs}

        for row in self.parameters:
            if not row.parameter or row.parameter not in param_config_map:
                continue

            param_config = param_config_map[row.parameter]
            param_code = param_config.parameter_code
            if not param_code:
                continue

            values_key = f"{param_code}_values"
            available_values = brand_values.get(values_key, [])

            if not isinstance(available_values, list):
                continue

            filtered_values = []
            filtered_values_with_pricing = []

            for val_obj in available_values:
                if not isinstance(val_obj, dict) or "value" not in val_obj:
                    continue

                include = True

                if param_config.motor_type_dependent and "motor_type" in val_obj:
                    expected_type = "FLP" if self.is_flameproof_flp else "Non-FLP"
                    if val_obj["motor_type"] != expected_type:
                        include = False

                if param_config.frame_size_dependent and "frame_size" in val_obj:
                    if str(val_obj["frame_size"]) != str(self.frame_size):
                        include = False

                if include:
                    filtered_values.append(val_obj["value"])
                    filtered_values_with_pricing.append(val_obj)

            if filtered_values:
                row_data[row.name] = {
                    "options": "\n".join(filtered_values),
                    "values": filtered_values_with_pricing,
                    "config": {
                        "motor_type_dependent": param_config.motor_type_dependent,
                        "frame_size_dependent": param_config.frame_size_dependent,
                        "pricing_type": param_config.pricing_type,
                    },
                }

        self.set_onload("row_data", row_data)

    # ---------------------------------------------------------
    # VALIDATE – PRICE RECALCULATION CORE
    # ---------------------------------------------------------
    def validate(self):
        # Validate that parameters are selected
        if not self.parameters or len(self.parameters) == 0:
            frappe.throw("Please select at least one parameter before saving the configuration")

        self.recalculate_price()

    # ---------------------------------------------------------
    # ON SUBMIT – CREATE ITEM
    # ---------------------------------------------------------
    def on_submit(self):
        """Create Item automatically on submission"""
        self.create_item()

    def create_item(self):
        """Create a new Item from the Non Standard Item Creation"""
        # Check if item already exists
        if frappe.db.exists("Item", self.new_item_code):
            frappe.msgprint(f"Item {self.new_item_code} already exists")
            return

        # Get HSN/SAC code from base item
        base_item_doc = frappe.get_doc("Item", self.base_item)
        gst_hsn_code = base_item_doc.gst_hsn_code if hasattr(base_item_doc, 'gst_hsn_code') else None

        # Create new Item
        item = frappe.new_doc("Item")
        item.item_code = self.new_item_code
        item.item_name = self.new_item_code
        item.item_group = self.item_group
        item.brand = self.brand
        item.frame_size = self.frame_size
        item.is_flameproof = self.is_flameproof_flp
        item.is_non_standard = 1
        item.stock_uom = "Nos"  # Default UOM
        item.is_stock_item = 1
        item.valuation_rate = self.valuation_price

        # Set HSN/SAC code from base item
        if gst_hsn_code:
            item.gst_hsn_code = gst_hsn_code

        # Insert the item
        item.insert(ignore_permissions=True)

        frappe.msgprint(f"Item {self.new_item_code} created successfully", indicator="green")

    # ---------------------------------------------------------
    # PRICE LOGIC
    # ---------------------------------------------------------
    def recalculate_price(self):
        if not self.base_price:
            frappe.throw("Base Price is required")

        base_price = float(self.base_price)
        running_total = base_price

        item_code_parts = [self.base_item]
        description_parts = []

        # Separate percentage and absolute amount parameters
        percentage_params = []
        absolute_params = []

        for row in sorted(self.parameters, key=lambda d: d.idx or 0):
            if not row.parameter or not row.pricing_type:
                continue

            if row.pricing_type == "Percentage":
                percentage_params.append(row)
            elif row.pricing_type == "Fixed Amount":
                absolute_params.append(row)

        # Step 1: Add all percentage values to base price
        for row in percentage_params:
            percent = float(row.price_percentage or 0)
            increment = (base_price * percent) / 100
            running_total += increment

            # Add to item code
            if row.parameter_code and row.selected_value:
                item_code_parts.append(f"{row.parameter_code}-{row.selected_value}")

            # Add to description
            description_parts.append(f"{row.parameter} {percent}% - ₹{increment:,.2f}")

        # Add discount line to description (always 0% for Non Standard Item Creation)
        description_parts.append(f"Discount 0%")

        # Step 2: Add all absolute amount values
        for row in absolute_params:
            increment = float(row.price_amount or 0)
            running_total += increment

            # Add to item code
            if row.parameter_code and row.selected_value:
                item_code_parts.append(f"{row.parameter_code}-{row.selected_value}")

            # Add to description
            description_parts.append(f"{row.parameter} ₹{increment:,.2f}")

        # Set final values (no discount applied to Non Standard Item Creation)
        self.valuation_price = round(running_total, 2)
        self.discount_percentage = 0  # Always 0 for Non Standard Item Creation
        self.new_item_code = "_".join(item_code_parts)

        # Build description
        desc_text = f"Base Price: ₹{base_price:,.2f}\n"
        desc_text += "\n".join(description_parts)
        desc_text += f"\n\nFinal Price (Zero Discount): ₹{self.valuation_price:,.2f}"
        self.non_standard_item_description = desc_text

    # ---------------------------------------------------------
    # PRICE LOGS HTML RENDERING
    # ---------------------------------------------------------
    def render_price_logs_html(self):
        """Render Frappe list view style HTML for price logs"""
        # Fetch logs from Non Standard Price Log Entry
        logs = frappe.get_all(
            "Non Standard Price Log Entry",
            filters={"non_standard_item": self.name},
            fields=["*"],
            order_by="created_on desc"
        )

        if not logs or len(logs) == 0:
            self.price_log_html = """
                <div style="padding: 20px; text-align: center; color: #6c757d; font-style: italic;">
                    No price history available yet
                </div>
            """
            return

        html = """
        <style>
            .price-log-list-view {
                background: #fff;
                border: 1px solid #d1d8dd;
                border-radius: 4px;
                overflow: hidden;
            }
            .price-log-table {
                width: 100%;
                border-collapse: collapse;
            }
            .price-log-table thead {
                background: #f5f7fa;
                border-bottom: 1px solid #d1d8dd;
            }
            .price-log-table th {
                padding: 10px 12px;
                text-align: left;
                font-size: 12px;
                font-weight: 600;
                color: #6c7680;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .price-log-table tbody tr {
                border-bottom: 1px solid #ebeff2;
                transition: background-color 0.2s;
            }
            .price-log-table tbody tr:hover {
                background: #f5f7fa;
            }
            .price-log-table tbody tr:last-child {
                border-bottom: none;
            }
            .price-log-table td {
                padding: 12px;
                font-size: 13px;
                color: #36414c;
                vertical-align: middle;
            }
            .log-reference-cell {
                font-weight: 500;
                color: #2490ef;
            }
            .log-timestamp-cell {
                color: #6c7680;
                font-size: 12px;
            }
            .log-price-cell {
                font-weight: 600;
                text-align: right;
            }
            .log-discount-badge {
                display: inline-block;
                background: #fff3cd;
                border: 1px solid #ffc107;
                color: #856404;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 500;
            }
            .log-user-cell {
                color: #6c7680;
                font-size: 12px;
            }
            .log-description-icon {
                cursor: pointer;
                color: #2490ef;
                transition: color 0.2s;
            }
            .log-description-icon:hover {
                color: #1976d2;
            }
        </style>
        <div class="price-log-list-view">
            <table class="price-log-table">
                <thead>
                    <tr>
                        <th>Reference</th>
                        <th>Created On</th>
                        <th>Created By</th>
                        <th>Discount</th>
                        <th style="text-align: right;">ZDNS Price ( Zero Discount Non Std Price )</th>
                        <th style="text-align: right;">Final Price</th>
                        <th style="text-align: center; width: 50px;">Details</th>
                    </tr>
                </thead>
                <tbody>
        """

        for log in logs:
            # Format created_on timestamp
            from frappe.utils import format_datetime
            created_on_str = format_datetime(log.created_on) if log.created_on else "N/A"

            # Get created by user full name
            created_by_name = frappe.db.get_value("User", log.created_by, "full_name") if log.created_by else "System"

            # Format reference
            reference_display = f"{log.reference_doctype}: {log.reference_name}" if log.reference_doctype and log.reference_name else "Direct Creation"

            # Format discount info
            discount_display = "-"
            if log.discount_percentage and log.discount_percentage > 0:
                discount_display = f'<span class="log-discount-badge">{log.discount_percentage}% after {log.discount_parameter or "N/A"}</span>'

            # Format prices
            valuation_price = frappe.utils.fmt_money(log.valuation_price or 0, currency="INR")
            final_price = frappe.utils.fmt_money(log.final_price or 0, currency="INR")

            # Parse description into structured data
            description_lines = (self.non_standard_item_description or "No description available").split('\n')

            # Build structured breakdown data
            import json
            breakdown_data = {
                'base_price': self.base_price or 0,
                'items': [],
                'final_price': log.final_price or 0,
                'valuation_price': log.valuation_price or 0,
                'discount_percentage': log.discount_percentage or 0,
                'discount_parameter': log.discount_parameter or ''
            }

            for line in description_lines:
                line = line.strip()
                if line and not line.startswith('Base Price:') and not line.startswith('Final Price') and not line.startswith('Discount 0%'):
                    breakdown_data['items'].append(line)

            breakdown_json = json.dumps(breakdown_data).replace('"', '&quot;').replace("'", "&#39;")

            html += f"""
                    <tr>
                        <td class="log-reference-cell">{reference_display}</td>
                        <td class="log-timestamp-cell">{created_on_str}</td>
                        <td class="log-user-cell">{created_by_name}</td>
                        <td>{discount_display}</td>
                        <td class="log-price-cell">{valuation_price}</td>
                        <td class="log-price-cell">{final_price}</td>
                        <td style="text-align: center;">
                            <i class="fa fa-info-circle log-description-icon"
                               onclick="show_price_breakdown('{breakdown_json}')"
                               title="View price breakdown"></i>
                        </td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        <script>
        function show_price_breakdown(data_json) {
            try {
                // Decode HTML entities
                const decoded = data_json.replace(/&quot;/g, '"').replace(/&#39;/g, "'");
                const data = JSON.parse(decoded);

                // Build beautiful breakdown HTML
                let breakdown_html = `
                    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        <!-- Header Card -->
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px 8px 0 0; color: white; margin: -15px -15px 20px -15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 11px; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">NS Price Calculation ( Final NS Price )</div>
                                    <div style="font-size: 24px; font-weight: 700;">Breakdown Details</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 11px; opacity: 0.9; text-transform: uppercase;">Final Price</div>
                                    <div style="font-size: 28px; font-weight: 800;">${format_currency(data.final_price, 'INR')}</div>
                                </div>
                            </div>
                        </div>

                        <!-- Base Price -->
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #48bb78;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 10px; color: #6c7680; text-transform: uppercase; margin-bottom: 4px;">Base Price</div>
                                    <div style="font-size: 16px; font-weight: 600; color: #36414c;">Starting Value</div>
                                </div>
                                <div style="font-size: 20px; font-weight: 700; color: #48bb78;">${format_currency(data.base_price, 'INR')}</div>
                            </div>
                        </div>

                        <!-- Parameters -->
                        <div style="margin-bottom: 15px;">
                            <div style="font-size: 12px; font-weight: 700; color: #36414c; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                                <i class="fa fa-calculator" style="color: #667eea;"></i>
                                <span>Applied Parameters</span>
                            </div>
                `;

                // Add each parameter item
                data.items.forEach((item, idx) => {
                    // Check if it's a percentage (always positive) or contains negative indicator
                    const isPercentage = item.includes('%');
                    const hasNegativeAmount = item.match(/-₹/) || item.startsWith('Discount -');
                    const isPositive = isPercentage || !hasNegativeAmount;
                    const color = isPositive ? '#2e7d32' : '#c62828';
                    const bgColor = isPositive ? '#e8f5e9' : '#ffebee';
                    const icon = isPositive ? 'fa-plus-circle' : 'fa-minus-circle';

                    breakdown_html += `
                        <div style="background: ${bgColor}; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid ${color};">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <i class="fa ${icon}" style="color: ${color}; font-size: 16px;"></i>
                                <div style="flex: 1; font-size: 13px; font-weight: 500; color: #36414c;">${item}</div>
                            </div>
                        </div>
                    `;
                });

                breakdown_html += `
                        </div>

                        <!-- Valuation Price -->
                        <div style="background: #e3f2fd; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #2196f3;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 10px; color: #1565c0; text-transform: uppercase; margin-bottom: 4px;">Valuation Price</div>
                                    <div style="font-size: 14px; font-weight: 600; color: #1976d2;">Price Before Discount</div>
                                </div>
                                <div style="font-size: 20px; font-weight: 700; color: #2196f3;">${format_currency(data.valuation_price, 'INR')}</div>
                            </div>
                        </div>
                `;

                // Add discount section if applicable
                if (data.discount_percentage > 0) {
                    const discount_amount = data.valuation_price - data.final_price;
                    breakdown_html += `
                        <!-- Discount Applied -->
                        <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #ffc107;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <div>
                                    <div style="font-size: 10px; color: #856404; text-transform: uppercase; margin-bottom: 4px;">Discount Amount</div>
                                    <div style="font-size: 14px; font-weight: 600; color: #856404;">Discount applied ${data.discount_percentage}% after NS%</div>
                                </div>
                                <div style="font-size: 18px; font-weight: 700; color: #f57c00;">-${format_currency(discount_amount, 'INR')}</div>
                            </div>
                        </div>
                    `;
                }

                breakdown_html += `
                        <!-- Final Total -->
                        <div style="background: linear-gradient(135deg, #48bb78 0%, #2e7d32 100%); padding: 18px; border-radius: 6px; color: white;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 11px; opacity: 0.9; text-transform: uppercase; margin-bottom: 4px;">NS Price ( Final Non Std Item Price )</div>
                                    <div style="font-size: 16px; font-weight: 600;">Total Price</div>
                                </div>
                                <div style="font-size: 26px; font-weight: 800;">${format_currency(data.final_price, 'INR')}</div>
                            </div>
                        </div>
                    </div>
                `;

                // Show dialog
                frappe.msgprint({
                    title: '<i class="fa fa-calculator"></i> Price Breakdown',
                    message: breakdown_html,
                    indicator: 'blue',
                    primary_action: {
                        label: 'Close',
                        action: function(dialog) {
                            dialog.hide();
                        }
                    }
                });

            } catch (e) {
                console.error('Error parsing breakdown data:', e);
                frappe.msgprint({
                    title: 'Error',
                    message: 'Could not load price breakdown.',
                    indicator: 'red'
                });
            }
        }
        </script>
        """

        self.price_log_html = html


# ---------------------------------------------------------
# WHITELISTED API METHOD FOR DIALOG CREATION
# ---------------------------------------------------------
@frappe.whitelist()
def create_from_dialog(doc_data):
    """Create Non Standard Item Creation from dialog with price logs"""
    import json

    # Parse JSON if string
    if isinstance(doc_data, str):
        doc_data = json.loads(doc_data)

    # Create new document
    doc = frappe.new_doc("Non Standard Item Creation")

    # Set main fields
    doc.base_item = doc_data.get("base_item")
    doc.brand = doc_data.get("brand")
    doc.item_group = doc_data.get("item_group")
    doc.frame_size = doc_data.get("frame_size")
    doc.is_flameproof_flp = doc_data.get("is_flameproof_flp", 0)
    doc.base_price = doc_data.get("base_price")
    doc.apply_discount_after = doc_data.get("apply_discount_after")
    doc.discount_percentage = doc_data.get("discount_percentage")

    # Add parameters
    for param in doc_data.get("parameters", []):
        doc.append("parameters", {
            "parameter": param.get("parameter"),
            "parameter_code": param.get("parameter_code"),
            "selected_value": param.get("selected_value"),
            "pricing_type": param.get("pricing_type"),
            "price_percentage": param.get("price_percentage"),
            "price_amount": param.get("price_amount")
        })

    # Insert document
    doc.insert()

    # Submit document
    doc.submit()

    # Create price log entries
    price_logs = doc_data.get("price_logs", [])

    try:
        for log in price_logs:
            log_entry = frappe.new_doc("Non Standard Price Log Entry")
            log_entry.non_standard_item = doc.name
            log_entry.reference_doctype = log.get("reference_doctype")
            log_entry.reference_name = log.get("reference_name")
            log_entry.created_by = log.get("created_by")
            log_entry.created_on = log.get("created_on")
            log_entry.discount_parameter = log.get("discount_parameter")
            log_entry.discount_percentage = log.get("discount_percentage")
            log_entry.valuation_price = log.get("valuation_price")
            log_entry.final_price = log.get("final_price")

            log_entry.insert(ignore_permissions=True, ignore_links=True)

        frappe.db.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise

    return doc


@frappe.whitelist()
def get_price_logs_html(docname):
    """Get rendered HTML for price logs"""
    doc = frappe.get_doc("Non Standard Item Creation", docname)
    doc.render_price_logs_html()
    return doc.price_log_html


@frappe.whitelist()
def update_discount(docname, apply_discount_after=None, discount_percentage=0, reference_doctype=None, reference_name=None):
    """Update discount for existing Non Standard Item Creation and create price log"""
    import json

    # Parse inputs
    discount_percentage = float(discount_percentage) if discount_percentage else 0

    # Get the document
    doc = frappe.get_doc("Non Standard Item Creation", docname)

    # Check if document is submitted
    if doc.docstatus != 1:
        frappe.throw("Document must be submitted to update discount")

    # Store old values for comparison
    old_apply_discount_after = doc.apply_discount_after
    old_discount_percentage = doc.discount_percentage
    old_valuation_price = doc.valuation_price

    # Update apply_discount_after field only (discount_percentage stays 0 for master record)
    frappe.db.set_value("Non Standard Item Creation", docname, {
        "apply_discount_after": apply_discount_after
    }, update_modified=True)

    # Calculate final price with discount for the price log entry
    base_price = float(doc.base_price)
    running_total = base_price

    # Separate percentage and absolute amount parameters
    percentage_params = []
    absolute_params = []

    for row in sorted(doc.parameters, key=lambda d: d.idx or 0):
        if not row.parameter or not row.pricing_type:
            continue

        if row.pricing_type == "Percentage":
            percentage_params.append(row)
        elif row.pricing_type == "Fixed Amount":
            absolute_params.append(row)

    # Add all percentage parameters
    for row in percentage_params:
        percent = float(row.price_percentage or 0)
        increment = (base_price * percent) / 100
        running_total += increment

    # Calculate discount based on apply_discount_after
    final_price = running_total
    discount_amount = 0

    if apply_discount_after and discount_percentage > 0:
        if apply_discount_after == "Percentage Values":
            # Apply discount after percentage parameters, before absolute parameters
            discount_amount = (running_total * discount_percentage) / 100
            final_price = running_total - discount_amount
            # Add absolute parameters AFTER discount
            for row in absolute_params:
                increment = float(row.price_amount or 0)
                final_price += increment
        elif apply_discount_after == "Absolute Amount":
            # Add absolute parameters first, then apply discount
            for row in absolute_params:
                increment = float(row.price_amount or 0)
                running_total += increment
            # Apply discount on total (percentage + absolute)
            discount_amount = (running_total * discount_percentage) / 100
            final_price = running_total - discount_amount
    else:
        # No discount - add absolute parameters normally
        for row in absolute_params:
            increment = float(row.price_amount or 0)
            final_price += increment

    final_price = round(final_price, 2)

    # Create price log entry for this change
    log_entry = frappe.new_doc("Non Standard Price Log Entry")
    log_entry.non_standard_item = doc.name
    log_entry.reference_doctype = reference_doctype
    log_entry.reference_name = reference_name
    log_entry.created_by = frappe.session.user
    log_entry.created_on = frappe.utils.now_datetime()
    log_entry.discount_parameter = apply_discount_after
    log_entry.discount_percentage = discount_percentage
    log_entry.valuation_price = doc.valuation_price  # Master record valuation price (no discount)
    log_entry.final_price = final_price  # Price with discount applied

    log_entry.insert(ignore_permissions=True, ignore_links=True)
    frappe.db.commit()

    return {
        "success": True,
        "old_price": old_valuation_price,
        "new_price": final_price,
        "message": f"Discount updated from {old_discount_percentage}% to {discount_percentage}%"
    }
