import streamlit as st
import datetime
import pandas as pd
import numpy as np
from datetime import time, timedelta, datetime as dt

# --- Helper Function to handle cross-midnight time subtraction ---
def time_to_datetime(t, base_date):
    """Converts a datetime.time object to a datetime.datetime object on a base date."""
    # Handle the case where the input might be None if the block was skipped
    if t is None:
        return None
    return dt.combine(base_date, t)

def calculate_sleep_duration(time_start, time_end):
    """
    Calculates sleep duration (timedelta) handling cross-midnight sleep.
    time_start and time_end are datetime.time objects from st.time_input.
    """
    base_date = datetime.date(2000, 1, 1) # Arbitrary base date
    start_dt = time_to_datetime(time_start, base_date)
    end_dt = time_to_datetime(time_end, base_date)
    
    # If end time is earlier than start time, it means sleep crossed midnight.
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    
    duration = end_dt - start_dt
    return duration, end_dt # Return both duration and corrected end time

# --- Options Dictionaries (FIXED NameError: name 'educ' is not defined) ---
educ_options = {
    1:'základní nebo neúplné', 2:'vyučení', 3:'střední nebo střední odborné', 
    4:'vyšší odborné', 5:'VŠ bakalářské', 6:'VŠ Mgr/Ing/MUDr/apod.', 7:'VŠ postgraduální PhD'
}
slequal_options = {
    1:'velmi dobrá', 2:'spíše dobrá', 3:'spíše špatná', 4:'velmi špatná'
}


# --- Streamlit UI Setup ---

st.set_page_config(page_title="Chronotypový Kalkulátor (MCTQ)", layout="wide")
st.title("Chronotypový Kalkulátor")
st.markdown("Na základě upraveného dotazníku **MCTQ (Munich ChronoType Questionnaire)**.")

