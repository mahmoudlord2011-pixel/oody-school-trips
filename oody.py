import streamlit as st
import pandas as pd
import random
from supabase import create_client, Client

# ضبط إعدادات الصفحة
st.set_page_config(page_title="رحلات برايت فيجن - School Trips", page_icon="🚌", layout="wide")

# ---------------------------------------------------------
# 🌍 إعدادات اللغة (عربي / إنجليزي)
# ---------------------------------------------------------
st.sidebar.write("---")
st.sidebar.subheader("🌍 Language / اللغة")
lang_choice = st.sidebar.selectbox("اختر اللغة / Select Language:", ["العربية 🇸🇦", "English 🇺🇸"])

if lang_choice == "English 🇺🇸":
    TXT_LOGIN_TITLE = "🚌 Bright Vision Trips Platform - Login"
    TXT_USER = "Username:"
    TXT_PASS = "Password:"
    TXT_LOGIN_BTN = "🔑 Login 🚀"
    TXT_DEMO_BTN = "🚀 Guest Demo Login"
    TXT_LOGOUT = "Logout 🚪"
    TXT_CLEAR_CACHE = "🗑️ Clear Cache & Reload"
    TXT_PAGE1 = "🏠 School Trips & Suggest"
    TXT_PAGE2 = "🔔 Track Trip Suggestion"
    TXT_PAGE3 = "🏆 Approved Trips History"
    TXT_PAGE4 = "👨‍💼 Admin Dashboard"
    TXT_PAGE_MASTER = "⚡ Kill Switch Control Panel"
else:
    TXT_LOGIN_TITLE = "🚌 تسجيل الدخول إلى منصة اقتراحات رحلات المدرسة"
    TXT_USER = "اسم المستخدم (Username):"
    TXT_PASS = "كلمة السر (Password):"
    TXT_LOGIN_BTN = "تسجيل الدخول 🚀"
    TXT_DEMO_BTN = "🚀 تسجيل الدخول إلى نظام الديمو التجريبي"
    TXT_LOGOUT = "🚪 تسجيل الخروج"
    TXT_CLEAR_CACHE = "🗑️ تفريغ كاش الجلسة (إعادة تحميل)"
    TXT_PAGE1 = "🏠 رحلات المدرسة واقتراح رحلة"
    TXT_PAGE2 = "🔔 متابعة اقتراح برقم الرحلة"
    TXT_PAGE3 = "🏆 سجل الرحلات والفعاليات"
    TXT_PAGE4 = "👨‍💼 لوحة تحكم المدير للرحلات (Dashboard)"
    TXT_PAGE_MASTER = "⚡ Kill Switch Control Panel"

# ---------------------------------------------------------
# الاتصال بـ Supabase من خلال Secrets
# ---------------------------------------------------------
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# 🛡️ فلتر الألفاظ الممنوعة والنصوص المسيئة
# ---------------------------------------------------------
FORBIDDEN_WORDS = [
    "شتيمة", "احمق", "غبي", "كلب", "حمار", "زفت"
]

def contains_bad_words(text: str) -> bool:
    """فحص إذا كان النص يحتوي على أي كلمة غير لائقة"""
    text_lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

# ---------------------------------------------------------
# إدارة الجلسة والتصفير للديمو (Session State)
# ---------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None

# بيانات الديمو التجريبية لرحلات المدرسة
if "demo_trips" not in st.session_state:
    st.session_state.demo_trips = pd.DataFrame([
        {
            "trip_id": "TRP-1001", "title": "رحلة إلى الأهرامات والمتحف المصري الكبير 🏛️", 
            "description": "رحلة استكشافية تاريخية لمعالم مصر العظيمة", "destination": "الجيزة", 
            "budget": "200 ج.م", "student_name": "زائر تجريبي", 
            "upvotes": 12, "status": "New", "admin_reply": "تم إدراجها ضمن رحلات الفصل الدراسي الأول!"
        }
    ])

