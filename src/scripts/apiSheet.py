import gspread
from google.oauth2.service_account import Credentials
import json
import streamlit as st

def export_to_google_sheet(data, sheet_name="Test"):
    try:
        creds_dict = json.loads(st.session_state["google_api_key"])
        st.write("run")
        sheet_url="https://docs.google.com/spreadsheets/d/1Mx9RXJu1O-XX64Q24dlyk1MCbpJWptrrT-kMXR-BN6Q"
        
        creds = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)
        st.write(client)
        sheet = client.open_by_url(sheet_url)
        st.write(sheet)
        worksheet = sheet.get_worksheet(3)
        st.write(worksheet)
        # Convertit la data (list[dict]) en tableau
        if isinstance(data, dict):
            data = [data]

        headers = list(data[0].keys())
        values = [headers] + [[str(item.get(h, "")) for h in headers] for item in data]

        worksheet.update("A1", values)

        return sheet.url

    except Exception as e:
        st.error(f"Erreur export Google Sheets : {e}")
        return None
