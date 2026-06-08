import streamlit as st
import pandas as pd
import json
import numpy as np
import re

# --- 1. CẤU HÌNH HỆ THỐNG MÀN HÌNH CYBERPUNK PREMIUM V19.0 ---
st.set_page_config(page_title="Matrix 3D - Dynamic Filter V19.0", layout="wide")
TOTAL_POS = 107 

st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #10B981; color: #10B981; }
    
    .box-cang3d { background-color: #05070B; padding: 12px; border-radius: 12px; border: 2px solid #A855F7; margin-bottom: 12px; }
    .box-de2s { background-color: #0A0204; padding: 12px; border-radius: 12px; border: 2px solid #FF3344; margin-bottom: 12px; }
    .box-cangvip { background-color: #050C0A; padding: 15px; border-radius: 12px; border: 3px solid #FFD700; margin-bottom: 15px; }
    
    .title-cang3d { color: #A855F7 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-de2s { color: #FF3344 !important; font-size: 16px !important; font-weight: 900 !important; }
    .title-cangvip { color: #FFD700 !important; font-size: 16px !important; font-weight: 900 !important; }
    
    .text-cang3d { color: #E2E8F0 !important; font-size: 17px !important; font-weight: bold; font-family: monospace; letter-spacing: 2px; line-height: 1.4; word-wrap: break-word; }
    .text-de2s { color: #FFD700 !important; font-size: 22px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 3px; line-height: 1.5; word-wrap: break-word; }
    .text-cangvip { color: #FF3344 !important; font-size: 24px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 3px; line-height: 1.5; word-wrap: break-word; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo cấu trúc ma trận 3D
if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "wire_matrix_3d": np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "history": [],
        "last_predictions_groups": {},
        "last_de_vip_list": [],      # Két gối đầu đối chiếu GĐB
        "last_cang3c_2đ_raw": []     # Lưu trữ gốc dàn 3C nhóm 2đ để trích xuất động về sau
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""

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

# --- 3. ĐỘNG CƠ MA TRẬN TENSOR KHÔNG CAN THIỆP LỌC ĐẦU ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    
    old_matrix = np.array(db["wire_matrix_3d"], dtype=int)
    old_digits = db["last_digits"]
    old_preds = db.get("last_predictions_groups", {})
    old_de_vip = db.get("last_de_vip_list", [])
    
    # 🧠 BƯỚC 1: ĐỐI SOÁT TỰ ĐỘNG LỊCH SỬ KỲ TRƯỚC
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    if old_digits != "":
        if old_de_vip:
            if gdb_val in old_de_vip: hit_report["Dàn ĐB (Đuôi 3C 2đ)"] = f"🎯 ĂN ({gdb_val})"
            else: hit_report["Dàn ĐB (Đuôi 3C 2đ)"] = "Trượt"
        else: hit_report["Dàn ĐB (Đuôi 3C 2đ)"] = "Trống"

    if old_preds:
        for group_name, group_data in old_preds.items():
            pred_list = group_data.get("list", [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            if total_hits > 0: hit_report[f"Cột {group_name}"] = f"{total_hits} nháy ({', '.join(matched_nums)})"
            else: hit_report[f"Cột {group_name}"] = "0"
                
    # 🧠 BƯỚC 2: TIẾN HÀNH CĂNG DÂY MA TRẬN 3D PHẲNG TRÊN RAM
    new_matrix = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23: new_matrix[i][j][k] = old_matrix[i][j][k] + 1
                    else: new_matrix[i][j][k] = 0

    # 🧠 BƯỚC 3: PHÂN LOẠI NHÓM ĐIỂM + LỌC ĐỘC QUYỀN ĐƠN DÂY TỰ NHIÊN
    max_score = int(new_matrix.max())
    current_predictions = {}
    next_de_vip_list = []
    next_cang3c_2đ_raw = [] # Két chứa gốc toàn bộ con 3C của nhóm 2đ
    
    if max_score >= 1:
        for s in range(1, max_score + 1):
            coords = np.argwhere(new_matrix == s)
            if len(coords) == 0: continue
            
            total_wires_in_group = len(coords)
            cang_frequency_in_group = {}
            for r, c, l in coords:
                num_cang = digits_107[r] + digits_107[c] + digits_107[l]
                cang_frequency_in_group[num_cang] = cang_frequency_in_group.get(num_cang, 0) + 1
                
            unique_cang_list = [cang for cang, freq in cang_frequency_in_group.items() if freq == 1]
            
            if unique_cang_list:
                current_predictions[f"{s} đ"] = {
                    "total_wires": total_wires_in_group,
                    "list": sorted(unique_cang_list)
                }
                
                # Trích xuất dữ liệu gốc cho nhóm dây 2 ngày ăn thông
                if s == 2:
                    next_cang3c_2đ_raw = sorted(unique_cang_list)
                    loto_ends = [cang3c[-2:] for cang3c in unique_cang_list]
                    next_de_vip_list = sorted(list(set(loto_ends)))

    # Đồng bộ lưu trữ két sắt
    db["wire_matrix_3d"] = new_matrix.tolist()
    db["last_digits"] = digits_107
    db["last_predictions_groups"] = current_predictions
    db["last_de_vip_list"] = next_de_vip_list
    db["last_cang3c_2đ_raw"] = next_cang3c_2đ_raw
    
    if old_digits != "": db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Kỳ khởi tạo ma trận"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ MATRIX 3D - DYNAMIC FILTER OPERATOR v19.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp file JSON 3D", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        st.session_state['db_3d'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db_3d']['last_digits']:
        st.download_button("💾 XUẤT FILE SAO LƯU JSON", json.dumps(st.session_state['db_3d']), "matrix_3d_v190.json")
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ THÔ")
    st.session_state['raw_input'] = st.text_area("Dán bảng giải thô chuẩn từ Web:", value=st.session_state.get('raw_input', ""), height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(st.session_state['raw_input'])
        if digits_107 and len(digits_107) == TOTAL_POS:
            gdb_val = digits_107[3:5]
            process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
            st.rerun()
        else:
            st.error("Lỗi cấu trúc bảng giải! Vui lòng kiểm tra lại dữ liệu dán vào.")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC ĐIỀU HÀNH VÀ TRÍCH XUẤT TRUNG TÂM ---
st.markdown("<h3><font color='#FFD700'><b>👑 TRẠM KHAI THÁC 3 CÀNG THEO DÀN ĐỘNG</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FFD700; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

cang3c_2đ_gốc = st.session_state['db_3d'].get("last_cang3c_2đ_raw", [])
next_de_vip = st.session_state['db_3d'].get("last_de_vip_list", [])

if next_de_vip:
    total_de = len(next_de_vip)
    de_list_str = "   -   ".join(next_de_vip)
    
    # 1. Giữ nguyên cái hộp Đề thô rực rỡ để mày đối chiếu GĐB
    st.markdown(f"""
        <div class="box-de2s">
            <span class="title-de2s">🎯 DÀN ĐỀ THÔ ĐỐI CHIẾU GĐB (Tạo từ đuôi 3C nhóm 2đ độc nhất -> Bỏ trùng: {total_de} quân)</span><br>
            <p class="text-de2s">{de_list_str}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 2. 🛠️ 🛠️ Ô NHẬP DÀN 2D ĐỘNG TẠI TRUNG TÂM THEO Ý MÀY
    st.markdown("#### 📥 NHẬP DÀN SỐ 2D CỦA MÀY VÀO ĐÂY ĐỂ TRÍCH XUẤT 3 CÀNG ĐÍCH DANH:")
    input_dynamic_2d = st.text_input("Gõ hoặc dán dàn số 2D bất kỳ (Ví dụ: 12, 34, 56, 78...):", key="dynamic_loto_filter")
    
    # Xử lý cắt chuỗi lấy mảng số từ ô văn bản động
    parsed_dynamic_2d = [n.strip() for n in input_dynamic_2d.replace(",", " ").split() if n.isdigit()]
    
    if parsed_dynamic_2d:
        # Chạy thuật toán lọc động trực tiếp trên RAM: Chỉ nhặt con 3C có đuôi nằm trong dàn 2D vừa gõ
        extracted_cang_vip = [cang for cang in cang3c_2đ_gốc if cang[-2:] in parsed_dynamic_2d]
        total_vip_cang = len(extracted_cang_vip)
        
        if extracted_cang_vip:
            vip_cang_str = "   -   ".join(extracted_cang_vip)
            st.markdown(f"""
                <div class="box-cangvip">
                    <span class="title-cangvip">👑 DÀN 3 CÀNG TRÍCH XUẤT ĐÍCH DANH (Khớp theo dàn 2D nhập vào -> Lọc được: {total_vip_cang} quân)</span><br>
                    <p class="text-cangvip">{vip_cang_str}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("❌ Không tìm thấy con 3 Càng nào trong nhóm 2đ có đuôi trùng khớp với dàn 2D mày vừa nhập!")
            
st.divider()

# Hiển thị các dàn thô nhóm điểm cũ ở bên dưới
preds_groups = st.session_state['db_3d'].get("last_predictions_groups", {})
if preds_groups:
    for group_name, group_data in preds_groups.items():
        total_dây = group_data.get("total_wires", 0) 
        pred_list = group_data.get("list", [])
        total_quân = len(pred_list)
        list_str = "   -   ".join(pred_list)
        st.markdown(f"""
            <div class="box-cang3d">
                <span class="title-cang3d">📦 DÀN 3 CÀNG THÔ NHÓM {group_name.upper()} (Số dây: {total_dây} đ -> Lọc độc quyền: {total_quân} quân)</span><br>
                <p class="text-cang3d">{list_str}</p>
            </div>
            """, unsafe_allow_html=True)
else:
    if not next_de_vip: st.info("Hệ thống trống. Vui lòng dán kết quả thô vào Sidebar bên trái để kích hoạt cỗ máy!")

# --- 6. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TỰ ĐỘNG ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TENSOR 3D</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    df_hist = pd.DataFrame(hist_data).fillna("0")
    cols = list(df_hist.columns)
    
    if "GĐB" in cols: cols.insert(0, cols.pop(cols.index("GĐB")))
    if "Dàn ĐB (Đuôi 3C 2đ)" in cols: cols.insert(1, cols.pop(cols.index("Dàn ĐB (Đuôi 3C 2đ)")))
    
    def highlight_wins(val):
        val_str = str(val)
        if "🎯 ĂN" in val_str: return 'background-color: #450A0A; color: #FF3344; font-weight: 900; border: 1px solid #FF3344;'
        elif "nháy" in val_str: return 'background-color: #1F2937; color: #10B981; font-weight: 900; border: 1px solid #10B981;'
        elif val_str in ["Trượt", "0"]: return 'color: #4B5563; font-weight: normal;'
        return ''

    st.dataframe(df_hist[cols].style.map(highlight_wins), use_container_width=True, height=450)
