import streamlit as st
import pandas as pd
import json
import gzip  
import numpy as np
import re
import io

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM LAB-TESTING V24.0 ---
st.set_page_config(page_title="Matrix 3D - Lab Testing V24.0", layout="wide")
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

# Khởi tạo cấu trúc dữ liệu thí nghiệm gối đầu trên RAM Session V24.0
if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "wire_matrix_3d": np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "history": [],
        "last_lab_predictions": {} 
    }

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

# --- 3. ĐỘNG CƠ TRÍCH XUẤT PHÂN TÁCH MẬD ĐỘ DÂY V24.0 ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    
    old_matrix = np.array(db["wire_matrix_3d"], dtype=int)
    old_digits = db["last_digits"]
    old_lab_preds = db.get("last_lab_predictions", {})
    
    # 🧠 BƯỚC 1: ĐỐI SOÁT TỰ ĐỘNG KỲ TRƯỚC THEO ĐÚNG ĐỊNH DẠNG 7 DÀN MỚI
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    
    if old_digits != "" and old_lab_preds:
        keys_mapping = {
            "d1_0đ_low": "1. 0đ Ít Dây",
            "d2_0đ_high": "2. 0đ Nhiều Dây",
            "d3_1đ_low": "3. 1đ Ít Dây",
            "d4_1đ_high": "4. 1đ Nhiều Dây",
            "d5_2đ_plus_thô": "5. Dàn 2đ+",
            "d6_1đ_unique": "6. 1đ Độc Quyền",
            "d7_2đ_unique": "7. 2đ Độc Quyền"
        }
        for internal_key, column_name in keys_mapping.items():
            pred_list = old_lab_preds.get(internal_key, [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            
            if total_hits > 0:
                hit_report[column_name] = f"{total_hits} quân ({', '.join(matched_nums)})"
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

    # 🧠 BƯỚC 3: PHÂN TÍCH THỐNG KÊ MẬT ĐỘ SỢI DÂY THEO TỪNG QUÂN SỐ 3D
    # Tạo kho chứa để đếm xem mỗi con 3 càng được hình thành từ bao nhiêu sợi dây (score)
    d1_wires_count = {}  # Lưu con số: số lượng dây đạt 0đ
    d2_wires_count = {}  # Lưu con số: số lượng dây đạt 1đ
    d5_set = set()       # Tập hợp các dây từ 2đ trở lên thô
    
    frequency_in_1đ = {}
    frequency_in_2đ = {}
    
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            for k in range(TOTAL_POS):
                num_cang = digits_107[i] + digits_107[j] + digits_107[k]
                score = new_matrix[i][j][k]
                
                if score == 0:
                    d1_wires_count[num_cang] = d1_wires_count.get(num_cang, 0) + 1
                elif score == 1:
                    d2_wires_count[num_cang] = d2_wires_count.get(num_cang, 0) + 1
                    frequency_in_1đ[num_cang] = frequency_in_1đ.get(num_cang, 0) + 1
                elif score >= 2:
                    d5_set.add(num_cang)
                    if score == 2:
                        frequency_in_2đ[num_cang] = frequency_in_2đ.get(num_cang, 0) + 1

    # 🧠 BƯỚC 4: SẮP XẾP VÀ TRÍCH XUẤT ĐÚNG TOP 50 THEO TIÊU CHÍ CỦA MÀY
    # Dàn 1: 50 số ánh xạ 0đ có ít dây hình thành nhất
    sorted_d1_low = sorted(d1_wires_count.items(), key=lambda x: x[1])
    d1_low_list = [item[0] for item in sorted_d1_low[:50]]
    
    # Dàn 2: 50 số ánh xạ 0đ có nhiều dây hình thành nhất
    sorted_d1_high = sorted(d1_wires_count.items(), key=lambda x: x[1], reverse=True)
    d2_0đ_high_list = [item[0] for item in sorted_d1_high[:50]]
    
    # Dàn 3: 50 số ánh xạ 1đ có ít dây hình thành nhất
    sorted_d2_low = sorted(d2_wires_count.items(), key=lambda x: x[1])
    d3_1đ_low_list = [item[0] for item in sorted_d2_low[:50]]
    
    # Dàn 4: 50 số ánh xạ 1đ có nhiều dây hình thành nhất
    sorted_d2_high = sorted(d2_wires_count.items(), key=lambda x: x[1], reverse=True)
    d4_1đ_high_list = [item[0] for item in sorted_d2_high[:50]]

    # Trích xuất dải số Độc quyền đơn dây (chỉ xuất hiện đúng 1 lần trong nhóm)
    d6_unique_list = [cang for cang, freq in frequency_in_1đ.items() if freq == 1]
    d7_unique_list = [cang for cang, freq in frequency_in_2đ.items() if freq == 1]

    # Lưu trữ trọn gói 7 loại dàn chiến thuật mới vào bộ nhớ RAM
    db["last_lab_predictions"] = {
        "d1_0đ_low": sorted(d1_low_list),
        "d2_0đ_high": sorted(d2_0đ_high_list),
        "d3_1đ_low": sorted(d3_1đ_low_list),
        "d4_1đ_high": sorted(d4_1đ_high_list),
        "d5_2đ_plus_thô": sorted(list(d5_set)),
        "d6_1đ_unique": sorted(d6_unique_list),
        "d7_2đ_unique": sorted(d7_unique_list)
    }

    # Đồng bộ bộ nhớ ma trận
    db["wire_matrix_3d"] = new_matrix.tolist()
    db["last_digits"] = digits_107
    
    if old_digits != "" and old_lab_preds: 
        db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Kỳ khởi tạo ma trận thí nghiệm V4.0"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ TENSOR MATRIX 3D - ADAPTIVE LAB v24.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp tệp JSON hoặc GZ 3D", type=['json', 'gz'])
    
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        try:
            filename = uploaded_file.name
            if filename.endswith(".gz"):
                with gzip.open(uploaded_file, "rb") as f:
                    st.session_state['db_3d'] = json.loads(f.read().decode("utf-8"))
            else:
                st.session_state['db_3d'] = json.load(uploaded_file)
            st.success("Đã hồi sinh bộ nhớ Tensor V24.0 thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tệp cấu trúc: {e}")
            
    if st.session_state['db_3d']['last_digits']:
        json_string = json.dumps(st.session_state['db_3d'])
        gzip_buffer = io.BytesIO()
        with gzip.open(gzip_buffer, "wb", compresslevel=9) as f:
            f.write(json_string.encode("utf-8"))
        
        st.download_button(
            label="💾 XUẤT FILE NÉN TỐI ƯU (.JSON.GZ)", 
            data=gzip_buffer.getvalue(), 
            file_name="matrix_3d_v240.json.gz",
            mime="application/gzip"
        )
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    raw_input_text = st.text_area("Dán bảng giải thô chuẩn từ Web:", key="web_raw_field_v24", height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        if raw_input_text:
            digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(raw_text=raw_input_text)
            if digits_107 and len(digits_107) == TOTAL_POS:
                gdb_val = digits_107[3:5]
                process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
                st.toast("🔥 Phân lập 7 dàn mật độ dây thành công!", icon="🎯")
                st.rerun()
            else:
                st.error("Lỗi cấu trúc 107 số thô!")
        else:
            st.warning("Ô nạp trống kìa đại ca!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN (ĐƯA LÊN ĐẦU THEO LỆNH) ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ KIỂM ĐỊNH ĐỐI SOÁT QUÂN ĂN CỦA 7 DÀN CHIẾN THUẬT</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    df_hist = pd.DataFrame(hist_data).fillna("0")
    cols = list(df_hist.columns)
    
    order_cols = [
        "GĐB", 
        "1. 0đ Ít Dây", "2. 0đ Nhiều Dây", 
        "3. 1đ Ít Dây", "4. 1đ Nhiều Dây", 
        "5. Dàn 2đ+", "6. 1đ Độc Quyền", "7. 2đ Độc Quyền"
    ]
    final_cols = [c for c in order_cols if c in cols] + [c for c in cols if c not in order_cols]
    
    def highlight_wins(val):
        val_str = str(val)
        if "quân" in val_str:
            return 'background-color: #1F2937; color: #10B981; font-weight: 900; border: 1px solid #10B981;'
        elif val_str == "0":
            return 'color: #4B5563; font-weight: normal;'
        return ''

    st.dataframe(df_hist[final_cols].style.map(highlight_wins), use_container_width=True, height=400)
else:
    st.info("Hệ thống gối đầu dữ liệu đang chờ kỳ quay tiếp theo để khải hoàn bảng kiểm định đối soát số quân ăn!")

st.divider()

# --- 6. KHU VỰC PHƠI BÀY CHI TIẾT 7 LOẠI DÀN TRÍCH XUẤT MỚI ---
st.markdown("<h3><font color='#A855F7'><b>🔮 CHI TIẾT DANH SÁCH 7 PHÂN LỚP SỐ THEO THIẾT KẾ MỚI</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #A855F7; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

preds = st.session_state['db_3d'].get("last_lab_predictions", {})

if preds:
    # 🌟 DÀN 6: 1 điểm độc quyền
    d6 = preds.get("d6_1đ_unique", [])
    st.markdown(f"""<div class="box-vip"><span class="title-vip">💎 6. DÀN 1 ĐIỂM ĐỘC QUYỀN TRỰC DIỆN (Tổng số: {len(d6)} quân)</span><br>
    <p class="text-vip">{"   -   ".join(d6) if d6 else "Trống số!"}</p></div>""", unsafe_allow_html=True)

    # 🌟 DÀN 7: 2 điểm độc quyền
    d7 = preds.get("d7_2đ_unique", [])
    st.markdown(f"""<div class="box-vip"><span class="title-vip">💎 7. DÀN 2 ĐIỂM ĐỘC QUYỀN TRỰC DIỆN (Tổng số: {len(d7)} quân)</span><br>
    <p class="text-vip">{"   -   ".join(d7) if d7 else "Trống số!"}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📦 CÁC DÀN TRÍCH XUẤT THEO TRỤC MẬT ĐỘ DÂY ĐỘNG:")

    # 📦 DÀN 1: 0đ ít dây nhất
    d1 = preds.get("d1_0đ_low", [])
    with st.expander(f"📦 1. DÀN 50 SỐ ÁNH XẠ 0Đ CÓ ÍT DÂY HÌNH THÀNH NHẤT"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d1)}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 2: 0đ nhiều dây nhất
    d2 = preds.get("d2_0đ_high", [])
    with st.expander(f"📦 2. DÀN 50 SỐ ÁNH XẠ 0Đ CÓ NHIỀU DÂY HÌNH THÀNH NHẤT"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d2)}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 3: 1đ ít dây nhất
    d3 = preds.get("d3_1đ_low", [])
    with st.expander(f"📦 3. DÀN 50 SỐ ÁNH XẠ 1Đ CÓ ÍT DÂY HÌNH THÀNH NHẤT"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d3)}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 4: 1đ nhiều dây nhất
    d4 = preds.get("d4_1đ_high", [])
    with st.expander(f"📦 4. DÀN 50 SỐ ÁNH XẠ 1Đ CÓ NHIỀU DÂY HÌNH THÀNH NHẤT"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d4)}</p></div>', unsafe_allow_html=True)

    # 📦 DÀN 5: Dàn dây từ 2đ trở lên
    d5 = preds.get("d5_2đ_plus_thô", [])
    with st.expander(f"📦 5. DÀN TẬP HỢP CÁC DÂY TỪ 2Đ TRỞ LÊN THÔ (Tổng số: {len(d5)} quân)"):
        st.markdown(f'<div class="box-cang3d"><p class="text-cang3d">{"   -   ".join(d5)}</p></div>', unsafe_allow_html=True)

else:
    st.info("Hệ thống đang trống. Vui lòng nạp bảng giải thô để phân tách trận hình mới!")
