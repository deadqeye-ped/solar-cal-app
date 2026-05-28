import streamlit as st
import pandas as pd
import math

# ตั้งค่าหน้าเว็บให้เป็นแนวกว้างและเปลี่ยนไอคอนแท็บ
st.set_page_config(page_title="Solar Cell Calculator", layout="wide", page_icon="☀️")

# ----------------- 1. ข้อมูลอ้างอิง (Data References) -----------------

# รายการเครื่องใช้ไฟฟ้าและกำลังวัตต์มาตรฐาน
APPLIANCES = {
    "เครื่องปรับอากาศ 12,000 BTU": 1000,
    "เครื่องปรับอากาศ 18,000 BTU": 1500,
    "เครื่องปรับอากาศ 24,000 BTU": 2000,
    "ตู้เย็น 10-15 คิว": 150,
    "ตู้เย็นขนาดใหญ่/Side-by-Side": 300,
    "ทีวี LED 55-65 นิ้ว": 120,
    "เครื่องซักผ้า (ฝาบน/ฝาหน้า)": 500,
    "เครื่องอบผ้า": 2500,
    "ไมโครเวฟ": 1200,
    "เตาอบไฟฟ้า": 2000,
    "ปั๊มน้ำบ้านอัตโนมัติ": 300,
    "หลอดไฟแสงสว่าง LED (ชุด)": 12,
    "คอมพิวเตอร์ทำงาน / PC": 150,
    "โน้ตบุ๊ก / Laptop": 60,
    "เครื่องทำน้ำอุ่น": 3500,
    "พัดลมตั้งพื้น / พัดลมเพดาน": 50,
    "หม้อหุงข้าวไฟฟ้า": 600
}

# ตารางราคาขายระบบ On-Grid
ON_GRID_PRICING = {
    "3k 1p": 99000, "5k 1p": 149000, "10k 1p": "สอบถามราคา", "15k 1p": "สอบถามราคา",
    "5k 3p": 169000, "10k 3p": 249000, "15k 3p": 289000, "20k 3p": 389000
}

# ตารางราคาขายระบบ Hybrid (แยกตามตัวเลือกแบตเตอรี่)
HYBRID_PRICING = {
    "5k 1p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 299000, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": "ไม่มี", "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": "ไม่มี"},
    "5k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 339000, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": "ไม่มี", "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": "ไม่มี"},
    "10k 1p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 389000, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 452000, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 515000},
    "10k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 419000, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 482000, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 545000},
    "15k 1p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": "สอบถามราคา", "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": "สอบถามราคา", "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": "สอบถามราคา"},
    "15k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 479000, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 542000, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 605000},
    "20k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 629000, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 692000, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 755000}
}

# ฟังก์ชันสำหรับเลือกขนาดรุ่นอินเวอร์เตอร์ที่เหมาะสม (kW)
def get_recommended_model(kw_needed, phase_str):
    p_suffix = "1p" if "1 Phase" in phase_str else "3p"
    if kw_needed <= 3 and p_suffix == "1p": return f"3k {p_suffix}"
    elif kw_needed <= 5: return f"5k {p_suffix}"
    elif kw_needed <= 10: return f"10k {p_suffix}"
    elif kw_needed <= 15: return f"15k {p_suffix}"
    elif kw_needed <= 20: return f"20k {p_suffix}"
    else: return f"เกินขนาด 20k {p_suffix}"

# ----------------- 2. ออกแบบหน้าตาแอป (UI & Inputs) -----------------

st.title("☀️ ระบบวิเคราะห์ขนาดและคำนวณการลงทุน Solar Cell")
st.markdown("---")

st.subheader("1. ตั้งค่าตัวแปรและประเภทระบบไฟฟ้าของบ้าน")
col1, col2, col3 = st.columns(3)

with col1:
    cost_per_unit = st.number_input("ค่าไฟฟ้าเฉลี่ยต่อหน่วย (บาท)", min_value=0.0, value=5.0)
    days_per_month = st.number_input("จำนวนวันต่อเดือน (วัน)", min_value=1, value=30)
