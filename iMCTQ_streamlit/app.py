import streamlit as st
import datetime
import pandas as pd
import numpy as np
from datetime import time, timedelta, datetime as dt

# --- Options Dictionaries (DEFINED ONCE) ---
educ_options = {
    1:'základní nebo neúplné', 2:'vyučení', 3:'střední nebo střední odborné', 
    4:'vyšší odborné', 5:'VŠ bakalářské', 6:'VŠ Mgr/Ing/MUDr/apod.', 7:'VŠ postgraduální PhD'
}
slequal_options = {
    1:'velmi dobrá', 2:'spíše dobrá', 3:'spíše špatná', 4:'velmi špatná'
}

# --- Helper Functions ---
def time_to_datetime(t, base_date):
    """Converts a datetime.time object to a datetime.datetime object on a base date."""
    if t is None:
        return None
    return dt.combine(base_date, t)

def calculate_sleep_duration(time_start, time_end):
    """Calculates sleep duration (timedelta) handling cross-midnight sleep."""
    base_date = datetime.date(2000, 1, 1)
    start_dt = time_to_datetime(time_start, base_date)
    end_dt = time_to_datetime(time_end, base_date)
    
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    
    duration = end_dt - start_dt
    return duration, end_dt

# --- Streamlit UI Setup ---

st.set_page_config(page_title="Chronotypový Kalkulátor (MCTQ)", layout="wide")
st.title("Chronotypový Kalkulátor")
st.markdown("Na základě upraveného dotazníku **MCTQ (Munich ChronoType Questionnaire)**.")

