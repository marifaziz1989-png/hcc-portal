import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Holiday Country Club | Executive Portal",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ADVANCED DESKTOP DARK THEME, ANIMATIONS & PRINT CSS ---
st.markdown("""
<style>
    .stApp { background-color: #12141e; color: #e2e8f0; }
    .dark-header {
        background-color: #1a1c29;
        padding: 15px 25px;
        border-bottom: 2px solid #3b82f6;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .dark-title { font-size: 22px; font-weight: 800; margin: 0; color: #ffffff; letter-spacing: 1px; }
    .weather-badge {
        background: linear-gradient(135deg, #1e3a8a, #0891b2);
        padding: 8px 15px;
        border-radius: 8px;
        color: white;
        text-align: right;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    @keyframes blinkEffect {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .blinking-heading {
        animation: blinkEffect 1.5s infinite;
    }
    
    .panel-container {
        background: linear-gradient(135deg, #1a1c29, #212538);
        border: 1px solid #3b82f6;
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }

    .stTextInput label, .stSelectbox label, .stNumberInput label, .stDateInput label, h4 {
        color: #f97316 !important;
        font-weight: 700 !important;
    }
    .stButton > button, div.stFormSubmitButton > button {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: white !important;
        font-weight: 700 !important;
        border: 1px solid #60a5fa !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4) !important;
    }
    .metric-card {
        padding: 15px;
        border-radius: 6px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 15px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .metric-title { font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; opacity: 0.9;}
    .metric-value { font-size: 26px; font-weight: 800; margin: 0; }
    .invoice-box {
        background: #1a1c29; padding: 30px; border-radius: 10px; border: 1px dashed #475569;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5); margin-top: 20px; font-family: monospace; color: #e2e8f0;
    }
    @media print {
        body { background-color: white !important; color: black !important; }
        .stApp { background-color: white !important; color: black !important; }
        .dark-header, [data-testid="stSidebar"], .stButton, hr, .stTabs, .panel-container { display: none !important; }
        .invoice-box { background: white !important; color: black !important; border: 1px solid black !important; box-shadow: none !important; width: 100% !important; margin: 0 !important; }
    }
</style>
""", unsafe_allow_html=True)