with col2:
    peak_sun_hours = st.number_input("ชั่วโมงแดดเฉลี่ยต่อวัน (Peak Sun Hours)", min_value=0.0, value=4.5)
    sys_efficiency = st.number_input("ประสิทธิภาพของระบบ (System Efficiency)", min_value=0.0, max_value=1.0, value=0.8)
with col3:
    phase = st.selectbox("เลือกประเภทระบบไฟฟ้าบ้านลูกค้า (Phase)", ["1 Phase (ไฟ 1 เฟส)", "3 Phase (ไฟ 3 เฟส)"])
    battery_option = st.selectbox("ออปชันการเลือกขนาดแบตเตอรี่ (สำหรับระบบ Hybrid)", [
        "แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)",
        "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)",
        "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)"
    ])

st.markdown("---")

st.subheader("2. โปรแกรมคำนวณโหลดไฟฟ้าแยกช่วงเวลา")
st.write("เลือกเครื่องใช้ไฟฟ้าและใส่จำนวนเพื่อคำนวณหาปริมาณการใช้ไฟรวม")

# ตัวเก็บข้อมูลรายการชั่วคราว (Session State) เพื่อไม่ให้หายเวลาโหลดหน้าใหม่
if 'load_items' not in st.session_state:
    st.session_state.load_items = []
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

# ฟอร์มสำหรับกดเพิ่มเครื่องใช้ไฟฟ้า
with st.form("add_appliance_form"):
    c_app, c_num, c_day, c_night = st.columns([3, 1, 1, 1])
    with c_app:
        selected_app = st.selectbox("เลือกเครื่องใช้ไฟฟ้า", ["-- เลือกเครื่องใช้ไฟฟ้า --"] + list(APPLIANCES.keys()))
    with c_num:
        num_units = st.number_input("จำนวน (เครื่อง)", min_value=1, value=1)
    with c_day:
        hours_day = st.number_input("ใช้งานกลางวัน (ชม.)", min_value=0, max_value=24, value=0)
    with c_night:
        hours_night = st.number_input("ใช้งานกลางคืน (ชม.)", min_value=0, max_value=24, value=0)
    
    add_btn = st.form_submit_button("➕ เพิ่มเครื่องใช้ไฟฟ้าลงในรายการ")
    
    # เมื่อกดปุ่มเพิ่มข้อมูล ให้คำนวณกำลังไฟฟ้าและเก็บค่าไว้
    if add_btn and selected_app != "-- เลือกเครื่องใช้ไฟฟ้า --":
        watt = APPLIANCES[selected_app]
        wh_day = watt * num_units * hours_day
        wh_night = watt * num_units * hours_night
        total_wh = wh_day + wh_night
        total_kwh = total_wh / 1000
        
        st.session_state.load_items.append({
            "เครื่องใช้ไฟฟ้า": selected_app,
            "กำลังไฟฟ้า (วัตต์)": watt,
            "จำนวน (เครื่อง)": num_units,
            "ใช้งานกลางวัน (ชม.)": hours_day,
            "ใช้งานกลางคืน (ชม.)": hours_night,
            "พลังงานกลางวัน (Wh)": wh_day,
            "พลังงานกลางคืน (Wh)": wh_night,
            "รวมพลังงานต่อวัน (Wh)": total_wh,
            "รวมต่อวัน (หน่วย หรือ kWh)": total_kwh
        })
        st.session_state.calculated = False # เมื่อเพิ่มของใหม่ ให้เคลียร์สถานะกดคำนวณ เพื่อให้ลูกค้ากดใหม่อีกครั้ง

# แสดงตารางรายการที่กดเพิ่มเข้ามาแล้ว
if st.session_state.load_items:
    df_load = pd.DataFrame(st.session_state.load_items)
    st.dataframe(df_load)
    
    if st.button("🗑️ ล้างรายการทั้งหมด"):
        st.session_state.load_items = []
        st.session_state.calculated = False
        st.rerun()
else:
    st.info("💡 กรุณาเพิ่มรายการเครื่องใช้ไฟฟ้าด้านบน เพื่อเริ่มต้นการวิเคราะห์ระบบ")

