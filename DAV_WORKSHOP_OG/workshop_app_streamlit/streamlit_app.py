import streamlit as st
import psycopg2  # Updated from sqlite3
import pandas as pd
import qrcode
import io
from PIL import Image
import re
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import altair as alt
from fpdf import FPDF
import uuid # This was already in your code, but moved it to top for best practice
#import streamlit as st

# Function to set background
def set_background(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Call function here
set_background("bj.jpg")

# Rest of your Streamlit code
#st.title("My App")


def send_email(to_address, subject, message_body):
    sender_email = "konchadachatresh.23.csd@anits.edu.in"
    app_password = "idoo pzkz gdjr mkhj"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_address
    msg["Subject"] = subject

    msg.attach(MIMEText(message_body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Email failed:", e)


def send_email_with_pdf(to_address, subject, message_body, pdf_bytes, filename):
    sender_email = "konchadachatresh.23.csd@anits.edu.in"  # replace with your Gmail
    app_password = "idoo pzkz gdjr mkhj"  # 16-char app password

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_address
    msg["Subject"] = subject

    # Add text
    msg.attach(MIMEText(message_body, "plain"))

    # Attach PDF
    part = MIMEApplication(pdf_bytes.read(), Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.send_message(msg)
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Email failed:", e)
        
def generate_team_qr(data: str):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
    
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_team_pdf(team_data, username):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Workshop Team Details", ln=True, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, txt=clean_text(f"Username (Email): {username}"), ln=True)
    pdf.cell(200, 10, txt=clean_text(f"Team Size: {team_data['team_size']}"), ln=True)
    pdf.ln(5)

    for i, member in enumerate(team_data["members"], start=1):
        title = "Team Leader" if i == 1 else f"Member {i}"
        pdf.set_font("Arial", "B", size=12)
        pdf.cell(200, 10, txt=clean_text(title), ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 8, txt=clean_text(f"Name: {member['name']}"), ln=True)
        pdf.cell(200, 8, txt=clean_text(f"Reg No: {member['reg']}"), ln=True)
        pdf.cell(200, 8, txt=clean_text(f"Year: {member['year']}"), ln=True)
        pdf.cell(200, 8, txt=clean_text(f"Branch: {member['branch']}"), ln=True)
        pdf.cell(200, 8, txt=clean_text(f"Section: {member['section']}"), ln=True)
        pdf.ln(4)

    pdf_output = pdf.output(dest="S").encode("latin1")
    return io.BytesIO(pdf_output)


st.set_page_config(page_title="Workshop Portal", layout="centered")
# Track whether to show Register or Login
if "form_view" not in st.session_state:
    st.session_state.form_view = None

def show_register():
    st.session_state.form_view = "register"

def show_login():
    st.session_state.form_view = "login"


# Initialize DB
def init_db():
    try:
        conn = psycopg2.connect(
            host=st.secrets["db_host"],
            database=st.secrets["db_name"],
            user=st.secrets["db_username"],
            password=st.secrets["db_password"],
            port=5432,
            sslmode="require",
            sslrootcert="prod-ca-2021.crt",
            options="-c pool_mode=session"
        )
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS teams (
            username TEXT,
            team_size TEXT,
            name1 TEXT, reg1 TEXT, year1 TEXT, branch1 TEXT, section1 TEXT,
            name2 TEXT, reg2 TEXT, year2 TEXT, branch2 TEXT, section2 TEXT,
            name3 TEXT, reg3 TEXT, year3 TEXT, branch3 TEXT, section3 TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS transactions (
            username TEXT,
            amount INTEGER,
            txn_id TEXT PRIMARY KEY, 
            screenshot BYTEA
        )""")
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None
        
conn = init_db()

# Email validation function
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


# Safe rerun function
def safe_rerun():
    try:
        st.rerun()
    except RuntimeError as e:
        if "Session state" not in str(e):
            raise


# Session state
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "clear_team_form" not in st.session_state:
    st.session_state.clear_team_form = False
if "txn_success" not in st.session_state:
    st.session_state.txn_success = False
if "logout_triggered" not in st.session_state:
    st.session_state.logout_triggered = False


def get_sidebar_choice():
    if st.session_state.user_logged_in:
        c = conn.cursor()
        c.execute("SELECT name1, reg1, year1 FROM teams WHERE username=%s", (st.session_state.username,))
        row = c.fetchone()
        has_team = row and all(row)
        if has_team:
            menu = ["Team Selection", "Transaction", "Logout"]
        else:
            menu = ["Team Selection", "Logout"]

        default_index = 0
        if "menu_redirect" in st.session_state and st.session_state.menu_redirect in menu:
            default_index = menu.index(st.session_state.menu_redirect)
        return st.sidebar.selectbox("Navigation", menu, index=default_index)

    elif st.session_state.admin_logged_in:
        menu = ["Admin", "Logout"]
        default_index = 0
        if "menu_redirect" in st.session_state and st.session_state.menu_redirect in menu:
            default_index = menu.index(st.session_state.menu_redirect)
        return st.sidebar.selectbox("Navigation", menu, index=default_index)

    return None

# Set sidebar choice globally
choice = get_sidebar_choice()

if st.session_state.logout_triggered:
    st.session_state.logout_triggered = False
    st.session_state.form_view = None
    st.rerun()

if "menu_redirect" in st.session_state:
    if st.session_state.menu_redirect != choice:
        # Set correct default in the selectbox and rerun
        st.rerun()
    del st.session_state.menu_redirect


# Homepage for non-logged-in users
if not st.session_state.user_logged_in and not st.session_state.admin_logged_in:
    st.title("👋 Welcome to EXCELERATE")

    col1, col2 = st.columns(2)
    with col1:
        st.button("📝 Register", on_click=lambda: st.session_state.update(form_view="register"))
    with col2:
        st.button("🔐 Login", on_click=lambda: st.session_state.update(form_view="login"))

    if st.session_state.form_view == "register":
        st.subheader("Register")
        with st.form("register_form"):
            username = st.text_input("Email ID (will be your username)")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Register")
            if submitted:
                if not username or not password:
                    st.error("All fields are required.")
                elif not is_valid_email(username):
                    st.error("Please enter a valid email address.")
                else:
                    c = conn.cursor()
                    c.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                    if c.fetchone():
                        st.error("This email is already registered. Please login.")
                    else:
                        try:
                            c.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                            conn.commit()
                            st.success("Registered successfully. Please login.")
                            send_email(
                                username,
                                "Workshop Registration Confirmed ✅",
                                "Thank you for registering! You've successfully created an account in the Workshop Portal."
                            )
                        except Exception as e:
                            st.error(f"Error occurred while registering: {e}")

    elif st.session_state.form_view == "login":
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Email ID")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
            if login_btn:
                if username == "admin" and password == "admin123":
                    st.session_state.admin_logged_in = True
                    st.success("Admin login successful.")
                    safe_rerun()
                else:
                    c = conn.cursor()
                    c.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
                    if c.fetchone():
                        st.session_state.user_logged_in = True
                        st.session_state.username = username
                        st.success("Logged in successfully!")
                        safe_rerun()  # 🚨 This restarts the app, so don't put anything after it.
                    else:
                        st.error("Invalid credentials.")


    if st.session_state.form_view:
        st.button("🔙 Back", on_click=lambda: st.session_state.update(form_view=None))


elif choice and choice == "Team Selection":
    if "username" in st.session_state and st.session_state.username != st.session_state.get("last_team_user"):
    # This block executes when a new user logs in
        st.session_state.pop("team_saved_successfully", None)
        st.session_state.pop("qr_details", None)
        st.session_state.pop("qr_team_size", None)
        st.session_state.pop("team_code", None)
        st.session_state.pop("clear_team_form", None)

    # Store the current username to prevent this from running on every rerun
        st.session_state.last_team_user = st.session_state.username
        st.rerun()
    
    st.title("Team Selection")
    team_size = st.radio("Select Team Size", ["Single (₹50)", "Duo (₹80)", "Trio (₹100)"])
    size_map = {"Single (₹50)": 1, "Duo (₹80)": 2, "Trio (₹100)": 3}
    size = size_map[team_size]

    if st.session_state.clear_team_form:
        for i in range(1, 4):
            for field in ["name", "reg", "year", "branch", "section"]:
                st.session_state.pop(f"{field}_{i}", None)
        st.session_state.clear_team_form = False
        safe_rerun()

    with st.form("team_form"):
        details = []
        for i in range(1, size + 1):
            with st.expander(f"👥 Member {i} Details", expanded=True):
                name = st.text_input(f"👤 Name", key=f"name_{i}")
                reg = st.text_input("🆔 Reg Number", key=f"reg_{i}")
                year = st.selectbox("🎓 Year", ["", "2", "3", "4"], key=f"year_{i}")
                branch = st.selectbox("🏫 Branch", ["", "CSD", "CSM", "CSE", "IT"], key=f"branch_{i}")
                section = st.selectbox("🔤 Section", ["", "A", "B", "C", "D"], key=f"section_{i}")

                details.extend([name, reg, year, branch, section])


        col1, col2 = st.columns(2)
        with col1:
            submit_team = st.form_submit_button("Submit Team")
        with col2:
            clear_btn = st.form_submit_button("Clear")

        if clear_btn:
            st.session_state.clear_team_form = True

        if submit_team:
            if not details[0].strip() or not details[1].strip() or not details[2].strip():
                st.error("❌ Please fill at least the first member's Name, Reg Number, and Year.")
            else:
                c = conn.cursor()
                c.execute("DELETE FROM teams WHERE username=%s", (st.session_state.username,))
                placeholders = ",".join(["%s"] * 17) # Updated placeholder
                c.execute(f"INSERT INTO teams VALUES ({placeholders})",
                          (st.session_state.username, team_size, *details, *[""] * (15 - len(details))))
                conn.commit()

                team_code = f"DAVTEAM-{uuid.uuid4().hex[:8].upper()}"
                st.session_state.team_code = team_code
                st.session_state.qr_details = details
                st.session_state.qr_team_size = size
                st.session_state.team_saved_successfully = True

                # ✅ Clear form inputs after submission
                for i in range(1, size + 1):
                    for field in ["name", "reg", "year", "branch", "section"]:
                        st.session_state.pop(f"{field}_{i}", None)

                safe_rerun()


    # ✅ After rerun, show QR and transaction link
    if (
        st.session_state.get("team_saved_successfully")
        and "qr_details" in st.session_state
        and "qr_team_size" in st.session_state
        and "team_code" in st.session_state
    ):
        details = st.session_state.qr_details
        size = st.session_state.qr_team_size
        team_code = st.session_state.team_code

        team_info = f"Team Code: {team_code}\n"
        team_info += f"Team Leader: {details[0]} ({details[1]})\n"
        for i in range(1, size):
            team_info += f"Member {i+1}: {details[i*5]} ({details[i*5+1]})\n"

        qr_bytes = generate_team_qr(team_info)

        st.success("✅ Team saved successfully!")
        st.image(qr_bytes, caption="Your Team QR Code", width=250)
        st.download_button("📥 Download QR Code", data=qr_bytes, file_name="team_qr.png")
        st.text_area("Team Code Info", team_info, height=120)

        st.info("✅ Team saved successfully. Now proceed to the **Transaction** page from the sidebar.")
        st.markdown("👉 Use the **Navigation** panel on the left to open the Transaction page.")


# Transaction
elif choice == "Transaction":
    st.title("Transaction")

    if "txn_success" not in st.session_state:
        st.session_state.txn_success = False

    team_cost = {"Single (₹50)": 50, "Duo (₹80)": 80, "Trio (₹100)": 100}
    qr_map = {
        "Single (₹50)": "DAV_WORKSHOP_OG/workshop_app_streamlit/qr-code.png",
        "Duo (₹80)": "DAV_WORKSHOP_OG/workshop_app_streamlit/qr-code (1).png",
        "Trio (₹100)": "DAV_WORKSHOP_OG/workshop_app_streamlit/qr-code (2).png"
    }

    c = conn.cursor()
    c.execute("SELECT team_size FROM teams WHERE username=%s", (st.session_state.username,))
    row = c.fetchone()

    if row:
        team_size = row[0]
        price = team_cost.get(team_size)
        qr_file = qr_map.get(team_size)
        st.write(f"Team Size: {team_size}")
        st.write(f"💰 Amount to be paid: ₹{price}")

        try:
            with open(qr_file, "rb") as f:
                st.image(f.read(), caption=f"Scan to Pay for {team_size}", width=250)
        except FileNotFoundError:
            st.error(f"QR code image not found: {qr_file}")

        with st.form("txn_form"):
            txn_id = st.text_input("Enter Transaction ID")
            valid_txn = bool(re.match(r"^T\d{22}$", txn_id)) if txn_id else False
            screenshot = st.file_uploader("Upload Payment Screenshot", type=["png", "jpg", "jpeg"])
            submit_txn = st.form_submit_button("Submit")

            if submit_txn:
                if not valid_txn:
                    st.error("❌ Invalid Transaction ID format.")
                elif not screenshot:
                    st.error("❌ Please upload the transaction screenshot.")
                else:
                    # ✅ Check if the transaction ID already exists in the database
                    c.execute("SELECT txn_id FROM transactions WHERE txn_id = %s", (txn_id,))
                    existing_txn = c.fetchone()

                    if existing_txn:
                        st.error("❌ Transaction ID already exists. Please check your entry.")
                    else:
                        # ✅ Insert the new transaction if ID is unique
                        image_bytes = screenshot.read()
                        c.execute(
                            """
                            INSERT INTO transactions (username, amount, txn_id, screenshot)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (st.session_state.username, price, txn_id, psycopg2.Binary(image_bytes))
                        )

                        conn.commit()
                        st.session_state.last_txn_id = txn_id
                        st.session_state.last_price = price
                        st.session_state.txn_success = True
                        st.success("✅ Transaction submitted successfully.")
                        safe_rerun()
    else:
        st.warning("⚠️ Please fill out team details first on the 'Team Selection' page.")

    # ✅ After rerun - show WhatsApp join link and confirmation
    if st.session_state.txn_success:
        st.success("Transaction recorded successfully!")

        # ✅ Fetch team details from DB
        c.execute("SELECT * FROM teams WHERE username=%s", (st.session_state.username,))
        team_row = c.fetchone()
        if team_row:
            team_size = team_row[1]
            members = []
            for i in range(1, 4):
                name = team_row[2 + (i - 1) * 5]
                reg = team_row[3 + (i - 1) * 5]
                year = team_row[4 + (i - 1) * 5]
                branch = team_row[5 + (i - 1) * 5]
                section = team_row[6 + (i - 1) * 5]
                if name and reg:
                    members.append({
                        "name": name,
                        "reg": reg,
                        "year": year,
                        "branch": branch,
                        "section": section
                    })

            team_data = {"team_size": team_size, "members": members}
            pdf_bytes = generate_team_pdf(team_data, st.session_state.username)

            # ✅ Send email with PDF
            try:
                send_email_with_pdf(
                    to_address=st.session_state.username,
                    subject="Workshop Payment Received 💰",
                    message_body=(
                        f"Hi,\n\nYour payment of ₹{st.session_state.last_price} was received successfully. "
                        f"Your transaction ID is: {st.session_state.last_txn_id}.\n\n"
                        f"Attached is your team confirmation.\n\nThanks for registering!"
                    ),
                    pdf_bytes=pdf_bytes,
                    filename="team_info.pdf"
                )
                st.success("📧 Confirmation email with team PDF sent.")
            except Exception as e:
                st.warning(f"📧 Email failed to send: {e}")

            # ✅ Show WhatsApp join button
            st.markdown(
                """
                <a href="https://chat.whatsapp.com/CGE0UiKKPeu63xzZqs8sMW" target="_blank"
                    style="display: inline-flex; align-items: center; padding: 10px 20px;
                            background-color: #25D366; color: black; border-radius: 6px;
                            text-decoration: none; font-weight: bold;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg"
                            alt="WhatsApp" width="24" style="margin-right: 10px;">
                    Join WhatsApp Group
                </a>
                """,
                unsafe_allow_html=True
            )

            st.session_state.txn_success = False


    else:
        st.warning("⚠️ Please fill out team details first on the 'Team Selection' page.")

# Admin Panel
elif choice == "Admin" and st.session_state.admin_logged_in:
    st.title("Admin Panel")
    st.subheader("Download Registration Details")
    reg_df = pd.read_sql_query("SELECT * FROM teams", conn)

    # 💰 Total Revenue Generated (All Registrations)
    total_df = reg_df.copy()
    team_price_map = {
        "Single (₹50)": 50,
        "Duo (₹80)": 80,
        "Trio (₹100)": 100
    }
    total_revenue = sum(team_price_map.get(ts, 0) for ts in total_df["team_size"])

    st.markdown("""
    <div style='
        padding: 1rem;
        background-color: #262730;
        border-left: 5px solid #00C851;
        border-radius: 8px;
        font-size: 18px;
        color: white;
        margin-bottom: 1.5rem;
    '>
        🧾 <strong>Total Revenue Generated:</strong> ₹{:,}
    </div>
    """.format(total_revenue), unsafe_allow_html=True)


    st.subheader("🔍 Filter Registrations")
    year_filter = st.selectbox("Filter by Year", options=["All", "2", "3", "4"])
    branch_filter = st.selectbox("Filter by Branch", options=["All", "CSD", "CSE", "CSM", "IT"])
    section_filter = st.selectbox("Filter by Section", options=["All", "A", "B", "C", "D"])
    team_size_filter = st.selectbox("Filter by Team Size", options=["All", "Single (₹50)", "Duo (₹80)", "Trio (₹100)"])

    filtered_df = reg_df.copy()

    if year_filter != "All":
        filtered_df = filtered_df[
            (filtered_df["year1"] == year_filter) |
            (filtered_df["year2"] == year_filter) |
            (filtered_df["year3"] == year_filter)
        ]

    if branch_filter != "All":
        filtered_df = filtered_df[
            (filtered_df["branch1"] == branch_filter) |
            (filtered_df["branch2"] == branch_filter) |
            (filtered_df["branch3"] == branch_filter)
        ]

    if section_filter != "All":
        filtered_df = filtered_df[
            (filtered_df["section1"] == section_filter) |
            (filtered_df["section2"] == section_filter) |
            (filtered_df["section3"] == section_filter)
        ]

    if team_size_filter != "All":
        filtered_df = filtered_df[filtered_df["team_size"] == team_size_filter]

    st.dataframe(filtered_df)

    # ✅ Summary Stats
    st.subheader("📊 Summary Stats")

    total_filtered_teams = len(filtered_df)
    team_price_map = {
        "Single (₹50)": 50,
        "Duo (₹80)": 80,
        "Trio (₹100)": 100
    }
    total_filtered_revenue = sum(team_price_map.get(ts, 0) for ts in filtered_df["team_size"])
    team_size_counts = filtered_df["team_size"].value_counts()

    st.markdown(f"- Total Filtered Teams: **{total_filtered_teams}**")
    st.markdown(f"- Revenue from Filtered Teams: **₹{total_filtered_revenue}**")
    for team_label, count in team_size_counts.items():
        st.markdown(f"- {team_label}: {count} teams")

    # ✅ Branch-wise chart from filtered data
    st.subheader("📈 Branch-wise Registration Chart")
    chart_df = filtered_df["branch1"].value_counts().reset_index()
    chart_df.columns = ["Branch", "Count"]

    chart = alt.Chart(chart_df).mark_bar().encode(
    x=alt.X("Branch:N", sort='-y', axis=alt.Axis(labelColor='white', titleColor='white')),
    y=alt.Y("Count:Q", axis=alt.Axis(labelColor='white', titleColor='white')),
    tooltip=["Branch:N", "Count:Q"]
).properties(
    title=alt.TitleParams(text="Branch-wise Registration Chart", color='white', fontSize=18),
    width=600,
    height=400,
    background='#0E1117'  # Ensures chart has dark bg
).configure_view(
    strokeWidth=0
).configure_axis(
    grid=False
).configure_title(
    fontSize=18,
    anchor='start',
    color='white'
)

    st.altair_chart(chart, use_container_width=True)

    # ✅ Full Data Download
    st.subheader("📁 Download Full Data")
    st.dataframe(reg_df)
    st.download_button("Download Registration CSV", reg_df.to_csv(index=False), "registrations.csv", "text/csv")

    st.subheader("Download Transaction Details")
    txn_df = pd.read_sql_query("SELECT username, amount, txn_id FROM transactions", conn)
    st.dataframe(txn_df)
    st.download_button("Download Transaction CSV", txn_df.to_csv(index=False), "transactions.csv", "text/csv")

    # ✅ Screenshot Preview
    st.subheader("🖼️ Preview Uploaded Screenshots and Amounts")
    c = conn.cursor()
    c.execute("SELECT username, amount, txn_id, screenshot FROM transactions")
    txn_rows = c.fetchall()

    for idx, (username, amount, txn_id, screenshot_blob) in enumerate(txn_rows):
        st.markdown(f"**👤 Username:** `{username}`  \n**💸 Amount Paid:** ₹{amount}  \n**🔖 Transaction ID:** `{txn_id}`")

        if screenshot_blob:
            b64 = base64.b64encode(screenshot_blob).decode()
            file_ext = "png"
            img_html = f'''
            <style>
            .tooltip-container {{
                position: relative;
                display: inline-block;
            }}
            .tooltip-container .tooltip-img {{
                visibility: hidden;
                width: 200px;
                background-color: transparent;
                text-align: center;
                border-radius: 6px;
                position: absolute;
                z-index: 1;
                bottom: 125%; 
                left: 50%;
                margin-left: -100px;
            }}
            .tooltip-container:hover .tooltip-img {{
                visibility: visible;
            }}
            </style>
            <div class="tooltip-container">
                <span style="font-size: 22px; cursor: pointer;">👁️</span>
                <div class="tooltip-img">
                    <img src="data:image/{file_ext};base64,{b64}" width="200"/>
                </div>
            </div>
            '''
            st.markdown(img_html, unsafe_allow_html=True)
        else:
            st.info("No screenshot uploaded.")
        st.markdown("---")

    # ✅ Wipe Data Section
    st.subheader("💨 Danger Zone: Wipe All Data")
    with st.form("wipe_form"):
        admin_pwd = st.text_input("Enter Admin Password to Confirm", type="password")
        confirm_wipe = st.form_submit_button("Wipe All Data")
        if confirm_wipe:
            if admin_pwd == "admin6677":
                c.execute("DELETE FROM users")
                c.execute("DELETE FROM teams")
                c.execute("DELETE FROM transactions")
                conn.commit()
                st.success("✅ All data wiped successfully from the database.")
                safe_rerun()
            else:
                st.error("❌ Incorrect password. Wipe operation aborted.")

    # ✅ Send Feedback Form
    st.subheader("📩 Send Feedback Form to All Participants")

    with st.form("feedback_form"):
        feedback_pwd = st.text_input("Enter Admin Password", type="password")
        send_form = st.form_submit_button("Send Feedback Form")

        if send_form:
            if feedback_pwd == "admin6677":
                feedback_link = "https://forms.gle/XUemm3T2YQQBMDhN9"  # ✅ Your actual Google Form link

                c.execute("SELECT username FROM users")
                users = c.fetchall()

                sent_count = 0
                for (email,) in users:
                    try:
                        send_email(
                            to_address=email,
                            subject="📋 We value your feedback!",
                            message_body=(
                                "Thank you for participating in our workshop! We'd love your feedback.\n\n"
                                f"Please take a moment to fill out this form: {feedback_link}\n\n"
                                "Your feedback helps us improve future events. 😊"
                            )
                        )
                        sent_count += 1
                    except Exception as e:
                        st.warning(f"❌ Failed to send to {email}: {e}")

                st.success(f"✅ Feedback form sent to {sent_count} participants.")
            else:
                st.error("❌ Incorrect admin password.")


# Logout
elif choice == "Logout":
    st.session_state.logout_triggered = True
    for key in ["user_logged_in", "admin_logged_in", "username", "menu_redirect"]:
        st.session_state.pop(key, None)
    st.session_state.pop("team_saved_successfully", None)
    st.session_state.pop("qr_details", None)
    st.session_state.pop("qr_team_size", None)
    st.session_state.pop("team_code", None)
    st.session_state.pop("clear_team_form", None)
    st.session_state.pop("last_team_user", None)
    st.success("✅ Logged out successfully! Redirecting to home...")
    safe_rerun()