# Use a form to group all inputs and trigger the calculation only on submit
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
        # Changed to text input as postal codes start with a zero in some countries
        postal = st.text_input("PSČ bydliště (zadejte bez mezery, např. 14800):", value="10000")
    with col6:
        # FIXED NameError: The format_func now correctly uses educ_options
        educ_key = st.selectbox("Dosažené vzdělání:", 
                            options=educ_options.keys(),
                            format_func=lambda x: f"{x} - {educ_options[x]}",
                            index=2) 
        educ = educ_options[educ_key] # Store the text description if needed later

    st.header("2. Pracovní/Volné Dny")
    
    WD = st.number_input("Kolik dní v týdnu (0 až 7) máte pravidelný pracovní rozvrh?", 
                         min_value=0, max_value=8, value=5, step=1, 
                         help="8 znamená zcela nepravidelný rozvrh. I pokud je vaše odpověď 0 či 7, prosím uvažte, že se Vaše doba spánku může lišit.")
    FD = 7 - WD
    
    
    # --- Initialize all conditional variables to None/safe values ---
    # This prevents NameErrors if a block is skipped
    BTw, SPrepw, SLatwi, SEw = None, None, 15, None
    Alarmw, BAlarmw, SIw = 0, 0, 5
    LEwh, LEwm, LEw = 0, 0, 0.0
    
    BTf, SPrepf, SLatfi, SEf = None, None, 15, None
    Alarmf, BAlarmf, SIf = 0, 0, 10
    LEfh, LEfm, LEf = 0, 0, 0.0

    
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
    # FIXED NameError: The format_func now correctly uses slequal_options
    Slequal_key = st.radio("Je kvalita vašeho spánku:", 
                       options=slequal_options.keys(),
                       format_func=lambda x: f"{slequal_options[x]} ({x})")
    Slequal = slequal_options[Slequal_key] # Store the text description if needed later

    Bastart = st.time_input("Kdy se během dne začínáte cítit psychicky nejaktivnější?", time(9, 0), key='Bastart')
    
    # Custom handling for Baend (can be past midnight)
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
        
    try:
        # --- 1. Preparation of Time Variables ---
        base_date = datetime.date(2000, 1, 1)

        # --- Working Day Calculations ---
        if WD > 0:
            SLatw = timedelta(minutes=SLatwi)
            SPrepw_dt = time_to_datetime(SPrepw, base_date)
            SOw_dt = SPrepw_dt + SLatw
            SOw = SOw_dt.time()
            SDw, SEw_dt = calculate_sleep_duration(SOw, SEw)
            SDw_i = SDw.total_seconds() / 3600
            
            # Check for extreme duration
            if SDw_i < 4 or SDw_i > 14:
                st.error(f"Vypočtená délka spánku ve všední dny ({round(SDw_i, 2)} h) není reálná. Zkontrolujte prosím časy.")
                st.stop()

            # Mid-Sleep (MS) in hours
            MSW_dt = SOw_dt + (SDw / 2)
            MSW = MSW_dt.hour + MSW_dt.minute/60
        else:
            SDw = timedelta(0)
            SDw_i = 0.0
            MSW = 0.0 # Placeholder for MSW when WD=0

        # --- Free Day Calculations ---
        if FD > 0:
            SLatf = timedelta(minutes=SLatfi)
            SPrepf_dt = time_to_datetime(SPrepf, base_date)
            SOf_dt = SPrepf_dt + SLatf
            SOf = SOf_dt.time()
            SDf, SEf_dt = calculate_sleep_duration(SOf, SEf)
            SDf_i = SDf.total_seconds() / 3600
            
            # Check for extreme duration
            if SDf_i < 4 or SDf_i > 14:
                st.error(f"Vypočtená délka spánku ve volné dny ({round(SDf_i, 2)} h) není reálná. Zkontrolujte prosím časy.")
                st.stop()

            # Mid-Sleep (MS) in hours
            MSF_dt = SOf_dt + (SDf / 2)
            MSF = MSF_dt.hour + MSF_dt.minute/60
        else:
            SDf = timedelta(0)
            SDf_i = 0.0
            MSF = 0.0 # Placeholder for MSF when FD=0

        # --- Shared Calculations ---
        
        # Mid-point of most active time
        Bastart_dt = time_to_datetime(Bastart, base_date)
        Baend_dt = time_to_datetime(Baend_time, base_date)
        if Baend_past_midnight:
             Baend_dt += timedelta(days=1)

        Bamid_dt = Bastart_dt + (Baend_dt - Bastart_dt)/2
        Bamid = Bamid_dt.hour + Bamid_dt.minute/60 # In hours (0-24+)

        # Average weekly sleep duration, in h
        SDweek = round(((SDw.total_seconds() * WD + SDf.total_seconds() * FD)/7) / 3600, 3)

        # Corrected Mid-Sleep on Free Day (MSFsc) - The Chronotype
        MSFsc = np.nan
        if FD > 0 and (Alarmf == 0 or (Alarmf == 1 and BAlarmf == 0)):
            if SDf_i <= SDw_i:
                MSFsc = MSF
            else:
                MSFsc = MSF - (SDf_i - SDweek)/2
        
        # Social jetlag
        SJL = np.nan
        if WD > 0 and FD > 0:
            SJLrel = MSF - MSW
            SJL = abs(SJLrel)
        
        
        # --- 2. Display Results ---
                
        st.subheader("VÝSLEDKY VÝPOČTU")
        st.markdown("---")
        
        # Chronotype Display
        if not np.isnan(MSFsc):
            st.success(f'Váš **chronotyp** (MSFsc) je: **{round(MSFsc, 2)}**')
            st.write("")
            
            # Classification
            if MSFsc <= 1.50584:
                st.info('Jste **extrémní skřivan** (Early Morning).')
            elif MSFsc <= 1.935:
                st.info('Jste **skřivan** (Morning).')
            elif MSFsc <= 2.3984:
                st.info('Jste **spíše skřivan** (Slightly Morning).')
            elif MSFsc <= 3.5817:
                st.info('Máte **průměrný chronotyp** (Intermediate).')
            elif MSFsc <= 4.145:
                st.info('Jste **spíše sova** (Slightly Evening).')
            elif MSFsc <= 4.66584:
                st.info('Jste **sova** (Evening).')
            else:
                st.info('Jste **extrémní sova** (Late Evening).')
                
        else:
            st.warning('Váš přesný chronotyp nelze určit, protože máte nepravidelný režim nebo se budíte až s budíkem i během víkendu.')
            
            # Bamid estimate
            if not np.isnan(Bamid):
                st.info(f'Nicméně, lze přibližně odhadnout (Mid-point of most active time): **{round(Bamid, 2)}**')
                if Bamid <= 10.72:
                    st.info('Jste spíše **skřivan**.')
                elif Bamid <= 13.204:
                    st.info('Máte spíše **průměrný chronotyp**.')
                else:
                    st.info('Jste spíše **sova**.')
            else:
                st.error('Ani váš přibližný chronotyp nelze odhadnout.')

        st.markdown("---")
        
        # Social Jetlag
        if not np.isnan(SJL):
            st.success(f'Váš **sociální jetlag** (SJL) je: **{round(SJL, 2)} hodin**')
            st.caption("(Rozdíl mezi středem spánku ve volné dny a ve všední dny)")
            
            if SJL < 0.65:
                st.info('Váš vnitřní časový systém je v souladu s vaším rozvrhem.')
            elif SJL <= 1.67:
                st.warning('Trpíte obvyklým sociálním jetlagem, doporučujeme úpravu vašeho rozvrhu.')
            else:
                st.error('Trpíte velkým sociálním jetlagem, doporučujeme úpravu vašeho rozvrhu a životního stylu.')
        else:
             st.warning('Váš sociální jetlag nelze určit, protože nemáte volné a všední dny, nebo máte nepravidelný režim.')
             
        st.markdown("---")
        st.info('Děkujeme za vyplnění MCTQ dotazníku.')


        # --- 3. Data Storage ---
                
        # 3.1. Create a dictionary of results
        vd = {
            'ID': dt.now().strftime('%Y-%m-%d_%H-%M-%S'), # Unique ID
            'age': age,
            'sex': sex,
            'height': height,
            'weight': weight,
            'postal': postal,
            'educ': educ,
            'WD': WD,
            'FD': FD,
            'BTw': BTw.strftime('%H%M') if BTw else None,
            'SPrepw': SPrepw.strftime('%H%M') if SPrepw else None,
            'SLatwi': SLatwi,
            'SEw': SEw.strftime('%H%M') if SEw else None,
            'Alarmw': Alarmw,
            'BAlarmw': BAlarmw,
            'SIw': SIw,
            'LEw': LEw,
            'BTf': BTf.strftime('%H%M') if BTf else None,
            'SPrepf': SPrepf.strftime('%H%M') if SPrepf else None,
            'SLatfi': SLatfi,
            'SEf': SEf.strftime('%H%M') if SEf else None,
            'Alarmf': Alarmf,
            'BAlarmf': BAlarmf,
            'SIf': SIf,
            'LEf': LEf,
            'Slequal': Slequal_key, # Store the numerical key
            'Bastart': Bastart.strftime('%H%M'),
            'Baend_time': Baend_time.strftime('%H%M'),
            'Baend_past_midnight': Baend_past_midnight,
            'MSFsc': round(MSFsc, 3) if not np.isnan(MSFsc) else 'N/A',
            'SJL': round(SJL, 3) if not np.isnan(SJL) else 'N/A',
            'Bamid': round(Bamid, 3), 
            # Add any other variables you want to save
        }
        
        # 3.2. Connect and Save to Google Sheets
        try:
            import gspread
            # NOTE: st.secrets is how Streamlit securely loads the credentials
            gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])

            # Open the sheet by its ID (REPLACE THIS WITH YOUR ACTUAL SHEET ID)
            # SHEET_ID = "https://docs.google.com/spreadsheets/d/10FfTOk_hLShUk1EEQi9ndBlZcbsME1ORfs7btm6IjDc/edit?usp=sharing"
            SHEET_ID = "10FfTOk_hLShUk1EEQi9ndBlZcbsME1ORfs7btm6IjDc"
            workbook = gc.open_by_key(SHEET_ID)
            worksheet = workbook.get_worksheet(0)  # Use the first sheet

            # Append the row of values (ensuring order matches your sheet's header row)
            # This is a critical step: ensure the keys in vd are the same as your SHEET HEADER!
            header_keys = list(worksheet.row_values(1)) # Get the headers from the sheet
            
            # Map vd values to the order of header_keys
            row_to_save = [vd.get(key, '') for key in header_keys] 
            
            worksheet.append_row(row_to_save)
            
            st.success("Data byla anonymně uložena pro další analýzu. Děkujeme!")

        except Exception as sheet_error:
            # st.error(f"Chyba při ukládání dat: {sheet_error}") # Comment out for public
            st.warning("Data nebyla uložena. Děkujeme za vyplnění.")
        
    except Exception as e:
        st.error(f"Při výpočtu došlo k neočekávané chybě. Zkontrolujte prosím zadaná data. Detaily chyby: {e}")
