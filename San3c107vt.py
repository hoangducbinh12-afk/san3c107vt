import streamlit as st
import pandas as pd
import json
import gzip  
import numpy as np
import re
import io

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM LAB-TESTING V27.1 ---
st.set_page_config(page_title="Matrix 3D - Tensor Purify V27.1", layout="wide")
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

# 🛠️ NÂNG CẤP TOÁN TỔ HỢP: Tự động lập bộ 280 con bằng thuật toán, loại bỏ 100% lỗi gõ tay trùng số!
@st.cache_data
def get_pure_kep_ganh_280():
    pure_list = []
    for i in range(1000):
        num_str = str(i).zfill(3)
        # Nếu số lượng chữ số độc nhất (Unique characters) từ 1 đến 2 -> Thuộc bộ của đại ca
        if 1 <= len(set(num_str)) <= 2:
            pure_list.append(num_str)
    return pure_list

KEP_GANH_280 = get_pure_kep_ganh_280()
KEP_GANH_SET = set(KEP_GANH_280)

# Hàm lập dàn 280 con dựa theo bộ lọc nén 3 chữ số (3 Chạm)
def generate_k_g_by_touches(touches):
    touch_set = set(str(t) for t in touches)
    result_dan = []
    for num in KEP_GANH_280:
        if all(char in touch_set for char in num):
            result_dan.append(num)
    return sorted(result_dan)

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