st.markdown("---")

# ปุ่มกดสำหรับคำนวณผลลัพธ์แดชบอร์ดสรุปผล
calc_btn = st.button("🔮 กดคำนวณผลลัพธ์ระบบ Solar Cell", type="primary", use_container_width=True)
if calc_btn:
    if not st.session_state.load_items:
        st.warning("⚠️ ไม่สามารถคำนวณได้ เนื่องจากยังไม่มีรายการเครื่องใช้ไฟฟ้าในตาราง!")
    else:
        st.session_state.calculated = True

# ----------------- 3. ส่วนประมวลผลสูตรคำนวณย้อนกลับและการแสดงผล Dashboard -----------------
st.subheader("3. รายงานการวิเคราะห์และดึงราคาขายระบบ (Dashboard)")

# ตั้งค่าเริ่มต้นกรณีที่ยังไม่ได้กดปุ่มคำนวณผลลัพธ์
kw_ongrid_needed_str = "---"
kw_hybrid_needed_str = "---"
model_ongrid = "---"
model_hybrid = "---"
gen_ongrid_month_str = "---"
gen_hybrid_month_str = "---"
save_ongrid_month_str = "---"
save_hybrid_month_str = "---"
price_ongrid_str = "---"
price_hybrid_str = "---"
payback_ongrid_str = "---"
payback_hybrid_str = "---"

# ถ้าผู้ใช้กดคำนวณเรียบร้อยแล้ว ให้เริ่มคำนวณสูตรคณิตศาสตร์จริงแทนค่าว่าง
if st.session_state.calculated and st.session_state.load_items:
    df_load = pd.DataFrame(st.session_state.load_items)
    
    sum_wh_day = df_load["พลังงานกลางวัน (Wh)"].sum()
    sum_wh_night = df_load["พลังงานกลางคืน (Wh)"].sum()
    kwh_day = sum_wh_day / 1000
    kwh_night = sum_wh_night / 1000
    total_kwh_day = kwh_day + kwh_night

    # สูตรที่ A. ขนาดกำลังผลิตคํานวณจริงขั้นต่ำ (kW)
    kw_ongrid_needed = kwh_day / (peak_sun_hours * sys_efficiency)
    kw_hybrid_needed = total_kwh_day / (peak_sun_hours * sys_efficiency)
    
    kw_ongrid_needed_str = f"{kw_ongrid_needed:.3f} kW"
    kw_hybrid_needed_str = f"{kw_hybrid_needed:.3f} kW"

    # สูตรที่ B. ขนาดรุ่นของระบบที่แนะนำขาย
    model_ongrid = get_recommended_model(kw_ongrid_needed, phase)
    model_hybrid = get_recommended_model(kw_hybrid_needed, phase)

    # สิ่งที่หายไป 2.1: ปริมาณไฟฟ้าที่คาดว่าผลิตได้จริง (หน่วย / เดือน)
    # ผลิตหน่วย/เดือน = ขนาด kW คำนวณจริง * แดด * ประสิทธิภาพ * จำนวนวัน (ซึ่งก็คือ ค่าหน่วยไฟต่อวัน * จำนวนวัน)
    gen_ongrid_month = kw_ongrid_needed * peak_sun_hours * sys_efficiency * days_per_month
    gen_hybrid_month = kw_hybrid_needed * peak_sun_hours * sys_efficiency * days_per_month
    
    gen_ongrid_month_str = f"{gen_ongrid_month:.2f} หน่วย / เดือน"
    gen_hybrid_month_str = f"{gen_hybrid_month:.2f} หน่วย / เดือน"

    # สิ่งที่หายไป 2.2: มูลค่าไฟฟ้าที่ประหยัดได้ต่อเดือน (บาท / เดือน)
    save_ongrid_month = gen_ongrid_month * cost_per_unit
    save_hybrid_month = gen_hybrid_month * cost_per_unit
    
    save_ongrid_month_str = f"{save_ongrid_month:,.2f} บาท / เดือน"
    save_hybrid_month_str = f"{save_hybrid_month:,.2f} บาท / เดือน"

    # สิ่งที่หายไป 2.3: ราคาขายสุทธิยกมาจากตารางเงื่อนไข (บาท)
    price_ongrid = ON_GRID_PRICING.get(model_ongrid, "ไม่พบข้อมูล")
    price_hybrid = HYBRID_PRICING.get(model_hybrid, {}).get(battery_option, "ไม่พบข้อมูล")
    
    if isinstance(price_ongrid, (int, float)):
        price_ongrid_str = f"{price_ongrid:,.2f} บาท"
    else:
        price_ongrid_str = str(price_ongrid)
        
    if isinstance(price_hybrid, (int, float)):
        price_hybrid_str = f"{price_hybrid:,.2f} บาท"
    else:
        price_hybrid_str = str(price_hybrid)

    # สิ่งที่หายไป 2.4: ระยะเวลาคืนทุนของระบบโดยประมาณ (ปี)
    # คืนทุน (ปี) = ราคาขายระบบ / (ประหยัดได้ต่อเดือน * 12)
    if isinstance(price_ongrid, (int, float)) and save_ongrid_month > 0:
        payback_ongrid = price_ongrid / (save_ongrid_month * 12)
        payback_ongrid_str = f"{payback_ongrid:.2f} ปี"
    else:
        payback_ongrid_str = "คำนวณไม่ได้ (ราคาเป็นแบบติดต่อสอบถาม หรือ ประหยัดเป็น 0)"

    if isinstance(price_hybrid, (int, float)) and save_hybrid_month > 0:
        payback_hybrid = price_hybrid / (save_hybrid_month * 12)
        payback_hybrid_str = f"{payback_hybrid:.2f} ปี"
    else:
        payback_hybrid_str = "คำนวณไม่ได้ (ราคาเป็นแบบติดต่อสอบถาม หรือ ประหยัดเป็น 0)"

