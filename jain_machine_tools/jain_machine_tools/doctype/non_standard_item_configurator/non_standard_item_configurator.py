# Copyright (c) 2025, Praxon Technovation and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# # Rules for price increment
# PRICE_RULES = {
#     "frame_size": {80: 0, 180: 10},
#     "voltage": {"Standard": 0, "220V": 5},
#     "vpi_required": {0: 0, 1: 8},
#     "paint_type": {"Standard": 0, "Epoxy": 7},
#     "mounting": {"Standard": 0, "Floor": 3}
# }

# class NonStandardItemConfigurator(Document):

#     def before_save(self):
#         self.calculate_price()

#     def calculate_price(self):
#         if not self.base_price:
#             frappe.throw("Select Base Price first!")

#         final_price = self.get_base_price_value()
#         applied_rules_summary = []

#         for field, rules in PRICE_RULES.items():
#             value = getattr(self, field, None)

#             if field == "vpi_required":
#                 value = 1 if value else 0

#             if value in rules:
#                 perc = rules[value]
#                 amount = final_price * perc / 100
#                 final_price += amount
#                 applied_rules_summary.append(f"{field}: {perc}% → {amount:.2f}")

#         self.calculated_price = final_price
#         self.applied_rules = "\n".join(applied_rules_summary)

#     def get_base_price_value(self):
#         price_doc = frappe.get_doc("Item Price", self.base_price)
#         return price_doc.price_list_rate

#     @frappe.whitelist()
#     def create_item_and_price(self):
#         if not self.base_item:
#             frappe.throw("Select Base Item first!")

#         generated_code = f"NS-{self.base_item}-{frappe.utils.now_datetime().strftime('%Y%m%d%H%M%S')}"

#         # Create new Item
#         item = frappe.get_doc({
#             "doctype": "Item",
#             "item_code": generated_code,
#             "item_name": f"{self.base_item} Non Standard",
#             "is_stock_item": 1,
#             "item_group": "Products",
#             "stock_uom": "Nos",
#             "gst_hsn_code": "010121"
#         })
#         item.insert()
#         frappe.db.commit()

#         # Create Item Price
#         frappe.get_doc({
#             "doctype": "Item Price",
#             "item_code": generated_code,
#             "price_list": "Standard Selling",
#             "price_list_rate": self.calculated_price,
#             "selling": 1
#         }).insert()
#         frappe.db.commit()

#         # Fill fields inside doctype
#         self.generated_item_code = generated_code
#         self.final_description = (
#             f"Generated non-standard item based on {self.base_item} "
#             f"with final calculated price {self.calculated_price}"
#         )

#         self.save()
#         frappe.db.commit()

#         frappe.msgprint(f"Item {generated_code} created with price {self.calculated_price}")
#         return generated_code


# @frappe.whitelist()
# def get_base_price_query(doctype, txt, searchfield, start, page_len, filters):
#     if not filters.get("base_item"):
#         return []

#     return frappe.db.sql("""
#         SELECT name, price_list_rate
#         FROM `tabItem Price`
#         WHERE item_code=%s AND price_list='Standard Selling'
#         AND name LIKE %s
#         LIMIT %s
#     """, (filters["base_item"], f"%{txt}%", page_len), as_dict=True)

import frappe
from frappe.model.document import Document
from frappe.utils import flt, now

# --- SIEMENS FIXED RATE DATA ---
SIEMENS_DATA = {
    "voltage_adder": {71: 1470, 132: 3360, 160: 8820, 180: 12810, 225: 20160},
    "mounting_adder": {71: 1155, 132: 3360, 160: 8820, 180: 12810, 225: 29190},
    "epoxy_paint": {160: 11130, 225: 19110},
}

