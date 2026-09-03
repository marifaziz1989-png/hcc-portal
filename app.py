import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import streamlit.components.v1 as components

# --- SUPABASE CONFIGURATION (SAFE FALLBACK) ---
try:
    from supabase import create_client, Client
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    supabase: Client = create_client(url, key) if url and key else None
except Exception:
    supabase = None

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
    
    /* --- BLINKING ANIMATION FOR HEADINGS --- */
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
    
    /* --- ELEGANT FOOTER STYLE --- */
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
        {"name": "Luggage / Pick & Drop Service", "price": 2500},
        {"name": "Airport/City Transfer", "price": 4000},
        {"name": "Guided Resort Tour", "price": 1500}
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

# --- DYNAMIC 5-SECOND FLIP PANELS SECTION ---
panels_html = f"""
<div style="display: flex; gap: 20px; width: 100%; font-family: sans-serif; margin-bottom: 20px;">
    
    <!-- PENDING TASKS PANEL -->
    <div style="flex: 1; background: linear-gradient(135deg, #1a1c29, #251b2d); border: 1px solid #f97316; padding: 12px 15px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
        <div class="blinking-heading" style="font-size: 12px; font-weight: 700; color: #f97316; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>⚡</span> PENDING & CLEANING TASKS
        </div>
        <div id="pending-carousel" style="min-height: 50px; display: flex; align-items: center; color: #ffedd5; font-size: 11px; font-weight: 400;">
            Loading...
        </div>
    </div>

    <!-- TODAY CHECK-OUTS PANEL -->
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

# 1. STAY BOOKINGS TAB (Updated with complete Guest Reservation Portal fields)
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

        with st.expander("➕ Create New Stay Booking (Comprehensive Guest Portal Form)", expanded=False):
            with st.form("resort_booking_form", clear_on_submit=True):
                b_id = st.text_input("Booking ID (Sequential Unique)", value=auto_b_id)
                st.markdown("---")
                
                # 1. Guest Personal Information
                st.subheader("1. Guest Personal Information")
                col1, col2 = st.columns(2)
                with col1:
                    full_name = st.text_input("Full Name (with Title e.g., Mr./Mrs.)")
                    contact = st.text_input("Mobile / WhatsApp Number")
                    email = st.text_input("Email Address")
                with col2:
                    address = st.text_input("City / Residential Address")
                    cnic_passport = st.text_input("CNIC / Passport Number")

                st.markdown("---")
                
                # 2. Reservation & Stay Details
                st.subheader("2. Reservation & Stay Details")
                col3, col4 = st.columns(2)
                with col3:
                    check_in = st.date_input("Check-in Date")
                    adults = st.number_input("Number of Adults", min_value=1, value=2, step=1)
                with col4:
                    check_out = st.date_input("Check-out Date")
                    children = st.number_input("Number of Children", min_value=0, value=0, step=1)

                st.markdown("---")
                
                # 3. Accommodation Type Selection
                st.subheader("3. Accommodation Type")
                col5, col6 = st.columns(2)
                with col5:
                    room_category = st.selectbox(
                        "Select Accommodation Type",
                        ["Deluxe Room", "Family Suite", "Wooden Cottage", "Treehouse", "Jacuzzi Villa"]
                    )
                    unit = st.selectbox("Assign Specific Cottage / Unit", options=st.session_state.units)
                with col6:
                    units_count = st.number_input("Number of Units", min_value=1, value=1, step=1)
                    bedding = st.selectbox("Bedding Preference", ["Double Bed", "Twin Beds"])
                    status = st.selectbox("Status", ["Reserved", "Booked", "Occupied", "Checked-Out", "Cancelled"], index=0)
                    staytype = st.selectbox("Stay Type", ["Paid Regular", "Complimentary", "Corporate"])
                    rent = st.text_input("Cottage Rent Bill (PKR)", "0")

                st.markdown("---")
                
                # 4. Special Requests & Add-ons
                st.subheader("4. Special Requests & Add-ons")
                special_requests = st.text_area("Special Requests (e.g., food allergies, honeymoon setup)")
                addons = st.multiselect(
                    "Add-on Services",
                    ["Airport/City Transfer", "Jacuzzi Access", "BBQ Arrangement", "Guided Resort Tour"]
                )

                st.markdown("---")
                
                # 5. Payment & Billing Details
                st.subheader("5. Payment & Billing Details")
                col7, col8 = st.columns(2)
                with col7:
                    payment_method = st.selectbox(
                        "Advance Payment Method",
                        ["Bank Transfer", "JazzCash / EasyPaisa", "Credit/Debit Card", "Cash on Arrival"]
                    )
                with col8:
                    advance_amount = st.number_input("Advance Amount Paid (PKR)", min_value=0, value=0, step=1000)

                st.markdown("---")
                
                # Restaurant Menu Order Selection
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
                
                # 6. Terms & Conditions
                st.subheader("6. Terms & Conditions")
                terms_accepted = st.checkbox("I agree to the Resort's Cancellation Policy and Check-in/Check-out Rules.")

                force_override = st.checkbox("⚠️ Force Manual Override (Bypass Conflict Check)")
                submit_button = st.form_submit_button(label="Submit Booking")

                if submit_button:
                    if not terms_accepted:
                        st.error("Please accept the Terms & Conditions to proceed.")
                    elif not full_name.strip() or not contact.strip():
                        st.warning("Please fill in your Full Name and Contact Number.")
                    elif any(str(b.get("id")) == b_id for b in st.session_state.bookings):
                        st.error(f"❌ Error: Booking ID '{b_id}' already exists!")
                    else:
                        conflict_found = False
                        if not force_override:
                            new_in = pd.to_datetime(check_in)
                            new_out = pd.to_datetime(check_out)
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
                            new_booking_dict = {
                                "id": b_id, "name": full_name, "phone": contact, "email": email,
                                "address": address, "cnic_passport": cnic_passport, "unit": unit,
                                "checkin": check_in.strftime('%d/%m/%Y'), "checkout": check_out.strftime('%d/%m/%Y'), 
                                "adults": adults, "children": children, "room_category": room_category,
                                "units_booked": units_count, "bedding": bedding, "special_requests": special_requests,
                                "addons": addons, "payment_method": payment_method, "advance_amount": advance_amount,
                                "terms_accepted": terms_accepted, "status": status, "staytype": staytype, 
                                "rent": rent, "food": menu_total, "food_items": menu_items_ordered,
                                "activities": [], "activities_total": 0
                            }
                            st.session_state.bookings.append(new_booking_dict)
                            st.session_state.housekeeping[unit] = "Dirty"
                            save_data()
                            if supabase:
                                try:
                                    supabase.table("booking").upsert({"id": b_id, "data": new_booking_dict}).execute()
                                except Exception:
                                    pass
                            st.success("Booking submitted successfully!")

        st.markdown("### 📋 Active Bookings Directory & Management")
        
        booking_options = ["-- Select --"] + [f"{b.get('id', 'N/A')} - {b.get('name', 'Guest')}" for b in st.session_state.bookings]
        with st.expander("🛠️ Edit Booking, Update Running Bills & Mark Check-Out", expanded=True):
            edit_b_sel_raw = st.selectbox("Select Booking ID to Edit / Update / Check-Out", options=booking_options, key="edit_b_target")
            edit_b_sel = edit_b_sel_raw.split(" - ")[0] if edit_b_sel_raw != "-- Select --" else "-- Select --"
            
            if edit_b_sel != "-- Select --":
                target_b = next((b for b in st.session_state.bookings if str(b.get("id")) == edit_b_sel), None)
                
                if target_b:
                    with st.form("update_booking_form"):
                        st.markdown(f"**Editing Booking:** {target_b.get('id', 'N/A')} - **Guest:** {target_b.get('name', 'N/A')} ({target_b.get('unit', 'N/A')})")
                        uc_col1, uc_col2 = st.columns(2)
                        current_status = target_b.get('status', 'Reserved')
                        status_list = ["Reserved", "Booked", "Occupied", "Checked-Out", "Cancelled"]
                        status_idx = status_list.index(current_status) if current_status in status_list else 2
                        new_status = uc_col1.selectbox("Update Status", status_list, index=status_idx)
                        new_rent = uc_col2.text_input("Update Rent (PKR)", value=str(target_b.get("rent", "0")))
                        
                        current_staytype = target_b.get("staytype", "Paid Regular")
                        staytype_list = ["Paid Regular", "Complimentary", "Corporate"]
                        staytype_idx = staytype_list.index(current_staytype) if current_staytype in staytype_list else 0
                        new_staytype = st.selectbox("Update Stay Type", staytype_list, index=staytype_idx)
                        
                        submit_updates = st.form_submit_button("Save & Update Booking / Check-Out")
                        if submit_updates:
                            target_b['status'] = new_status
                            target_b['staytype'] = new_staytype
                            target_b['rent'] = new_rent
                            if new_status == "Checked-Out":
                                st.session_state.housekeeping[target_b['unit']] = "Dirty"
                            save_data()
                            if supabase:
                                try:
                                    supabase.table("booking").upsert({"id": target_b.get("id"), "data": target_b}).execute()
                                except:
                                    pass
                            st.success(f"✅ Booking {edit_b_sel} updated successfully!")
                            st.rerun()

        table_rows = []
        for b in st.session_state.bookings:
            r_val = int(b.get("rent", 0)) if str(b.get("rent", 0)).isdigit() else 0
            f_val = int(b.get("food", 0)) if str(b.get("food", 0)).isdigit() else 0
            grand = r_val + f_val
            
            table_rows.append({
                "ID": b.get('id', 'N/A'),
                "Name": b.get('name', 'N/A'),
                "Phone": b.get('phone', 'N/A'),
                "Unit": b.get('unit', 'N/A'),
                "Check-In": b.get('checkin', 'N/A'),
                "Check-Out": b.get('checkout', 'N/A'),
                "Status": b.get('status', 'N/A'),
                "Type": b.get('staytype', 'Paid Regular'),
                "Grand Total (PKR)": f"Rs. {grand:,}"
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            conflict_found = False
                        if not force_override:
                            new_in = pd.to_datetime(check_in)
                            new_out = pd.to_datetime(check_out)
                            for b in st.session_state.bookings:
                                if b.get("unit") == unit and b.get("status") not in ["Checked-Out", "Cancelled"]:
                                    existing_in = pd.to_datetime(b.get("checkin", ""), format='%d/%m/%Y', errors='coerce')
                                    existing_out = pd.to_datetime(b.get("checkout", ""), format='%d/%m/%Y', errors='coerce')
                                    if pd.notnull(existing_in) and pd.notnull(existing_out):
                                        if max(new_in, existing_in) < min(new_out, existing_out):
                                            conflict_found = True
                                            break
                        save_data()
                        st.success("Booking deleted and saved to recycle bin!")
                        st.rerun()
                else:
                    st.warning("Please select a valid Booking ID.")
                    
        with col_d2:
            valid_deleted_b = [item for item in st.session_state.deleted_bookings if isinstance(item, dict) and "record" in item]
            if valid_deleted_b:
                undo_options = ["-- Select --"] + [f"{item['record'].get('id', 'HCC')} - {item['record'].get('name', 'Guest')}" for item in valid_deleted_b]
                undo_sel = st.selectbox("Restore Deleted Booking (Undo)", options=undo_options, key="undo_b_select")
                if st.button("🔄 Undo / Restore Booking"):
                    if undo_sel != "-- Select --":
                        chosen_id = undo_sel.split(" - ")[0]
                        item_entry = next((item for item in valid_deleted_b if str(item['record'].get('id')) == chosen_id), None)
                        if item_entry:
                            orig_idx = min(item_entry.get('index', 0), len(st.session_state.bookings))
                            restored_rec = item_entry['record']
                            st.session_state.bookings.insert(orig_idx, restored_rec)
                            st.session_state.deleted_bookings = [item for item in st.session_state.deleted_bookings if str(item.get('record', {}).get('id')) != chosen_id]
                            save_data()
                            if supabase:
                                try:
                                    supabase.table("booking").upsert({"id": restored_rec.get("id"), "data": restored_rec}).execute()
                                except:
                                    pass
                            st.success("Booking restored successfully!")
                            st.rerun()
            else:
                st.info("Recycle bin is empty.")
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
                st.error(f"🛠️ **{check_unit}** is **UNDER MAINTENANCE** in Housekeeping records and is unavailable for booking on {target_date_str}!")
            else:
                st.warning(f"🧹 **{check_unit}** is currently marked as **DIRTY** in Housekeeping (Turnaround cleaning required).")
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
                if checkout_match: status_msg += f"📤 **Checkout:** {checkout_match.get('name', 'N/A')}\n\n"
                if checkin_match: status_msg += f"📥 **Check-In:** {checkin_match.get('name', 'N/A')}\n"
                if active_stay_match: status_msg += f"🔴 **Fully Occupied:** {active_stay_match.get('name', 'N/A')}\n"
                st.warning(status_msg)
            else:
                st.success(f"🟢 **{check_unit}** is **COMPLETELY AVAILABLE** on {target_date_str}!")

    st.markdown("---")
    st.markdown(f"<h4 style='color: #f97316;'>📅 Full Resort Status Overview for Date: {check_date.strftime('%d/%m/%Y')}</h4>", unsafe_allow_html=True)
    
    overview_data = []
    target_dt = pd.to_datetime(check_date)
    for unit in st.session_state.units:
        hk_status = st.session_state.housekeeping.get(unit, "Clean")
        if hk_status == "Maintenance":
            status_text, client_info = "🛠️ UNAVAILABLE - Under Maintenance", "Housekeeping Block"
        elif hk_status == "Dirty":
            status_text, client_info = "🟠 Turnaround Required (Dirty)", "Cleaning Pending"
        else:
            status_text, client_info = "🟢 Available All Day", "None"
            full_match = next((b for b in st.session_state.bookings if b.get("unit") == unit and b.get("status") not in ["Checked-Out", "Cancelled"] and pd.to_datetime(b.get("checkin"), format='%d/%m/%Y', errors='coerce') <= target_dt <= pd.to_datetime(b.get("checkout"), format='%d/%m/%Y', errors='coerce')), None)
            if full_match:
                status_text, client_info = "🔴 Booked (Occupied)", f"{full_match.get('name', 'N/A')}"
                
        overview_data.append({"Cottage / Unit": unit, "Housekeeping": hk_status, "Status": status_text, "Client Details": client_info})
    st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)

# 3. DAY VISITORS & RESTAURANT TAB
with get_tab("🍽️ Day Visitors & Restaurant"):
    st.markdown("<h3 style='color: #f97316;'>🍽️ Day Visitors & Restaurant Management</h3>", unsafe_allow_html=True)
    st.info("Manage walk-in restaurant guests and day visitors here.")

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
            
            new_hk_status = st.selectbox(f"Update {unit}", ["Clean", "Dirty", "Maintenance"], index=["Clean", "Dirty", "Maintenance"].index(curr_status), key=f"hk_sel_{idx}")
            if new_hk_status != curr_status:
                st.session_state.housekeeping[unit] = new_hk_status
                save_data()
                st.rerun()

# 5. INVOICE GENERATOR TAB
with get_tab("🧾 Invoice Generator"):
    st.markdown("<h3 style='color: #f97316;'>🧾 Executive Invoice Generator</h3>", unsafe_allow_html=True)
    booking_inv_options = [f"{b.get('id', 'HCC-1001')} - {b.get('name', 'Guest')}" for b in st.session_state.bookings if isinstance(b, dict)]
    if booking_inv_options:
        sel_inv_raw = st.selectbox("Select Booking for Invoice", options=["-- Select --"] + booking_inv_options)
        if sel_inv_raw != "-- Select --":
            sel_id = sel_inv_raw.split(" - ")[0]
            b_data = next((b for b in st.session_state.bookings if str(b.get('id')) == sel_id), None)
            if b_data:
                rent = int(b_data.get('rent', 0)) if str(b_data.get('rent', 0)).isdigit() else 0
                st.markdown(f"""
                <div class='invoice-box'>
                    <h2>HOLIDAY COUNTRY CLUB</h2>
                    <p><b>Booking ID:</b> {b_data.get('id')}</p>
                    <p><b>Guest Name:</b> {b_data.get('name')}</p>
                    <p><b>Email:</b> {b_data.get('email', 'N/A')} | <b>Phone:</b> {b_data.get('phone')}</p>
                    <p><b>CNIC/Passport:</b> {b_data.get('cnic_passport', 'N/A')} | <b>Address:</b> {b_data.get('address', 'N/A')}</p>
                    <p><b>Cottage:</b> {b_data.get('unit')} ({b_data.get('checkin')} to {b_data.get('checkout')})</p>
                    <p><b>Special Requests:</b> {b_data.get('special_requests', 'None')}</p>
                    <hr>
                    <h3>Total Rent: Rs. {rent:,}</h3>
                </div>
                """, unsafe_allow_html=True)

# 6. ACCOUNTS & EXPENSES TAB
if role in MANAGEMENT_ACCESS or role == "Auditor":
    with get_tab("💰 Accounts & Expenses"):
        st.markdown("<h3 style='color: #f97316;'>💰 Expense Tracking & Financial Audits</h3>", unsafe_allow_html=True)
        if st.session_state.expenses:
            st.dataframe(pd.DataFrame(st.session_state.expenses), use_container_width=True)
        else:
            st.info("No expenses recorded yet.")

# 7. SETUP & ADMIN CONTROLS TAB
if role in FULL_ACCESS:
    with get_tab("⚙️ Setup & Admin Controls"):
        st.markdown("<h3 style='color: #f97316;'>⚙️ Resort Setup & Inventory Management</h3>", unsafe_allow_html=True)
        st.write(f"Current Cottages in Inventory: {len(st.session_state.units)}")

# --- FOOTER ---
st.markdown("""
<div class='decent-footer'>
    <div style='margin-bottom: 5px;'>
        © 2026 <strong>Holiday Country Club | Executive Portal</strong>. All Rights Reserved.
    </div>
    <div style='font-size: 12px; color: #64748b;'>
        Designed, Engineered & Maintained with Precision by <span class='dev-name'>M. Arif Aziz</span>
    </div>
</div>
""", unsafe_allow_html=True)