# แสดงผลการจัดเลย์เอาต์หน้า Dashboard บล็อกซ้าย-ขวา
dash_col1, dash_col2 = st.columns(2)

with dash_col1:
    st.info("💡 **ระบบ On-Grid (เน้นประหยัดกลางวัน)**")
    st.markdown(f"- A. ขนาดกำลังผลิตคํานวณจริงขั้นต่ำ: **{kw_ongrid_needed_str}**")
    st.markdown(f"- B. ขนาดรุ่นของระบบที่แนะนำขาย: **{model_ongrid}**")
    st.markdown(f"- **ปริมาณไฟฟ้าที่คาดว่าผลิตได้จริง:** `{gen_ongrid_month_str}`")
    st.markdown(f"- **มูลค่าไฟฟ้าที่ประหยัดได้ต่อเดือน:** `{save_ongrid_month_str}`")
    st.markdown(f"- **ราคาขายสุทธิของระบบ:** ` {price_ongrid_str} `")
    st.markdown(f"- **ระยะเวลาคืนทุนโดยประมาณ:** 🔥 **{payback_ongrid_str}**")

with dash_col2:
    st.success("🔋 **ระบบ Hybrid - HW (กลางวัน + กลางคืน)**")
    st.markdown(f"- A. ขนาดกำลังผลิตคํานวณจริงขั้นต่ำ: **{kw_hybrid_needed_str}**")
    st.markdown(f"- B. ขนาดรุ่นของระบบที่แนะนำขาย: **{model_hybrid}**")
    st.markdown(f"- _ตัวเลือกขนาดแบตเตอรี่ที่ระบุ:_ *{battery_option if st.session_state.calculated else '---'}*")
    st.markdown(f"- **ปริมาณไฟฟ้าที่คาดว่าผลิตได้จริง:** `{gen_hybrid_month_str}`")
    st.markdown(f"- **มูลค่าไฟฟ้าที่ประหยัดได้ต่อเดือน:** `{save_hybrid_month_str}`")
    st.markdown(f"- **ราคาขายสุทธิของระบบ:** ` {price_hybrid_str} `")
    st.markdown(f"- **ระยะเวลาคืนทุนโดยประมาณ:** 🔥 **{payback_hybrid_str}**")