# --- 3. ĐỘNG CƠ MA TRẬN PHÂN TÁCH SỢI DÂY TINH KHIẾT V27.1 ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    old_matrix = st.session_state['matrix_np'] 
    old_digits = db["last_digits"]
    old_lab_preds = db.get("last_lab_predictions", {})
    
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    
    if old_digits != "" and old_lab_preds:
        keys_mapping = {
            "d1_pa1_high": "Dàn 1 (PA1-3ChạmCao)",
            "d2_pa1_low": "Dàn 2 (PA1-3ChạmThấp)",
            "d3_pa2_high": "Dàn 3 (PA2-3ChạmCao)",
            "d4_pa2_low": "Dàn 4 (PA2-3ChạmThấp)"
        }
        for internal_key, column_name in keys_mapping.items():
            pred_list = old_lab_preds.get(internal_key, [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            if total_hits > 0:
                hit_report[column_name] = f"{total_hits} nháy ({', '.join(matched_nums)})"
            else:
                hit_report[column_name] = "0"
                
    new_matrix = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=np.int32)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23 and num_past in KEP_GANH_SET: 
                        new_matrix[i][j][k] = old_matrix[i][j][k] + 1

    touch_score_pa1 = {str(i): 0 for i in range(10)}  
    touch_score_pa2 = {str(i): 0 for i in range(10)}  
    
    frequency_in_1đ = {}
    frequency_in_2đ = {}
    
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            for k in range(TOTAL_POS):
                num_cang = digits_107[i] + digits_107[j] + digits_107[k]
                if num_cang in KEP_GANH_SET:
                    score = int(new_matrix[i][j][k])
                    
                    if score >= 1:
                        for char in set(num_cang):  
                            touch_score_pa1[char] += score
                            
                    if score == 1:
                        frequency_in_1đ[num_cang] = frequency_in_1đ.get(num_cang, 0) + 1
                    elif score == 2:
                        frequency_in_2đ[num_cang] = frequency_in_2đ.get(num_cang, 0) + 1

    d6_unique = [cang for cang, freq in frequency_in_1đ.items() if freq == 1]
    d7_unique = [cang for cang, freq in frequency_in_2đ.items() if freq == 1]
    all_unique_3c = d6_unique + d7_unique
    
    for num in all_unique_3c:
        for char in set(num):
            touch_score_pa2[char] += 1

    sorted_pa1 = sorted(touch_score_pa1.items(), key=lambda x: x[1], reverse=True)
    pa1_high_touches = [item[0] for item in sorted_pa1[:3]]  
    pa1_low_touches = [item[0] for item in sorted_pa1[-3:]]   
    
    sorted_pa2 = sorted(touch_score_pa2.items(), key=lambda x: x[1], reverse=True)
    pa2_high_touches = [item[0] for item in sorted_pa2[:3]]  
    pa2_low_touches = [item[0] for item in sorted_pa2[-3:]]   

    d1_list = generate_k_g_by_touches(pa1_high_touches)
    d2_list = generate_k_g_by_touches(pa1_low_touches)
    d3_list = generate_k_g_by_touches(pa2_high_touches)
    d4_list = generate_k_g_by_touches(pa2_low_touches)

    db["last_lab_predictions"] = {
        "pa1_high_txt": ", ".join(pa1_high_touches),
        "pa1_low_txt": ", ".join(pa1_low_touches),
        "pa2_high_txt": ", ".join(pa2_high_touches),
        "pa2_low_txt": ", ".join(pa2_low_touches),
        
        "d1_pa1_high": d1_list,
        "d2_pa1_low": d2_list,
        "d3_pa2_high": d3_list,
        "d4_pa2_low": d4_list
    }

    st.session_state['matrix_np'] = new_matrix
    db["last_digits"] = digits_107
    
    # Lưu mảng thực tế phục vụ đếm ngày khan
    hit_report["Saved_3C_Real"] = cang3c_23
    
    if old_digits != "" and old_lab_preds: 
        db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Khởi tạo ma trận Purify V27.1"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ TENSOR MATRIX 3D - TRI-TOUCH PURIFY v27.1</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp tệp GZ Sao Lưu Ma Trận V27", type=['gz'])
    
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        try:
            with gzip.open(uploaded_file, "rb") as f:
                payload = json.loads(f.read().decode("utf-8"))
                st.session_state['db_3d'] = payload["db_3d"]
                st.session_state['matrix_np'] = np.array(payload["matrix_raw"], dtype=np.int32)
            st.success("Đã hồi sinh trạm lọc siêu đặc Purify V27.1 chuẩn 280 con!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi cấu trúc RAM nhị phân: {e}")
            
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
            file_name="matrix_3d_v271.json.gz",
            mime="application/gzip"
        )
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    raw_input_text = st.text_area("Dán bảng giải thô chuẩn từ Web:", key="web_raw_field_v27", height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        if raw_input_text:
            digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(raw_text=raw_input_text)
            if digits_107 and len(digits_107) == TOTAL_POS:
                gdb_val = digits_107[3:5]
                process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
                st.toast("🔥 Phân lập ma trận dây 3 chạm tinh khiết thành công!", icon="⚡")
                st.rerun()
            else:
                st.error("Lỗi cấu trúc giải thô 107 số!")
        else:
            st.warning("Ô nhập trống kìa đại ca!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN 4 DÀN CHẠM CHIẾN THUẬT (CHUẨN 280 CON THƯỚC NGẮM)</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    display_history = []
    for h in hist_data:
        cleaned_h = {k: v for k, v in h.items() if k != "Saved_3C_Real"}
        display_history.append(cleaned_h)
        
    df_hist = pd.DataFrame(display_history).fillna("0")
    cols = list(df_hist.columns)
    
    order_cols = ["GĐB", "Dàn 1 (PA1-3ChạmCao)", "Dàn 2 (PA1-3ChạmThấp)", "Dàn 3 (PA2-3ChạmCao)", "Dàn 4 (PA2-3ChạmThấp)"]
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
    st.info("Hệ thống ma trận siêu đặc V27.1 đã nạp RAM! Hãy dán giải kỳ sau để xuất bản đối soát quân ăn.")

st.divider()

# --- 6. KHU VỰC PHƠI BÀY CHI TIẾT 4 DÀN 3 CHẠM HIỆN TẠI ---
st.markdown("<h3><font color='#A855F7'><b>🔮 BẢNG PHÂN LẬP TRÍCH XUẤT 3 CHẠM VÀ CÁC DÀN 21 CON KỲ NÀY</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #A855F7; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

preds = st.session_state['db_3d'].get("last_lab_predictions", {})

if preds:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📡 PHƯƠNG ÁN 1: RỐN CẦU TỤ")
        st.success(f"🔥 3 Chạm Cao Điểm Nhất: [ {preds.get('pa1_high_txt')} ]")
        st.error(f"❄️ 3 Chạm Thấp Điểm Nhất: [ {preds.get('pa1_low_txt')} ]")
    with col2:
        st.subheader("🎯 PHƯƠNG ÁN 2: LÕI ĐỘC QUYỀN")
        st.success(f"🔥 3 Chạm Cao Điểm Nhất: [ {preds.get('pa2_high_txt')} ]")
        st.error(f"❄️ 4 Chạm Thấp Điểm Nhất: [ {preds.get('pa2_low_txt')} ]")
        
    st.divider()
    st.markdown("### 📦 DANH SÁCH 4 DÀN CHIẾN THUẬT 3 CHẠM KÉP GÁNH (21 CON KINH TẾ):")

    # 📦 DÀN 1
    d1 = preds.get("d1_pa1_high", [])
    with st.expander(f"📦 DÀN 1: PHƯƠNG ÁN 1 CAO ĐIỂM (Tổng số: {len(d1)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d1) if d1 else "Kỳ này trống số do chạm khuyết!"}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 2
    d2 = preds.get("d2_pa1_low", [])
    with st.expander(f"📦 DÀN 2: PHƯƠNG ÁN 1 THẤP ĐIỂM (Tổng số: {len(d2)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d2) if d2 else "Kỳ này trống số!"}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 3
    d3 = preds.get("d3_pa2_high", [])
    with st.expander(f"📦 DÀN 3: PHƯƠNG ÁN 2 CAO ĐIỂM (Tổng số: {len(d3)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d3) if d3 else "Kỳ này trống số!"}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 4
    d4 = preds.get("d4_pa2_low", [])
    with st.expander(f"📦 DÀN 4: PHƯƠNG ÁN 2 THẤP ĐIỂM (Tổng số: {len(d4)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d4) if d4 else "Kỳ này trống số!"}</p></div>', unsafe_allow_html=True)

else:
    st.info("Hệ thống đang trống. Vui lòng nạp kết quả thô để bốc đầu 3 bộ chạm băm nát nhà đài!")
