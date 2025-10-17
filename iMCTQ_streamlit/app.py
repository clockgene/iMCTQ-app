import streamlit as st
import datetime
import pandas as pd
import numpy as np
from datetime import time, timedelta

# --- Helper Function to handle cross-midnight time subtraction ---
def time_to_datetime(t, base_date):
    """Converts a datetime.time object to a datetime.datetime object on a base date."""
    return datetime.datetime.combine(base_date, t)

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

# --- Streamlit UI Setup ---

st.set_page_config(page_title="Chronotypový Kalkulátor (MCTQ)", layout="wide")
st.title("Chronotypový Kalkulátor")
st.markdown("Na základě upraveného dotazníku **MCTQ (Munich ChronoType Questionnaire)**.")

# Use a form to group all inputs and trigger the calculation only on submit
with st.form("mctq_form"):
    
    st.header("1. Základní informace")
    
    # Personal Info (Simplified for the web app)
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
        postal = st.text_input("PSČ bydliště (např. 14800):")
    with col6:
        educ = st.selectbox("Dosažené vzdělání:", 
                            options={1:'základní nebo neúplné', 2:'vyučení', 3:'střední nebo střední odborné', 
                                     4:'vyšší odborné', 5:'VŠ bakalářské', 6:'VŠ Mgr/Ing/MUDr/apod.', 7:'VŠ postgraduální PhD'},
                            format_func=lambda x: f"{x} - {educ[x]}")

    st.header("2. Pracovní/Volné Dny")
    
    WD = st.number_input("Kolik dní v týdnu (0 až 7) máte pravidelný pracovní rozvrh (zaměstnání, školu, apod.)?", 
                         min_value=0, max_value=8, value=5, step=1, 
                         help="8 znamená zcela nepravidelný rozvrh. Pokud je váš rozvrh zcela nepravidelný, zadejte 8.")
    FD = 7 - WD
    
    
    # --- Working Days (VŠEDNÍ DNY) Block ---
    BTw, SPrepw, SLatwi, SEw, Alarmw, SIw, LEwh, LEwm = None, None, None, None, None, None, None, None
    
    if WD > 0 and WD < 8:
        st.subheader("2.1. Režim během **VŠEDNÍCH** dnů ({} dní)".format(WD))
        
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            BTw = st.time_input("V kolik hodin si chodíte obvykle lehnout do postele?", time(23, 0))
        with col_w2:
            SPrepw = st.time_input("V kolik hodin se obvykle připravujete ke spánku (zhasnete světlo)?", time(23, 30))
        with col_w3:
            SLatwi = st.number_input("Kolik minut vám obvykle trvá usnout?", min_value=0, value=15)
        
        SEw = st.time_input("V kolik hodin se obvykle probouzíte ve všední dny?", time(7, 0))
        
        Alarmw = st.radio("Používáte obvykle budík ve všední dny?", [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=0)
        
        if Alarmw == 1:
            BAlarmw = st.radio("Probouzíte se pravidelně před tím, než budík zazvoní?", [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=1)
        else:
            BAlarmw = 0 # Default if no alarm is used
            
        SIw = st.number_input("Za kolik minut vstanete po probuzení z postele ve všední dny?", min_value=0, value=5)
        
        st.markdown("Jak dlouhou dobu strávíte venku na přirozeném světle ve všední den?")
        col_le_w1, col_le_w2 = st.columns(2)
        with col_le_w1:
            LEwh = st.number_input("Hodiny:", min_value=0, value=0)
        with col_le_w2:
            LEwm = st.number_input("Minuty:", min_value=0, max_value=59, value=30)
        
    elif WD == 8:
        st.warning("Váš chronotyp nelze bohužel určit kvůli zcela nepravidelnému rozvrhu.")


    # --- Free Days (VOLNÉ DNY) Block ---
    BTf, SPrepf, SLatfi, SEf, Alarmf, BAlarmf, SIf, LEfh, LEfm = None, None, None, None, None, None, None, None, None

    if WD >= 0 and WD < 7:
        st.subheader("2.2. Režim během **VOLNÝCH** dnů ({} dní)".format(FD))
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            BTf = st.time_input("V kolik hodin si chodíte obvykle lehnout do postele (volný den)?", time(0, 30))
        with col_f2:
            SPrepf = st.time_input("V kolik hodin se obvykle připravujete ke spánku (zhasnete světlo, volný den)?", time(1, 0))
        with col_f3:
            SLatfi = st.number_input("Kolik minut vám obvykle trvá usnout (volný den)?", min_value=0, value=15, key='slatfi')
            
        SEf = st.time_input("V kolik hodin se obvykle probouzíte ve volné dny?", time(9, 0))
        
        Alarmf = st.radio("Máte nějaký důvod, kvůli kterému si nemůžete zvolit čas pro spánek a probouzení ve volné dny?", 
                          [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=1)
        
        if Alarmf == 1:
            BAlarmf = st.radio("Potřebujete obvykle k probuzení ve volný den použít budík?", [1, 0], format_func=lambda x: 'Ano' if x == 1 else 'Ne', index=1, key='balarmf')
        else:
            BAlarmf = 0
            
        SIf = st.number_input("Za kolik minut vstanete po probuzení z postele ve volné dny?", min_value=0, value=10)
        
        st.markdown("Jak dlouhou dobu strávíte venku na přirozeném světle ve volný den?")
        col_le_f1, col_le_f2 = st.columns(2)
        with col_le_f1:
            LEfh = st.number_input("Hodiny:", min_value=0, value=1, key='lefh')
        with col_le_f2:
            LEfm = st.number_input("Minuty:", min_value=0, max_value=59, value=0, key='lefm')

    st.header("3. Doplňující otázky")
    Slequal = st.radio("Je kvalita vašeho spánku:", 
                       options={1:'velmi dobrá', 2:'spíše dobrá', 3:'spíše špatná', 4:'velmi špatná'},
                       format_func=lambda x: f"{Slequal[x]} ({x})")

    Bastart = st.time_input("Kdy se během dne začínáte cítit psychicky nejaktivnější?", time(9, 0))
    
    # Custom handling for Baend (can be past midnight)
    st.markdown("**Kdy se během dne přestáváte cítit psychicky nejaktivnější?**")
    col_ba1, col_ba2 = st.columns(2)
    with col_ba1:
        Baend_time = st.time_input("Čas (HH:MM):", time(17, 0))
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
        
        # Convert all minute/hour inputs to usable timedelta/float
        SLatw = timedelta(minutes=SLatwi)
        SLatf = timedelta(minutes=SLatfi)
        LEw = LEwh + LEwm/60
        LEf = LEfh + LEfm/60

        # Calculate Sleep Onset (SO) times
        # Note: We must use a base datetime object for time addition (can't add time + timedelta directly)
        base_date = datetime.date(2000, 1, 1)

        SPrepw_dt = time_to_datetime(SPrepw, base_date)
        SOw_dt = SPrepw_dt + SLatw
        SOw = SOw_dt.time()
        
        SPrepf_dt = time_to_datetime(SPrepf, base_date)
        SOf_dt = SPrepf_dt + SLatf
        SOf = SOf_dt.time()
        
        # Calculate Sleep Duration (SD) and correct End Time (SE)
        SDw, SEw_dt = calculate_sleep_duration(SOw, SEw)
        SDf, SEf_dt = calculate_sleep_duration(SOf, SEf)

        SDw_i = SDw.total_seconds() / 3600
        SDf_i = SDf.total_seconds() / 3600
        
        # Basic Validation (as in the original script)
        if SDw_i < 4 or SDw_i > 14:
             st.error(f"Vypočtená délka spánku ve všední dny ({round(SDw_i, 2)} h) není reálná. Zkontrolujte prosím časy.")
             st.stop()
        if SDf_i < 4 or SDf_i > 14:
             st.error(f"Vypočtená délka spánku ve volné dny ({round(SDf_i, 2)} h) není reálná. Zkontrolujte prosím časy.")
             st.stop()
             
        # Calculate Get Up (GU) times
        GUw = SEw_dt + timedelta(minutes=SIw)
        GUf = SEf_dt + timedelta(minutes=SIf)
        
        # Total Time in Bed (TBT) in hours
        # Use BTw/BTf in datetime format for TBT calculation (similar cross-midnight logic needed)
        BTw_dt = time_to_datetime(BTw, base_date)
        if BTw_dt > GUw: # If TBT crosses midnight
            GUw += timedelta(days=1)
        TBTw = (GUw - BTw_dt).total_seconds() / 3600
        
        BTf_dt = time_to_datetime(BTf, base_date)
        if BTf_dt > GUf: # If TBT crosses midnight
            GUf += timedelta(days=1)
        TBTf = (GUf - BTf_dt).total_seconds() / 3600

        # Mid-Sleep (MS) in hours (relative to midnight of day 1)
        MSW_dt = SOw_dt + (SDw / 2)
        MSF_dt = SOf_dt + (SDf / 2)
        
        # Normalize MS to a 24-hour clock (hour + minute/60)
        MSW = MSW_dt.hour + MSW_dt.minute/60
        MSF = MSF_dt.hour + MSF_dt.minute/60
        
        # Handle the Baend (most active end time) which can be past 24:00
        Baend_hour = Baend_time.hour
        if Baend_past_midnight:
            Baend_hour += 24

        Bastart_dt = time_to_datetime(Bastart, base_date)
        Baend_dt = time_to_datetime(Baend_time, base_date)
        if Baend_past_midnight:
             Baend_dt += timedelta(days=1) # Add one day if it's past midnight

        # Most active mid point
        Bamid_dt = Bastart_dt + (Baend_dt - Bastart_dt)/2
        Bamid = Bamid_dt.hour + Bamid_dt.minute/60 # In hours (0-24+)

        # Average weekly sleep duration, in h
        SDweek = round(((SDw.total_seconds() * WD + SDf.total_seconds() * FD)/7) / 3600, 3)

        # Corrected Mid-Sleep on Free Day (MSFsc) - The Chronotype
        MSFsc = None
        if Alarmf == 0 or (Alarmf == 1 and BAlarmf == 0):
            if SDf <= SDw:
                MSFsc = MSF
            else:
                MSFsc = MSF - (SDf_i - SDweek)/2
        else: # Alarmf == 1 and BAlarmf == 1
            MSFsc = np.nan # Cannot be determined

        # Social jetlag
        SJLrel = MSF - MSW
        SJL = abs(SJLrel)
        
        # --- 2. Display Results ---
        
        st.subheader("VÝSLEDKY VÝPOČTU")
        
        st.markdown("---")
        
        try:
            st.success(f'Váš **chronotyp** (MSFsc) je: **{round(MSFsc, 2)}**')
            st.write("")
            
            # Chronotype Classification (Simplified for 30-60 year olds)
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
                
        except TypeError:
            st.warning('Váš přesný chronotyp nelze určit, protože máte nepravidelný režim nebo se budíte až s budíkem i během víkendu.')
            try:
                st.info(f'Nicméně, lze přibližně odhadnout (Mid-point of most active time): **{round(Bamid, 2)}**')
                if Bamid <= 10.72:
                    st.info('Jste spíše **skřivan**.')
                elif Bamid <= 13.204:
                    st.info('Máte spíše **průměrný chronotyp**.')
                else:
                    st.info('Jste spíše **sova**.')
            except Exception:
                st.error('Ani váš přibližný chronotyp nelze odhadnout.')

        st.markdown("---")
        
        # Social Jetlag
        try:
            st.success(f'Váš **sociální jetlag** (SJL) je: **{round(SJL, 2)} hodin**')
            st.caption("(Rozdíl mezi středem spánku ve volné dny a ve všední dny)")
            
            if SJL < 0.65:
                st.info('Váš vnitřní časový systém je v souladu s vaším rozvrhem.')
            elif SJL <= 1.67:
                st.warning('Trpíte obvyklým sociálním jetlagem, doporučujeme úpravu vašeho rozvrhu.')
            else:
                st.error('Trpíte velkým sociálním jetlagem, doporučujeme úpravu vašeho rozvrhu a životního stylu.')
        except Exception:
             st.warning('Váš sociální jetlag nelze určit, protože máte nepravidelný režim.')
             
        st.markdown("---")
        st.info('Děkujeme za vyplnění MCTQ dotazníku.')
        
    except Exception as e:
        st.error(f"Při výpočtu došlo k chybě. Zkontrolujte prosím zadaná data. Detaily chyby: {e}")
