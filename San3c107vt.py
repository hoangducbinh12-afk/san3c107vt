import streamlit as st
import pandas as pd
import json
import numpy as np
import re

# --- 1. CẤU HÌNH HỆ THỐNG MÀN HÌNH CYBERPUNK PREMIUM V18.0 ---
st.set_page_config(page_title="Matrix 3D - Sniper Core V18.0", layout="wide")
TOTAL_POS = 107 

st.markdown("""
    <style>
    .main { background-color: #0A0D14; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3.5em; background-color: #161B26; color: #F0F4F8; border: 1px solid #2D3748; font-weight: bold; }
    .stButton>button:hover { border-color: #10B981; color: #10B981; }
    
    .box-cang3d { background-color: #05070B; padding: 12px; border-radius: 12px; border: 2px solid #A855F7; margin-bottom: 12px; }
    .box-de2s { background-color: #0A0204; padding: 12px; border-radius: 12px; border: 2px solid #FF3344; margin-bottom: 12px; }
    .box-cang10 { background-color: #050C0A; padding: 15px; border-radius: 12px; border: 3px solid #FFD700; margin-bottom: 15px; }
    
    .title-cang3d { color: #A855F7 !important; font-size: 15px !important; font-weight: 900 !important; }
    .title-de2s { color: #FF3344 !important; font-size: 16px !important; font-weight: 900 !important; }
    .title-cang10 { color: #FFD700 !important; font-size: 16px !important; font-weight: 900 !important; }
    
    .text-cang3d { color: #E2E8F0 !important; font-size: 17px !important; font-weight: bold; font-family: monospace; letter-spacing: 2px; line-height: 1.4; word-wrap: break-word; }
    .text-de2s { color: #FFD700 !important; font-size: 22px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 3px; line-height: 1.5; word-wrap: break-word; }
    .text-cang10 { color: #FF3344 !important; font-size: 26px !important; font-weight: 900 !important; font-family: monospace; letter-spacing: 4px; line-height: 1.5; word-wrap: break-word; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo cấu trúc dữ liệu Tensor trên RAM Session
if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "wire_matrix_3d": np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "history": [],
        "last_predictions_groups": {},
        "last_de_vip_list": [], # Két gối đầu đối chiếu GĐB
        "top_10_cang": []       # Két gối đầu đối soát 3 Càng tinh nhuệ
    }
if 'raw_input' not in st.session_state: st.session_state['raw_input'] = ""
if 'input_loto_4s' not in st.session_state: st.session_state['input_loto_4s'] = ""

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

# --- 3. ĐỘNG CƠ MA TRẬN 3D KẾT HỢP VAN CHẶN GIAO THOA LOTO 2D ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val, filter_loto_list):
    db = st.session_state['db_3d']
    
    old_matrix = np.array(db["wire_matrix_3d"], dtype=int)
    old_digits = db["last_digits"]
    old_preds = db.get("last_predictions_groups", {})
    old_de_vip = db.get("last_de_vip_list", [])
    old_top_10 = db.get("top_10_cang", [])
    
    # 🧠 BƯỚC 1: ĐỐI SOÁT TỰ ĐỘNG LỊCH SỬ KỲ TRƯỚC (CO GIÃN ĐẦY ĐỦ CÁC CỘT)
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    
    if old_digits != "":
        # 1. Đối soát mạch Đề thô gối đầu so với GĐB thực tế hôm nay
        if old_de_vip:
            if gdb_val in old_de_vip: hit_report["Dàn ĐB (Đuôi 3C 2đ)"] = f"🎯 ĂN ({gdb_val})"
            else: hit_report["Dàn ĐB (Đuôi 3C 2đ)"] = "Trượt"
        else: hit_report["Dàn ĐB (Đuôi 3C 2đ)"] = "Trống"
        
        # 2. Đối soát mạch 10 Siêu quân 3 Càng tinh nhuệ ép theo Lô của hôm qua
        if old_top_10:
            matched_top10 = [num for num in old_top_10 if num in cang3c_23]
            if matched_top10: hit_report["👑 MẠCH 10 CÀNG VIP"] = f"🔥 HỐC {len(matched_top10)} NHÁY ({', '.join(matched_top10)})"
            else: hit_report["👑 MẠCH 10 CÀNG VIP"] = "❌ Trượt"
        else: hit_report["👑 MẠCH 10 CÀNG VIP"] = "Trống"

    # Đối soát các dàn thô nhóm điểm cũ
    if old_preds:
        for group_name, group_data in old_preds.items():
            pred_list = group_data.get("list", [])
            matched_nums = [num for num in pred_list if num in cang3c_23]
            total_hits = len(matched_nums)
            if total_hits > 0: hit_report[f"Cột {group_name}"] = f"{total_hits} nháy ({', '.join(matched_nums)})"
            else: hit_report[f"Cột {group_name}"] = "0"
                
    # 🧠 BƯỚC 2: CĂNG DÂY TENSOR LẬP PHƯƠNG KHÔNG GIAN
    new_matrix = np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int)
    if len(old_digits) == TOTAL_POS:
        for i in range(TOTAL_POS):
            for j in range(TOTAL_POS):
                for k in range(TOTAL_POS):
                    num_past = old_digits[i] + old_digits[j] + old_digits[k]
                    if num_past in cang3c_23: new_matrix[i][j][k] = old_matrix[i][j][k] + 1
                    else: new_matrix[i][j][k] = 0

    # 🧠 BƯỚC 3: PHÂN LOẠI NHÓM ĐIỂM + ĐẾM DÂY + TRÍCH XUẤT ÁNH XẠ ĐỘC QUYỀN
    max_score = int(new_matrix.max())
    current_predictions = {}
    next_de_vip_list = []      # Két chứa dàn Đề thô 2 số của ngày mai
    candidates_for_top10 = []  # Toàn bộ kho 3 càng của các nhóm dính đuôi 4 con lô
    
    if max_score >= 1:
        for s in range(1, max_score + 1):
            coords = np.argwhere(new_matrix == s)
            if len(coords) == 0: continue
            
            total_wires_in_group = len(coords)
            cang_frequency_in_group = {}
            for r, c, l in coords:
                num_cang = digits_107[r] + digits_107[c] + digits_107[l]
                cang_frequency_in_group[num_cang] = cang_frequency_in_group.get(num_cang, 0) + 1
                
            # Lọc độc quyền đơn dây chuẩn ý mày
            unique_cang_list = [cang for cang, freq in cang_frequency_in_group.items() if freq == 1]
            
            if unique_cang_list:
                current_predictions[f"{s} đ"] = {
                    "total_wires": total_wires_in_group,
                    "list": sorted(unique_cang_list)
                }
                
                # GIỮ NGUYÊN TẤT CẢ TÁC DỤNG CỦA DÀN ĐỀ THÔ 2S TỪ DÂY 2 ĐIỂM ĐỂ ĐỐI CHIẾU
                if s == 2:
                    loto_ends = [cang3c[-2:] for cang3c in unique_cang_list]
                    next_de_vip_list = sorted(list(set(loto_ends)))
                
                # GOM QUÂN TẤT CẢ CÁC DÀN HÌNH THÀNH CÓ ĐUÔI NẰM TRONG 4 CON LÔ CHIẾN LƯỢC
                if filter_loto_list:
                    for cang_code in unique_cang_list:
                        if cang_code[-2:] in filter_loto_list:
                            # Lưu trữ kèm cấp độ nhóm điểm để tí nữa xếp hạng ưu tiên
                            candidates_for_top10.append({"code": cang_code, "weight": s})

    # 🧠 BƯỚC 4: TRÍCH XUẤT CHÍNH XÁC 10 SIÊU QUÂN 3 CÀNG THEO TRỤC 4 CON LÔ
    final_top_10 = []
    if candidates_for_top10:
        # Sắp xếp ưu tiên: Thằng nào nằm ở nhóm điểm cao hơn (2đ, 3đ...) đẩy lên trên
        sorted_candidates = sorted(candidates_for_top10, key=lambda x: x["weight"], reverse=True)
        # Loại bỏ trùng lặp nếu trùng số (giữ cấu trúc phẳng)
        seen = set()
        for item in sorted_candidates:
            if item["code"] not in seen:
                seen.add(item["code"])
                final_top_10.append(item["code"])
        final_top_10 = final_top_10[:10] # Ép giữ cứng đúng 10 con sát thủ tinh nhuệ nhất

    # Đồng bộ két sắt Session RAM
    db["wire_matrix_3d"] = new_matrix.tolist()
    db["last_digits"] = digits_107
    db["last_predictions_groups"] = current_predictions
    db["last_de_vip_list"] = next_de_vip_list
    db["top_10_cang"] = final_top_10
    
    if old_digits != "": db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Kỳ khởi tạo ma trận"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ MATRIX 3D - SNIPER CORE OPERATOR v18.0</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 💾 HỆ THỐNG DỮ LIỆU TENSOR")
    uploaded_file = st.file_uploader("Nạp file JSON 3D", type=['json'])
    if uploaded_file and st.button("📥 PHỤC HỒI BỘ NHỚ 3D"):
        st.session_state['db_3d'] = json.load(uploaded_file)
        st.rerun()
    if st.session_state['db_3d']['last_digits']:
        st.download_button("💾 XUẤT FILE SAO LƯU JSON", json.dumps(st.session_state['db_3d']), "matrix_3d_v180.json")
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP SỐ THÔ & BỘ VAN LỌC LOTO 2D")
    st.session_state['raw_input'] = st.text_area("Dán bảng giải (Copy chuẩn từ Web):", value=st.session_state.get('raw_input', ""), height=150)
    
    # Ô NHẬP 4 CON LÔ CHIẾN LƯỢC ĐÃ ĂN ỔN ĐỊNH CỦA MÀY ĐỂ ÉP SỐ 3 CÀNG
    st.session_state['input_loto_4s'] = st.text_input("Nhập dàn 4 con Lô chiến lược (Ví dụ: 12, 34, 56, 78):", value=st.session_state.get('input_loto_4s', ""))
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(st.session_state['raw_input'])
        if digits_107 and len(digits_107) == TOTAL_POS:
            gdb_val = digits_107[3:5]
            
            # Xử lý bóc tách dải 4 con lô từ ô nhập văn bản thành mảng list
            filter_loto = [n.strip() for n in st.session_state['input_loto_4s'].replace(",", " ").split() if n.isdigit()]
            
            process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val, filter_loto)
            st.rerun()
        else:
            st.error("Lỗi định dạng kết quả dán vào! Vui lòng kiểm tra lại bảng giải.")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. TRUNG TÂM PHÁT LỰC HIỂN THỊ CÁC DÀN MA TRẬN PHẲNG ---
st.markdown("<h3><font color='#FFD700'><b>👑 KHÔNG GIAN TRIỂN KHAI SĂN LÙNG 3 CÀNG TINH NHUỆ</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #FFD700; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# 👑 CỘT MỐC 1: XUẤT HIỆN 10 CON KÍNH NGẮM 3 CÀNG VIP ÉP THEO ĐÚNG 4 CON LÔ CỦA MÀY
top_10_list = st.session_state['db_3d'].get("top_10_cang", [])
if top_10_list:
    total_10 = len(top_10_list)
    top_10_str = "   -   ".join(top_10_list)
    st.markdown(f"""
        <div class="box-cang10">
            <span class="title-cang10">👑 TOP {total_10} SÁT THỦ 3 CÀNG VIP (Lọc giao thoa: Chỉ ôm cứng đuôi 4 con Lô chiến lược ở mọi nhóm dây)</span><br>
            <p class="text-cang10">{top_10_str}</p>
        </div>
        """, unsafe_allow_html=True)

# 🎯 CỘT MỐC 2: GIỮ NGUYÊN 100% CÁI HỘP ĐỀ THÔ ĐỂ ĐỐI CHIẾU GĐB THEO PHÁT HIỆN ĐẮT GIÁ CỦA MÀY
next_de_vip = st.session_state['db_3d'].get("last_de_vip_list", [])
if next_de_vip:
    total_de = len(next_de_vip)
    de_list_str = "   -   ".join(next_de_vip)
    st.markdown(f"""
        <div class="box-de2s">
            <span class="title-de2s">🎯 ĐỀ THÔ ĐỐI CHIẾU GĐB (Rút trích 2 số cuối từ dàn 3C nhóm 2đ độc nhất -> Bỏ trùng: {total_de} quân)</span><br>
            <p class="text-de2s">{de_list_str}</p>
        </div>
        """, unsafe_allow_html=True)

# Hiển thị các dàn thô nhóm điểm bên dưới
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
    if not top_10_list: st.info("Hệ thống trống. Vui lòng dán kết quả thô và gõ 4 con lô chiến lược vào Sidebar để kích hoạt radar!")

# --- 6. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TỰ ĐỘNG TĂNG TRƯỞNG ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT ĐƯỜNG CẦU TENSOR 3D</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    df_hist = pd.DataFrame(hist_data).fillna("0")
    cols = list(df_hist.columns)
    
    # Định tuyến găm các cột kiểm định chính lên tiền tuyến đầu bảng
    if "GĐB" in cols: cols.insert(0, cols.pop(cols.index("GĐB")))
    if "Dàn ĐB (Đuôi 3C 2đ)" in cols: cols.insert(1, cols.pop(cols.index("Dàn ĐB (Đuôi 3C 2đ)")))
    if "👑 MẠCH 10 CÀNG VIP" in cols: cols.insert(2, cols.pop(cols.index("👑 MẠCH 10 CÀNG VIP")))
    
    def highlight_wins(val):
        val_str = str(val)
        if "🎯 ĂN" in val_str: return 'background-color: #450A0A; color: #FF3344; font-weight: 900; border: 1px solid #FF3344;'
        elif "🔥 HỐC" in val_str: return 'background-color: #451A03; color: #FFD700; font-weight: 900; border: 2px solid #FFD700;'
        elif "nháy" in val_str: return 'background-color: #1F2937; color: #10B981; font-weight: 900; border: 1px solid #10B981;'
        elif val_str in ["Trượt", "❌ Trượt", "0"]: return 'color: #4B5563; font-weight: normal;'
        return ''

    st.dataframe(df_hist[cols].style.map(highlight_wins), use_container_width=True, height=450)
else:
    st.info("Nhật ký trống. Hệ thống tự động liên kết đối soát gối đầu kể từ kỳ quay tiếp theo.")
