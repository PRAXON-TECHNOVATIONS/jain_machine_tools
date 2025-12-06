# Copyright (c) 2025, Praxon Technovation and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, now

# --- SIEMENS FIXED RATE DATA ---
SIEMENS_DATA = {
    "voltage_adder": {71: 1470, 80: 1785, 90: 1995, 100: 2415, 112: 3045, 132: 4830, 160: 6510, 180: 8820, 200: 12810, 225: 19110, 250: 39375, 280: 51975, 315: 70350},
    "mounting_adder": {71: 1155, 80: 1785, 90: 2415, 100: 3045, 112: 3360, 132: 3360, 160: 8820, 180: 12810, 200: 20160, 225: 29190, 250: 45675, 280: 59850, 315: 105525},
    "epoxy_paint": {71: 2835, 80: 2835, 90: 2835, 100: 4095, 112: 4095, 132: 7560, 160: 12810, 180: 12810, 200: 23940, 225: 23940, 250: 48300, 280: 63000, 315: 101850},
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
        m_val = self.mounting
        p_val = self.paint_type
        
        # Helper bools
        is_volt_changed_hm = v_val not in ["Standard (415V)", "380V"]
        is_freq_changed_hm = f_val == "60 Hz"
        # CG ke liye standard check (Note: >500V wala logic alag se handle hoga)
        is_volt_changed_cg_basic = v_val not in ["Standard (415V)", "380V", "460V", "Inverter Duty Winding (> 500V)"]
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
            # --- CG Special Logic for Inverter Winding > 500V ---
            if "Inverter Duty Winding (> 500V)" in v_val:
                if frame >= 280:
                    # Fixed Price Rule for Large Frames
                    cost = 25000
                    total_fixed_cost += cost
                    rules_log.append(f"Voltage (>500V, Fr:{frame}): +₹ {cost:,.0f}")
                else:
                    # 5% Rule for Small Frames
                    pct = 5
                    amt = (base * pct) / 100
                    total_hike_pct += pct
                    rules_log.append(f"Voltage (>500V, Fr:{frame}): +{pct}% → ₹ {amt:,.0f}")
            
            # --- Other Non-Standard Voltages (Dual, Triple, Other) ---
            elif is_volt_changed_cg_basic:
                pct = 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Voltage ({v_val}): +{pct}% → ₹ {amt:,.0f}")
            
            # 60Hz is Free for CG
            if f_val == "60 Hz":
                rules_log.append(f"Frequency ({f_val}): Free (CG Standard)")

        elif make == "Siemens":
            if is_volt_changed_siemens:
                cost = self.get_siemens_cost("voltage_adder", frame)
                total_fixed_cost += cost
                rules_log.append(f"Voltage ({v_val}) (Siemens): +₹ {cost:,.0f}")

        # ============================================================
        # 2. MOUNTING LOGIC
        # ============================================================
        
        if not m_val or ("B3" in m_val and "35" not in m_val and "34" not in m_val):
            pass 

        elif make in ["Hindustan Electric Motors", "CG Power"]:
            if "B35" in m_val or "B34" in m_val:
                pct = 3
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Mounting ({m_val}): +{pct}% → ₹ {amt:,.0f}")
            else:
                pct = 3 if frame <= 160 else 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Mounting ({m_val}): +{pct}% → ₹ {amt:,.0f}")

        elif make == "Siemens":
            cost = self.get_siemens_cost("mounting_adder", frame)
            total_fixed_cost += cost
            rules_log.append(f"Mounting ({m_val}) (Siemens): +₹ {cost:,.0f}")

        # ============================================================
        # 3. PAINT LOGIC
        # ============================================================
        if p_val == "Epoxy Paint":
            if make in ["Hindustan Electric Motors", "CG Power"]:
                pct = 3
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Epoxy Paint: +{pct}% → ₹ {amt:,.0f}")
            elif make == "Siemens":
                cost = self.get_siemens_cost("epoxy_paint", frame)
                total_fixed_cost += cost
                rules_log.append(f"Epoxy Paint (Siemens): +₹ {cost:,.0f}")

        elif p_val == "Epoxy Gel Coat":
            if make == "Hindustan Electric Motors":
                pct = 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Epoxy Gel Coat: +{pct}% → ₹ {amt:,.0f}")
            elif make == "CG Power":
                pct = 2
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Epoxy Gel Coat / Tropicalization: +{pct}% → ₹ {amt:,.0f}")
            else:
                pct = 5
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Epoxy Gel Coat: +{pct}% (Est.) → ₹ {amt:,.0f}")

        elif p_val == "PU Paint (Polyurethane)":
            if make == "Siemens":
                rules_log.append(f"{p_val} (Siemens): Free/Standard")
            else:
                pct = 15
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"{p_val}: +{pct}% (Est.) → ₹ {amt:,.0f}")

        elif p_val == "Zinc Silicate":
            if make == "CG Power":
                pct = 10
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Zinc Silicate: +{pct}% → ₹ {amt:,.0f}")
            else:
                pct = 15
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"Zinc Silicate: +{pct}% (Est.) → ₹ {amt:,.0f}")
        
        elif p_val == "C3 / C4 / C5 High Grade":
            pct = 20
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"High Grade Paint: +{pct}% → ₹ {amt:,.0f}")

        elif p_val == "Primer Only (Red Oxide)":
            rules_log.append("Primer Only: No Price Reduction")

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
            else:
                rules_log.append("VPI Treatment: Standard/Free")

        # ============================================================
        # FINAL CALCULATION
        # ============================================================
        percentage_amt = (base * total_hike_pct) / 100
        final_total = base + percentage_amt + total_fixed_cost

        self.calculated_price = round(final_total)
        self.applied_rules = "\n".join(rules_log) if rules_log else "Standard Specification"

    def generate_description(self):
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
        if self.mounting and not ("B3" in self.mounting and "35" not in self.mounting and "34" not in self.mounting):
            desc_lines.append(f"• Mounting: {self.mounting}")
        if self.paint_type != "Standard Paint":
            desc_lines.append(f"• Paint Type: {self.paint_type}")
        if self.vpi_required:
            desc_lines.append("• VPI: With VPI Treatment")

        self.final_description = "\n".join(desc_lines)

    def get_siemens_cost(self, key, frame):
        data = SIEMENS_DATA.get(key, {})
        if frame in data: return data[frame]
        
        # Fallback logic
        sorted_frames = sorted(data.keys())
        for f in sorted_frames:
            if f >= frame:
                return data[f]
        return 0

    def generate_smart_item_code(self):
        suffix_list = []

        # Voltage Suffix
        if "380V" in self.voltage: suffix_list.append("380V")
        elif "460V" in self.voltage: suffix_list.append("460V")
        elif "690V" in self.voltage: suffix_list.append("690V")
        elif "Dual" in self.voltage: suffix_list.append("DUAL")
        elif "Inverter" in self.voltage: suffix_list.append("VFD") # Added VFD suffix for Inverter Duty

        # Frequency Suffix
        if "60" in self.frequency: suffix_list.append("60HZ")

        # Mounting Suffix
        if self.mounting and "B3" in self.mounting and "35" not in self.mounting and "34" not in self.mounting:
             pass 
        else:
            if "B5" in self.mounting: suffix_list.append("B5")
            elif "B14" in self.mounting: suffix_list.append("B14")
            elif "B35" in self.mounting: suffix_list.append("B35")
            elif "B34" in self.mounting: suffix_list.append("B34")
            elif "V18" in self.mounting or "V19" in self.mounting: suffix_list.append("V18")
            elif "V1" in self.mounting: suffix_list.append("V1")

        # Paint Suffix
        if "Epoxy" in self.paint_type: suffix_list.append("EPX")
        elif "PU" in self.paint_type: suffix_list.append("PU")
        elif "Zinc" in self.paint_type: suffix_list.append("ZN")
        elif "High Grade" in self.paint_type: suffix_list.append("C4")

        # VPI Suffix
        if self.vpi_required: suffix_list.append("VPI")

        if len(suffix_list) > 0:
            smart_suffix = "_" + "_".join(suffix_list)
            return f"{self.base_item}{smart_suffix}"
        else:
            return f"{self.base_item}_NS"

    @frappe.whitelist()
    def create_item_and_price(self):
        if not self.base_item:
            frappe.throw("Select Base Item!")
        
        self.calculate_price()
        generated_code = self.generate_smart_item_code()

        if frappe.db.exists("Item", generated_code):
            msg = f"<b>Item Already Exists:</b> {generated_code}<br>"
            
            existing_price = frappe.db.get_value("Item Price", {"item_code": generated_code, "price_list": "Standard Buying"}, "name")
            
            if existing_price:
                frappe.db.set_value("Item Price", existing_price, "price_list_rate", self.calculated_price)
                msg += f"Price updated to: ₹ {self.calculated_price:,.2f}"
            else:
                new_price = frappe.new_doc("Item Price")
                new_price.item_code = generated_code
                new_price.price_list = "Standard Buying"
                new_price.price_list_rate = self.calculated_price
                new_price.buying = 1
                new_price.currency = "INR"
                new_price.insert(ignore_permissions=True)
                msg += f"New Price added: ₹ {self.calculated_price:,.2f}"

            self.generated_item_code = generated_code
            self.save()
            frappe.db.commit()
            
            frappe.msgprint(msg)
            return generated_code

        else:
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

            new_price = frappe.new_doc("Item Price")
            new_price.item_code = generated_code
            new_price.price_list = "Standard Buying" 
            new_price.price_list_rate = self.calculated_price
            new_price.buying = 1
            new_price.currency = "INR"
            new_price.insert(ignore_permissions=True)

            self.generated_item_code = generated_code
            self.save()
            frappe.db.commit()

            frappe.msgprint(f"<b>New Item Created:</b> {generated_code}<br><b>Price:</b> ₹ {self.calculated_price:,.2f}")
            return generated_code