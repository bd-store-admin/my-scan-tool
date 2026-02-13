import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from linebot import LineBotApi
from linebot.models import TextSendMessage
from streamlit_qrcode_scanner import qrcode_scanner
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim

# --- 1. ตั้งค่า LINE (ใส่รหัสที่คุณให้มาแล้ว) ---
LINE_TOKEN = "UQYOCYmqVmCuktPpx/6lgoBJ7tPKZDC2oJsYNLUf7l4m5e3vlNbE5K5sltM4I2bxKtD"
GROUP_ID = "C7986c8ec91cb3ee8919cb0fd1dfc249f"
line_bot_api = LineBotApi(LINE_TOKEN)

# --- 2. ฐานข้อมูลอุปกรณ์สำรอง (รหัส QR : ชื่ออุปกรณ์) ---
tool_database = {
    "W01": "ตู้เชื่อม 01", "W02": "ตู้เชื่อม 02", "W03": "ตู้เชื่อม 03", "W10": "ตู้เชื่อม 10",
    "G01": "หินเจียร์ 01", "G05": "หินเจียร์ 05",
    "R01": "รอก 01", "R10": "รอก 10"
}

st.set_page_config(page_title="ระบบเบิก-คืนอุปกรณ์", layout="centered")

# --- 3. ฟังก์ชันดึงที่อยู่จากพิกัด (ภาษาไทย) ---
def get_address(lat, lon):
    try:
        geolocator = Nominatim(user_agent="inventory_system_v1")
        location = geolocator.reverse(f"{lat}, {lon}", language='th')
        addr = location.raw['address']
        # ดึง เขต/อำเภอ และ จังหวัด
        city = addr.get('city', addr.get('province', addr.get('state', '')))
        district = addr.get('district', addr.get('suburb', addr.get('city_district', '')))
        return f"{district}, {city}"
    except:
        return "ไม่สามารถระบุที่อยู่ได้"

# --- 4. ดึงข้อมูลจาก URL (ถ้าสแกนผ่าน QR แบบฝังชื่อ) ---
query_params = st.query_params
item_from_url = query_params.get("item", "")

st.title("🛠 ระบบเบิก-คืนอุปกรณ์")

# ส่วนข้อมูลผู้ใช้งาน
user_name = st.text_input("👤 ชื่อผู้ทำรายการ:")
status = st.selectbox("📝 ประเภทรายการ:", ["เบิกอุปกรณ์ ✅", "คืนอุปกรณ์ 🔄"])

st.divider()

# --- 5. ระบบพิกัด GPS ---
loc = get_geolocation()
address_display = "กำลังโหลดพิกัด..."
lat, lon = None, None

if loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    address_display = get_address(lat, lon)
    st.info(f"📍 ตำแหน่งปัจจุบันของคุณ: {address_display}")

# --- 6. ส่วนระบุอุปกรณ์ (สแกนจากกล้อง หรือ รับจาก URL) ---
final_item_name = ""

if item_from_url:
    final_item_name = item_from_url
    st.success(f"📦 อุปกรณ์ที่ตรวจพบ: {final_item_name}")
else:
    st.subheader("📷 สแกนคิวอาร์โค้ดที่ตัวเครื่องมือ")
    qr_data = qrcode_scanner(key='scanner')
    if qr_data:
        # เช็คชื่อจากฐานข้อมูล ถ้าไม่เจอให้โชว์รหัสที่สแกนได้
        final_item_name = tool_database.get(qr_data, qr_data)
        st.success(f"📦 ตรวจพบ: {final_item_name}")

# --- 7. ปุ่มส่งข้อมูลเข้า LINE กลุ่ม ---
if st.button("🚀 ยืนยันข้อมูลและส่งแจ้งเตือน", use_container_width=True):
    if user_name and final_item_name:
        # เวลาไทย (GMT+7)
        now = datetime.now() + timedelta(hours=7)
        time_str = now.strftime("%d/%m/%Y %H:%M:%S")
        
        # ลิงก์แผนที่
        map_link = f"https://www.google.com/maps?q={lat},{lon}" if lat else "ไม่มีข้อมูลพิกัด"
        
        # จัดรูปแบบข้อความส่ง LINE
        msg = (
            f"📦 {status}\n"
            f"👤 ชื่อผู้ใช้งาน: {user_name}\n"
            f"🛠 อุปกรณ์: {final_item_name}\n"
            f"📅 วันที่/เวลา: {time_str}\n"
            f"📍 สถานที่: {address_display}\n"
            f"🔗 แผนที่: {map_link}"
        )
        
        try:
            line_bot_api.push_message(GROUP_ID, TextSendMessage(text=msg))
            st.balloons()
            st.success("ส่งข้อมูลเข้ากลุ่ม LINE สำเร็จ!")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}\n(ตรวจสอบว่าดึงบอทเข้ากลุ่มหรือยัง?)")
    else:
        st.warning("⚠️ กรุณากรอกชื่อและสแกนอุปกรณ์ให้เรียบร้อย")
      