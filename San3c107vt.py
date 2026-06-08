import streamlit as st
import pandas as pd
import json
import numpy as np
import re

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM CYBERPUNK V20.0 ---
st.set_page_config(page_title="Matrix 3D - Counter Strike V20.0", layout="wide")
TOTAL_POS = 107 

st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #FF3344; color: #FF3344; }
    
    .box-cang3d { background-color: #05070B; padding: 12px; border-radius: 12px; border: 2px solid #A855F7; margin-bottom: 12px; }
    .box-blacklist { background-color: #0F0305; padding: 12px; border-radius: 12px; border: 2px solid #EF4444; margin-bottom: 12px; }
    .box-survived { background-color: #020C08; padding: 15px; border-radius: 12px; border: 3px solid #10B981; margin-bottom: 15px; }
    
    .title-cang3d { color: #A855F7 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-blacklist { color: #EF4444 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-survived { color: #10B981 !important; font-size: 16px !important; font-weight: 900 !important; }
    
    .text-cang3d { color: #E2E8F0 !important; font-size: 16px !important; font-weight: bold; font-family: monospace; letter-spacing: 2px; line-height: 1.4; word-wrap: break-word; }
    .text-blacklist { color: #94A3B8 !important; font-size: 15px !important; font-family: monospace; letter-spacing: 1px; word-wrap: break-word; }
    .text-survived { color: #FFD700 !important; font-size: 26px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 4px; line-height: 1.5; word-wrap: break-word; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo cấu trúc dữ liệu ma trận 3D gối đầu trên RAM
if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "wire_matrix_3d": np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "history": [],
        "last_predictions_groups": {},
        "all_cang3c_2đ_plus_raw": [], # Két chứa TOÀN BỘ ánh xạ từ dây 2đ trở lên (Không lọc độc quyền)
        "last_survived_predictions": [] # Lưu dàn sống sót hôm qua để hôm sau đối soát nháy nổ
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

# --- 3. ĐỘNG CƠ MA TRẬN TENSOR 3D - THU THẬP TẤT CẢ ÁNH XẠ DÂY >= 2Đ ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    
    old_matrix = np.array(db["wire_matrix_3d"], dtype=int)
    old_digits = db["last_digits"]
    old_preds = db.get("last_predictions_groups", {})
    old_survived_cang = db.get("last_survived_predictions", []) # Dàn lọc động sống sót hôm qua
    
    # 🧠 BƯỚC 1: ĐỐI SOÁT TỰ ĐỘNG LỊCH SỬ KỲ TRƯỚC
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    if old_digits != "":
        # 1. Đối soát riêng cho Dàn 3 Càng lọc ngược sống sót
        if old_survived_cang:
            matched_survived = [num for num in old_survived_cang if num in cang3c_23]
            if matched_survived:
                hit_report["💥 DÀN 3C NGƯỢC"] = f"🔥 HỐC {len(matched_survived)} NHÁY ({', '.join(matched_survived)})"
            else:
                hit_report["💥 DÀN 3C NGƯỢC"] = "Trượt"
        else:
            hit_report["💥 DÀN 3C NGƯỢC"] = "Trống"

    # Đối soát các cột dàn thô đơn dây (vẫn giữ lại để theo dõi hệ thống)
    if old_preds:
        for group_name, group_data in old_preds.items():
            pred_list = group_data.get("list", [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            if total_hits > 0: hit_report[f"Cột {group_name}"] = f"{total_hits} nháy ({', '.join(matched_nums)})"
            else: hit_report[f"Cột {group_name}"] = "0"
                
    # 🧠 BƯỚC 2: TIẾN HÀNH CĂNG DÂY MA TRẬN 3D
    new_matrix = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23: new_matrix[i][j][k] = old_matrix[i][j][k] + 1
                    else: new_matrix[i][j][k] = 0

    # 🧠 BƯỚC 3: PHÂN LOẠI NHÓM ĐIỂM + THU HOẠCH TẬP HỢP TỬ HÌNH KHÔNG GIỚI HẠN
    max_score = int(new_matrix.max())
    current_predictions = {}
    blacklist_3d_accumulator = set() # Dùng Set để tự động gộp và loại bỏ con trùng trong danh sách đen
    
    if max_score >= 1:
        for s in range(1, max_score + 1):
            coords = np.argwhere(new_matrix == s)
            if len(coords) == 0: continue
            
            total_wires_in_group = len(coords)
            cang_frequency_in_group = {}
            for r, c, l in coords:
                num_cang = digits_107[r] + digits_107[c] + digits_107[l]
                cang_frequency_in_group[num_cang] = cang_frequency_in_group.get(num_cang, 0) + 1
                
                # CHÍNH SÁCH MỚI: Cứ thuộc nhóm dây từ 2 điểm trở lên (s >= 2) là tống hết vào danh sách đen phá hủy số
                if s >= 2:
                    blacklist_3d_accumulator.add(num_cang)
                    
            # Trích xuất dàn thô đơn dây nguyên thủy phục vụ theo dõi đối chiếu
            unique_cang_list = [cang for cang, freq in cang_frequency_in_group.items() if freq == 1]
            if unique_cang_list:
                current_predictions[f"{s} đ"] = {
                    "total_wires": total_wires_in_group,
                    "list": sorted(unique_cang_list)
                }

    # Đồng bộ kho trạng thái ẩn trên RAM
    db["wire_matrix_3d"] = new_matrix.tolist()
    db["last_digits"] = digits_107
    db["last_predictions_groups"] = current_predictions
    db["all_cang3c_2đ_plus_raw"] = sorted(list(blacklist_3d_accumulator)) # Lưu toàn bộ kho đen
    
    if old_digits != "": db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Kỳ khởi tạo ma trận"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ MATRIX 3D - COUNTER STRIKE OPERATOR v20.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp file JSON 3D", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        st.session_state['db_3d'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db_3d']['last_digits']:
        st.download_button("💾 XUẤT FILE SAO LƯU JSON", json.dumps(st.session_state['db_3d']), "matrix_3d_v200.json")
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    st.session_state['raw_input'] = st.text_area("Dán bảng giải thô chuẩn từ Web:", value=st.session_state.get('raw_input', ""), height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(st.session_state['raw_input'])
        if digits_107 and len(digits_107) == TOTAL_POS:
            gdb_val = digits_107[3:5]
            process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
            st.rerun()
        else:
            st.error("Lỗi cấu trúc bảng giải dán vào!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC ĐIỀU HÀNH VÀ LỌC NGƯỢC KHÔNG GIAN TRUNG TÂM ---
st.markdown("<h3><font color='#10B981'><b>👑 TRẠM BẮN TỈA 3 CÀNG THEO CHIẾN THUẬT LOẠI TRỪ</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

blacklist_3d_gốc = st.session_state['db_3d'].get("all_cang3c_2đ_plus_raw", [])

# Luôn hiển thị trạng thái tổng số lượng "Tử tù 3D" để mày nắm bắt độ loãng ma trận
total_black = len(blacklist_3d_gốc)

# 🛠️ Ô NHẬP DÀN SỐ ĐỀ/LÔ 2D CẦU SOI TẠI TRUNG TÂM MÀN HÌNH MÀY YÊU CẦU
st.markdown("#### 📥 NHẬP DÀN SỐ LOTO/ĐỀ 2D CẦU SOI VÀO ĐÂY ĐỂ ĐỘT PHÁ CÀNG CHỐNG TRÙNG:")
input_dynamic_2d = st.text_input("Gõ hoặc dán dàn loto 2D chiến lược (Ví dụ: 12, 34, 56...):", key="dynamic_loto_strike")

parsed_dynamic_2d = [n.strip() for n in input_dynamic_2d.replace(",", " ").split() if n.isdigit()]

if parsed_dynamic_2d:
    # 🧠 THUẬT TOÁN COUNTER-STRIKE: 
    # 1. Dựng lưới thô đầy đủ 10 đầu càng (từ 0 đến 9) ứng với tất cả các số 2D nhập vào
    grid_3c_thô = []
    for loto_2s in parsed_dynamic_2d:
        loto_clean = loto_2s.zfill(2)
        for càng_digit in range(10):
            grid_3c_thô.append(f"{càng_digit}{loto_clean}")
            
    # 2. KIỂM TRA ĐIỀU KIỆN CHỐNG TRÙNG TUYỆT ĐỐI: Con nào CÓ trong tập hợp đen -> LOẠI. Con nào KHÔNG CÓ -> HIỂN THỊ
    survived_3c_list = [cang for cang in grid_3c_thô if cang not in blacklist_3d_gốc]
    total_survived = len(survived_3c_list)
    
    # Đồng bộ lưu lại dàn sống sót này vào bộ nhớ để ngày mai so nháy tự động ở bảng lịch sử
    st.session_state['db_3d']["last_survived_predictions"] = survived_3c_list
    
    # In kết quả rực rỡ lên màn hình trung tâm
    if survived_3c_list:
        survived_str = "   -   ".join(survived_3c_list)
        st.markdown(f"""
            <div class="box-survived">
                <span class="title-survived">👑 DÀN 3 CÀNG TINH KHIẾT SỐNG SÓT (Vượt qua lưới quét chống trùng -> Còn lại: {total_survived} quân)</span><br>
                <p class="text-survived">{survived_str}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("🚨 Toàn bộ các đầu càng của dàn 2D này đều bị dính líu nằm trọn trong danh sách dây sụp đổ! Không còn con nào sống sót.")
else:
    # Nếu chưa nhập loto 2D, nhắc nhở găm số
    st.info("💡 Vui lòng nhập dàn số 2D cần soi vào ô trên. Hệ thống sẽ ngay lập tức đối chiếu với kho dây sụp đổ để khạc số càng sạch!")

# Hiển thị khối thông tin danh sách đen bên dưới để mày đối chiếu trực quan
if blacklist_3d_gốc:
    black_str = "  ,  ".join(blacklist_3d_gốc)
    st.markdown(f"""
        <div class="box-blacklist">
            <span class="title-blacklist">💀 TẬP HỢP TỬ HÌNH 3D (Ánh xạ của toàn bộ hệ thống dây đạt từ 2 điểm trở lên -> Tổng số: {total_black} quân)</span><br>
            <div class="text-blacklist" style="max-height: 80px; overflow-y: auto;">{black_str}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Hiển thị các dàn thô đơn dây nguyên thủy ở dưới đáy bảng
preds_groups = st.session_state['db_3d'].get("last_predictions_groups", {})
if preds_groups:
    for group_name, group_data in preds_groups.items():
        total_dây = group_data.get("total_wires", 0) 
        pred_list = group_data.get("list", [])
        total_quân = len(pred_list)
        list_str = "   -   ".join(pred_list)
        st.markdown(f"""
            <div class="box-cang3d">
                <span class="title-cang3d">📦 THAM KHẢO DÀN ĐƠN DÂY ĐỘC QUYỀN NHÓM {group_name.upper()} (Số dây: {total_dây} đ -> {total_quân} quân)</span><br>
                <p class="text-cang3d">{list_str}</p>
            </div>
            """, unsafe_allow_html=True)

# --- 6. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TỰ ĐỘNG ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TENSOR 3D</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    df_hist = pd.DataFrame(hist_data).fillna("0")
    cols = list(df_hist.columns)
    
    if "GĐB" in cols: cols.insert(0, cols.pop(cols.index("GĐB")))
    if "💥 DÀN 3C NGƯỢC" in cols: cols.insert(1, cols.pop(cols.index("💥 DÀN 3C NGƯỢC")))
    
    def highlight_wins(val):
        val_str = str(val)
        if "🔥 HỐC" in val_str: # Ăn 3 càng lọc ngược nổ rực rỡ màu Cam lửa viền đỏ cực ngầu
            return 'background-color: #451A03; color: #F97316; font-weight: 900; border: 2px solid #F97316;'
        elif "nháy" in val_str: # Ăn các giải dàn thô giữ màu xanh lục
            return 'background-color: #1F2937; color: #10B981; font-weight: 900; border: 1px solid #10B981;'
        elif val_str in ["Trượt", "0"]: return 'color: #4B5563; font-weight: normal;'
        return ''

    st.dataframe(df_hist[cols].style.map(highlight_wins), use_container_width=True, height=450)
