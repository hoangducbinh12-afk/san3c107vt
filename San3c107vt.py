import streamlit as st
import pandas as pd
import json
import gzip  
import numpy as np
import re
import io

# --- 1. CẤU HÌNH GIAO DIỆN PREMIUM LAB-TESTING V25.0 ---
st.set_page_config(page_title="Matrix 3D - Touch Master V25.0", layout="wide")
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

# Khởi tạo dữ liệu gối đầu RAM Session V25.0
if 'db_3d' not in st.session_state:
    st.session_state['db_3d'] = {
        "wire_matrix_3d": np.zeros((TOTAL_POS, TOTAL_POS, TOTAL_POS), dtype=int).tolist(),
        "last_digits": "",
        "history": [],
        "last_lab_predictions": {} 
    }

# 🌌 BỘ KHO 280 HẠT NHÂN KÉP GÁNH GỐC CỦA ĐẠI CA
KEP_GANH_280 = [
    "000", "001", "002", "003", "004", "005", "006", "007", "008", "009", "010", "011", "020", "022", "030", "033", "040", "044", "050", "055", "060", "066", "070", "077", "080", "088", "090", "099", 
    "100", "101", "110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "121", "122", "131", "133", "141", "144", "151", "155", "161", "166", "171", "177", "181", "188", "191", "199", 
    "200", "202", "211", "212", "220", "221", "222", "223", "224", "225", "226", "227", "228", "229", "232", "233", "242", "244", "252", "255", "262", "266", "272", "277", "282", "288", "289", "292", "299", 
    "300", "303", "311", "313", "322", "323", "330", "331", "332", "333", "334", "335", "336", "337", "338", "339", "343", "344", "353", "355", "363", "366", "373", "377", "383", "388", "393", "399", 
    "400", "404", "411", "414", "422", "424", "433", "434", "440", "441", "442", "443", "444", "445", "446", "447", "448", "449", "454", "455", "464", "466", "474", "477", "484", "488", "494", "499", 
    "500", "505", "511", "515", "522", "525", "533", "535", "544", "545", "550", "551", "552", "553", "554", "555", "556", "557", "558", "559", "565", "566", "575", "577", "585", "588", "595", "599", 
    "600", "606", "611", "616", "622", "626", "633", "636", "644", "646", "655", "656", "660", "661", "662", "663", "664", "665", "666", "667", "668", "669", "676", "677", "686", "688", "696", "699", 
    "700", "707", "711", "717", "722", "727", "733", "737", "744", "747", "755", "757", "766", "767", "770", "771", "772", "773", "774", "775", "776", "777", "778", "779", "787", "788", "797", "799", 
    "800", "808", "811", "818", "822", "828", "833", "838", "844", "848", "855", "858", "866", "868", "877", "878", "880", "881", "882", "883", "884", "885", "886", "887", "888", "889", "898", "899", 
    "900", "909", "911", "919", "922", "929", "933", "939", "944", "949", "955", "959", "966", "969", "977", "979", "988", "989", "990", "991", "992", "993", "994", "995", "996", "997", "998", "999"
]

# Hàm lập dàn 280 con dựa theo bộ lọc nén chữ số (Chạm)
def generate_k_g_by_touches(touches):
    touch_set = set(str(t) for t in touches)
    result_ dàn = []
    for num in KEP_GANH_280:
        # Kiểm tra xem TẤT CẢ các chữ số của con số này có nằm trong bộ chạm không
        if all(char in touch_set for char in num):
            result_ dàn.append(num)
    return sorted(result_ dàn)

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