# Use a form to group all inputs
with st.form("mctq_form"):
    
    st.header("1. Základní informace")
    
    # --- Personal Info ---
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Věk:", min_value=10, max_value=100, value=30, step=1)
    with col2:
        sex = st.selectbox("Pohlaví:", options=['žena (f)', 'muž (m)', 'jiné (o)'])
    with col3:
        height = st.number_input("Výška v cm:", min_value=100, max_value=250, value=170, step=1)
        
    col4, col5, col6 = st.columns(3)
    with col4:
        weight = st.number_input("Váha v kg:", min_value=30, max_value=300, value=70, step=1)
    with col5:
        postal = st.text_input("PSČ bydliště (např. 14800):", value="10000")
    with col6:
        # **FIXED 'str' object error:** Using list() and a unique variable name
        educ_choice = st.selectbox("Dosažené vzdělání:", 
                            options=list(educ_options.keys()),
                            format_func=lambda x: f"{x} - {educ_options[x]}",
                            index=2, key='educ_select')

    st.header("2. Pracovní/Volné Dny")
    
    WD = st.number_input("Kolik dní v týdnu (0 až 7) máte pravidelný pracovní rozvrh?", 
                         min_value=0, max_value=8, value=5, step=1, key='WD_input')
    FD = 7 - WD
    
    # --- Initialize ALL conditional variables to safe defaults (avoids NameError) ---
    BTw, SPrepw, SLatwi, SEw, Alarmw, BAlarmw, SIw = None, None, 15, None, 0, 0, 5
    LEw = 0.0
    BTf, SPrepf, SLatfi, SEf, Alarmf, BAlarmf, SIf = None, None, 15, None, 0, 0, 10
    LEf = 0.0
    
    # --- Working Days (VŠEDNÍ DNY) Block ---
    if WD > 0 and WD < 8:
        st.subheader("2.1. Režim během **VŠEDNÍCH** dnů ({} dní)".format(WD))
        
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            BTw = st.time_input("V kolik hodin si chodíte obvykle lehnout do postele?", time(23, 0), key='BTw')
        with col_w2:
            SPrepw = st.time_input("V kolik hodin se obvykle připravujete ke spánku (zhasnete světlo)?", time(23, 30), key='SPrepw')
        with col_w3:
            SLatwi = st.number_input("Kolik minut vám obvykle trvá usnout?", min_value=0, value=15, key='SLatwi')
        
        SEw = st.time_input("V kolik hodin se obvykle probouzíte ve všední dny?", time(7, 0), key='SEw')
        
        Alarmw = st.radio("Používáte obvykle budík ve všední dny?", [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=0, key='Alarmw')
        
        if Alarmw == 1:
            BAlarmw = st.radio("Probouzíte se pravidelně před tím, než budík zazvoní?", [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=1, key='BAlarmw')
        
        SIw = st.number_input("Za kolik minut vstanete po probuzení z postele ve všední dny?", min_value=0, value=5, key='SIw')
        
        st.markdown("Jak dlouhou dobu strávíte venku na přirozeném světle ve všední den?")
        col_le_w1, col_le_w2 = st.columns(2)
        with col_le_w1:
            LEwh = st.number_input("Hodiny:", min_value=0, value=0, key='LEwh')
        with col_le_w2:
            LEwm = st.number_input("Minuty:", min_value=0, max_value=59, value=30, key='LEwm')
        LEw = LEwh + LEwm/60

    elif WD == 8:
        st.warning("Váš chronotyp nelze bohužel určit kvůli zcela nepravidelnému rozvrhu.")


    # --- Free Days (VOLNÉ DNY) Block ---
    if WD >= 0 and WD < 7:
        st.subheader("2.2. Režim během **VOLNÝCH** dnů ({} dní)".format(FD))
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            BTf = st.time_input("V kolik hodin si chodíte obvykle lehnout do postele (volný den)?", time(0, 30), key='BTf')
        with col_f2:
            SPrepf = st.time_input("V kolik hodin se obvykle připravujete ke spánku (zhasnete světlo, volný den)?", time(1, 0), key='SPrepf')
        with col_f3:
            SLatfi = st.number_input("Kolik minut vám obvykle trvá usnout (volný den)?", min_value=0, value=15, key='SLatfi')
            
        SEf = st.time_input("V kolik hodin se obvykle probouzíte ve volné dny?", time(9, 0), key='SEf')
        
        Alarmf = st.radio("Máte nějaký důvod, kvůli kterému si nemůžete zvolit čas pro spánek a probouzení ve volné dny?", 
                          [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=1, key='Alarmf')
        
        if Alarmf == 1:
            BAlarmf = st.radio("Potřebujete obvykle k probuzení ve volný den použít budík?", [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=1, key='BAlarmf')
            
        SIf = st.number_input("Za kolik minut vstanete po probuzení z postele ve volné dny?", min_value=0, value=10, key='SIf')
        
        st.markdown("Jak dlouhou dobu strávíte venku na přirozeném světle ve volný den?")
        col_le_f1, col_le_f2 = st.columns(2)
        with col_le_f1:
            LEfh = st.number_input("Hodiny:", min_value=0, value=1, key='LEfh')
        with col_le_f2:
            LEfm = st.number_input("Minuty:", min_value=0, max_value=59, value=0, key='LEfm')
        LEf = LEfh + LEfm/60


    st.header("3. Doplňující otázky")
    # **FIXED 'str' object error:** Using list() and a unique variable name
    slequal_choice = st.radio("Je kvalita vašeho spánku:", 
                       options=list(slequal_options.keys()),
                       format_func=lambda x: f"{slequal_options[x]} ({x})",
                       key='slequal_radio')

    Bastart = st.time_input("Kdy se během dne začínáte cítit psychicky nejaktivnější?", time(9, 0), key='Bastart')
    
    st.markdown("**Kdy se během dne přestáváte cítit psychicky nejaktivnější?**")
    col_ba1, col_ba2 = st.columns(2)
    with col_ba1:
        Baend_time = st.time_input("Čas (HH:MM):", time(17, 0), key='Baend_time')
    with col_ba2:
        Baend_past_midnight = st.checkbox("Čas je po půlnoci (např. 01:00 ráno)")
        
    submit_button = st.form_submit_button("Vypočítat chronotyp")

# --- Calculation and Output Block ---

if submit_button:
    
    if WD == 8:
        st.error("Výpočet nelze provést, protože máte zcela nepravidelný rozvrh.")
        st.stop()
        
    # --- Initialize all calculation outputs to safe values for display/save ---
    SDw, SDw_i, MSW = timedelta(0), 0.0, 0.0
    SDf, SDf_i, MSF = timedelta(0), 0.0, 0.0
    MSFsc, SJL, Bamid = np.nan, np.nan, np.nan
    SDweek = 0.0
    
    base_date = datetime.date(2000, 1, 1)

    try:
        # --- 1. Core MCTQ Calculations ---
        
        # Working Day Calculations
        if WD > 0 and BTw and SPrepw and SEw:
            SLatw = timedelta(minutes=SLatwi)
            SPrepw_dt = time_to_datetime(SPrepw, base_date)
            SOw_dt = SPrepw_dt + SLatw
            SOw = SOw_dt.time()
            SDw, SEw_dt = calculate_sleep_duration(SOw, SEw)
            SDw_i = SDw.total_seconds() / 3600
            
            if SDw_i < 4 or SDw_i > 14:
                st.error(f"Vypočtená délka spánku ve všední dny ({round(SDw_i, 2)} h) není reálná. Zkontrolujte prosím časy.")
                st.stop()
            
            MSW_dt = SOw_dt + (SDw / 2)
            MSW = MSW_dt.hour + MSW_dt.minute/60
            
        # Free Day Calculations
        if FD > 0 and BTf and SPrepf and SEf:
            SLatf = timedelta(minutes=SLatfi)
            SPrepf_dt = time_to_datetime(SPrepf, base_date)
            SOf_dt = SPrepf_dt + SLatf
            SOf = SOf_dt.time()
            SDf, SEf_dt = calculate_sleep_duration(SOf, SEf)
            SDf_i = SDf.total_seconds() / 3600
            
            if SDf_i < 4 or SDf_i > 14:
                st.error(f"Vypočtená délka spánku ve volné dny ({round(SDf_i, 2)} h) není reálná. Zkontrolujte prosím časy.")
                st.stop()
            
            MSF_dt = SOf_dt + (SDf / 2)
            MSF = MSF_dt.hour + MSF_dt.minute/60

        # Shared Calculations
        
        # Bamid
        Bastart_dt = time_to_datetime(Bastart, base_date)
        Baend_dt = time_to_datetime(Baend_time, base_date)
        if Baend_past_midnight:
             Baend_dt += timedelta(days=1)
        Bamid_dt = Bastart_dt + (Baend_dt - Bastart_dt)/2
        Bamid = Bamid_dt.hour + Bamid_dt.minute/60

        # SDweek
        SDweek = round(((SDw.total_seconds() * WD + SDf.total_seconds() * FD)/7) / 3600, 3)

        # MSFsc (Chronotype)
        if FD > 0 and (Alarmf == 0 or (Alarmf == 1 and BAlarmf == 0)):
            if SDf_i <= SDw_i:
                MSFsc = MSF
            else:
                MSFsc = MSF - (SDf_i - SDweek)/2
        
        # Social Jetlag
        if WD > 0 and FD > 0:
            SJLrel = MSF - MSW
            SJL = abs(SJLrel)
        
        # --- 2. Data Storage ---
        
        # 2.1. Create a dictionary of results
        vd = {
            'ID': dt.now().strftime('%Y-%m-%d_%H-%M-%S'), 
            'age': age,
            'sex': sex,
            'height': height,
            'weight': weight,
            'postal': postal,
            'educ': educ_choice, # Store the integer key
            'WD': WD,
            'FD': FD,
            'BTw': BTw.strftime('%H%M') if BTw else 'N/A',
            'SPrepw': SPrepw.strftime('%H%M') if SPrepw else 'N/A',
            'SLatwi': SLatwi,
            'SEw': SEw.strftime('%H%M') if SEw else 'N/A',
            'Alarmw': Alarmw,
            'BAlarmw': BAlarmw,
            'SIw': SIw,
            'LEw': LEw,
            'BTf': BTf.strftime('%H%M') if BTf else 'N/A',
            'SPrepf': SPrepf.strftime('%H%M') if SPrepf else 'N/A',
            'SLatfi': SLatfi,
            'SEf': SEf.strftime('%H%M') if SEf else 'N/A',
            'Alarmf': Alarmf,
            'BAlarmf': BAlarmf,
            'SIf': SIf,
            'LEf': LEf,
            'Slequal': slequal_choice, # Store the integer key
            'Bastart': Bastart.strftime('%H%M'),
            'Baend_time': Baend_time.strftime('%H%M'),
            'Baend_past_midnight': Baend_past_midnight,
            'MSFsc': round(MSFsc, 3) if not np.isnan(MSFsc) else 'N/A',
            'SJL': round(SJL, 3) if not np.isnan(SJL) else 'N/A',
            'Bamid': round(Bamid, 3) if not np.isnan(Bamid) else 'N/A',
        }
        
        # 2.2. Connect and Save to Google Sheets
        try:
            import gspread
            # NOTE: st.secrets is how Streamlit securely loads the credentials
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])

            SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE" # <<< CHECK THIS ID
            workbook = gc.open_by_key(SHEET_ID)
            worksheet = workbook.get_worksheet(0)  # Use the first sheet

            header_keys = list(worksheet.row_values(1)) # Get the headers from the sheet
            row_to_save = [vd.get(key, '') for key in header_keys] 
            
            worksheet.append_row(row_to_save)
            
            st.success("Data byla anonymně uložena pro další analýzu. Děkujeme!")

        except Exception as sheet_error:
            # st.error(f"FATAL SHEET ERROR: {sheet_error}") # REMOVE FOR PUBLIC DEPLOY
            st.warning("Data nebyla uložena. Děkujeme za vyplnění.")


        # --- 3. Display Results ---
        
        st.subheader("VÝSLEDKY VÝPOČTU")
        st.markdown("---")
        
        # ... (Rest of the display results code: Chronotype, Social Jetlag, etc. - Keep as is)
        
    except Exception as e:
        st.error(f"Při výpočtu došlo k neočekávané chybě: {e}") # REMOVE FOR PUBLIC DEPLOY
        st.error("Při výpočtu došlo k neočekávané chybě. Zkontrolujte prosím zadaná data.")
