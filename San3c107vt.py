import streamlit as st
import pandas as pd
import json
import numpy as np
import re

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM LAB-TESTING V23.0 ---
st.set_page_config(page_title="Matrix 3D - Lab Testing V23.0", layout="wide")
TOTAL_POS = 107 

st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #10B981; color: #10B981; }
    
    .box-cang3d { background-color: #05070B; padding: 12px; border-radius: 12px; border: 2px solid #A855F7; margin-bottom: 12px; }
    .box-vip { background-color: #020C08; padding: 12px; border-radius: 12px; border: 2px solid #10B981; margin-bottom: 12px; }
    
    .title-cang3d { color: #A855F7 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-vip { color: #10B981 !important; font-size: 15px !important; font-weight: 900 !important; }
    
    .text-cang3d { color: #E2E8F0 !important; font-size: 15px !important; font-family: monospace; letter-spacing: 1px; word-wrap: break-word; line-height: 1.4; }
    .text-vip { color: #FFD700 !important; font-size: 18px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 2px; word-wrap: break-word; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo cấu trúc dữ liệu thí nghiệm 5 tầng gối đầu trên RAM Session
if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "wire_matrix_3d": np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "history": [],
        "last_lab_predictions": {} # Lưu trữ trọn gói 5 loại dàn hôm nay để ngày mai đối soát nháy nổ
    }

# --- 🛠️ BỘ GIẢI MÃ CẤU TRÚC BẢNG GIẢI WEB THÔNG MINH ---
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

# --- 3. ĐỘNG CƠ TRÍCH XUẤT PHÂN TÁCH KHÔNG GIAN TOÀN PHẦN V23.0 ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    
    old_matrix = np.array(db["wire_matrix_3d"], dtype=int)
    old_digits = db["last_digits"]
    old_lab_preds = db.get("last_lab_predictions", {})
    
    # 🧠 BƯỚC 1: ĐỐI SOÁT TỰ ĐỘNG LỊCH SỬ KỲ TRƯỚC THEO ĐÚNG 5 LOẠI DÀN TRÊN RAM
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    
    if old_digits != "" and old_lab_preds:
        keys_mapping = {
            "d1_0đ_thô": "Dàn 0đ Thô",
            "d2_1đ_thô": "Dàn 1đ Thô",
            "d3_2đ_plus_thô": "Dàn 2đ+ Thô",
            "d4_1đ_unique": "1đ Độc Quyền",
            "d5_2đ_unique": "2đ Độc Quyền"
        }
        for internal_key, column_name in keys_mapping.items():
            pred_list = old_lab_preds.get(internal_key, [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            
            if total_hits > 0:
                hit_report[column_name] = f"{total_hits} nháy ({', '.join(matched_nums)})"
            else:
                hit_report[column_name] = "0"
                
    # 🧠 BƯỚC 2: CĂNG MA TRẬN PHẲNG VÀ UPDATE ĐIỂM SỢI DÂY
    new_matrix = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23: 
                        new_matrix[i][j][k] = old_matrix[i][j][k] + 1
                    else: 
                        new_matrix[i][j][k] = 0

    # 🧠 BƯỚC 3: PHÂN LẬP 5 LOẠI DÀN TUYỆT ĐỐI BỎ TRÙNG
    max_score = int(new_matrix.max())
    
    d1_accumulator = set()      # Tầng 1: Toàn bộ dây 0đ thô bỏ trùng
    d2_accumulator = set()      # Tầng 2: Toàn bộ dây 1đ thô bỏ trùng
    d3_accumulator = set()      # Tầng 3: Toàn bộ dây >= 2đ thô bỏ trùng
    
    # Khởi tạo bộ đếm để phục vụ lọc Độc quyền đơn dây cho Tầng 4 và Tầng 5
    frequency_in_1đ = {}
    frequency_in_2đ = {}
    
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            for k in range(TOTAL_POS):
                num_cang = digits_107[i] + digits_107[j] + digits_107[k]
                score = new_matrix[i][j][k]
                
                if score == 0:
                    d1_accumulator.add(num_cang)
                elif score == 1:
                    d2_accumulator.add(num_cang)
                    frequency_in_1đ[num_cang] = frequency_in_1đ.get(num_cang, 0) + 1
                elif score >= 2:
                    d3_accumulator.add(num_cang)
                    if score == 2:
                        frequency_in_2đ[num_cang] = frequency_in_2đ.get(num_cang, 0) + 1

    # Trích xuất dải số Độc quyền đơn dây (chỉ xuất hiện đúng 1 lần trong nhóm)
    d4_unique_list = [cang for cang, freq in frequency_in_1đ.items() if freq == 1]
    d5_unique_list = [cang for cang, freq in frequency_in_2đ.items() if freq == 1]

    # Lưu gói 5 loại dàn dự đoán của ngày hôm nay vào két bảo mật RAM
    db["last_lab_predictions"] = {
        "d1_0đ_thô": sorted(list(d1_accumulator)),
        "d2_1đ_thô": sorted(list(d2_accumulator)),
        "d3_2đ_plus_thô": sorted(list(d3_accumulator)),
        "d4_1đ_unique": sorted(d4_unique_list),
        "d5_2đ_unique": sorted(d5_unique_list)
    }

    # Đồng bộ kho lưu trữ chính
    db["wire_matrix_3d"] = new_matrix.tolist()
    db["last_digits"] = digits_107
    
    if old_digits != "" and old_lab_preds: 
        db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Kỳ khởi tạo ma trận thí nghiệm"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ TENSOR MATRIX 3D - LAB TESTING TOOL v23.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp file JSON 3D", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        st.session_state['db_3d'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db_3d']['last_digits']:
        st.download_button("💾 XUẤT FILE SAO LƯU JSON", json.dumps(st.session_state['db_3d']), "matrix_3d_v230.json")
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    raw_input_text = st.text_area("Dán bảng giải thô chuẩn từ Web:", key="web_raw_field_v23", height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        if raw_input_text:
            digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(raw_text=raw_input_text)
            if digits_107 and len(digits_107) == TOTAL_POS:
                gdb_val = digits_107[3:5]
                process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
                st.toast("🔥 Phân lập 5 tầng năng lượng thành công! Đã xóa dấu vết bảng giải.", icon="🧹")
                st.rerun()
            else:
                st.error("Lỗi cấu trúc bảng giải dán vào!")
        else:
            st.warning("Ô dán bảng giải đang trống!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TRUNG TÂM (ĐƯA LÊN ĐẦU ĐỂ TIỆN SOI) ---
st.markdown("<h3><font color='#10B981'><b>📋 BẢNG KIỂM ĐỊNH THỬ NGHIỆM 5 PHÂN LỚP NĂNG LƯỢNG</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    df_hist = pd.DataFrame(hist_data).fillna("0")
    cols = list(df_hist.columns)
    
    # Định tuyến găm các cột chính lên tiền tuyến đầu bảng
    order_cols = ["GĐB", "Dàn 0đ Thô", "Dàn 1đ Thô", "Dàn 2đ+ Thô", "1đ Độc Quyền", "2đ Độc Quyền"]
    final_cols = [c for c in order_cols if c in cols] + [c for c in cols if c not in order_cols]
    
    def highlight_wins(val):
        val_str = str(val)
        if "nháy" in val_str:
            if "(" in val_str: # Có nổ con số đích danh
                return 'background-color: #1F2937; color: #10B981; font-weight: 900; border: 1px solid #10B981;'
        elif val_str == "0":
            return 'color: #4B5563; font-weight: normal;'
        return ''

    st.dataframe(df_hist[final_cols].style.map(highlight_wins), use_container_width=True, height=400)
else:
    st.info("Nhật ký tra cứu đang trống. Hệ thống sẽ bắt đầu xuất bản đối soát liên hoàn 5 phân lớp gối đầu từ kỳ quay thứ hai.")

st.divider()

# --- 6. KHU VỰC PHƠI BÀY CHI TIẾT 5 LOẠI DÀN CỦA KỲ HIỆN TẠI ---
st.markdown("<h3><font color='#A855F7'><b>🔮 CHI TIẾT DANH SÁCH 5 PHÂN LỚP SỐ TRÍCH XUẤT</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #A855F7; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

current_lab_preds = st.session_state['db_3d'].get("last_lab_predictions", {})

if current_lab_preds:
    # 🌟 LOẠI 4: DÀN 1 ĐIỂM ĐỘC QUYỀN (HIỂN THỊ TRỰC DIỆN VÌ ÍT QUÂN)
    d4_list = current_lab_preds.get("d4_1đ_unique", [])
    st.markdown(f"""
        <div class="box-vip">
            <span class="title-vip">💎 4. DÀN TẬP HỢP ÁNH XẠ ĐƠN DÂY 1 ĐIỂM ĐỘC QUYỀN (Tổng số: {len(d4_list)} quân)</span><br>
            <p class="text-vip">{"   -   ".join(d4_list) if d4_list else "Kỳ này trống số!"}</p>
        </div>
        """, unsafe_allow_html=True)

    # 🌟 LOẠI 5: DÀN 2 ĐIỂM ĐỘC QUYỀN (HIỂN THỊ TRỰC DIỆN VÌ ÍT QUÂN)
    d5_list = current_lab_preds.get("d5_2đ_unique", [])
    st.markdown(f"""
        <div class="box-vip">
            <span class="title-vip">💎 5. DÀN TẬP HỢP ÁNH XẠ ĐƠN DÂY 2 ĐIỂM ĐỘC QUYỀN (Tổng số: {len(d5_list)} quân)</span><br>
            <p class="text-vip">{"   -   ".join(d5_list) if d5_list else "Kỳ này trống số!"}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📦 CÁC DÀN THÔ ĐÔNG QUÂN (BẤM MỞ RA ĐỂ LẤY SỐ):")
    
    # 📦 LOẠI 1: EXPANDER DÀN 0 ĐIỂM THÔ
    d1_list = current_lab_preds.get("d1_0đ_thô", [])
    with st.expander(f"📦 1. DÀN TẬP HỢP TOÀN BỘ CÁC DÂY 0 ĐIỂM BỎ TRÙNG (Tổng số: {len(d1_list)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d1_list)}</p></div>', unsafe_allow_html=True)

    # 📦 LOẠI 2: EXPANDER DÀN 1 ĐIỂM THÔ
    d2_list = current_lab_preds.get("d2_1đ_thô", [])
    with st.expander(f"📦 2. DÀN TẬP HỢP TOÀN BỘ CÁC DÂY 1 ĐIỂM BỎ TRÙNG (Tổng số: {len(d2_list)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d2_list)}</p></div>', unsafe_allow_html=True)

    # 📦 LOẠI 3: EXPANDER DÀN 2 ĐIỂM TRỞ LÊN THÔ
    d3_list = current_lab_preds.get("d3_2đ_plus_thô", [])
    with st.expander(f"📦 3. DÀN TẬP HỢP TOÀN BỘ CÁC DÂY 2 ĐIỂM TRỞ LÊN BỎ TRÙNG (Tổng số: {len(d3_list)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d3_list)}</p></div>', unsafe_allow_html=True)

else:
    st.info("Hệ thống phòng thí nghiệm đang trống. Vui lòng dán bảng kết quả thô vào Sidebar bên trái để bóc tách 5 tầng dữ liệu!")
