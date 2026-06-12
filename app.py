import streamlit as st
import os, zipfile, shutil, geopandas as gpd, pandas as pd, io, gc

st.set_page_config(page_title="Detector de Passivos", layout="centered")

# --- LÓGICA DE LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

def tela_login():
    st.title("🔒 Acesso ao Sistema")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "gabriel" and p == "Gab1914.":
            st.session_state.auth = True
            st.rerun()
        else: st.error("Usuário ou senha inválidos.")

# --- LÓGICA PRINCIPAL ---
def tela_principal():
    st.title("🗺️ Detector de Passivos: CAR vs PRODES")
    arquivo = st.file_uploader("Suba o arquivo CARS.zip", type=["zip"])
    
    if arquivo and st.button("🚀 Rodar Processamento"):
        st.write("Processando...")
        # (O código de processamento continua aqui...)
        st.success("Concluído!")

# --- ESCOLHA DA TELA ---
if not st.session_state.auth:
    tela_login()
else:
    tela_principal()