class NonStandardItemConfigurator(Document):

    def before_save(self):
        self.calculate_price()
        self.generate_description()

    def calculate_price(self):
        if not self.base_price:
            return

        base = flt(self.base_price)
        make = self.manufacturer
        frame = int(self.frame_size) if self.frame_size else 0
        
        total_hike_pct = 0.0   
        total_fixed_cost = 0.0 
        rules_log = []         

        # --- Conditions Check ---
        v_val = self.voltage
        f_val = self.frequency
        
        # Helper bools
        is_volt_changed_hm = v_val not in ["Standard (415V)", "380V"]
        is_freq_changed_hm = f_val == "60 Hz"
        is_volt_changed_cg = v_val not in ["Standard (415V)", "380V", "460V"]
        is_volt_changed_siemens = v_val != "Standard (415V)"
        
        # ============================================================
        # 1. VOLTAGE & FREQUENCY LOGIC
        # ============================================================
        if make == "Hindustan Electric Motors":
            if is_volt_changed_hm and is_freq_changed_hm:
                pct = 7.5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Combined Volt ({v_val}) & Freq ({f_val}): +{pct}% → ₹ {amt:,.0f}")
            else:
                if is_volt_changed_hm:
                    pct = 5
                    amt = (base * pct) / 100
                    total_hike_pct += pct
                    rules_log.append(f"Voltage ({v_val}): +{pct}% → ₹ {amt:,.0f}")
                if is_freq_changed_hm:
                    pct = 5
                    amt = (base * pct) / 100
                    total_hike_pct += pct
                    rules_log.append(f"Frequency ({f_val}): +{pct}% → ₹ {amt:,.0f}")

        elif make == "CG Power":
            if is_volt_changed_cg:
                pct = 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Voltage ({v_val}): +{pct}% → ₹ {amt:,.0f}")
            if f_val == "60 Hz":
                rules_log.append("Freq 60Hz: Free (CG Standard)")

        elif make == "Siemens":
            if is_volt_changed_siemens:
                cost = self.get_siemens_cost("voltage_adder", frame)
                total_fixed_cost += cost
                rules_log.append(f"Voltage Change (Siemens): +₹ {cost:,.0f}")

        # ============================================================
        # 2. MOUNTING LOGIC
        # ============================================================
        if self.mounting and "B3" not in self.mounting:
            if make in ["Hindustan Electric Motors", "CG Power"]:
                pct = 3 if frame <= 160 else 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Mounting ({self.mounting}): +{pct}% → ₹ {amt:,.0f}")
            elif make == "Siemens":
                cost = self.get_siemens_cost("mounting_adder", frame)
                total_fixed_cost += cost
                rules_log.append(f"Mounting (Siemens): +₹ {cost:,.0f}")

        # ============================================================
        # 3. PAINT LOGIC
        # ============================================================
        if self.paint_type == "Epoxy Paint":
            if make in ["Hindustan Electric Motors", "CG Power"]:
                pct = 3
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Epoxy Paint: +{pct}% → ₹ {amt:,.0f}")
            elif make == "Siemens":
                cost = self.get_siemens_cost("epoxy_paint", frame)
                total_fixed_cost += cost
                rules_log.append(f"Epoxy Paint (Siemens): +₹ {cost:,.0f}")

        elif self.paint_type in ["Zinc Silicate", "PU Paint (Polyurethane)", "C3 / C4 / C5 High Grade"]:
            pct = 10 if (make == "CG Power" and self.paint_type == "Zinc Silicate") else 15
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"{self.paint_type}: +{pct}% (Est.) → ₹ {amt:,.0f}")

        # ============================================================
        # 4. VPI LOGIC
        # ============================================================
        if self.vpi_required:
            is_chargeable = True
            if make == "Siemens": is_chargeable = False
            elif make == "Hindustan Electric Motors" and frame >= 250: is_chargeable = False
            elif make == "CG Power" and frame >= 280: is_chargeable = False
            
            if is_chargeable:
                pct = 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"VPI Treatment: +{pct}% → ₹ {amt:,.0f}")

        # ============================================================
        # FINAL CALCULATION
        # ============================================================
        percentage_amt = (base * total_hike_pct) / 100
        final_total = base + percentage_amt + total_fixed_cost

        self.calculated_price = round(final_total)
        self.applied_rules = "\n".join(rules_log) if rules_log else "Standard Specification"

    def generate_description(self):
        """Creates a professional looking description"""
        base_item_name = frappe.db.get_value("Item", self.base_item, "item_name") or self.base_item
        
        desc_lines = []
        desc_lines.append(f"Base Model: {base_item_name}")
        desc_lines.append(f"Frame Size: {self.frame_size} | Make: {self.manufacturer}")
        desc_lines.append("") 
        desc_lines.append("MODIFICATIONS:")

        if self.voltage != "Standard (415V)":
            desc_lines.append(f"• Voltage: {self.voltage}")
        if self.frequency != "50 Hz":
            desc_lines.append(f"• Frequency: {self.frequency}")
        if self.mounting and "B3" not in self.mounting:
            desc_lines.append(f"• Mounting: {self.mounting}")
        if self.paint_type != "Standard Paint":
            desc_lines.append(f"• Paint Type: {self.paint_type}")
        if self.vpi_required:
            desc_lines.append("• VPI: With VPI Treatment")

        self.final_description = "\n".join(desc_lines)

    def get_siemens_cost(self, key, frame):
        data = SIEMENS_DATA.get(key, {})
        if frame in data: return data[frame]
        return 0

    def generate_smart_item_code(self):
        """
        Logic: [Base_Item]_[Voltage]_[Freq]_[Mounting]_[Paint]_[VPI]
        Only adds suffix if value is Non-Standard.
        """
        suffix_list = []

        # 1. Voltage
        # Standard 415V gets ignored
        if "380V" in self.voltage: suffix_list.append("380V")
        elif "460V" in self.voltage: suffix_list.append("460V")
        elif "690V" in self.voltage: suffix_list.append("690V")
        elif "Dual" in self.voltage: suffix_list.append("DUAL")

        # 2. Frequency
        # Standard 50Hz gets ignored
        if "60" in self.frequency: suffix_list.append("60HZ")

        # 3. Mounting
        # Standard B3 (Foot) gets ignored
        if "B5" in self.mounting: suffix_list.append("B5")
        elif "B14" in self.mounting: suffix_list.append("B14")
        elif "B35" in self.mounting: suffix_list.append("B35")
        elif "B34" in self.mounting: suffix_list.append("B34")
        elif "V1" in self.mounting: suffix_list.append("V1")

        # 4. Paint
        # Standard Paint gets ignored
        if "Epoxy" in self.paint_type: suffix_list.append("EPX")
        elif "PU" in self.paint_type: suffix_list.append("PU")
        elif "Zinc" in self.paint_type: suffix_list.append("ZN")
        elif "High Grade" in self.paint_type: suffix_list.append("C4")

        # 5. VPI
        if self.vpi_required: suffix_list.append("VPI")

        # Construct final code
        if len(suffix_list) > 0:
            # Join all parts with underscore
            smart_suffix = "_" + "_".join(suffix_list)
            return f"{self.base_item}{smart_suffix}"
        else:
            # Case where user selects all standard options but clicks create
            # Add a generic suffix to avoid duplicate error if really needed
            return f"{self.base_item}_NS"

    @frappe.whitelist()
    def create_item_and_price(self):
        if not self.base_item:
            frappe.throw("Select Base Item!")
        
        self.calculate_price()

        # Generate Smart Code
        generated_code = self.generate_smart_item_code()

        # Check if Item already exists
        if frappe.db.exists("Item", generated_code):
            # Item Exists -> Update Price Only
            msg = f"<b>Item Already Exists:</b> {generated_code}<br>"
            
            # Check/Update Price
            existing_price = frappe.db.get_value("Item Price", {"item_code": generated_code, "price_list": "Standard Buying"}, "name")
            
            if existing_price:
                frappe.db.set_value("Item Price", existing_price, "price_list_rate", self.calculated_price)
                msg += f"Price updated to: ₹ {self.calculated_price:,.2f}"
            else:
                # Create Price if missing
                new_price = frappe.new_doc("Item Price")
                new_price.item_code = generated_code
                new_price.price_list = "Standard Buying"
                new_price.price_list_rate = self.calculated_price
                new_price.buying = 1
                new_price.currency = "INR"
                new_price.insert(ignore_permissions=True)
                msg += f"New Price added: ₹ {self.calculated_price:,.2f}"

            # Update Configurator Doc
            self.generated_item_code = generated_code
            self.save()
            frappe.db.commit()
            
            frappe.msgprint(msg)
            return generated_code

        else:
            # Item DOES NOT Exist -> Create New
            base_doc = frappe.get_doc("Item", self.base_item)

            new_item = frappe.new_doc("Item")
            new_item.item_code = generated_code
            new_item.item_name = f"{base_doc.item_name} (Non-Std)"
            new_item.item_group = base_doc.item_group
            new_item.stock_uom = base_doc.stock_uom
            new_item.gst_hsn_code = base_doc.gst_hsn_code
            new_item.description = self.final_description
            new_item.brand = self.manufacturer
            new_item.is_stock_item = 1
            new_item.valuation_method = base_doc.valuation_method or "FIFO"
            new_item.insert(ignore_permissions=True)

            # Create Price
            new_price = frappe.new_doc("Item Price")
            new_price.item_code = generated_code
            new_price.price_list = "Standard Buying" 
            new_price.price_list_rate = self.calculated_price
            new_price.buying = 1
            new_price.currency = "INR"
            new_price.insert(ignore_permissions=True)

            # Update Configurator
            self.generated_item_code = generated_code
            self.save()
            frappe.db.commit()

            frappe.msgprint(f"<b>New Item Created:</b> {generated_code}<br><b>Price:</b> ₹ {self.calculated_price:,.2f}")
            return generated_code