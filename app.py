import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="centered")

if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Verifique se digitou exatamente: gabriel e Gab1914.
        if u.strip() == "gabriel" and p.strip() == "Gab1914.":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos. Tente novamente.")
else:
    st.title("🗺️ Analisador Geográfico")
    f_p = st.file_uploader("Upload PRODES (Zip)", type="zip")
    f_c = st.file_uploader("Upload CARs (Zip)", type="zip")
    
    if st.button("Processar"):
        if f_p and f_c:
            # ... (o resto da lógica de processamento)
            st.success("Arquivos prontos para processar!")
        else:
            st.error("Por favor, selecione ambos os arquivos.")