# ---------------------------------------------------------
# وظائف قراءة وتحديث قاعدة البيانات (مع التمييز للديمو)
# ---------------------------------------------------------
def is_guest_demo():
    return st.session_state.get("user_role") == "guest"

def load_data(include_pending: bool = False):
    """جلب اقتراحات الرحلات من السحابة أو من ذاكرة الديمو"""
    if is_guest_demo():
        df = st.session_state.demo_trips
        if not include_pending and not df.empty and "status" in df.columns:
            return df[df["status"] != "Pending"]
        return df

    if not supabase:
        return pd.DataFrame(columns=[
            "trip_id", "title", "description", "destination", 
            "budget", "student_name", "upvotes", "status", "admin_reply"
        ])

    try:
        if include_pending:
            response = supabase.table("school_trips").select("*").execute()
        else:
            response = supabase.table("school_trips").select("*").neq("status", "Pending").execute()
        data = response.data
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass

    return pd.DataFrame(columns=[
        "trip_id", "title", "description", "destination", 
        "budget", "student_name", "upvotes", "status", "admin_reply"
    ])

def is_system_locked():
    if is_guest_demo():
        return False
    if not supabase:
        return False
    try:
        response = supabase.table("system_config").select("kill_switch").eq("id", 1).execute()
        if response.data:
            return response.data[0]["kill_switch"]
    except Exception:
        pass
    return False

def set_system_lock(status: bool):
    if not is_guest_demo() and supabase:
        try:
            supabase.table("system_config").update({"kill_switch": status}).eq("id", 1).execute()
        except Exception:
            pass

def reset_database():
    if is_guest_demo():
        st.session_state.demo_trips = pd.DataFrame(columns=[
            "trip_id", "title", "description", "destination", 
            "budget", "student_name", "upvotes", "status", "admin_reply"
        ])
    elif supabase:
        try:
            supabase.table("school_trips").delete().neq("trip_id", "NONE").execute()
        except Exception:
            pass

# 🛑 فحص Kill Switch الشامل
if is_system_locked():
    if st.session_state.user_role != "master":
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.username = None
        
        st.error("⛔ النظام متوقف حالياً للصيانة أو بواسطة الإدارة العليا (Kill Switch Active).")
        st.info("لا يمكن لأي طالب أو مدير الوصول للنظام في الوقت الحالي.")
        st.write("---")
        
        with st.expander("👑 تسجيل دخول المالك الأعظم (Master Oody) للتحكم"):
            master_user = st.text_input("Master Username:")
            master_pass = st.text_input("Master Password:", type="password")
            if st.button("فك الحظر وتشغيل النظام 🔓"):
                if master_user == "oody" and master_pass == "Mahmoud@2011":
                    set_system_lock(False)
                    st.session_state.logged_in = True
                    st.session_state.user_role = "master"
                    st.session_state.username = "Master Oody 👑"
                    st.success("تم إيقاف الـ Kill Switch وبدء تشغيل النظام!")
                    st.rerun()
                else:
                    st.error("بيانات الماستر غير صحيحة!")
        st.stop()

