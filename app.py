import streamlit as st
from supabase import create_client, Client

# Supabase Credentials
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    supabase = None

import pandas as pd
from datetime import datetime, timedelta
import json
import os
import streamlit.components.v1 as components

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
    
    .decent-footer {
        background: linear-gradient(135deg, #1a1c29, #0f172a);
        border-top: 1px solid #3b82f6;
        padding: 20px;
        margin-top: 40px;
        border-radius: 10px;
        text-align: center;
        color: #94a3b8;
        font-size: 13px;
        box-shadow: 0 -4px 10px rgba(0,0,0,0.3);
    }
    .decent-footer strong {
        color: #ffffff;
    }
    .decent-footer .dev-name {
        color: #f97316;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    @media print {
        body { background-color: white !important; color: black !important; }
        .stApp { background-color: white !important; color: black !important; }
        .dark-header, [data-testid="stSidebar"], .stButton, hr, .stTabs, .panel-container, .decent-footer { display: none !important; }
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

# --- USERS & ROLES ---
USERS = {
    "ceo": {"password": "ceo123", "role": "CEO", "name": "Chief Executive Officer"},
    "gm": {"password": "gm123", "role": "General Manager", "name": "M. Arif Aziz"},
    "manager": {"password": "manager123", "role": "Resort Manager", "name": "Resort Manager"},
    "frontdesk": {"password": "desk123", "role": "Front Desk Officer", "name": "Front Desk Team"},
    "auditor": {"password": "audit", "role": "Auditor", "name": "Head Office Auditor"}
}

FULL_ACCESS = ["CEO", "General Manager"]
MANAGEMENT_ACCESS = ["CEO", "General Manager", "Resort Manager"]
OPERATIONS_ACCESS = ["CEO", "General Manager", "Resort Manager", "Front Desk Officer"]

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
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Secure Login", use_container_width=True)
            
            if submit_login:
                if u_input in USERS and USERS[u_input]["password"] == p_input:
                    st.session_state.logged_in = True
                    st.session_state.username = u_input
                    st.session_state.role = USERS[u_input]["role"]
                    st.session_state.name = USERS[u_input]["name"]
                    st.rerun()
                else:
                    st.error("Invalid Username or Password!")

        st.markdown("""
        <div style='text-align: center; margin-top: 30px; font-size: 12px; color: #64748b;'>
            © 2026 <strong>Holiday Country Club</strong>. All Rights Reserved.<br>
            <span style='color: #94a3b8;'>Engineered & Developed with Excellence by </span><span style='color: #f97316; font-weight: 700;'>M. Arif Aziz</span>
        </div>
        """, unsafe_allow_html=True)

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

    st.markdown("<br><hr style='border: 0.5px solid #334155;'><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: rgba(30, 41, 59, 0.5); padding: 15px; border-radius: 8px; border: 1px solid #334155; text-align: center;'>
        <p style='color: #94a3b8; font-size: 11px; margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px;'>System Architecture</p>
        <p style='color: #e2e8f0; font-size: 13px; font-weight: 700; margin-bottom: 2px;'>Designed & Developed By</p>
        <p style='color: #f97316; font-size: 14px; font-weight: 800; margin-bottom: 10px;'>M. Arif Aziz</p>
        <p style='color: #64748b; font-size: 10px; margin: 0;'>© 2026 Holiday Country Club<br>All Rights Reserved</p>
    </div>
    """, unsafe_allow_html=True)

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

# --- DYNAMIC FLIP PANELS SECTION ---
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

# --- FINANCIAL ANALYTICS DASHBOARD ---
if role in MANAGEMENT_ACCESS or role == "Auditor":
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

# --- NAVIGATION TABS ---
tab_titles = ["🏨 Stay Bookings", "🔍 Availability Checker", "🍽️ Day Visitors & Restaurant", "🧹 Housekeeping", "🧾 Invoice Generator"]
if role in MANAGEMENT_ACCESS or role == "Auditor":
    tab_titles.append("💰 Accounts & Expenses")
if role in FULL_ACCESS:
    tab_titles.append("⚙️ Setup & Admin Controls")

tabs = st.tabs(tab_titles)
def get_tab(name):
    return tabs[tab_titles.index(name)] if name in tab_titles else None

# 1. STAY BOOKINGS TAB
with get_tab("🏨 Stay Bookings"):
    st.markdown("<h3 style='color: #f97316;'>🚀 Upcoming Bookings Quick-Tracking Panel</h3>", unsafe_allow_html=True)
    upcoming_list = [b for b in st.session_state.bookings if b.get("status") in ["Booked", "Reserved"]]
    
    upcoming_list = sorted(
        upcoming_list, 
        key=lambda x: pd.to_datetime(x.get('checkin', ''), format='%d/%m/%Y', errors='coerce') or pd.Timestamp.max
    )
    
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

    if role in OPERATIONS_ACCESS:
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

        with st.expander("➕ Create New Stay Booking (CNIC & Address Included)", expanded=False):
            with st.form("booking_form", clear_on_submit=True):
                b_id = st.text_input("Booking ID (Sequential Unique)", value=auto_b_id)
                colA, colB = st.columns(2)
                g_name = colA.text_input("Guest Name")
                g_phone = colB.text_input("Contact Number")
                g_cnic = colA.text_input("CNIC / ID Card Number (شناختی کارڈ)")
                g_address = colB.text_input("Residential Address (ایڈریس)")
                
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
                        conflict_found = False
                        if not force_override:
                            new_in = pd.to_datetime(c_in_date)
                            new_out = pd.to_datetime(c_out_date)
                            for b in st.session_state.bookings:
                                if b.get("unit") == unit and b.get("status") not in ["Checked-Out", "Cancelled"]:
                                    existing_in = pd.to_datetime(b.get("checkin", ""), format='%d/%m/%Y', errors='coerce')
                                    existing_out = pd.to_datetime(b.get("checkout", ""), format='%d/%m/%Y', errors='coerce')
                                    if pd.notnull(existing_in) and pd.notnull(existing_out):
                                        if max(new_in, existing_in) < min(new_out, existing_out):
                                            conflict_found = True
                                            break
                        
                        if conflict_found:
                            st.error(f"❌ Conflict Error: Cottage '{unit}' is booked during these dates!")
                        else:
                            st.session_state.bookings.append({
                                "id": b_id, "name": g_name, "phone": g_phone, "cnic": g_cnic, "address": g_address, "unit": unit,
                                "checkin": c_in_date.strftime('%d/%m/%Y'), "checkout": c_out_date.strftime('%d/%m/%Y'), 
                                "status": status, "staytype": staytype, "rent": rent, "food": menu_total,
                                "food_items": menu_items_ordered,
                                "activities": selected_act, "activities_total": act_total
                            })
                            st.session_state.housekeeping[unit] = "Dirty"
                            save_data()
                            st.success("✅ Booking Saved Successfully!")
                            st.rerun()

        if supabase:
            try:
                for b in st.session_state.bookings:
                    supabase.table("booking").upsert({"id": b.get("id"), "data": b}).execute()
            except Exception:
                pass
            
        st.markdown("### 📋 Active Bookings Directory & Full Edit Management")
        
        booking_options = ["-- Select --"] + [f"{b.get('id', 'N/A')} - {b.get('name', 'Guest')}" for b in st.session_state.bookings]
        with st.expander("🛠️ Full Edit Booking Window (Name, CNIC, Address, Bills & Check-Out)", expanded=True):
            edit_b_sel_raw = st.selectbox("Select Booking ID to Edit / Update / Check-Out", options=booking_options, key="edit_b_target")
            edit_b_sel = edit_b_sel_raw.split(" - ")[0] if edit_b_sel_raw != "-- Select --" else "-- Select --"
            
            if edit_b_sel != "-- Select --":
                target_b = next((b for b in st.session_state.bookings if str(b.get("id")) == edit_b_sel), None)
                
                if target_b:
                    with st.form("update_booking_form"):
                        st.markdown(f"**Full Edit Window for Booking ID:** {target_b.get('id', 'N/A')}")
                        
                        uc_col1, uc_col2 = st.columns(2)
                        up_name = uc_col1.text_input("Edit Guest Name", value=target_b.get('name', ''))
                        up_phone = uc_col2.text_input("Edit Contact Number", value=target_b.get('phone', ''))
                        up_cnic = uc_col1.text_input("Edit CNIC", value=target_b.get('cnic', ''))
                        up_address = uc_col2.text_input("Edit Address", value=target_b.get('address', ''))
                        
                        curr_unit = target_b.get('unit', st.session_state.units[0])
                        unit_idx = st.session_state.units.index(curr_unit) if curr_unit in st.session_state.units else 0
                        up_unit = uc_col1.selectbox("Edit Cottage / Unit", options=st.session_state.units, index=unit_idx)
                        
                        current_status = target_b.get('status', 'Reserved')
                        status_list = ["Reserved", "Booked", "Occupied", "Checked-Out", "Cancelled"]
                        status_idx = status_list.index(current_status) if current_status in status_list else 2
                        new_status = uc_col2.selectbox("Update Status", status_list, index=status_idx)
                        
                        # Dates
                        default_in = pd.to_datetime(target_b.get('checkin', ''), format='%d/%m/%Y', errors='coerce')
                        if pd.isnull(default_in): default_in = datetime.today()
                        default_out = pd.to_datetime(target_b.get('checkout', ''), format='%d/%m/%Y', errors='coerce')
                        if pd.isnull(default_out): default_out = datetime.today() + timedelta(days=1)
                        
                        up_cin = uc_col1.date_input("Check-in Date", value=default_in)
                        up_cout = uc_col2.date_input("Check-out Date", value=default_out)
                        
                        current_staytype = target_b.get("staytype", "Paid Regular")
                        staytype_list = ["Paid Regular", "Complimentary", "Corporate"]
                        staytype_idx = staytype_list.index(current_staytype) if current_staytype in staytype_list else 0
                        new_staytype = uc_col1.selectbox("Update Stay Type", staytype_list, index=staytype_idx)
                        new_rent = uc_col2.text_input("Update Rent (PKR)", value=str(target_b.get("rent", "0")))
                        
                        st.markdown("---")
                        st.markdown("<h5 style='color: #f97316;'>Add / Update Food Items</h5>", unsafe_allow_html=True)
                        added_f_items = []
                        existing_f_map = {item['name']: item.get('comp', False) for item in target_b.get("food_items", []) if isinstance(item, dict)}
                        for i, m in enumerate(st.session_state.restaurant_menu):
                            cols_fm = st.columns([3, 2])
                            cols_fm[0].markdown(f"**{m['item']}** (Rs. {m['price']})")
                            default_choice_idx = 0
                            if m['item'] in existing_f_map:
                                default_choice_idx = 2 if existing_f_map[m['item']] else 1
                            m_choice = cols_fm[1].radio("Type", ["Unselected", "Paid", "Complimentary"], index=default_choice_idx, key=f"edit_b_menu_choice_{i}", horizontal=True, label_visibility="collapsed")
                            if m_choice != "Unselected":
                                is_comp = (m_choice == "Complimentary")
                                added_f_items.append({'name': m['item'], 'price': m['price'], 'comp': is_comp})
                                
                        st.markdown("---")
                        st.markdown("<h5 style='color: #f97316;'>Add / Update Services & Pick & Drop</h5>", unsafe_allow_html=True)
                        added_act_items = []
                        existing_act_map = {item['name']: item.get('comp', False) for item in target_b.get("activities", []) if isinstance(item, dict)}
                        for i, s in enumerate(st.session_state.services_catalog):
                            cols_am = st.columns([3, 2])
                            cols_am[0].markdown(f"**{s['name']}** (Rs. {s['price']})")
                            default_act_idx = 0
                            if s['name'] in existing_act_map:
                                default_act_idx = 2 if existing_act_map[s['name']] else 1
                            s_choice = cols_am[1].radio("Type", ["Unselected", "Paid", "Complimentary"], index=default_act_idx, key=f"edit_b_act_choice_{i}", horizontal=True, label_visibility="collapsed")
                            if s_choice != "Unselected":
                                is_comp = (s_choice == "Complimentary")
                                added_act_items.append({'name': s['name'], 'price': s['price'], 'comp': is_comp})
                                
                        submit_updates = st.form_submit_button("Save & Update Booking / Check-Out")
                        if submit_updates:
                            new_food_total = sum(item['price'] for item in added_f_items if not item.get('comp', False))
                            new_act_total = sum(item['price'] for item in added_act_items if not item.get('comp', False))
                            
                            target_b['name'] = up_name
                            target_b['phone'] = up_phone
                            target_b['cnic'] = up_cnic
                            target_b['address'] = up_address
                            target_b['unit'] = up_unit
                            target_b['checkin'] = up_cin.strftime('%d/%m/%Y')
                            target_b['checkout'] = up_cout.strftime('%d/%m/%Y')
                            target_b['status'] = new_status
                            target_b['staytype'] = new_staytype
                            target_b['rent'] = new_rent
                            target_b['food_items'] = added_f_items
                            target_b['food'] = new_food_total
                            target_b['activities'] = added_act_items
                            target_b['activities_total'] = new_act_total
                            
                            if new_status == "Checked-Out":
                                st.session_state.housekeeping[up_unit] = "Dirty"
                                
                            save_data()
                            st.success(f"✅ Booking {edit_b_sel} updated successfully!")
                            st.rerun()

        st.markdown("### 📋 Direct Row-Level Delete & Booking Management")
        if st.session_state.bookings:
            for idx, b in enumerate(st.session_state.bookings):
                r_val = int(b.get("rent", 0)) if str(b.get("rent", 0)).isdigit() else 0
                f_val = int(b.get("food", 0)) if str(b.get("food", 0)).isdigit() else 0
                a_val = int(b.get("activities_total", 0)) if str(b.get("activities_total", 0)).isdigit() else 0
                grand = r_val + f_val + a_val
                
                rc1, rc2, rc3 = st.columns([5, 2, 1])
                rc1.markdown(f"**{b.get('id')}** — {b.get('name')} | **Unit:** {b.get('unit')} | **CNIC:** {b.get('cnic', 'N/A')} | **Total:** Rs. {grand:,} ({b.get('status')})")
                rc2.markdown(f"In: {b.get('checkin')} | Out: {b.get('checkout')}")
                
                # Direct delete button per row
                if rc3.button("🗑️ Delete", key=f"del_book_row_{b.get('id')}_{idx}"):
                    removed = st.session_state.bookings.pop(idx)
                    st.session_state.deleted_bookings.insert(0, {"record": removed, "index": idx})
                    save_data()
                    st.success(f"Booking {removed.get('id')} deleted successfully!")
                    st.rerun()
                st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #334155;'>", unsafe_allow_html=True)
        else:
            st.info("No active bookings found.")
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
        target_date_str = check_date.strftime('%d/%m/%Y')
        
        hk_status = st.session_state.housekeeping.get(check_unit, "Clean")
        if hk_status in ["Maintenance", "Dirty"]:
            if hk_status == "Maintenance":
                st.error(f"🛠️ **{check_unit}** is **UNDER MAINTENANCE** and unavailable on {target_date_str}!")
            else:
                st.warning(f"🧹 **{check_unit}** is currently marked as **DIRTY** (Cleaning required).")
        else:
            checkout_match, checkin_match, active_stay_match = None, None, None
            for b in st.session_state.bookings:
                if b.get("unit") == check_unit and b.get("status") not in ["Checked-Out", "Cancelled"]:
                    b_in = pd.to_datetime(b.get("checkin", ""), format='%d/%m/%Y', errors='coerce')
                    b_out = pd.to_datetime(b.get("checkout", ""), format='%d/%m/%Y', errors='coerce')
                    if pd.notnull(b_in) and pd.notnull(b_out):
                        if b_out == target_dt: checkout_match = b
                        if b_in == target_dt: checkin_match = b
                        if b_in < target_dt < b_out: active_stay_match = b

            if checkout_match or checkin_match or active_stay_match:
                status_msg = f"📅 **Status Breakdown for {check_unit} on {target_date_str}:**\n\n"
                if checkout_match: status_msg += f"📤 **Checkout:** {checkout_match.get('name')} (ID: {checkout_match.get('id')})\n"
                if checkin_match: status_msg += f"📥 **Check-In:** {checkin_match.get('name')} (ID: {checkin_match.get('id')})\n"
                if active_stay_match: status_msg += f"🔴 **Occupied:** {active_stay_match.get('name')} (ID: {active_stay_match.get('id')})\n"
                st.warning(status_msg)
            else:
                st.success(f"🟢 **{check_unit}** is **COMPLETELY AVAILABLE** on {target_date_str}!")

# 3. DAY VISITORS & RESTAURANT TAB
with get_tab("🍽️ Day Visitors & Restaurant"):
    with st.expander("➕ Register New Day Visitor / Walk-In Table", expanded=False):
        v_existing_nums = []
        for v in st.session_state.visitors:
            v_identifier = v.get("id", "")
            if str(v_identifier).startswith("VIS-"):
                try: v_existing_nums.append(int(str(v_identifier).split("-")[1]))
                except: pass
        v_next_id_num = max(v_existing_nums) + 1 if v_existing_nums else 1
        auto_v_id = f"VIS-{v_next_id_num}"

        with st.form("visitor_form", clear_on_submit=True):
            v_id = st.text_input("Visitor ID (Unique)", value=auto_v_id)
            colA, colB = st.columns(2)
            v_name = colA.text_input("Visitor Name")
            v_phone = colB.text_input("Contact Number")
            v_date = colA.date_input("Visit Date", datetime.today())
            v_type = colB.selectbox("Visitor Type", ["Paid", "Complimentary", "Corporate"], key="new_visitor_type_select")
            
            st.markdown("---")
            st.markdown("<h4 style='color: #f97316;'>🍽️ Restaurant Menu Items</h4>", unsafe_allow_html=True)
            v_menu_items, v_food_total = [], 0
            for i, m in enumerate(st.session_state.restaurant_menu):
                cols_vm = st.columns([3, 2])
                cols_vm[0].markdown(f"**{m['item']}** (Rs. {m['price']})")
                m_choice = cols_vm[1].radio("Type", ["Unselected", "Paid", "Complimentary"], key=f"vis_menu_choice_{i}", horizontal=True, label_visibility="collapsed")
                if m_choice != "Unselected":
                    is_comp = (m_choice == "Complimentary")
                    v_menu_items.append({'name': m['item'], 'price': m['price'], 'comp': is_comp})
                    if not is_comp: v_food_total += m['price']
            
            st.markdown("---")
            st.markdown("<h4 style='color: #f97316;'>⚡ Resort Activities & Services</h4>", unsafe_allow_html=True)
            v_selected_act, v_act_total = [], 0
            for i, s in enumerate(st.session_state.services_catalog):
                cols_vs = st.columns([3, 2])
                cols_vs[0].markdown(f"**{s['name']}** (Rs. {s['price']})")
                s_choice = cols_vs[1].radio("Type", ["Unselected", "Paid", "Complimentary"], key=f"vis_act_choice_{i}", horizontal=True, label_visibility="collapsed")
                if s_choice != "Unselected":
                    is_comp = (s_choice == "Complimentary")
                    v_selected_act.append({'name': s['name'], 'price': s['price'], 'comp': is_comp})
                    if not is_comp: v_act_total += s['price']
            
            if st.form_submit_button("Save Day Visitor Entry"):
                if any(str(v.get("id")) == v_id for v in st.session_state.visitors):
                    st.error(f"❌ Error: Visitor ID '{v_id}' already exists!")
                elif not v_name:
                    st.error("❌ Error: Visitor Name cannot be empty.")
                else:
                    st.session_state.visitors.append({
                        "id": v_id, "name": v_name, "phone": v_phone, "date": v_date.strftime('%d/%m/%Y'),
                        "v_type": v_type, "food_items": v_menu_items, "food_bill": v_food_total,
                        "activities": v_selected_act, "activities_total": v_act_total
                    })
                    save_data()
                    st.success("✅ Day Visitor Added Successfully!")
                    st.rerun()

    st.markdown("### 📋 Day Visitors & Direct Row Delete")
    if st.session_state.visitors:
        for idx, v in enumerate(st.session_state.visitors):
            f_bill = int(v.get("food_bill", 0)) if str(v.get("food_bill", 0)).isdigit() else 0
            s_total = int(v.get("activities_total", 0)) if str(v.get("activities_total", 0)).isdigit() else 0
            
            vc1, vc2 = st.columns([5, 1])
            vc1.markdown(f"**{v.get('id')}** — {v.get('name')} ({v.get('phone')}) | Food: Rs. {f_bill:,} | Services: Rs. {s_total:,} [{v.get('v_type')}]")
            if vc2.button("🗑️ Delete", key=f"del_vis_row_{v.get('id')}_{idx}"):
                removed_v = st.session_state.visitors.pop(idx)
                st.session_state.deleted_visitors.insert(0, {"record": removed_v, "index": idx})
                save_data()
                st.success("Visitor deleted successfully!")
                st.rerun()
            st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #334155;'>", unsafe_allow_html=True)
    else:
        st.info("No visitor records found.")

# 4. HOUSEKEEPING TAB
with get_tab("🧹 Housekeeping"):
    st.markdown("<h3 style='color: #f97316;'>🧹 Housekeeping & Room Turnaround Management</h3>", unsafe_allow_html=True)
    hk_cols = st.columns(3)
    for idx, unit in enumerate(st.session_state.units):
        curr_status = st.session_state.housekeeping.get(unit, "Clean")
        status_color = "#16a34a" if curr_status == "Clean" else "#dc2626" if curr_status == "Maintenance" else "#ea580c"
        
        with hk_cols[idx % 3]:
            st.markdown(f"""
            <div style='background: #1a1c29; padding: 15px; border-radius: 8px; border-left: 5px solid {status_color}; margin-bottom: 15px;'>
                <b style='color: white;'>{unit}</b><br>
                <span style='font-size: 12px; color: {status_color}; font-weight: 700;'>Status: {curr_status}</span>
            </div>
            """, unsafe_allow_html=True)
            
            hk_status_list = ["Clean", "Dirty", "Maintenance"]
            hk_idx = hk_status_list.index(curr_status) if curr_status in hk_status_list else 0
            new_hk_status = st.selectbox(f"Update {unit}", hk_status_list, index=hk_idx, key=f"hk_sel_{idx}")
            if new_hk_status != curr_status:
                st.session_state.housekeeping[unit] = new_hk_status
                save_data()
                st.rerun()

# 5. INVOICE GENERATOR TAB
with get_tab("🧾 Invoice Generator"):
    st.markdown("<h3 style='color: #f97316;'>🧾 Executive Invoice Generator & Detailed Word Export</h3>", unsafe_allow_html=True)
    booking_inv_options = [f"{b.get('id', 'HCC-1001')} - {b.get('name', 'Guest')}" for b in st.session_state.bookings if isinstance(b, dict)]
    visitor_inv_options = [f"{v.get('id', 'VIS-1')} - {v.get('name', 'Visitor')}" for v in st.session_state.visitors if isinstance(v, dict)]
    all_inv_display_options = ["-- Select Booking or Visitor --"] + booking_inv_options + visitor_inv_options
    
    if len(all_inv_display_options) > 1:
        sel_inv_raw = st.selectbox("Select Booking or Visitor ID for Detailed Invoice", options=all_inv_display_options)
        if sel_inv_raw != "-- Select Booking or Visitor --":
            sel_inv = sel_inv_raw.split(" - ")[0]
            is_visitor = not sel_inv.startswith("HCC-")
            inv_data = next((b for b in st.session_state.bookings if str(b.get('id', '')) == sel_inv), None) if not is_visitor else next((v for v in st.session_state.visitors if str(v.get('id', '')) == sel_inv), None)
            
            if inv_data:
                paid_items_list, comp_items_list, total_payable, total_comp_value = [], [], 0, 0
                if not is_visitor:
                    stay_type = inv_data.get('staytype', 'Paid Regular')
                    rent_val = int(inv_data.get("rent", 0)) if str(inv_data.get("rent", 0)).isdigit() else 0
                    if stay_type == 'Complimentary':
                        comp_items_list.append({"name": f"Cottage Rent ({inv_data.get('unit', 'N/A')})", "price": rent_val})
                        total_comp_value += rent_val
                    else:
                        paid_items_list.append({"name": f"Cottage Rent ({inv_data.get('unit', 'N/A')})", "price": rent_val})
                        total_payable += rent_val
                        
                    for f_item in inv_data.get('food_items', []):
                        if isinstance(f_item, dict):
                            if f_item.get('comp'):
                                comp_items_list.append({"name": f_item.get('name'), "price": f_item.get('price')})
                                total_comp_value += f_item.get('price')
                            else:
                                paid_items_list.append({"name": f_item.get('name'), "price": f_item.get('price')})
                                total_payable += f_item.get('price')
                
                inv_html = f"""
                <div class='invoice-box'>
                    <h2 style='text-align: center; color: #f97316; margin-bottom: 5px;'>HOLIDAY COUNTRY CLUB</h2>
                    <p style='text-align: center; color: #94a3b8; font-size: 12px;'>Murree Hills Development Project | Detailed Executive Invoice</p>
                    <hr style='border: 1px solid #475569;'>
                    <p><b>Reference ID:</b> {sel_inv}</p>
                    <p><b>Name:</b> {inv_data.get('name', 'N/A')} | <b>CNIC:</b> {inv_data.get('cnic', 'N/A')}</p>
                    <p><b>Contact:</b> {inv_data.get('phone', 'N/A')} | <b>Address:</b> {inv_data.get('address', 'N/A')}</p>
                    <h3 style='text-align: right; color: #16a34a;'>Net Payable Grand Total: Rs. {total_payable:,}</h3>
                </div>
                """
                st.markdown(inv_html, unsafe_allow_html=True)

# 6. ACCOUNTS & EXPENSES TAB
if role in MANAGEMENT_ACCESS or role == "Auditor":
    with get_tab("💰 Accounts & Expenses"):
        st.markdown("<h3 style='color: #f97316;'>💰 Expense Tracking & Financial Audits</h3>", unsafe_allow_html=True)
        if "deleted_expenses" not in st.session_state: st.session_state.deleted_expenses = []

        with st.expander("➕ Add New Expense", expanded=False):
            with st.form("expense_form", clear_on_submit=True):
                col_e1, col_e2, col_e3 = st.columns([2, 1, 1])
                e_title = col_e1.text_input("Expense Description / Title")
                e_amt = col_e2.text_input("Amount (PKR)", "0")
                e_cat = col_e3.selectbox("Category", ["Maintenance", "Utilities", "Kitchen Supplies", "Staff Salaries", "Miscellaneous"])
                
                if st.form_submit_button("Record Expense"):
                    if e_title and e_amt.isdigit() and int(e_amt) > 0:
                        new_id = f"EXP-{len(st.session_state.expenses) + 1}"
                        st.session_state.expenses.append({"id": new_id, "title": e_title, "amount": int(e_amt), "category": e_cat, "date": datetime.today().strftime('%d/%m/%Y')})
                        save_data()
                        st.success("✅ Expense Recorded Successfully!")
                        st.rerun()

        st.markdown("#### 📋 Recorded Expenses & Direct Delete")
        if st.session_state.expenses:
            for idx, e in enumerate(st.session_state.expenses):
                ec1, ec2 = st.columns([5, 1])
                ec1.markdown(f"**[{e.get('id')}]** {e.get('title')} — **Rs. {int(e.get('amount', 0)):,}** ({e.get('category')}) on {e.get('date')}")
                if ec2.button("🗑️ Delete", key=f"del_exp_row_{e.get('id')}_{idx}"):
                    removed_e = st.session_state.expenses.pop(idx)
                    save_data()
                    st.success("Expense deleted successfully!")
                    st.rerun()
                st.markdown("<hr style='margin: 5px 0; border: 0.5px solid #334155;'>", unsafe_allow_html=True)
        else:
            st.info("No expense records found.")

# 7. SETUP & ADMIN CONTROLS TAB
if role in FULL_ACCESS:
    with get_tab("⚙️ Setup & Admin Controls"):
        st.markdown("<h3 style='color: #f97316;'>⚙️ Resort Setup & Inventory Management</h3>", unsafe_allow_html=True)
        st.markdown("#### 🏨 Cottages & Units Control")
        
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            with st.form("add_unit_form", clear_on_submit=True):
                new_unit_name = st.text_input("Add New Cottage / Unit Name")
                if st.form_submit_button("Add Unit"):
                    if new_unit_name.strip() and new_unit_name not in st.session_state.units:
                        st.session_state.units.append(new_unit_name)
                        st.session_state.housekeeping[new_unit_name] = "Clean"
                        save_data()
                        st.success(f"✅ Unit '{new_unit_name}' added successfully!")
                        st.rerun()
        with col_u2:
            with st.form("del_unit_form"):
                del_unit_sel = st.selectbox("Select Unit to Delete", options=["-- Select --"] + st.session_state.units)
                if st.form_submit_button("Delete Unit"):
                    if del_unit_sel != "-- Select --":
                        st.session_state.units.remove(del_unit_sel)
                        if del_unit_sel in st.session_state.housekeeping:
                            del st.session_state.housekeeping[del_unit_sel]
                        save_data()
                        st.success(f"Unit '{del_unit_sel}' deleted!")
                        st.rerun()

st.markdown("""
<div class='decent-footer'>
    <div style='margin-bottom: 5px;'>© 2026 <strong>Holiday Country Club | Executive Portal</strong>. All Rights Reserved.</div>
    <div style='font-size: 12px; color: #64748b;'>Designed, Engineered & Maintained with Precision by <span class='dev-name'>M. Arif Aziz</span></div>
</div>
""", unsafe_allow_html=True)
