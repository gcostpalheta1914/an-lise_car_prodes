import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")
st.title("🗺️ Detector de Passivos: CAR vs PRODES")

f_c = st.file_uploader("1. Suba o arquivo dos CARs (CARS.zip)", type="zip")
f_p = st.file_uploader("2. Suba o arquivo do PRODES (PRODES_2008_A_2023.zip)", type="zip")

def buscar_shp_na_pasta(pasta_raiz):
    """Procura por qualquer arquivo .shp dentro de uma pasta e suas subpastas."""
    for root, dirs, files in os.walk(pasta_raiz):
        for file in files:
            if file.endswith(".shp"):
                return os.path.join(root, file)
    return None

if st.button("🚀 Processar"):
    if f_c and f_p:
        with st.spinner("Processando dados..."):
            try:
                # Limpeza
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                os.makedirs("tmp/p", exist_ok=True)
                os.makedirs("tmp/c", exist_ok=True)
                
                # Extração
                with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
                with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
                
                # Busca robusta
                shp_p = buscar_shp_na_pasta("tmp/p")
                shp_c = buscar_shp_na_pasta("tmp/c")
                
                if not shp_p or not shp_c:
                    st.error(f"Não encontrei arquivo .shp! Procura PRODES: {shp_p}, CAR: {shp_c}")
                    st.stop()
                
                g_p = gpd.read_file(shp_p, engine='pyogrio').to_crs("EPSG:31982")
                g_c = gpd.read_file(shp_c, engine='pyogrio').to_crs("EPSG:31982")
                
                # Detecta coluna de ano
                col_ano = next((c for c in g_p.columns if any(x in c.lower() for x in ['ano', 'date', 'prodes'])), g_p.columns[0])
                st.write(f"Coluna detectada: **{col_ano}**")
                
                inter = gpd.overlay(g_c, g_p, how='intersection')
                
                if not inter.empty:
                    # Exibe resultado
                    df = inter[[inter.columns[0], col_ano]].copy()
                    st.table(df.head(10))
                else:
                    st.write("Nenhuma intersecção encontrada.")
                
                shutil.rmtree("tmp")
            except Exception as e:
                st.error(f"Erro detalhado: {e}")