# ---------------------------------------------------------
# شاشة تسجيل الدخول
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown(f"<h2 style='text-align: center; color: #1E88E5;'>{TXT_LOGIN_TITLE}</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input(TXT_USER)
        password = st.text_input(TXT_PASS, type="password")
        
        login_btn = st.button(TXT_LOGIN_BTN, type="primary", use_container_width=True)
        demo_btn = st.button(TXT_DEMO_BTN, use_container_width=True)

        if login_btn:
            if username == "student" and password == "student123":
                st.session_state.logged_in = True
                st.session_state.user_role = "student"
                st.session_state.username = "طالب / ولي أمر"
                st.rerun()
            elif username == "admin" and password == "Dr.RagabBV842":
                st.session_state.logged_in = True
                st.session_state.user_role = "admin"
                st.session_state.username = "المدير (Dr. Ragab)"
                st.rerun()
            elif username == "oody" and password == "Mahmoud@2011":
                st.session_state.logged_in = True
                st.session_state.user_role = "master"
                st.session_state.username = "Master Oody 👑"
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة!")
                
        if demo_btn:
            st.session_state.logged_in = True
            st.session_state.user_role = "guest"
            st.session_state.username = "زائر الديمو التجريبي 🎓"
            st.rerun()

    st.stop()

# ---------------------------------------------------------
# القائمة الجانبية
# ---------------------------------------------------------
st.sidebar.title(f"👤 {st.session_state.username}")
st.sidebar.caption(f"الصلاحية: `{st.session_state.user_role.upper()}`")

if st.sidebar.button(TXT_LOGOUT, use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()

st.sidebar.write("---")

if st.sidebar.button(TXT_CLEAR_CACHE, use_container_width=True):
    st.cache_resource.clear()
    st.rerun()

if st.session_state.user_role == "student":
    available_pages = [TXT_PAGE1, TXT_PAGE2, TXT_PAGE3]
elif st.session_state.user_role == "admin":
    available_pages = [TXT_PAGE4, TXT_PAGE3]
elif st.session_state.user_role == "guest":
    available_pages = [TXT_PAGE1, TXT_PAGE2, TXT_PAGE4, TXT_PAGE3]
elif st.session_state.user_role == "master":
    available_pages = [TXT_PAGE_MASTER]

page = st.sidebar.radio("اختر الصفحة / Select Page:", available_pages)

# ---------------------------------------------------------
# الصفحات
# ---------------------------------------------------------
if page == TXT_PAGE1:
    st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🚌 اقترح رحلة أحلامك لمدرسَتِك</h1>", unsafe_allow_html=True)
    st.write("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 اقترح وجهة رحلة مدرسية جديدة")
        with st.form("trip_form", clear_on_submit=True):
            title = st.text_input("اسم أو عنوان الرحلة (مثال: رحلة دريم پارك) *")
            description = st.text_area("تفاصيل الأنشطة والبرنامج المقترح للرحلة *")
            destination = st.text_input("مكان أو مدينة الوجهة 📍")
            budget = st.text_input("التكلفة التقديرية المقترحة لكل طالب (مثال: 150 ج.م)")
            anonymous = st.checkbox("🕶️ إخفاء الاسم")
            student_name = "مجهول" if anonymous else st.text_input("اسمك (اختياري)", value="طالب/ولي أمر")

            submitted = st.form_submit_button("إرسال الاقتراح 🚀")

            if submitted:
                if not title or not description:
                    st.error("يرجى ملء اسم الرحلة والتفاصيل!")
                elif contains_bad_words(title) or contains_bad_words(description):
                    st.error("⚠️ عفواً، يحتوي الاقتراح على ألفاظ غير لائقة. يرجى تعديل الصياغة.")
                else:
                    trip_id = f"TRP-{random.randint(1000, 9999)}"
                    new_trip = {
                        "trip_id": trip_id,
                        "title": title,
                        "description": description,
                        "destination": destination,
                        "budget": budget if budget else "غير محدد",
                        "student_name": student_name,
                        "upvotes": 1,
                        "status": "Pending",
                        "admin_reply": ""
                    }
                    if is_guest_demo():
                        st.session_state.demo_trips = pd.concat([st.session_state.demo_trips, pd.DataFrame([new_trip])], ignore_index=True)
                    elif supabase:
                        supabase.table("school_trips").insert(new_trip).execute()

                    st.success(f"تم إرسال اقتراح الرحلة بنجاح! 🎉 رقم المتابعة: **{trip_id}**")
                    st.info("💡 ملاحظة: سيظهر الاقتراح للجميع بعد مراجعة الإدارة واعتدامه.")

    with col2:
        st.subheader("🔥 الرحلات الأكثر تصويتاً ودعماً")
        df = load_data(include_pending=False)
        if not df.empty:
            sorted_df = df.sort_values(by="upvotes", ascending=False)
            for idx, row in sorted_df.head(5).iterrows():
                with st.container():
                    st.markdown(f"**{row['title']}**")
                    st.caption(f"📍 الوجهة: {row['destination']} | 💰 التكلفة: {row.get('budget', 'غير محدد')}")
                    c1, c2 = st.columns([1, 1])
                    c1.write(f"🔥 {row['upvotes']} صوت")
                    if c2.button("تصويت 👍", key=f"upvote_{row['trip_id']}"):
                        if is_guest_demo():
                            st.session_state.demo_trips.loc[st.session_state.demo_trips['trip_id'] == row['trip_id'], 'upvotes'] += 1
                        elif supabase:
                            supabase.table("school_trips").update({"upvotes": int(row['upvotes']) + 1}).eq("trip_id", row['trip_id']).execute()
                        st.rerun()
                    st.divider()
        else:
            st.info("لا توجد رحلات مقترحة معتمدة حالياً.")

elif page == TXT_PAGE2:
    st.title("🔔 متابعة حالة اقتراح الرحلة")
    search_id = st.text_input("أدخل رقم متابعة الرحلة (مثال: TRP-1001):")

    if search_id:
        df = load_data(include_pending=True)
        if not df.empty:
            trip = df[df['trip_id'].astype(str).str.upper() == search_id.strip().upper()]
            if not trip.empty:
                row = trip.iloc[0]
                st.subheader(f"📌 الرحلة: {row['title']}")
                st.write(f"**البرنامج والتفاصيل:** {row['description']}")
                st.write(f"**الوجهة:** {row['destination']} | **التكلفة:** {row.get('budget', 'غير محدد')}")
                
                status = row['status']
                st.markdown("### 📊 حالة الرحلة:")
                if status == "Pending":
                    st.warning("⏳ المقترح حالياً قيد المراجعة بواسطة إدارة المدرسة.")
                else:
                    s1 = "✅" if status in ["New", "Reviewing", "Organizing", "Approved"] else "⚪"
                    s2 = "👀" if status in ["Reviewing", "Organizing", "Approved"] else "⚪"
                    s3 = "🚍" if status in ["Organizing", "Approved"] else "⚪"
                    s4 = "🎉" if status == "Approved" else "⚪"

                    st.write(f"{s1} **تم الاستلام** -> {s2} **دراسة المقترح** -> {s3} **جاري التنظيم والتجهيز** -> {s4} **معتمدة للرحلة!**")

                if pd.notna(row['admin_reply']) and str(row['admin_reply']).strip() != "":
                    st.info(f"💬 **رد إدارة المدرسة:** {row['admin_reply']}")
            else:
                st.error("رقم المتابعة غير موجود!")
        else:
            st.error("لا توجد مقترحات مسجلة حالياً.")

elif page == TXT_PAGE3:
    st.title("🏆 سجل ورحلات برايت فيجن المعتمدة")
    df = load_data(include_pending=False)
    approved_count = len(df[df['status'] == 'Approved']) if not df.empty and 'status' in df.columns else 0
    total_votes = int(df['upvotes'].sum()) if not df.empty and 'upvotes' in df.columns else 0
    
    st.markdown("### 🎉 إحصائيات نشاط الرحلات:")
    m1, m2, m3 = st.columns(3)
    m1.metric("رحلات تمت الموافقة عليها", f"{approved_count} رحلة 🚍")
    m2.metric("مقترحات قيد الدراسة", f"{len(df[df['status'] != 'Approved']) if not df.empty else 0} مقترح 💡")
    m3.metric("مجموع أصوات ودعم الطلاب", f"{total_votes} صوت 👥")

elif page == TXT_PAGE4:
    st.title("👨‍💼 لوحة تحكم المدير - تنظيم الرحلات")
    df = load_data(include_pending=True)
    
    if not df.empty:
        pending_df = df[df['status'] == 'Pending']
        if not pending_df.empty:
            st.warning(f"📩 لديك ({len(pending_df)}) مقترح رحلة جديد ينتظر المراجعة والموافقة!")
            for idx, row in pending_df.iterrows():
                with st.expander(f"🔍 مقترح: {row['title']} (من: {row['student_name']})"):
                    st.write(f"**البرنامج:** {row['description']}")
                    st.write(f"**الوجهة:** {row['destination']} | **الميزانية:** {row.get('budget', 'غير محدد')}")
                    col_acc, col_rej = st.columns(2)
                    if col_acc.button("موافقة ونشر المقترح ✅", key=f"app_{row['trip_id']}"):
                        if is_guest_demo():
                            st.session_state.demo_trips.loc[st.session_state.demo_trips['trip_id'] == row['trip_id'], 'status'] = "New"
                        elif supabase:
                            supabase.table("school_trips").update({"status": "New"}).eq("trip_id", row['trip_id']).execute()
                        st.success("تمت الموافقة بنجاح وأصبحت الرحلة ظاهرة لتصويت الطلاب!")
                        st.rerun()
                    if col_rej.button("رفض وحذف المقترح 🗑️", key=f"del_{row['trip_id']}"):
                        if is_guest_demo():
                            st.session_state.demo_trips = st.session_state.demo_trips[st.session_state.demo_trips['trip_id'] != row['trip_id']].reset_index(drop=True)
                        elif supabase:
                            supabase.table("school_trips").delete().eq("trip_id", row['trip_id']).execute()
                        st.warning("تم حذف المقترح!")
                        st.rerun()
            st.write("---")

        st.subheader("📋 قائمة المقترحات المعتمدة (مرتبة بالأعلى دعماً)")
        active_df = df[df['status'] != 'Pending'].sort_values(by="upvotes", ascending=False)
        if not active_df.empty:
            st.dataframe(active_df[["status", "upvotes", "title", "destination", "trip_id"]], use_container_width=True)

            selected_trip = st.selectbox("اختر رقم الرحلة للتعديل وتحديث الحالة:", active_df['trip_id'].tolist())
            if selected_trip:
                current_row = df[df['trip_id'] == selected_trip].iloc[0]
                status_list = ["New", "Reviewing", "Organizing", "Approved"]
                curr_status = current_row['status'] if current_row['status'] in status_list else "New"
                
                new_status = st.selectbox("تغيير حالة الرحلة:", status_list, index=status_list.index(curr_status))
                admin_reply = st.text_input("رد الإدارة للطلاب (موعد الرحلة، التعليمات):", value=str(current_row['admin_reply']) if pd.notna(current_row['admin_reply']) else "")

                if st.button("حفظ التغييرات وإشعار الطلاب 💾"):
                    if is_guest_demo():
                        st.session_state.demo_trips.loc[st.session_state.demo_trips['trip_id'] == selected_trip, 'status'] = new_status
                        st.session_state.demo_trips.loc[st.session_state.demo_trips['trip_id'] == selected_trip, 'admin_reply'] = admin_reply
                    elif supabase:
                        supabase.table("school_trips").update({"status": new_status, "admin_reply": admin_reply}).eq("trip_id", selected_trip).execute()
                    st.success("تم تحديث حالة الرحلة بنجاح!")
                    st.rerun()
        else:
            st.info("لا توجد مقترحات رحلات معتمدة حالياً.")
    else:
        st.info("لا توجد مقترحات مسجلة بالسيستم حتى الآن.")

elif page == TXT_PAGE_MASTER:
    st.title("👑 لوحة تحكم الماستر - أودي")
    is_locked = is_system_locked()

    if is_locked:
        st.error("🔴 النظام حالياً: مُغلق بالكامل (OFFLINE).")
        if st.button("🟢 تشغيل الويبسايت للجميع (Enable System)"):
            set_system_lock(False)
            st.rerun()
    else:
        st.success("🟢 النظام حالياً: يعمل بشكل طبيعي (ONLINE).")
        if st.button("🔴 تفعيل ה-Kill Switch (Shutdown System)"):
            set_system_lock(True)
            st.rerun()

    st.write("---")
    if st.button("⚠️ تصفير جميع مقترحات الرحلات والإحصائيات"):
        reset_database()
        st.success("تم تصفير الداتابيز بالكامل!")
        st.rerun()
