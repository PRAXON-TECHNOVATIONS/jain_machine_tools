# Copyright (c) 2025, Praxon Technovation and contributors
# For license information, please see license.txt
# Copyright (c) 2025, Praxon Technovation and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import flt

# --- CG POWER RATE DATA ---
CG_DATA = {
    "space_heater": {
        100: 2200, 112: 2200, 132: 2200,
        160: 2750, 180: 2750, 
        200: 4950, 225: 4950,
        250: 4950, 280: 4950, 
        315: 4950
    },
    "forced_cooling": {
        160: 8100, 180: 8100, 200: 19000, 225: 19000,
        250: 27750, 280: 33500, 
        315: 37000, 355: 45000
    },
    "roller_bearing": {
        160: 3850, 180: 3850, 
        200: 5850, 225: 5850,
        250: 5850, 280: 5850, 
        315: 5850, 355: 7000
    },
    "insulated_bearing_rates": {
        "160IB": 21000, "180IB": 21000, 
        "200IB": 21000, "225IB": 21000,
        "2Pole-250IB": 34700, "2Pole-280IB": 34700, "2Pole-315IB": 34700, "2Pole-355IB": 34700,
        "4Pole-250IB": 35200, "4Pole-280IB": 35200, "4Pole-315IB": 35200, "4Pole-355IB": 35200
    },
    "thermistor_rates": {
        "NONFLP-3-PTC": 2860, "NONFLP-6-PTC": 3800,
        "NONFLP-3-PTC-130": 5170, "NONFLP-3-PTC-150": 5170,
        "FLP-3-PTC-130": 5500, "FLP-6-PTC-130": 6000,
        "FLP-3-PTC-150": 6490, "FLP-6-PTC-150": 6850
    }
}