# --- 3. ĐỘNG CƠ MA TRẬN QUÉT CHẠM VÀ PHÂN TÁCH 4 DÀN CHIẾN THUẬT V25.0 ---
def process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val):
    db = st.session_state['db_3d']
    
    old_matrix = np.array(db["wire_matrix_3d"], dtype=int)
    old_digits = db["last_digits"]
    old_lab_preds = db.get("last_lab_predictions", {})
    
    # 🧠 BƯỚC 1: ĐỐI SOÁT TỰ ĐỘNG KỲ TRƯỚC THEO ĐÚNG 4 DÀN CHẠM CHIẾN THUẬT
    hit_report = {"GĐB": gdb_val if gdb_val else "00"}
    
    if old_digits != "" and old_lab_preds:
        keys_mapping = {
            "d1_pa1_high": "Dàn 1 (PA1-Cao)",
            "d2_pa1_low": "Dàn 2 (PA1-Thấp)",
            "d3_pa2_high": "Dàn 3 (PA2-Cao)",
            "d4_pa2_low": "Dàn 4 (PA2-Thấp)"
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

    # 🧠 BƯỚC 3: TRIỂN KHAI PHƯƠNG ÁN LỌC CHẠM TOÀN DIỆN
    touch_score_pa1 = {str(i): 0 for i in range(10)}  # PA1: Tổng điểm tụ sợi dây
    touch_score_pa2 = {str(i): 0 for i in range(10)}  # PA2: Đếm tần suất đơn dây độc quyền
    
    frequency_in_1đ = {}
    frequency_in_2đ = {}
    
    for i in range(TOTAL_POS):
        for j in range(TOTAL_POS):
            for k in range(TOTAL_POS):
                num_cang = digits_107[i] + digits_107[j] + digits_107[k]
                score = new_matrix[i][j][k]
                
                # --- THUẬT TOÁN PHƯƠNG ÁN 1: RỐN CẦU TỤ NĂNG LƯỢNG ---
                if score >= 1:
                    for char in set(num_cang):  # Tách các chữ số đơn lẻ cấu thành số 3 càng
                        touch_score_pa1[char] += int(score)
                        
                # Tích lũy để chuẩn bị chạy cho bộ lọc Độc quyền của Phương án 2
                if score == 1:
                    frequency_in_1đ[num_cang] = frequency_in_1đ.get(num_cang, 0) + 1
                elif score == 2:
                    frequency_in_2đ[num_cang] = frequency_in_2đ.get(num_cang, 0) + 1

    # --- THUẬT TOÁN PHƯƠNG ÁN 2: LỰC NÉN ĐỘC QUYỀN ĐƠN DÂY ---
    d6_unique = [cang for cang, freq in frequency_in_1đ.items() if freq == 1]
    d7_unique = [cang for cang, freq in frequency_in_2đ.items() if freq == 1]
    all_unique_3c = d6_unique + d7_unique
    
    for num in all_unique_3c:
        for char in set(num):
            touch_score_pa2[char] += 1

    # 🧠 BƯỚC 4: SẮP XẾP VÀ TRÍCH XUẤT CHẠM TUYỆT ĐỐI
    # Sắp xếp PA1
    sorted_pa1 = sorted(touch_score_pa1.items(), key=lambda x: x[1], reverse=True)
    pa1_high_touches = [item[0] for item in sorted_pa1[:4]]
    pa1_low_touches = [item[0] for item in sorted_pa1[-4:]]
    
    # Sắp xếp PA2
    sorted_pa2 = sorted(touch_score_pa2.items(), key=lambda x: x[1], reverse=True)
    pa2_high_touches = [item[0] for item in sorted_pa2[:4]]
    pa2_low_touches = [item[0] for item in sorted_pa2[-4:]]

    # 🧠 BƯỚC 5: ÉP DÀN 280 CON THEO CHẠM MỤC TIÊU KHẠC RA 4 DÀN CHIẾN THUẬT
    d1_list = generate_k_g_by_touches(pa1_high_touches)
    d2_list = generate_k_g_by_touches(pa1_low_touches)
    d3_list = generate_k_g_by_touches(pa2_high_touches)
    d4_list = generate_k_g_by_touches(pa2_low_touches)

    # Đóng gói két bảo mật RAM
    db["last_lab_predictions"] = {
        "pa1_high_txt": ", ".join(pa1_high_touches),
        "pa1_low_txt": ", ".join(pa1_low_touches),
        "pa2_high_txt": ", ".join(pa2_high_touches),
        "pa2_low_txt": ", ".join(pa2_low_touches),
        
        "d1_0đ_high": pa1_high_touches, # Giữ gốc để hiển thị
        "d1_pa1_high": d1_list,
        "d2_pa1_low": d2_list,
        "d3_pa2_high": d3_list,
        "d4_pa2_low": d4_list
    }

    # Đồng bộ bộ nhớ ma trận Tensor
    db["wire_matrix_3d"] = new_matrix.tolist()
    db["last_digits"] = digits_107
    
    if old_digits != "" and old_lab_preds: 
        db["history"].insert(0, hit_report)
    else:
        hit_report["Ghi chú"] = "⚙️ Kỳ khởi tạo ma trận chốt chạm V25.0"
        db["history"].insert(0, hit_report)

# --- 4. GIAO DIỆN ĐIỀU HÀNH CONTROL PANEL SIDEBAR ---
st.markdown("<h2 style='text-align: center; color: #E2E8F0; font-weight: bold;'>⚡ TENSOR MATRIX 3D - TOUCH MASTER v25.0</h2>", unsafe_allow_html=True)

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
            st.success("Đã hồi sinh trạm lọc chạm V25.0 thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi tệp cấu trúc nhị phân: {e}")
            
    if st.session_state['db_3d']['last_digits']:
        json_string = json.dumps(st.session_state['db_3d'])
        gzip_buffer = io.BytesIO()
        with gzip.open(gzip_buffer, "wb", compresslevel=9) as f:
            f.write(json_string.encode("utf-8"))
        
        st.download_button(
            label="💾 XUẤT FILE NÉN TỐI ƯU (.JSON.GZ)", 
            data=gzip_buffer.getvalue(), 
            file_name="matrix_3d_v250.json.gz",
            mime="application/gzip"
        )
        
    st.divider()
    st.markdown("### 📥 TRẠM NẠP KẾT QUẢ KỲ QUAY")
    raw_input_text = st.text_area("Dán bảng giải thô chuẩn từ Web:", key="web_raw_field_v25", height=200)
    
    if st.button("🔥 KHAI HỎA SNIPER TENSOR 3D", type="primary"):
        if raw_input_text:
            digits_107, loto_27, cang3c_23 = parse_vietnam_xsmb_format(raw_text=raw_input_text)
            if digits_107 and len(digits_107) == TOTAL_POS:
                gdb_val = digits_107[3:5]
                process_matrix_3d(digits_107, loto_27, cang3c_23, gdb_val)
                st.toast("🔥 Đồng bộ băm chạm 2D-3D thành công!", icon="🎯")
                st.rerun()
            else:
                st.error("Lỗi cấu trúc chuỗi 107 giải!")
        else:
            st.warning("Ô nhập trống kìa đại ca!")
            
    if st.button("🚨 XÓA TRẮNG BẢNG TẠM"):
        st.session_state.clear()
        st.rerun()

# --- 5. KHU VỰC BẢNG NHẬT KÝ ĐỐI SOÁT LIÊN HOÀN (ĐƯA LÊN ĐẦU TIỀN TUYẾN) ---
st.markdown("<h3><font color='#10B981'><b>📋 NHẬT KÝ ĐỐI SOÁT SỐ QUÂN ĂN CỦA 4 DÀN CHẠM KÉP GÁNH V25.0</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #10B981; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

hist_data = st.session_state['db_3d'].get("history", [])
if hist_data:
    df_hist = pd.DataFrame(hist_data).fillna("0")
    cols = list(df_hist.columns)
    
    order_cols = ["GĐB", "Dàn 1 (PA1-Cao)", "Dàn 2 (PA1-Thấp)", "Dàn 3 (PA2-Cao)", "Dàn 4 (PA2-Thấp)"]
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
    st.info("Hệ thống đang chờ dữ liệu kỳ sau để tự động khạc báo cáo số nháy ăn đối soát liên hoàn.")

st.divider()

# --- 6. KHU VỰC PHƠI BÀY CHI TIẾT 4 DÀN CHẠM KÉP GÁNH HIỆN TẠI ---
st.markdown("<h3><font color='#A855F7'><b>🔮 BẢNG PHÂN LẬP TRÍCH XUẤT CHẠM VÀ DÀN SỐ KỲ NÀY</b></font></h3>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #A855F7; margin-top: -5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

preds = st.session_state['db_3d'].get("last_lab_predictions", {})

if preds:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📡 PHƯƠNG ÁN 1: RỐN CẦU TỤ")
        st.success(f"🔥 4 Chạm Cao Điểm Nhất: [ {preds.get('pa1_high_txt')} ]")
        st.error(f"❄️ 4 Chạm Thấp Điểm Nhất: [ {preds.get('pa1_low_txt')} ]")
    with col2:
        st.subheader("🎯 PHƯƠNG ÁN 2: LÕI ĐỘC QUYỀN")
        st.success(f"🔥 4 Chạm Cao Điểm Nhất: [ {preds.get('pa2_high_txt')} ]")
        st.error(f"❄️ 4 Chạm Thấp Điểm Nhất: [ {preds.get('pa2_low_txt')} ]")
        
    st.divider()
    st.markdown("### 📦 DANH SÁCH 4 DÀN SỐ ÉP THEO KÉP GÁNH (280 CON GỐC):")

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
    st.info("Hệ thống đang trống. Vui lòng nạp kết quả thô để bốc đầu 4 bộ chạm băm nát nhà đài!")
