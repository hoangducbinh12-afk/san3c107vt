import streamlit as st
import pandas as pd
import json
import gzip  
import numpy as np
import re
import io

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM LAB-TESTING V32.2 ---
st.set_page_config(page_title="Matrix 3D - Tensor 12 Nukes V32.2", layout="wide")
TOTAL_POS = 107 

st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #10B981; color: #10B981; }
    
    .box-top6 { background-color: #140406; padding: 20px; border-radius: 12px; border: 3px solid #EF4444; margin-bottom: 20px; text-align: center; }
    .box-next6 { background-color: #030814; padding: 20px; border-radius: 12px; border: 3px solid #3B82F6; margin-bottom: 20px; text-align: center; }
    
    .title-top6 { color: #EF4444 !important; font-size: 22px !important; font-weight: 900 !important; text-shadow: 0 0 15px rgba(239, 68, 68, 0.6); }
    .title-next6 { color: #3B82F6 !important; font-size: 22px !important; font-weight: 900 !important; text-shadow: 0 0 15px rgba(59, 130, 246, 0.6); }
    
    .text-top6 { color: #EF4444 !important; font-size: 32px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 4px; }
    .text-next6 { color: #3B82F6 !important; font-size: 32px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 4px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo lưu trữ RAM hệ thống nhị phân Numpy phẳng
if 'matrix_np' not in st.session_state:
    st.session_state['matrix_np'] = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=np.int32)

if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "last_digits": "",
        "history": [],
        "last_lab_predictions": {},
        "luy_ke_counts": {},         
        "transition_memory": {},     
        "transition_memory_2": {},   
        "current_round_kep_ganh": [],
        "prev_round_kep_ganh": []    
    }

# TOÁN TỔ HỢP: Tự động lập bộ hằng số 280 con chuẩn đét từ thuật toán
@st.cache_data
def get_pure_kep_ganh_280():
    pure_list = []
    for i in range(1000):
        num_str = str(i).zfill(3)
        if 1 <= len(set(num_str)) <= 2: pure_list.append(num_str)
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

# --- 3. ĐỘNG CƠ MA TRẬN VÀ CHẤM ĐIỂM SỢI DÂY CỘNG HƯỞNG ĐA TẦNG V32.2 ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    old_matrix = st.session_state['matrix_np'] 
    old_digits = db["last_digits"]
    old_lab_preds = db.get("last_lab_predictions", {})
    
    if "luy_ke_counts" not in db: db["luy_ke_counts"] = {}
    if "transition_memory" not in db: db["transition_memory"] = {}
    if "transition_memory_2" not in db: db["transition_memory_2"] = {}
    if "current_round_kep_ganh" not in db: db["current_round_kep_ganh"] = []
    if "prev_round_kep_ganh" not in db: db["prev_round_kep_ganh"] = []
    
    luy_ke = db["luy_ke_counts"]
    trans_mem = db["transition_memory"]
    trans_mem_2 = db["transition_memory_2"]
    last_round_nums = db["current_round_kep_ganh"]  
    prev_round_nums = db["prev_round_kep_ganh"]     
    
    for num in KEP_GANH_280: 
        if num not in luy_ke: luy_ke[num] = 0

    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    cang3c_today_kep_ganh = [c for c in cang3c_23 if c in KEP_GANH_SET]

    if last_round_nums:
        for A in last_round_nums:
            if A not in trans_mem: trans_mem[A] = {}
            for B in cang3c_today_kep_ganh: trans_mem[A][B] = trans_mem[A].get(B, 0) + 1

    if prev_round_nums:
        for X in prev_round_nums:
            if X not in trans_mem_2: trans_mem_2[X] = {}
            for B in cang3c_today_kep_ganh: trans_mem_2[X][B] = trans_mem_2[X].get(B, 0) + 1

    for num in cang3c_today_kep_ganh: luy_ke[num] += 1

    new_matrix = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=np.int32)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23 and num_past in KEP_GANH_SET: 
                        new_matrix[i][j][k] = old_matrix[i][j][k] + 1

    wire_max_score = {num: 0 for num in KEP_GANH_280}
    wire_total_lines = {num: 0 for num in KEP_GANH_280} 

    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            for k in range(TOTAL_POS):
                num_cang = digits_107[i] + digits_107[j] + digits_107[k]
                if num_cang in KEP_GANH_SET:
                    score = int(new_matrix[i][j][k])
                    if score > 0:
                        wire_total_lines[num_cang] += 1
                        if score > wire_max_score[num_cang]: wire_max_score[num_cang] = score

    d1_0đ_uni, d2_1đ_uni, d3_2đ_uni, d4_2đ_plus, d6_overload = [], [], [], [], []

    for num in KEP_GANH_280:
        max_sc = wire_max_score[num]
        total_lines = wire_total_lines[num]
        if max_sc == 0: d1_0đ_uni.append(num)  
        elif max_sc == 1: d2_1đ_uni.append(num)  
        elif max_sc == 2: d3_2đ_uni.append(num)  
        if max_sc >= 2: d4_2đ_plus.append(num) 
        if total_lines > 15: d6_overload.append(num) 

    d5_0đ_khan = []
    d7_hist_5, d8_hist_10, d9_hist_15 = set(), set(), set()
    
    for index, h_day in enumerate(db["history"]):
        saved_c3c = h_day.get("Saved_3C_Real", [])
        clean_kep_ganh_day = [c for c in saved_c3c if c in KEP_GANH_SET]
        if index < 5:
            for num in clean_kep_ganh_day: d7_hist_5.add(num)
        if index < 10:
            for num in clean_kep_ganh_day: d8_hist_10.add(num)
        if index < 15:
            for num in clean_kep_ganh_day: d9_hist_15.add(num)

    if len(db["history"]) >= 5:
        for num in KEP_GANH_280:
            if num not in d7_hist_5 and num in d1_0đ_uni: d5_0đ_khan.append(num)

    scores_nền = {num: 0 for num in KEP_GANH_280}
    for num in KEP_GANH_280:
        if num in d2_1đ_uni: scores_nền[num] += 9
        if num in d9_hist_15: scores_nền[num] += 8
        if num in d8_hist_10: scores_nền[num] += 7
        if num in d6_overload: scores_nền[num] += 6
        if num in d1_0đ_uni: scores_nền[num] += 5
        if num in d5_0đ_khan: scores_nền[num] += 4
        if num in d7_hist_5: scores_nền[num] += 3
        if num in d3_2đ_uni or num in d4_2đ_plus: scores_nền[num] += 2
        scores_nền[num] += luy_ke[num] 

    predicted_set_by_t1 = set()
    for A in cang3c_today_kep_ganh:
        for B in trans_mem.get(A, {}).keys():
            if trans_mem[A][B] > 0: predicted_set_by_t1.add(B)
            
    predicted_set_by_t2 = set()
    for X in last_round_nums:
        for B in trans_mem_2.get(X, {}).keys():
            if trans_mem_2[X][B] > 0: predicted_set_by_t2.add(B)

    resonance_numbers_set = predicted_set_by_t1.intersection(predicted_set_by_t2)

    predicted_scores_kỳ_t = {}
    link_scores_log = {num: 0 for num in KEP_GANH_280}
    resonance_scores_log = {num: 0 for num in KEP_GANH_280} 

    for num in KEP_GANH_280:
        base_sc = scores_nền[num]
        
        transition_bonus = 0
        for A in cang3c_today_kep_ganh: transition_bonus += 10 * trans_mem.get(A, {}).get(num, 0)
        link_scores_log[num] = transition_bonus
        
        resonance_bonus = 20 if num in resonance_numbers_set else 0
        resonance_scores_log[num] = resonance_bonus
        
        pred_sc = base_sc + transition_bonus + resonance_bonus
        
        if num in cang3c_today_kep_ganh:
            if num in d2_1đ_uni: pred_sc += 5
            else: pred_sc -= 3
        if num in d5_0đ_khan: pred_sc += 4
        if num in d6_overload: pred_sc -= 5
            
        predicted_scores_kỳ_t[num] = pred_sc

    sorted_all_numbers = sorted(predicted_scores_kỳ_t.items(), key=lambda x: x[1], reverse=True)
    
    top_6_highest = [item[0] for item in sorted_all_numbers[:6]]
    next_6_highest = [item[0] for item in sorted_all_numbers[6:12]]

    db["last_lab_predictions"] = {
        "top_6_highest": top_6_highest,
        "next_6_highest": next_6_highest
    }

    score_board_data = []
    for num in KEP_GANH_280:
        if scores_nền[num] > 0 or link_scores_log[num] > 0 or resonance_scores_log[num] > 0:
            score_board_data.append({
                "Mã Số": num,
                "Điểm Nền Dàn": scores_nền[num] - luy_ke[num],
                "Lũy Kế Nổ Lịch Sử (+1đ)": luy_ke[num],
                "Nhân Quả T-1 (+10đ/Lần)": link_scores_log[num],
                "⚡ Cộng Hưởng T-2 (+20đ)": resonance_scores_log[num],
                "TỔNG ĐIỂM DỰ ĐOÁN KỲ T": predicted_scores_kỳ_t[num]
            })
    db["last_score_board"] = sorted(score_board_data, key=lambda x: x["TỔNG ĐIỂM DỰ ĐOÁN KỲ T"], reverse=True)[:20]

    db["prev_round_kep_ganh"] = last_round_nums
    db["current_round_kep_ganh"] = cang3c_today_kep_ganh
    
    st.session_state['matrix_np'] = new_matrix
    db["last_digits"] = digits_107
    hit_report["Saved_3C_Real"] = cang3c_23
    
    if old_digits != "" and old_lab_preds:
        matched_top6 = [n for n in old_lab_preds.get("top_6_highest", []) if n in cang3c_23]
        matched_next6 = [n for n in old_lab_preds.get("next_6_highest", []) if n in cang3c_23]
        
        hit_report["Dàn 6 Con Điểm Cao Nhất"] = f"{len(matched_top6)} nháy ({', '.join(matched_top6)})" if len(matched_top6) > 0 else "0"
        hit_report["Dàn 6 Con Điểm Cao Tiếp Theo"] = f"{len(matched_next6)} nháy ({', '.join(matched_next6)})" if len(matched_next6) > 0 else "0"
        db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Khởi tạo cấu trúc 12 hạt nhân V32.2"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ TENSOR MATRIX 3D - 12 NUKES ENGINE v32.2</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp tệp GZ Sao Lưu Ma Trận V32", type=['gz'])
    
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        try:
            with gzip.open(uploaded_file, "rb") as f:
                payload = json.loads(f.read().decode("utf-8"))
                st.session_state['db_3d'] = payload["db_3d"]
                st.session_state['matrix_np'] = np.array(payload["matrix_raw"], dtype=np.int32)
            st.success("Đã kích hoạt cỗ máy V32.2 an toàn!")
            st.rerun()
        except Exception as e: st.error(f"Lỗi cấu trúc RAM nhị phân: {e}")
            
    if st.session_state['db_3d']['last_digits']:
        export_pack = {
            "db_3d": st.session_state['db_3d'],
            "matrix_raw": st.session_state['matrix_np'].tolist()
        }
        json_string = json.dumps(export_pack)
        gzip_buffer = io.BytesIO()
        with gzip.open(gzip_buffer, "wb", compresslevel=9) as f: f.write(json_string.encode("utf-8"))
        st.download_button(label="💾 XUẤT FILE NÉN (.JSON.GZ)", data=gzip_buffer.getvalue(), file_name="matrix_3d_v322.json.gz", mime="application/gzip")
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    raw_input_text = st.text_area("Dán bảng giải thô chuẩn từ Web:", key="web_raw_field_v32", height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        if raw_input_text:
            digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(raw_text=raw_input_text)
            if digits_107 and len(digits_107) == TOTAL_POS:
                gdb_val = digits_107[3:5]
                process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
                st.toast("🔥 Cập nhật bảng điểm cơ khí an toàn thành công!", icon="🎯")
                st.rerun()
            else: st.error("Lỗi cấu trúc giải thô 107 số!")
        else: st.warning("Ô nhập trống kìa đại ca!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. BIỂU DIỄN 2 ĐẠI DÀN SIÊU TINH ANH CHIẾM SÓNG TRÊN ĐẦU TIỀN TUYẾN ---
st.markdown("<h3><font color='#A855F7'><b>🔮 PHÂN LẬP 12 HẠT NHÂN KỲ T - TỐI ƯU VỐN KỊCH TRẦN</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #A855F7; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

preds = st.session_state['db_3d'].get("last_lab_predictions", {})

if preds:
    top6 = preds.get("top_6_highest", [])
    st.markdown(f"""<div class="box-top6"><span class="title-top6">🔥 DÀN 6 CON ĐIỂM CAO NHẤT (ĐỎ SNIPER - ĐI TIỀN ĐẬM)</span><br>
    <p class="text-top6">{"   -   ".join(top6) if top6 else "Đang tính toán..."}</p></div>""", unsafe_allow_html=True)

    next6 = preds.get("next_6_highest", [])
    st.markdown(f"""<div class="box-next6"><span class="title-next6">🛡️ DÀN 6 CON ĐIỂM CAO TIẾP THEO (XANH BẢO HIỂM - ĐÁNH NHẸ TAY)</span><br>
    <p class="text-next6">{"   -   ".join(next6) if next6 else "Đang tính toán..."}</p></div>""", unsafe_allow_html=True)

    st.divider()
    
    # 🛠️ FIX CHÍ MẠNG DÒNG 357: Dẹp bỏ .background_gradient, dùng style nền mộc của Streamlit tự động đổ bóng
    st.markdown("<h3><font color='#3B82F6'><b>📊 BẢNG ĐIỂM ĐỘNG LỰC HỌC TENSOR - TOP 20 HẠT NHÂN CHU KỲ T</b></font></h3>", unsafe_allow_html=True)
    score_data = st.session_state['db_3d'].get("last_score_board", [])
    if score_data:
        df_score = pd.DataFrame(score_data)
        st.dataframe(df_score, use_container_width=True) # Sử dụng bảng phẳng mộc, loại bỏ hoàn toàn gánh nặng thư viện ngoài

st.divider()

# --- 6. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN CHUẨN KHÍT 2 DÀN MỚI ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN 2 DÀN SIÊU TINH ANH</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    display_history = []
    for h in hist_data:
        cleaned_h = {
            "GĐB": h.get("GĐB", "00"),
            "Dàn 6 Con Điểm Cao Nhất": h.get("Dàn 6 Con Điểm Cao Nhất", "0"),
            "Dàn 6 Con Điểm Cao Tiếp Theo": h.get("Dàn 6 Con Điểm Cao Tiếp Theo", "0"),
            "Ghi chú": h.get("Ghi chú", "")
        }
        if "Khởi tạo" in str(h.get("Ghi chú", "")): cleaned_h["Ghi chú"] = h["Ghi chú"]
        display_history.append(cleaned_h)
        
    df_hist = pd.DataFrame(display_history).fillna("0")
    
    def highlight_wins(val):
        val_str = str(val)
        if "nháy" in val_str:
            if "(" in val_str and "Dàn 6 Con Điểm Cao Nhất" in df_hist.columns[df_hist.isin([val]).any()]:
                return 'background-color: #3B0712; color: #EF4444; font-weight: 900;'
            return 'background-color: #1E3A8A; color: #3B82F6; font-weight: 900;'
        return ''

    st.dataframe(df_hist.style.map(highlight_wins), use_container_width=True, height=300)