class NonStandardItemConfigurator(Document):
    def before_save(self):
        if self.manufacturer == "CG Power":
            self.calculate_cg_price()
            self.generate_cg_description()

    def calculate_cg_price(self):
        if not self.base_price: return

        base = flt(self.base_price)
        frame = int(self.frame_size) if self.frame_size else 0
        total_hike_pct = 0.0   
        total_fixed_cost = 0.0 
        rules_log = []         

        # --- Percentage Adders ---
        if self.voltage_frequency and "415V50Hz" not in self.voltage_frequency:
            pct = 5
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"Volt/Freq ({self.voltage_frequency}): +{pct}% -> Rs {amt:,.0f}")

        if self.vpi_required_cg:
            pct = 5
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"VPI Treatment: +{pct}% -> Rs {amt:,.0f}")

        if self.ip_rating == "IP56":
            pct = 5
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"IP Rating (IP56): +{pct}% -> Rs {amt:,.0f}")
        elif self.ip_rating in ["IP65", "IP66"]:
            pct = 5
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"IP Rating ({self.ip_rating}): +{pct}% -> Rs {amt:,.0f}")

        if self.class_h_insulation:
            pct = 10
            amt = (base * pct) / 100
            total_hike_pct += pct
            rules_log.append(f"Class H Insulation: +{pct}% -> Rs {amt:,.0f}")

        if self.atex_certification:
            if self.derived_base_type == "FLAMEPROOF":
                pct = 10
                amt = (base * pct) / 100
                total_hike_pct += pct
                rules_log.append(f"ATEX Certification: +{pct}% -> Rs {amt:,.0f}")
            else:
                rules_log.append("ATEX Ignored: Base Item is not FLAMEPROOF")

        # --- Fixed Cost Adders ---
        if self.space_heater_required:
            cost = self.get_frame_cost("space_heater", frame)
            total_fixed_cost += cost
            rules_log.append(f"Space Heater (Fr:{frame}): +Rs {cost:,.0f}")

        if self.forced_cooling_required:
            cost = self.get_frame_cost("forced_cooling", frame)
            total_fixed_cost += cost
            rules_log.append(f"Forced Cooling (Fr:{frame}): +Rs {cost:,.0f}")

        if self.roller_bearing_required:
            cost = self.get_frame_cost("roller_bearing", frame)
            total_fixed_cost += cost
            rules_log.append(f"Roller Bearing (Fr:{frame}): +Rs {cost:,.0f}")

        if self.insulated_bearing:
            ib_cost = CG_DATA["insulated_bearing_rates"].get(self.insulated_bearing, 0)
            if ib_cost > 0:
                total_fixed_cost += ib_cost
                rules_log.append(f"Insulated Bearing ({self.insulated_bearing}): +Rs {ib_cost:,.0f}")
            else:
                rules_log.append(f"Insulated Bearing: Rs 0 (Rate not found for {self.insulated_bearing})")

        if self.thermistor_type:
            t_cost = CG_DATA["thermistor_rates"].get(self.thermistor_type, 0)
            if t_cost > 0:
                total_fixed_cost += t_cost
                rules_log.append(f"Thermistor ({self.thermistor_type}): +Rs {t_cost:,.0f}")
            else:
                 rules_log.append(f"Thermistor: Rs 0 (Rate not found for {self.thermistor_type})")

        # --- Final ---
        percentage_amt = (base * total_hike_pct) / 100
        final_total = base + percentage_amt + total_fixed_cost

        self.calculated_price = round(final_total)
        self.applied_rules = "\n".join(rules_log) if rules_log else "Standard Specification"

    def get_frame_cost(self, key, frame):
        data = CG_DATA.get(key, {})
        if frame in data: return data[frame]
        sorted_frames = sorted(data.keys())
        for f in sorted_frames:
            if f >= frame: return data[f]
        return 0 

    # def generate_cg_description(self):
    #     desc = []
    #     desc.append(f"Base Item: {self.base_item}")
    #     desc.append(f"Frame: {self.frame_size} | Type: {self.derived_base_type}")
    #     desc.append("--- Modifications ---")
    #     if self.voltage_frequency and "415V50Hz" not in self.voltage_frequency:
    #          desc.append(f"Supply: {self.voltage_frequency}")
    #     if self.vpi_required_cg: desc.append("With VPI Treatment")
    #     if self.class_h_insulation: desc.append("Insulation: Class H")
    #     if self.ip_rating: desc.append(f"Protection: {self.ip_rating}")
    #     if self.atex_certification and self.derived_base_type == "FLAMEPROOF":
    #         desc.append("Certification: ATEX")
    #     if self.space_heater_required: desc.append("Accessory: Space Heater")
    #     if self.forced_cooling_required: desc.append("Accessory: Forced Cooling")
    #     if self.roller_bearing_required: desc.append("Bearing: Roller")
    #     if self.insulated_bearing: desc.append(f"Bearing: Insulated ({self.insulated_bearing})")
    #     if self.thermistor_type: desc.append(f"Thermistor: {self.thermistor_type}")
    #     self.final_description = "\n".join(desc)
    
    def generate_cg_description(self):
        desc = []
        
        # <b> tag se text BOLD ho jayega header jaisa
        desc.append(f"<b>Base Item:</b> {self.base_item}")
        desc.append(f"<b>Frame:</b> {self.frame_size} | <b>Type:</b> {self.derived_base_type}")
        
        # <br> ka matlab nayi line. Do baar lagaya taaki gap dikhe header ke baad
        desc.append("<br><b>--- Modifications ---</b>")

        if self.voltage_frequency and "415V50Hz" not in self.voltage_frequency:
             desc.append(f"• Supply: {self.voltage_frequency}")
        
        if self.vpi_required_cg: desc.append("• With VPI Treatment")
        if self.class_h_insulation: desc.append("• Insulation: Class H")
        if self.ip_rating: desc.append(f"• Protection: {self.ip_rating}")
        
        if self.atex_certification and self.derived_base_type == "FLAMEPROOF":
            desc.append("• Certification: ATEX")
            
        if self.space_heater_required: desc.append("• Accessory: Space Heater")
        if self.forced_cooling_required: desc.append("• Accessory: Forced Cooling")
        if self.roller_bearing_required: desc.append("• Bearing: Roller")
        if self.insulated_bearing: desc.append(f"• Bearing: Insulated ({self.insulated_bearing})")
        if self.thermistor_type: desc.append(f"• Thermistor: {self.thermistor_type}")

        # Sabko <br> se joda taaki nayi item me alag lines me aaye
        self.final_description = "<br>".join(desc)
    
    def generate_smart_item_code(self):
        suffix_list = []
        frame = self.frame_size or 0

        # 1. Voltage/Freq (e.g. 220V50Hz)
        if self.voltage_frequency and "415V50Hz" not in self.voltage_frequency:
            # Spaces hata ke clean string
            suffix_list.append(self.voltage_frequency.replace(" ", "").replace("\n", ""))

        # 2. VPI
        if self.vpi_required_cg: suffix_list.append("VPI")

        # 3. IP Rating (e.g. IP65)
        if self.ip_rating: suffix_list.append(self.ip_rating)

        # 4. Class H
        if self.class_h_insulation: suffix_list.append("CLH")

        # 5. ATEX
        if self.atex_certification and self.derived_base_type == "FLAMEPROOF":
            suffix_list.append("ATEX")

        # 6. Space Heater -> Frame + SH (e.g. 100SH)
        if self.space_heater_required: suffix_list.append(f"{frame}SH")

        # 7. Forced Cooling -> Frame + FC (e.g. 160FC)
        if self.forced_cooling_required: suffix_list.append(f"{frame}FC")

        # 8. Roller Bearing -> Frame + RB (e.g. 160RB)
        if self.roller_bearing_required: suffix_list.append(f"{frame}RB")

        # 9. Insulated Bearing -> Option Value (e.g. 4Pole-250IB)
        if self.insulated_bearing:
            suffix_list.append(self.insulated_bearing)

        # 10. Thermistor -> Option Value (e.g. FLP-3-PTC-130)
        if self.thermistor_type:
            suffix_list.append(self.thermistor_type)

        # Result Generation
        if suffix_list:
            smart_suffix = "_" + "_".join(suffix_list)
            return f"{self.base_item}{smart_suffix}"
        else:
            # Agar kuch select nahi kiya to simple NS
            return f"{self.base_item}_NS"

    @frappe.whitelist()
    def create_item_and_price(self):
        if not self.base_item: frappe.throw("Select Base Item")
        
        # Ensure calculation is up to date
        self.calculate_cg_price()
        
        # Generate Smart Item Code
        new_code = self.generate_smart_item_code()
        
        # 1. Check/Create Item
        if not frappe.db.exists("Item", new_code):
            base_doc = frappe.get_doc("Item", self.base_item)
            new_item = frappe.new_doc("Item")
            new_item.item_code = new_code
            new_item.item_name = f"{base_doc.item_name} (Non-Std)"
            new_item.item_group = base_doc.item_group
            new_item.gst_hsn_code = base_doc.gst_hsn_code
            new_item.stock_uom = base_doc.stock_uom
            # Description wo HTML wala use hoga jo fix kiya tha
            new_item.description = self.final_description
            new_item.brand = self.manufacturer
            new_item.is_stock_item = 1
            new_item.insert(ignore_permissions=True)
            frappe.msgprint(f"Created New Item: <b>{new_code}</b>")

        # 2. Update/Create Prices in BOTH Lists
        price_lists = [
            {"name": "Standard Buying", "buying": 1, "selling": 0},
            {"name": "Standard Selling", "buying": 0, "selling": 1}
        ]

        for pl in price_lists:
            self.create_or_update_price(new_code, pl["name"], pl["buying"], pl["selling"])

        self.generated_item_code = new_code
        self.save()

    def create_or_update_price(self, item_code, price_list_name, is_buying, is_selling):
        existing_price = frappe.db.get_value("Item Price", 
            {"item_code": item_code, "price_list": price_list_name}, "name")

        if existing_price:
            frappe.db.set_value("Item Price", existing_price, "price_list_rate", self.calculated_price)
        else:
            new_price = frappe.new_doc("Item Price")
            new_price.item_code = item_code
            new_price.price_list = price_list_name
            new_price.price_list_rate = self.calculated_price
            new_price.buying = is_buying
            new_price.selling = is_selling
            new_price.currency = "INR"
            new_price.insert(ignore_permissions=True)