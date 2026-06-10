import streamlit as st
import pandas as pd
import json
import gzip  
import numpy as np
import re
import io

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM LAB-TESTING V28.0 ---
st.set_page_config(page_title="Matrix 3D - Tensor Purify V28.0", layout="wide")
TOTAL_POS = 107 

st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #10B981; color: #10B981; }
    
    .box-cang3d { background-color: #05070B; padding: 12px; border-radius: 12px; border: 2px solid #A855F7; margin-bottom: 12px; }
    .box-vip { background-color: #020C08; padding: 12px; border-radius: 12px; border: 2px solid #10B981; margin-bottom: 12px; }
    .box-orange { background-color: #0F0902; padding: 12px; border-radius: 12px; border: 2px solid #F59E0B; margin-bottom: 12px; }
    
    .title-cang3d { color: #A855F7 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-vip { color: #10B981 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-orange { color: #F59E0B !important; font-size: 15px !important; font-weight: 900 !important; }
    
    .text-cang3d { color: #E2E8F0 !important; font-size: 14px !important; font-family: monospace; letter-spacing: 1px; word-wrap: break-word; line-height: 1.4; }
    .text-vip { color: #FFD700 !important; font-size: 16px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 2px; word-wrap: break-word; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo ma trận phẳng nhị phân trực tiếp trên RAM máy chủ
if 'matrix_np' not in st.session_state:
    st.session_state['matrix_np'] = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=np.int32)

if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "last_digits": "",
        "history": [],
        "last_lab_predictions": {} 
    }

# TOÁN TỔ HỢP: Tự động lập bộ hằng số 280 con chuẩn đét từ thuật toán
@st.cache_data
def get_pure_kep_ganh_280():
    pure_list = []
    for i in range(1000):
        num_str = str(i).zfill(3)
        if 1 <= len(set(num_str)) <= 2:
            pure_list.append(num_str)
    return pure_list

KEP_GANH_280 = get_pure_kep_ganh_280()
KEP_GANH_SET = set(KEP_GANH_280)

# --- 2. BỘ GIẢI MÃ CẤU TRÚC BẢNG GIẢI WEB THÔNG MINH ---
def parse_vietnam_xsmb_format(raw_text):
    clean_text = " ".join(raw_text.split())
    patterns = {
        "DB": r"(?:Đặc biệt|Giải ĐB|ĐB)\s*(\d+)",
        "G1": r"(?:Giải nhất|Giải 1|G1)\s*(\d+)",
        "G2": r"(?:Giải nhì|Giải 2|G2)\s*(\d+)",
        "G3": r"(?:Giải ba|Giải 3|G3)\s*(\d+)",
        "G4": r"(?:Giải tư|Giải 4|G4)\s*(\d+)",
        "G5": r"(?:Giải năm|Giải 5|G5)\s*(\d+)",
        "G6": r"(?:Giải sáu|Giải 6|G6)\s*(\d+)",
        "G7": r"(?:Giải bảy|Giải 7|G7)\s*(\d+)"
    }
    extracted_g_nums = {}
    for g_key, pat in patterns.items():
        match = re.search(pat, clean_text, re.IGNORECASE)
        if match: extracted_g_nums[g_key] = match.group(1)
        else: return None, None, None
            
    digits_107 = (
        extracted_g_nums["DB"] + extracted_g_nums["G1"] + extracted_g_nums["G2"] +
        extracted_g_nums["G3"] + extracted_g_nums["G4"] + extracted_g_nums["G5"] +
        extracted_g_nums["G6"] + extracted_g_nums["G7"]
    )
    g2_nums = [extracted_g_nums["G2"][i:i+5] for i in range(0, len(extracted_g_nums["G2"]), 5)]
    g3_nums = [extracted_g_nums["G3"][i:i+5] for i in range(0, len(extracted_g_nums["G3"]), 5)]
    g4_nums = [extracted_g_nums["G4"][i:i+4] for i in range(0, len(extracted_g_nums["G4"]), 4)]
    g5_nums = [extracted_g_nums["G5"][i:i+4] for i in range(0, len(extracted_g_nums["G5"]), 4)]
    g6_nums = [extracted_g_nums["G6"][i:i+3] for i in range(0, len(extracted_g_nums["G6"]), 3)]
    g7_nums = [extracted_g_nums["G7"][i:i+2] for i in range(0, len(extracted_g_nums["G7"]), 2)]
    
    all_27_components = (
        [extracted_g_nums["DB"], extracted_g_nums["G1"]] + g2_nums + g3_nums + 
        g4_nums + g5_nums + g6_nums + g7_nums
    )
    loto_27_list = [num[-2:] for num in all_27_components if len(num) >= 2]
    cang3c_23_list = [num[-3:] for num in all_27_components[:23] if len(num) >= 3]
    return digits_107, loto_27_list, cang3c_23_list

# --- 3. ĐỘNG CƠ MA TRẬN PHÂN TÁCH SỢI DÂY TINH KHIẾT V28.0 ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    old_matrix = st.session_state['matrix_np'] 
    old_digits = db["last_digits"]
    old_lab_preds = db.get("last_lab_predictions", {})
    
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    
    # 🛠️ ĐỒNG BỘ ĐỐI SOÁT TOÀN DIỆN 9 LOẠI DÀN TRÊN BẢNG NHẬT KÝ
    if old_digits != "" and old_lab_preds:
        keys_mapping = {
            "d1_0đ_uni": "Dàn 1 (0đ Độc Nhất)",
            "d2_1đ_uni": "Dàn 2 (1đ Độc Nhất)",
            "d3_2đ_uni": "Dàn 3 (2đ Độc Nhất)",
            "d4_2đ_plus": "Dàn 4 (Dây >= 2đ)",
            "d5_0đ_khan": "Dàn 5 (0đ Khan >5Ngày)",
            "d6_overload": "Dàn 6 (Đa Dây Nhiễu)",
            "d7_hist_5": "Dàn 7 (Đã Ra 5 Kỳ)",
            "d8_hist_10": "Dàn 8 (Đã Ra 10 Kỳ)",
            "d9_hist_15": "Dàn 9 (Đã Ra 15 Kỳ)"
        }
        for internal_key, column_name in keys_mapping.items():
            pred_list = old_lab_preds.get(internal_key, [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            if total_hits > 0:
                hit_report[column_name] = f"{total_hits} nháy ({', '.join(matched_nums)})"
            else:
                hit_report[column_name] = "0"
                
    # Cập nhật ma trận tích lũy lũy tiến gối đầu liên kỳ
    new_matrix = np.copy(old_matrix)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23 and num_past in KEP_GANH_SET: 
                        new_matrix[i][j][k] += 1  

    # Kho đếm sợi và điểm dây cho từng quân số
    wire_score_registry = {num: [] for num in KEP_GANH_280}
    wire_active_count = {num: 0 for num in KEP_GANH_280} 

    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            for k in range(TOTAL_POS):
                num_cang = digits_107[i] + digits_107[j] + digits_107[k]
                if num_cang in KEP_GANH_SET:
                    score = int(new_matrix[i][j][k])
                    wire_active_count[num_cang] += 1
                    wire_score_registry[num_cang].append(score)

    d1_0đ_uni = []   
    d2_1đ_uni = []   
    d3_2đ_uni = []   
    d4_2đ_plus = []  
    d6_overload = [] 

    for num in KEP_GANH_280:
        score_list = wire_score_registry[num]
        total_active_wires = wire_active_count[num]
        if total_active_wires == 0: continue
        
        if len(set(score_list)) == 1:
            sc = score_list[0]
            if sc == 0: d1_0đ_uni.append(num)
            elif sc == 1: d2_1đ_uni.append(num)
            elif sc == 2: d3_2đ_uni.append(num)
            
        if any(sc >= 2 for sc in score_list):
            d4_2đ_plus.append(num)
            
        if total_active_wires > 15:
            d6_overload.append(num)

    # --- 🧠 ĐỘNG CƠ QUÉT NGƯỢC THỜI GIAN TRÍCH XUẤT 4 DÀN LỊCH SỬ KÉP GÁNH MỚI ---
    d5_0đ_khan = []
    d7_hist_5 = set()   # Dàn 7: Đã ra trong 5 kỳ gần nhất lọt lưới 280 con
    d8_hist_10 = set()  # Dàn 8: Đã ra trong 10 kỳ gần nhất lọt lưới 280 con
    d9_hist_15 = set()  # Dàn 9: Đã ra trong 15 kỳ gần nhất lọt lưới 280 con
    
    hist_len = len(db["history"])
    
    # 🛰️ VÒNG QUÈT LỊCH SỬ TOÀN DIỆN
    for index, h_day in enumerate(db["history"]):
        saved_c3c = h_day.get("Saved_3C_Real", [])
        # Lọc nhanh chỉ giữ lại những con thuộc bộ 280 của đại ca
        clean_kep_ganh_day = [c for c in saved_c3c if c in KEP_GANH_SET]
        
        if index < 5:
            for num in clean_kep_ganh_day: d7_hist_5.add(num)
        if index < 10:
            for num in clean_kep_ganh_day: d8_hist_10.add(num)
        if index < 15:
            for num in clean_kep_ganh_day: d9_hist_15.add(num)

    # Dàn 5: Nuôi lại logic cũ dựa trên mảng đập trùng của 5 ngày qua
    if hist_len >= 5:
        for num in KEP_GANH_280:
            if num not in d7_hist_5:
                if num in wire_score_registry and all(sc == 0 for sc in wire_score_registry[num]):
                    d5_0đ_khan.append(num)

    # Đóng gói chuẩn khít 9 tầng dữ liệu lên két bảo mật RAM
    db["last_lab_predictions"] = {
        "d1_0đ_uni": sorted(d1_0đ_uni),
        "d2_1đ_uni": sorted(d2_1đ_uni),
        "d3_2đ_uni": sorted(d3_2đ_uni),
        "d4_2đ_plus": sorted(d4_2đ_plus),
        "d5_0đ_khan": sorted(d5_0đ_khan),
        "d6_overload": sorted(d6_overload),
        
        "d7_hist_5": sorted(list(d7_hist_5)),
        "d8_hist_10": sorted(list(d8_hist_10)),
        "d9_hist_15": sorted(list(d9_hist_15))
    }

    st.session_state['matrix_np'] = new_matrix
    db["last_digits"] = digits_107
    
    # GĂM MẢNG GỐC CỦA KỲ NÀY LÊN LỊCH SỬ ĐỂ NUÔI KHUNG CHO CÁC KỲ SAU
    hit_report["Saved_3C_Real"] = cang3c_23
    
    if old_digits != "" and old_lab_preds: 
        db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Khởi tạo ma trận Purify V28.0"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ TENSOR MATRIX 3D - PURIFY ULTRA v28.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp tệp GZ Sao Lưu Ma Trận V28", type=['gz'])
    
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        try:
            with gzip.open(uploaded_file, "rb") as f:
                payload = json.loads(f.read().decode("utf-8"))
                st.session_state['db_3d'] = payload["db_3d"]
                st.session_state['matrix_np'] = np.array(payload["matrix_raw"], dtype=np.int32)
            st.success("Đã hồi sinh trạm lọc biên độ V28.0!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi cấu trúc RAM: {e}")
            
    if st.session_state['db_3d']['last_digits']:
        export_pack = {
            "db_3d": st.session_state['db_3d'],
            "matrix_raw": st.session_state['matrix_np'].tolist()
        }
        json_string = json.dumps(export_pack)
        gzip_buffer = io.BytesIO()
        with gzip.open(gzip_buffer, "wb", compresslevel=9) as f:
            f.write(json_string.encode("utf-8"))
        
        st.download_button(
            label="💾 XUẤT FILE NÉN TỐI ƯU (.JSON.GZ)", 
            data=gzip_buffer.getvalue(), 
            file_name="matrix_3d_v280.json.gz",
            mime="application/gzip"
        )
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    raw_input_text = st.text_area("Dán bảng giải thô chuẩn từ Web:", key="web_raw_field_v28", height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        if raw_input_text:
            digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(raw_text=raw_input_text)
            if digits_107 and len(digits_107) == TOTAL_POS:
                gdb_val = digits_107[3:5]
                process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
                st.toast("🔥 Đồng bộ băm vết 9 loại dàn biên độ thành công!", icon="⚡")
                st.rerun()
            else:
                st.error("Lỗi cấu trúc giải thô 107 số!")
        else:
            st.warning("Ô nhập trống kìa đại ca!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN (9 DÀN CỘT RỘNG) ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN 9 PHÂN LỚP BIÊN ĐỘ VÂN TAY</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    display_history = []
    for h in hist_data:
        cleaned_h = {k: v for k, v in h.items() if k != "Saved_3C_Real"}
        display_history.append(cleaned_h)
        
    df_hist = pd.DataFrame(display_history).fillna("0")
    cols = list(df_hist.columns)
    
    order_cols = [
        "GĐB", "Dàn 1 (0đ Độc Nhất)", "Dàn 2 (1đ Độc Nhất)", "Dàn 3 (2đ Độc Nhất)", 
        "Dàn 4 (Dây >= 2đ)", "Dàn 5 (0đ Khan >5Ngày)", "Dàn 6 (Đa Dây Nhiễu)",
        "Dàn 7 (Đã Ra 5 Kỳ)", "Dàn 8 (Đã Ra 10 Kỳ)", "Dàn 9 (Đã Ra 15 Kỳ)"
    ]
    final_cols = [c for c in order_cols if c in cols] + [c for c in cols if c not in order_cols]
    
    def highlight_wins(val):
        val_str = str(val)
        if "nháy" in val_str:
            return 'background-color: #1F2937; color: #10B981; font-weight: 900; border: 1px solid #10B981;'
        elif val_str == "0":
            return 'color: #4B5563; font-weight: normal;'
        return ''

    st.dataframe(df_hist[final_cols].style.map(highlight_wins), use_container_width=True, height=400)
else:
    st.info("Hệ thống ma trận biên độ V28.0 đã nạp RAM! Sẵn sàng khạc báo cáo quân ăn kỳ sau.")

st.divider()

# --- 6. PHƠI BÀY CHI TIẾT ĐỦ ĐÚNG 9 LOẠI DÀN TRÊN WEB ---
st.markdown("<h3><font color='#A855F7'><b>🔮 DANH SÁCH CHI TIẾT SỐ CỦA 9 PHÂN LỚP THỰC NGHIỆM</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #A855F7; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

preds = st.session_state['db_3d'].get("last_lab_predictions", {})

if preds:
    # 🌟 HIỂN THỊ TRỰC DIỆN 3 DÀN QUÉT NGƯỢC BIÊN ĐỘ THỜI GIAN MỚI CỦA ĐẠI CA
    d7 = preds.get("d7_hist_5", [])
    st.markdown(f"""<div class="box-orange"><span class="title-orange">⏳ 7. TẬP HỢP CÁC SỐ KÉP GÁNH ĐÃ VỀ TRONG 5 KỲ GẦN NHẤT (Tổng số: {len(d7)} quân)</span><br>
    <p class="text-cang3d">{"   -   ".join(d7) if d7 else "Chưa tích lũy đủ dữ liệu kỳ!"}</p></div>""", unsafe_allow_html=True)

    d8 = preds.get("d8_hist_10", [])
    st.markdown(f"""<div class="box-orange"><span class="title-orange">⏳ 8. TẬP HỢP CÁC SỐ KÉP GÁNH ĐÃ VỀ TRONG 10 KỲ GẦN NHẤT (Tổng số: {len(d8)} quân)</span><br>
    <p class="text-cang3d">{"   -   ".join(d8) if d8 else "Chưa tích lũy đủ dữ liệu kỳ!"}</p></div>""", unsafe_allow_html=True)

    d9 = preds.get("d9_hist_15", [])
    st.markdown(f"""<div class="box-orange"><span class="title-orange">⏳ 9. TẬP HỢP CÁC SỐ KÉP GÁNH ĐÃ VỀ TRONG 15 KỲ GẦN NHẤT (Tổng số: {len(d9)} quân)</span><br>
    <p class="text-cang3d">{"   -   ".join(d9) if d9 else "Chưa tích lũy đủ dữ liệu kỳ!"}</p></div>""", unsafe_allow_html=True)

    # 🌟 CÁC DÀN LỌC LOẠI CŨ
    d5 = preds.get("d5_0đ_khan", [])
    st.markdown(f"""<div class="box-vip"><span class="title-vip">🚨 5. DÀN CÁC DÂY 0 ĐIỂM TRÊN 5 NGÀY CHƯA VỀ (MÀNG LỌC LOẠI - Tổng số: {len(d5)} quân)</span><br>
    <p class="text-vip">{"   -   ".join(d5) if d5 else "Kỳ này không có số đóng băng!"}</p></div>""", unsafe_allow_html=True)

    d6 = preds.get("d6_overload", [])
    st.markdown(f"""<div class="box-vip"><span class="title-vip">⚠️ 6. DÀN CÁC PHẦN TỬ ĐA DÂY GÂY NHIỄU SÓNG (MÀNG LỌC LOẠI - Tổng số: {len(d6)} quân)</span><br>
    <p class="text-vip">{"   -   ".join(d6) if d6 else "Kỳ này không có số nhiễu!"}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📦 CÁC DÀN ĐƠN DÂY ĐỘC NHẤT VÀ TRỤC BỆT MA TRẬN:")

    # 📦 DÀN 1
    d1 = preds.get("d1_0đ_uni", [])
    with st.expander(f"📦 1. DÀN CÁC DÂY 0 ĐIỂM ĐỘC NHẤT (Tổng số: {len(d1)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d1) if d1 else "Trống số!"}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 2
    d2 = preds.get("d2_1đ_uni", [])
    with st.expander(f"📦 2. DÀN CÁC DÂY 1 ĐIỂM ĐỘC NHẤT (Tổng số: {len(d2)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d2) if d2 else "Trống số!"}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 3
    d3 = preds.get("d3_2đ_uni", [])
    with st.expander(f"📦 3. DÀN CÁC DÂY 2 ĐIỂM ĐỘC NHẤT (Tổng số: {len(d3)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d3) if d3 else "Trống số!"}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 4
    d4 = preds.get("d4_2đ_plus", [])
    with st.expander(f"📦 4. DÀN TẬP HỢP CỦA CÁC DÂY TỪ 2 ĐIỂM TRỞ LÊN THÔ (Tổng số: {len(d4)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d4) if d4 else "Trống số!"}</p></div>', unsafe_allow_html=True)

else:
    st.info("Hệ thống phòng thí nghiệm đang trống. Hãy dán kết quả thô để bóc tách 9 phân lớp ma trận biên độ!")