def render_metric(title, value, bg_color):
    st.markdown(f"""
    <div class='metric-card' style='background-color: {bg_color};'>
        <div class='metric-title'>{title}</div>
        <div class='metric-value'>{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- SAFE DATABASE HANDLING ---
DATA_FILE = "hcc_database.json"

def load_data():
    default_units = [
        "PH01 - Executive Loft Suite", "PH01 - Studio Suite Villa", 
        "FP01 - Two Bed Executive Villa", "W01 - Woody A-Frame Studio",
        "W02 - Woody A-Frame Studio", "W03 - Woody A-Frame Studio",
        "W04 - Woody A-Frame Studio", "TH01 - Treehouse"
    ]
    default_services = [
        {"name": "Swimming Pool", "price": 2000},
        {"name": "Jacuzzi", "price": 3000},
        {"name": "Bonfire", "price": 3500},
        {"name": "Birthday Decor", "price": 5000},
        {"name": "BBQ Setup", "price": 4000},
        {"name": "Luggage / Pick & Drop Service", "price": 2500}
    ]
    default_menu = [
        {"item": "Chicken Karahi (1 KG)", "price": 2500},
        {"item": "Mutton Karahi (1 KG)", "price": 4500},
        {"item": "Water Bottle (1.5L)", "price": 150},
        {"item": "Special Tea", "price": 200},
        {"item": "Green Tea", "price": 150},
        {"item": "BBQ Platter", "price": 3000},
        {"item": "Breakfast Platter", "price": 800}
    ]
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                del_b = data.get("deleted_bookings", [])
                safe_del_b = [item for item in del_b if isinstance(item, dict) and "record" in item]
                del_v = data.get("deleted_visitors", [])
                safe_del_v = [item for item in del_v if isinstance(item, dict) and "record" in item]
                
                del_units = data.get("deleted_units", [])
                del_menu = data.get("deleted_menu", [])
                del_services = data.get("deleted_services", [])

                return (
                    data.get("units", default_units), 
                    data.get("bookings", []), 
                    data.get("visitors", []), 
                    data.get("services_catalog", default_services),
                    data.get("restaurant_menu", default_menu),
                    data.get("expenses", []),
                    data.get("housekeeping", {u: "Clean" for u in data.get("units", default_units)}),
                    safe_del_b,
                    safe_del_v,
                    del_units,
                    del_menu,
                    del_services
                )
        except Exception:
            pass
            
    return default_units, [], [], default_services, default_menu, [], {u: "Clean" for u in default_units}, [], [], [], [], []

def save_data():
    data = {
        "units": st.session_state.units, 
        "bookings": st.session_state.bookings, 
        "visitors": st.session_state.visitors, 
        "services_catalog": st.session_state.services_catalog, 
        "restaurant_menu": st.session_state.restaurant_menu,
        "expenses": st.session_state.expenses, 
        "housekeeping": st.session_state.housekeeping, 
        "deleted_bookings": st.session_state.deleted_bookings,
        "deleted_visitors": st.session_state.deleted_visitors,
        "deleted_units": st.session_state.deleted_units,
        "deleted_menu": st.session_state.deleted_menu,
        "deleted_services": st.session_state.deleted_services
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

if "units" not in st.session_state:
    (st.session_state.units, st.session_state.bookings, st.session_state.visitors, 
     st.session_state.services_catalog, st.session_state.restaurant_menu, st.session_state.expenses, 
     st.session_state.housekeeping, st.session_state.deleted_bookings, st.session_state.deleted_visitors,
     st.session_state.deleted_units, st.session_state.deleted_menu, st.session_state.deleted_services) = load_data()

# --- AUTO-FIX FOR MISSING IDs ---
fix_updated = False
v_counter = 1
for v in st.session_state.visitors:
    current_id = str(v.get("id", "")).strip()
    if not current_id or current_id in ["N/A", "None", ""]:
        while any(str(item.get("id")) == f"VIS-{v_counter}" for item in st.session_state.visitors):
            v_counter += 1
        v["id"] = f"VIS-{v_counter}"
        fix_updated = True
    elif current_id.startswith("VIS-"):
        try:
            num = int(current_id.split("-")[1])
            if num >= v_counter:
                v_counter = num + 1
        except:
            pass

b_counter = 1001
for b in st.session_state.bookings:
    current_bid = str(b.get("id", "")).strip()
    if not current_bid or current_bid in ["N/A", "None", ""]:
        while any(str(item.get("id")) == f"HCC-{b_counter}" for item in st.session_state.bookings):
            b_counter += 1
        b["id"] = f"HCC-{b_counter}"
        fix_updated = True
    elif current_bid.startswith("HCC-"):
        try:
            num = int(current_bid.split("-")[1])
            if num >= b_counter:
                b_counter = num + 1
        except:
            pass

if fix_updated:
    save_data()

for u in st.session_state.units:
    if u not in st.session_state.housekeeping:
        st.session_state.housekeeping[u] = "Clean"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- USERS & ROLES CONFIGURATION (EXACTLY AS REQUESTED) ---
USERS = {
    "Role 1: CEO": {"password": "ceo123", "role": "CEO", "name": "Chief Executive Officer"},
    "Role 2: GM": {"password": "gm123", "role": "GM", "name": "M. Arif Aziz"},
    "Role 3: HOD": {"password": "hod123", "role": "HOD", "name": "Head of Department"},
    "Role 4: Site Accountant": {"password": "acc123", "role": "Site Accountant", "name": "Site Accountant"},
    "Role 5: Admin": {"password": "admin123", "role": "Admin", "name": "System Admin"},
    "Role 6: GM Hospitality": {"password": "hosp123", "role": "GM Hospitality", "name": "Hospitality Manager"},
    "Role 7: Front Desk Office": {"password": "desk123", "role": "Front Desk", "name": "Front Desk Officer"}
}

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='background: #1a1c29; padding: 35px; border-radius: 10px; border: 1px solid #3b82f6; text-align: center;'>
            <h2 style='color: #ffffff; margin-bottom: 5px; font-weight: 800;'>Holiday Country Club</h2>
            <p style='color: #94a3b8; font-size: 12px; margin-bottom: 25px; letter-spacing: 1px;'>SECURE EXECUTIVE PORTAL</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            selected_user_key = st.selectbox("Select Role", options=list(USERS.keys()))
            p_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Secure Login", use_container_width=True)
            
            if submit_login:
                if selected_user_key in USERS and USERS[selected_user_key]["password"] == p_input:
                    st.session_state.logged_in = True
                    st.session_state.username = selected_user_key
                    st.session_state.role = USERS[selected_user_key]["role"]
                    st.session_state.name = USERS[selected_user_key]["name"]
                    st.rerun()
                else:
                    st.error("Invalid Password!")
    st.stop()

role = st.session_state.role

# --- CORPORATE HEADER BAR ---
st.markdown(f"""
<div class='dark-header'>
    <div style='display: flex; align-items: center; gap: 15px;'>
        <div style='background: #12141e; padding: 6px; border-radius: 8px; border: 1px solid #f97316; display: flex; align-items: center; justify-content: center;'>
            <span style='font-size: 24px;'>🏔️</span>
        </div>
        <div>
            <p class='dark-title'>HOLIDAY COUNTRY CLUB | Executive Portal</p>
            <span style='font-size: 12px; color: #f97316; font-weight: 600;'>Logged in as: {st.session_state.name} ({role})</span>
        </div>
    </div>
    <div>
        <div class='weather-badge'>
            <b>🌤️ Murree Hills Weather:</b> 19.3°C (Clear)<br>
            <span style='font-size: 11px; opacity: 0.9;'>📅 {datetime.now().strftime('%A, %d %B %Y | %I:%M %p')}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- PREPARING PENDING TASKS & TODAY CHECK-OUTS DATA ---
pending_tasks_list = []
for u, status in st.session_state.housekeeping.items():
    if status == "Maintenance":
        pending_tasks_list.append(f"🛠️ {u}: Under Maintenance.")
    elif status == "Dirty":
        pending_tasks_list.append(f"🧹 {u}: Cleaning Required.")

if not pending_tasks_list:
    pending_tasks_list.append("🟢 All cottages are clean and fully operational.")

today_str = datetime.today().strftime('%d/%m/%Y')
today_checkouts_list = []
for b in st.session_state.bookings:
    if b.get('checkout') == today_str and b.get('status') != 'Cancelled':
        today_checkouts_list.append(f"📤 {b.get('unit').split('-')[0]}: {b.get('name')}")

if not today_checkouts_list:
    today_checkouts_list.append(f"📅 No check-outs for today ({today_str}).")

import streamlit.components.v1 as components

panels_html = f"""
<div style="display: flex; gap: 20px; width: 100%; font-family: sans-serif; margin-bottom: 20px;">
    <div style="flex: 1; background: linear-gradient(135deg, #1a1c29, #251b2d); border: 1px solid #f97316; padding: 12px 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
        <div class="blinking-heading" style="font-size: 12px; font-weight: 700; color: #f97316; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>⚡</span> PENDING & CLEANING TASKS
        </div>
        <div id="pending-carousel" style="min-height: 50px; display: flex; align-items: center; color: #ffedd5; font-size: 11px; font-weight: 400;">
            Loading...
        </div>
    </div>

    <div style="flex: 1; background: linear-gradient(135deg, #1a1c29, #1e3a8a); border: 1px solid #3b82f6; padding: 12px 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
        <div class="blinking-heading" style="font-size: 12px; font-weight: 700; color: #60a5fa; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>📅</span> TODAY CHECK-OUTS
        </div>
        <div id="checkout-carousel" style="min-height: 50px; display: flex; align-items: center; color: #e0f2fe; font-size: 11px; font-weight: 400;">
            Loading...
        </div>
    </div>
</div>

<script>
    const pendingTasks = {json.dumps(pending_tasks_list)};
    const todayCheckouts = {json.dumps(today_checkouts_list)};
    let pIndex = 0;
    let cIndex = 0;

    function chunkArray(arr, size) {{
        let results = [];
        for (let i = 0; i < arr.length; i += size) {{
            results.push(arr.slice(i, i + size));
        }}
        return results;
    }}

    const pChunks = chunkArray(pendingTasks, 6);
    const cChunks = chunkArray(todayCheckouts, 6);

    function renderGrid(items) {{
        let html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px 8px; width: 100%;">';
        items.forEach(item => {{
            html += `<div style="background: rgba(255,255,255,0.05); padding: 4px 6px; border-radius: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 11px; font-weight: 400;">• ${{item}}</div>`;
        }});
        html += '</div>';
        return html;
    }}

    function updateCarousels() {{
        const pEl = document.getElementById("pending-carousel");
        pEl.innerHTML = renderGrid(pChunks[pIndex]);
        pIndex = (pIndex + 1) % pChunks.length;

        const cEl = document.getElementById("checkout-carousel");
        cEl.innerHTML = renderGrid(cChunks[cIndex]);
        cIndex = (cIndex + 1) % cChunks.length;
    }}

    updateCarousels();
    setInterval(updateCarousels, 5000);
</script>
"""

components.html(panels_html, height=105)

# --- FINANCIAL ANALYTICS DASHBOARD (Visible to CEO, GM, HOD) ---
if role in ["CEO", "GM", "HOD"]:
    total_units = len(st.session_state.units)
    occupied = sum(1 for b in st.session_state.bookings if b.get("status") == "Occupied")
    upcoming = sum(1 for b in st.session_state.bookings if b.get("status") == "Booked")
    reserved = sum(1 for b in st.session_state.bookings if b.get("status") == "Reserved")
    available = max(0, total_units - (occupied + upcoming + reserved))
    
    gross_revenue, paid_rent, paid_food, paid_act, total_comp = 0, 0, 0, 0, 0
    for b in st.session_state.bookings:
        r = int(b.get("rent", 0)) if str(b.get("rent", 0)).isdigit() else 0
        f = int(b.get("food", 0)) if str(b.get("food", 0)).isdigit() else 0
        a = int(b.get("activities_total", 0)) if str(b.get("activities_total", 0)).isdigit() else 0
        
        if b.get("staytype") == "Complimentary":
            total_comp += (r + f + a)
        else:
            paid_rent += r
            paid_food += f
            paid_act += a

    for v in st.session_state.visitors:
        vf = int(v.get("food_bill", 0)) if str(v.get("food_bill", 0)).isdigit() else 0
        va = int(v.get("activities_total", 0)) if str(v.get("activities_total", 0)).isdigit() else 0
        if v.get("v_type") == "Complimentary":
            total_comp += (vf + va)
        else:
            paid_food += vf
            paid_act += va
            
    gross_revenue = paid_rent + paid_food + paid_act
    total_expenses = sum(int(e.get("amount", 0)) for e in st.session_state.expenses)
    net_profit = gross_revenue - total_expenses

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: render_metric("Total Inventory", total_units, "#1e3a8a")
    with c2: render_metric("Occupied Units", occupied, "#dc2626")
    with c3: render_metric("Upcoming Bookings", upcoming, "#0891b2")
    with c4: render_metric("Total Reserved", reserved, "#ea580c")
    with c5: render_metric("Available Units", available, "#16a34a")
    
    r1, r2, r3, r4, r5 = st.columns(5)
    with r1: render_metric("Complimentary (PKR)", f"PKR {total_comp:,}", "#9333ea")
    with r2: render_metric("Net Paid Rent", f"PKR {paid_rent:,}", "#2563eb")
    with r3: render_metric("Food & Services", f"PKR {paid_food + paid_act:,}", "#ea580c")
    with r4: render_metric("Total Expenses", f"PKR {total_expenses:,}", "#b91c1c")
    with r5: render_metric("Net Profit / Revenue", f"PKR {net_profit:,}", "#16a34a")

# --- NAVIGATION TABS SETUP BASED ON EXACT ROLE PERMISSIONS ---
tab_titles = ["🏨 Stay Bookings", "🔍 Availability Checker", "🍽️ Day Visitors & Restaurant", "🧹 Housekeeping", "🧾 Invoice Generator"]

if role in ["CEO", "GM", "HOD", "Site Accountant", "Admin"]:
    tab_titles.append("💰 Accounts & Expenses")
if role in ["CEO", "GM", "HOD", "Admin"]:
    tab_titles.append("⚙️ Setup & Admin Controls")

tabs = st.tabs(tab_titles)
def get_tab(name):
    return tabs[tab_titles.index(name)] if name in tab_titles else None

# 1. STAY BOOKINGS TAB
with get_tab("🏨 Stay Bookings"):
    st.markdown("<h3 style='color: #f97316;'>🚀 Upcoming Bookings Quick-Tracking Panel</h3>", unsafe_allow_html=True)
    upcoming_list = [b for b in st.session_state.bookings if b.get("status") in ["Booked", "Reserved"]]
    upcoming_list = sorted(upcoming_list, key=lambda x: pd.to_datetime(x.get('checkin', ''), format='%d/%m/%Y', errors='coerce') or pd.Timestamp.max)
    
    if upcoming_list:
        up_cols = st.columns(min(5, len(upcoming_list)))
        for idx, up_b in enumerate(upcoming_list[:5]):
            with up_cols[idx]:
                unit_split = str(up_b.get('unit', '')).split('-')[0]
                st.markdown(f"""
                <div style='background: #1a1c29; padding: 12px; border-radius: 8px; border: 1px solid #3b82f6; text-align: center;'>
                    <span style='font-size: 14px; color: #f97316; font-weight: 800;'>Cottage: {unit_split}</span><br>
                    <b style='color: white; font-size: 13px;'>{up_b.get('name', '')}</b><br>
                    <span style='font-size: 11px; color: #94a3b8;'>In: {up_b.get('checkin', '')}</span><br>
                    <span style='font-size: 10px; background: #0891b2; color: white; padding: 2px 6px; border-radius: 4px;'>ID: {up_b.get('id', 'N/A')}</span>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No upcoming bookings at the moment.")
    
    st.markdown("---")

    # Role 7 (Front Desk), Role 5 (Admin), and Full View roles can create bookings
    if role in ["CEO", "GM", "HOD", "Front Desk", "Admin"]:
        existing_nums = []
        for b in st.session_state.bookings:
            b_id_str = str(b.get("id", ""))
            if b_id_str.startswith("HCC-"):
                try:
                    existing_nums.append(int(b_id_str.split("-")[1]))
                except:
                    pass
        next_id_num = max(existing_nums) + 1 if existing_nums else 1001
        auto_b_id = f"HCC-{next_id_num}"

        with st.expander("➕ Create New Stay Booking", expanded=False):
            with st.form("booking_form", clear_on_submit=True):
                b_id = st.text_input("Booking ID (Sequential Unique)", value=auto_b_id)
                colA, colB = st.columns(2)
                g_name = colA.text_input("Guest Name")
                g_phone = colB.text_input("Contact Number")
                unit = colA.selectbox("Assign Cottage", options=st.session_state.units)
                status = colB.selectbox("Status", ["Reserved", "Booked", "Occupied", "Checked-Out", "Cancelled"])
                
                c_in_date = colA.date_input("Check-in Date", datetime.today())
                c_out_date = colB.date_input("Check-out Date", datetime.today() + timedelta(days=1))
                
                staytype = colA.selectbox("Stay Type", ["Paid Regular", "Complimentary", "Corporate"])
                rent = colB.text_input("Cottage Rent Bill (PKR)", "0")
                force_override = st.checkbox("⚠️ Force Manual Override (Bypass Conflict Check)")
                
                st.markdown("---")
                st.markdown("<h4 style='color: #f97316;'>🍲 Restaurant Menu Order</h4>", unsafe_allow_html=True)
                menu_items_ordered, menu_total = [], 0
                for i, m in enumerate(st.session_state.restaurant_menu):
                    cols_m = st.columns([3, 2])
                    cols_m[0].markdown(f"**{m['item']}** (Rs. {m['price']})")
                    m_choice = cols_m[1].radio("Type", ["Unselected", "Paid", "Complimentary"], key=f"stay_menu_choice_{i}", horizontal=True, label_visibility="collapsed")
                    if m_choice != "Unselected":
                        is_comp = (m_choice == "Complimentary")
                        menu_items_ordered.append({'name': m['item'], 'price': m['price'], 'comp': is_comp})
                        if not is_comp:
                            menu_total += m['price']
                
                st.markdown("---")
                st.markdown("<h4 style='color: #f97316;'>⚡ Resort Activities & Services</h4>", unsafe_allow_html=True)
                selected_act, act_total = [], 0
                for i, s in enumerate(st.session_state.services_catalog):
                    cols_s = st.columns([3, 2])
                    cols_s[0].markdown(f"**{s['name']}** (Rs. {s['price']})")
                    s_choice = cols_s[1].radio("Type", ["Unselected", "Paid", "Complimentary"], key=f"b_act_choice_{i}", horizontal=True, label_visibility="collapsed")
                    if s_choice != "Unselected":
                        is_comp = (s_choice == "Complimentary")
                        selected_act.append({'name': s['name'], 'price': s['price'], 'comp': is_comp})
                        if not is_comp:
                            act_total += s['price']
                
                submit_booking = st.form_submit_button("Save Booking Entry")
                if submit_booking:
                    if any(str(b.get("id")) == b_id for b in st.session_state.bookings):
                        st.error(f"❌ Error: Booking ID '{b_id}' already exists!")
                    elif not g_name:
                        st.error("❌ Error: Guest Name cannot be empty.")
                    else:
                        st.session_state.bookings.append({
                            "id": b_id, "name": g_name, "phone": g_phone, "unit": unit,
                            "checkin": c_in_date.strftime('%d/%m/%Y'), "checkout": c_out_date.strftime('%d/%m/%Y'), 
                            "status": status, "staytype": staytype, "rent": rent, "food": menu_total,
                            "food_items": menu_items_ordered,
                            "activities": selected_act, "activities_total": act_total
                        })
                        st.session_state.housekeeping[unit] = "Dirty"
                        save_data()
                        st.success("✅ Added Successfully!")
                        st.rerun()

    if st.session_state.bookings:
        st.markdown("### 📋 Active Bookings Directory & Management")
        
        # Role 6 (GM Hospitality), CEO, GM, HOD, Admin can edit bookings. Role 4 and Role 7 restricted from editing.
        if role in ["CEO", "GM", "HOD", "Admin", "GM Hospitality"]:
            booking_options = ["-- Select --"] + [f"{b.get('id', 'N/A')} - {b.get('name', 'Guest')}" for b in st.session_state.bookings]
            with st.expander("🛠️ Edit Booking, Update Running Bills & Mark Check-Out", expanded=True):
                edit_b_sel_raw = st.selectbox("Select Booking ID to Edit / Update / Check-Out", options=booking_options, key="edit_b_target")
                edit_b_sel = edit_b_sel_raw.split(" - ")[0] if edit_b_sel_raw != "-- Select --" else "-- Select --"
                
                if edit_b_sel != "-- Select --":
                    target_b = next((b for b in st.session_state.bookings if str(b.get("id")) == edit_b_sel), None)
                    if target_b:
                        with st.form("update_booking_form"):
                            st.markdown(f"**Editing Booking:** {target_b.get('id', 'N/A')} - **Guest:** {target_b.get('name', 'N/A')}")
                            uc_col1, uc_col2 = st.columns(2)
                            current_status = target_b.get('status', 'Reserved')
                            status_list = ["Reserved", "Booked", "Occupied", "Checked-Out", "Cancelled"]
                            new_status = uc_col1.selectbox("Update Status", status_list, index=status_list.index(current_status) if current_status in status_list else 2)
                            new_rent = uc_col2.text_input("Update Rent (PKR)", value=str(target_b.get("rent", "0")))
                            new_staytype = st.selectbox("Update Stay Type", ["Paid Regular", "Complimentary", "Corporate"], index=0)
                            
                            submit_updates = st.form_submit_button("Save & Update Booking / Check-Out")
                            if submit_updates:
                                target_b['status'] = new_status
                                target_b['staytype'] = new_staytype
                                target_b['rent'] = new_rent
                                if new_status == "Checked-Out":
                                    st.session_state.housekeeping[target_b['unit']] = "Dirty"
                                save_data()
                                st.success("✅ Booking updated successfully!")
                                st.rerun()

        table_rows = []
        for b in st.session_state.bookings:
            r_val = int(b.get("rent", 0)) if str(b.get("rent", 0)).isdigit() else 0
            f_val = int(b.get("food", 0)) if str(b.get("food", 0)).isdigit() else 0
            a_val = int(b.get("activities_total", 0)) if str(b.get("activities_total", 0)).isdigit() else 0
            grand = r_val + f_val + a_val
            
            table_rows.append({
                "ID": b.get('id', 'N/A'), "Name": b.get('name', 'N/A'), "Phone": b.get('phone', 'N/A'),
                "Unit": b.get('unit', 'N/A'), "Check-In": b.get('checkin', 'N/A'), "Check-Out": b.get('checkout', 'N/A'),
                "Status": b.get('status', 'N/A'), "Type": b.get('staytype', 'Paid Regular'), "Grand Total (PKR)": f"Rs. {grand:,}"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        
        # Only Admin, CEO, GM can delete bookings
        if role in ["CEO", "GM", "Admin"]:
            st.markdown("---")
            if st.button("🗑️ Delete Selected Booking Record", type="primary"):
                pass
    else:
        st.info("No active bookings found.")

# 2. AVAILABILITY CHECKER TAB
with get_tab("🔍 Availability Checker"):
    st.markdown("<h3 style='color: #f97316;'>🔍 Cottage Availability & Housekeeping Sync Calendar</h3>", unsafe_allow_html=True)
    col_chk1, col_chk2 = st.columns(2)
    check_date = col_chk1.date_input("Select Date to Check", datetime.today(), key="check_date_val")
    check_unit = col_chk2.selectbox("Select Cottage / Unit", options=st.session_state.units, key="check_unit_val")
    
    if st.button("Check Single Unit Status"):
        target_dt = pd.to_datetime(check_date)
        hk_status = st.session_state.housekeeping.get(check_unit, "Clean")
        if hk_status in ["Maintenance", "Dirty"]:
            st.error(f"🛠️ **{check_unit}** is currently marked as **{hk_status}** in Housekeeping records.")
        else:
            st.success(f"🟢 **{check_unit}** status checked successfully.")

    overview_data = []
    for unit in st.session_state.units:
        hk_status = st.session_state.housekeeping.get(unit, "Clean")
        overview_data.append({"Cottage / Unit": unit, "Housekeeping Status": hk_status, "Availability Status": "🟢 Available" if hk_status == "Clean" else "🛠️ Maintenance/Dirty", "Client Details": "N/A"})
    st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)

# 3. DAY VISITORS & RESTAURANT TAB
with get_tab("🍽️ Day Visitors & Restaurant"):
    # Role 7 (Front Desk) and Admin / Full access roles can register visitors
    if role in ["CEO", "GM", "HOD", "Front Desk", "Admin"]:
        with st.expander("➕ Register New Day Visitor / Walk-In Table", expanded=False):
            with st.form("visitor_form", clear_on_submit=True):
                v_name = st.text_input("Visitor Name")
                v_phone = st.text_input("Contact Number")
                submit_visitor = st.form_submit_button("Save Day Visitor Entry")
                if submit_visitor and v_name:
                    st.session_state.visitors.append({"id": f"VIS-{len(st.session_state.visitors)+1}", "name": v_name, "phone": v_phone, "v_type": "Paid"})
                    save_data()
                    st.success("✅ Visitor added!")
                    st.rerun()

    st.markdown("### 📋 Day Visitors & Restaurant Directory")
    if st.session_state.visitors:
        st.dataframe(pd.DataFrame(st.session_state.visitors), use_container_width=True, hide_index=True)
    else:
        st.info("No day visitor records found.")

# 4. HOUSEKEEPING TAB
with get_tab("🧹 Housekeeping"):
    st.markdown("<h3 style='color: #f97316;'>🧹 Housekeeping & Room Turnaround Management</h3>", unsafe_allow_html=True)
    hk_cols = st.columns(3)
    for idx, unit in enumerate(st.session_state.units):
        curr_status = st.session_state.housekeeping.get(unit, "Clean")
        with hk_cols[idx % 3]:
            st.markdown(f"""
            <div style='background: #1a1c29; padding: 15px; border-radius: 8px; border-left: 5px solid #16a34a; margin-bottom: 15px;'>
                <b style='color: white;'>{unit}</b><br>
                <span style='font-size: 12px; color: #f97316; font-weight: 700;'>Status: {curr_status}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Role 6 (GM Hospitality), Admin, CEO, GM, HOD can change housekeeping status
            if role in ["CEO", "GM", "HOD", "Admin", "GM Hospitality"]:
                new_hk_status = st.selectbox(f"Update {unit}", ["Clean", "Dirty", "Maintenance"], index=["Clean", "Dirty", "Maintenance"].index(curr_status), key=f"hk_sel_{idx}")
                if new_hk_status != curr_status:
                    st.session_state.housekeeping[unit] = new_hk_status
                    save_data()
                    st.rerun()

# 5. INVOICE GENERATOR TAB
with get_tab("🧾 Invoice Generator"):
    st.markdown("<h3 style='color: #f97316;'>🧾 Executive Invoice Generator & Detailed Word Export</h3>", unsafe_allow_html=True)
    booking_inv_options = [f"{b.get('id', 'HCC-1001')} - {b.get('name', 'Guest')}" for b in st.session_state.bookings]
    if booking_inv_options:
        sel_inv = st.selectbox("Select Booking ID for Invoice", options=booking_inv_options)
        st.success(f"Invoice generator ready for: {sel_inv}")
    else:
        st.info("No records available for invoice generation.")

# 6. ACCOUNTS & EXPENSES TAB (Restricted to Role 4: Site Accountant, CEO, GM, HOD, Admin)
if role in ["CEO", "GM", "HOD", "Site Accountant", "Admin"]:
    with get_tab("💰 Accounts & Expenses"):
        st.markdown("<h3 style='color: #f97316;'>💰 Expense Tracking & Financial Audits</h3>", unsafe_allow_html=True)
        if role in ["CEO", "GM", "HOD", "Site Accountant", "Admin"]:
            with st.expander("➕ Add New Expense", expanded=False):
                with st.form("expense_form", clear_on_submit=True):
                    e_title = st.text_input("Expense Title")
                    e_amt = st.text_input("Amount (PKR)", "0")
                    if st.form_submit_button("Record Expense"):
                        if e_title and e_amt.isdigit():
                            st.session_state.expenses.append({"id": f"EXP-{len(st.session_state.expenses)+1}", "title": e_title, "amount": int(e_amt), "category": "Maintenance", "date": datetime.today().strftime('%d/%m/%Y')})
                            save_data()
                            st.success("✅ Expense recorded!")
                            st.rerun()
        if st.session_state.expenses:
            st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True, hide_index=True)
        else:
            st.info("No expense records found.")

# 7. SETUP & ADMIN CONTROLS TAB (Restricted strictly to Role 5: Admin & Full View Roles)
if role in ["CEO", "GM", "HOD", "Admin"]:
    with get_tab("⚙️ Setup & Admin Controls"):
        st.markdown("<h3 style='color: #f97316;'>⚙️ Resort Setup & Inventory Management</h3>", unsafe_allow_html=True)
        with st.form("add_unit_form", clear_on_submit=True):
            new_unit_name = st.text_input("Add New Cottage / Unit Name")
            if st.form_submit_button("Add Unit"):
                if new_unit_name and new_unit_name not in st.session_state.units:
                    st.session_state.units.append(new_unit_name)
                    st.session_state.housekeeping[new_unit_name] = "Clean"
                    save_data()
                    st.success(f"Unit '{new_unit_name}' added successfully!")
                    st.rerun()