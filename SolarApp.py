import streamlit as st
import pandas as pd
import math

# ตั้งค่าหน้าเว็บให้เป็นแนวกว้างและเปลี่ยนไอคอนแท็บ
st.set_page_config(page_title="Solar Cell Calculator", layout="wide", page_icon="☀️")

# ----------------- 1. ข้อมูลอ้างอิงและตั้งราคาเริ่มต้น (Session State) -----------------

# รายการเครื่องใช้ไฟฟ้าและกำลังวัตต์มาตรฐาน (ล็อกค่าให้เลือกตามนี้เท่านั้น)
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

# กำหนดรากฐานราคาระบบดั้งเดิม
if 'ongrid_prices' not in st.session_state:
    st.session_state.ongrid_prices = {
        "3k 1p": 99000.0, "5k 1p": 149000.0, "10k 1p": 0.0, "15k 1p": 0.0,
        "5k 3p": 169000.0, "10k 3p": 249000.0, "15k 3p": 289000.0, "20k 3p": 389000.0
    }

if 'hybrid_prices' not in st.session_state:
    st.session_state.hybrid_prices = {
        "5k 1p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 299000.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 0.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 0.0},
        "5k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 339000.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 0.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 0.0},
        "10k 1p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 389000.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 452000.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 515000.0},
        "10k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 419000.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 482000.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 545000.0},
        "15k 1p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 0.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 0.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 0.0},
        "15k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 479000.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 542000.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 605000.0},
        "20k 3p": {"แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)": 629000.0, "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)": 692000.0, "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)": 755000.0}
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

# ล็อกวันต่อเดือนเป็นค่าคงที่ 30 วัน
DAYS_PER_MONTH = 30

# ----------------- 2. ออกแบบหน้าตาแอป (UI & Inputs) -----------------

st.title("☀️ ระบบวิเคราะห์ขนาดและคำนวณการลงทุน Solar Cell ☀️")
st.markdown("---")

st.subheader("1. โปรแกรมคำนวณโหลดไฟฟ้าแยกช่วงเวลา")
st.write("เลือกเครื่องใช้ไฟฟ้ามาตรฐานและใส่จำนวนเพื่อคำนวณหาปริมาณการใช้ไฟรวม")

if 'load_items' not in st.session_state:
    st.session_state.load_items = []
if 'calculated' not in st.session_state:
    st.session_state.calculated = False

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
        st.session_state.calculated = False

if st.session_state.load_items:
    st.markdown("#### 📋 รายการเครื่องใช้ไฟฟ้าที่เลือกไว้")
    
    total_w_day = 0
    total_w_night = 0
    total_wh_day_sum = 0
    total_wh_night_sum = 0

    for index, item in enumerate(st.session_state.load_items):
        col_idx, col_name, col_detail, col_del = st.columns([1, 4, 6, 2])
        with col_idx:
            st.markdown(f"**{index + 1}.**")
        with col_name:
            st.markdown(f"**{item['เครื่องใช้ไฟฟ้า']}**")
        with col_detail:
            st.write(f"{item['จำนวน (เครื่อง)']} เครื่อง | กลางวัน {item['ใช้งานกลางวัน (ชม.)']} ชม. | กลางคืน {item['ใช้งานกลางคืน (ชม.)']} ชม. ({item['รวมต่อวัน (หน่วย หรือ kWh)']:.2f} หน่วย/วัน)")
        with col_del:
            if st.button(f"❌ ลบรายการนี้", key=f"del_{index}"):
                st.session_state.load_items.pop(index)
                st.session_state.calculated = False
                st.rerun()

        if item['ใช้งานกลางวัน (ชม.)'] > 0:
            total_w_day += (item['กำลังไฟฟ้า (วัตต์)'] * item['จำนวน (เครื่อง)'])
        if item['ใช้งานกลางคืน (ชม.)'] > 0:
            total_w_night += (item['กำลังไฟฟ้า (วัตต์)'] * item['จำนวน (เครื่อง)'])
            
        total_wh_day_sum += item['พลังงานกลางวัน (Wh)']
        total_wh_night_sum += item['พลังงานกลางคืน (Wh)']

    total_kwh_day_sum = total_wh_day_sum / 1000
    total_kwh_night_sum = total_wh_night_sum / 1000
    total_kwh_all_day = total_kwh_day_sum + total_kwh_night_sum

    st.markdown("##### 📊 สรุปกำลังไฟฟ้าที่เลือกใช้งานรวมทั้งหมด")
    sum_col1, sum_col2, sum_col3 = st.columns(3)
    with sum_col1:
        st.warning(f"☀️ **ตอนกลางวัน:** \n- กำลังไฟฟ้ารวม: `{total_w_day:,} วัตต์` \n- พลังงานที่ใช้: `{total_kwh_day_sum:.2f} หน่วย / วัน`")
    with sum_col2:
        st.info(f"🌙 **ตอนกลางคืน:** \n- กำลังไฟฟ้ารวม: `{total_w_night:,} วัตต์` \n- พลังงานที่ใช้: `{total_kwh_night_sum:.2f} หน่วย / วัน`")
    with sum_col3:
        st.success(f"🔋 **รวมทั้งวัน:** \n- พลังงานรวมสุทธิ: `{total_kwh_all_day:.2f} หน่วย / วัน` \n- คิดเป็นโหลดเฉลี่ย: `{(total_wh_day_sum+total_wh_night_sum):,} Wh/วัน`")
                
    st.markdown("---")
    if st.button("🗑️ ล้างรายการทั้งหมด", type="secondary"):
        st.session_state.load_items = []
        st.session_state.calculated = False
        st.rerun()
else:
    st.info("💡 กรุณาเพิ่มรายการเครื่องใช้ไฟฟ้าด้านบน เพื่อเริ่มต้นการวิเคราะห์ระบบ")

st.markdown("---")

st.subheader("2. ตั้งค่าประเภทระบบไฟฟ้าและตัวแปรของบ้าน")
col1, col2, col3 = st.columns(3)

with col1:
    cost_per_unit = st.number_input("ค่าไฟฟ้าเฉลี่ยต่อหน่วย (บาท)", min_value=0.0, value=5.0)
    phase = st.selectbox("เลือกประเภทระบบไฟฟ้าบ้านลูกค้า (Phase)", ["1 Phase (ไฟ 1 เฟส)", "3 Phase (ไฟ 3 เฟส)"])
with col2:
    peak_sun_hours = st.number_input("ชั่วโมงแดดเฉลี่ยต่อวัน (Peak Sun Hours)", min_value=0.0, value=4.5)
    battery_option = st.selectbox("ออปชันการเลือกขนาดแบตเตอรี่ (สำหรับระบบ Hybrid)", [
        "แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)",
        "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)",
        "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)"
    ])
with col3:
    sys_efficiency = st.number_input("ประสิทธิภาพของระบบ (System Efficiency)", min_value=0.0, max_value=1.0, value=0.8)

st.markdown("---")

calc_btn = st.button("🔮 กดคำนวณผลลัพธ์ระบบ Solar Cell", type="primary", use_container_width=True)
if calc_btn:
    if not st.session_state.load_items:
        st.warning("⚠️ ไม่สามารถคำนวณได้ เนื่องจากยังไม่มีรายการเครื่องใช้ไฟฟ้าในตาราง!")
    else:
        st.session_state.calculated = True

# ----------------- 3. ส่วนประมวลผลและการแสดงผล Dashboard -----------------
st.subheader("3. รายงานการวิเคราะห์และดึงราคาขายระบบ (Dashboard)")

# ตั้งค่าฟอนต์เริ่มต้นเมื่อเปิดมาครั้งแรก (ยังไม่กดคำนวณ)
kw_ongrid_html = "<span style='font-size:20px; font-weight:bold; color:#666666;'>---</span>"
kw_hybrid_html = "<span style='font-size:20px; font-weight:bold; color:#666666;'>---</span>"
model_ongrid_html = "<span style='font-size:20px; font-weight:bold; color:#666666;'>---</span>"
model_hybrid_html = "<span style='font-size:20px; font-weight:bold; color:#666666;'>---</span>"

gen_ongrid_month_str = "---"
gen_hybrid_month_str = "---"
save_ongrid_month_str = "---"
save_hybrid_month_str = "---"
price_ongrid_str = "---"
price_hybrid_str = "---"
payback_ongrid_html = "<span style='font-size:20px; font-weight:bold; color:#666666;'>---</span>"
payback_hybrid_html = "<span style='font-size:20px; font-weight:bold; color:#666666;'>---</span>"

if st.session_state.calculated and st.session_state.load_items:
    df_load = pd.DataFrame(st.session_state.load_items)
    
    sum_wh_day = df_load["พลังงานกลางวัน (Wh)"].sum()
    sum_wh_night = df_load["พลังงานกลางคืน (Wh)"].sum()
    kwh_day = sum_wh_day / 1000
    kwh_night = sum_wh_night / 1000
    total_kwh_day = kwh_day + kwh_night

    kw_ongrid_needed = kwh_day / (peak_sun_hours * sys_efficiency)
    kw_hybrid_needed = total_kwh_day / (peak_sun_hours * sys_efficiency)
    
    # ✨ ปรับตัวเลขผลลัพธ์หลักให้ ตัวหนา ใหญ่ และมีสีสันสวยงามแยกประเภทระบบ
    kw_ongrid_html = f"<span style='font-size:22px; font-weight:bold; color:#2E7D32;'>{kw_ongrid_needed:.3f} kW</span>"
    kw_hybrid_html = f"<span style='font-size:22px; font-weight:bold; color:#1565C0;'>{kw_hybrid_needed:.3f} kW</span>"

    model_ongrid = get_recommended_model(kw_ongrid_needed, phase)
    model_hybrid = get_recommended_model(kw_hybrid_needed, phase)
    
    model_ongrid_html = f"<span style='font-size:22px; font-weight:bold; color:#2E7D32;'>{model_ongrid}</span>"
    model_hybrid_html = f"<span style='font-size:22px; font-weight:bold; color:#1565C0;'>{model_hybrid}</span>"

    gen_ongrid_month = kw_ongrid_needed * peak_sun_hours * sys_efficiency * DAYS_PER_MONTH
    gen_hybrid_month = kw_hybrid_needed * peak_sun_hours * sys_efficiency * DAYS_PER_MONTH
    
    gen_ongrid_month_str = f"{gen_ongrid_month:.2f} หน่วย / เดือน"
    gen_hybrid_month_str = f"{gen_hybrid_month:.2f} หน่วย / เดือน"

    save_ongrid_month = gen_ongrid_month * cost_per_unit
    save_hybrid_month_base = gen_hybrid_month * cost_per_unit
    
    bonus_saving = 0.0
    if battery_option == "แบตเตอรี่มาตรฐาน 1 ลูก (7 kWh)":
        bonus_saving = 1000.0
    elif battery_option == "เพิ่มแบต1 (รวมเป็น 2 ลูก / 14 kWh)":
        bonus_saving = 2000.0
    elif battery_option == "เพิ่มแบต2 (รวมเป็น 3 ลูก / 21 kWh)":
        bonus_saving = 3000.0
        
    save_hybrid_month = save_hybrid_month_base + bonus_saving
    
    save_ongrid_month_str = f"{save_ongrid_month:,.2f} บาท / เดือน"
    save_hybrid_month_str = f"{save_hybrid_month:,.2f} บาท / เดือน"

    price_ongrid = st.session_state.ongrid_prices.get(model_ongrid, 0.0)
    price_hybrid = st.session_state.hybrid_prices.get(model_hybrid, {}).get(battery_option, 0.0)
    
    if price_ongrid > 0:
        price_ongrid_str = f"{price_ongrid:,.2f} บาท"
    else:
        price_ongrid_str = "สอบถามราคา / ไม่มีข้อมูลราคา"
        
    if price_hybrid > 0:
        price_hybrid_str = f"{price_hybrid:,.2f} บาท"
    else:
        price_hybrid_str = "สอบถามราคา / ไม่มีข้อมูลราคา"

    if price_ongrid > 0 and save_ongrid_month > 0:
        payback_ongrid = price_ongrid / (save_ongrid_month * 12)
        payback_ongrid_html = f"<span style='font-size:24px; font-weight:bold; color:#E65100;'>🔥 {payback_ongrid:.2f} ปี</span>"
    else:
        payback_ongrid_html = "<span style='font-size:16px; color:#c62828;'>สอบถามราคาพิเศษ</span>"

    if price_hybrid > 0 and save_hybrid_month > 0:
        payback_hybrid = price_hybrid / (save_hybrid_month * 12)
        payback_hybrid_html = f"<span style='font-size:24px; font-weight:bold; color:#E65100;'>🔥 {payback_hybrid:.2f} ปี</span>"
    else:
        payback_hybrid_html = "<span style='font-size:16px; color:#c62828;'>สอบถามราคาพิเศษ</span>"

dash_col1, dash_col2 = st.columns(2)
with dash_col1:
    st.info("💡 **ระบบ On-Grid (เน้นประหยัดกลางวัน)**")
    st.write(f"- A. ขนาดกำลังผลิตคํานวณจริงขั้นต่ำ: ", unsafe_allow_html=True)
    st.markdown(kw_ongrid_html, unsafe_allow_html=True)
    st.write(f"- B. ขนาดรุ่นของระบบที่แนะนำขาย: ", unsafe_allow_html=True)
    st.markdown(model_ongrid_html, unsafe_allow_html=True)
    st.markdown(f"- **ปริมาณไฟฟ้าที่คาดว่าผลิตได้จริง:** `{gen_ongrid_month_str}`")
    st.markdown(f"- **มูลค่าไฟฟ้าที่ประหยัดได้ต่อเดือน:** `{save_ongrid_month_str}`")
    st.markdown(f"- **ราคาขายสุทธิของระบบ:** ` {price_ongrid_str} `")
    st.write(f"- **ระยะเวลาคืนทุนโดยประมาณ:**")
    st.markdown(payback_ongrid_html, unsafe_allow_html=True)

with dash_col2:
    st.success("🔋 **ระบบ Hybrid - HW (กลางวัน + กลางคืน)**")
    st.write(f"- A. ขนาดกำลังผลิตคํานวณจริงขั้นต่ำ: ", unsafe_allow_html=True)
    st.markdown(kw_hybrid_html, unsafe_allow_html=True)
    st.write(f"- B. ขนาดรุ่นของระบบที่แนะนำขาย: ", unsafe_allow_html=True)
    st.markdown(model_hybrid_html, unsafe_allow_html=True)
    st.markdown(f"- _ตัวเลือกขนาดแบตเตอรี่ที่ระบุ:_ *{battery_option if st.session_state.calculated else '---'}*")
    st.markdown(f"- **ปริมาณไฟฟ้าที่คาดว่าผลิตได้จริง:** `{gen_hybrid_month_str}`")
    st.markdown(f"- **มูลค่าไฟฟ้าที่ประหยัดได้ต่อเดือน:** `{save_hybrid_month_str}` *(รวมมูลค่าเพิ่มจากแบตแล้ว)*")
    st.markdown(f"- **ราคาขายสุทธิของระบบ:** ` {price_hybrid_str} `")
    st.write(f"- **ระยะเวลาคืนทุนโดยประมาณ:**")
    st.markdown(payback_hybrid_html, unsafe_allow_html=True)

st.markdown("---")

# ----------------- 4. หมวดจัดการราคากลาง (Price List Management) -----------------
with st.expander("⚙️ 4. ตารางจัดการราคาขายระบบและการปรับปรุงราคา (Price List Management) - คลิกเพื่อเปิด/ปิด", expanded=False):
    st.write("แก้ไขปรับราคาขายของแต่ละรุ่นตรงช่องด้านล่างนี้")
    
    p_col1, p_col2 = st.columns(2)

    with p_col1:
        st.markdown("### 🗂️ ราคาระบบ On-Grid")
        for model_key in list(st.session_state.ongrid_prices.keys()):
            init_val = st.session_state.ongrid_prices[model_key]
            new_price = st.number_input(f"ราคาขายรุ่น {model_key} (บาท)", min_value=0.0, value=float(init_val), step=1000.0, key=f"input_ongrid_{model_key}")
            st.session_state.ongrid_prices[model_key] = new_price

    with p_col2:
        st.markdown("### 🔋 ราคาระบบ Hybrid (ตามตัวเลือกแบตเตอรี่)")
        for model_key in list(st.session_state.hybrid_prices.keys()):
            st.markdown(f"**⚙️ ขนาดรุ่นอินเวอร์เตอร์: {model_key}**")
            for bat_key in list(st.session_state.hybrid_prices[model_key].keys()):
                init_val = st.session_state.hybrid_prices[model_key][bat_key]
                new_price = st.number_input(f"└ ราคา {bat_key} (บาท)", min_value=0.0, value=float(init_val), step=1000.0, key=f"input_hy_{model_key}_{bat_key}")
                st.session_state.hybrid_prices[model_key][bat_key] = new_price
            st.markdown("---")
