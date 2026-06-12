import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")
st.title("🗺️ Detector de Passivos: CAR vs PRODES")

f_c = st.file_uploader("1. Suba o arquivo dos CARs (CARS.zip)", type="zip")
f_p = st.file_uploader("2. Suba o arquivo do PRODES (PRODES_2008_A_2023.zip)", type="zip")

def extrair_e_buscar_shp(caminho_zip, pasta_destino):
    os.makedirs(pasta_destino, exist_ok=True)
    with zipfile.ZipFile(caminho_zip, 'r') as z:
        z.extractall(pasta_destino)
    # Busca recursiva por arquivos .shp
    for root, _, files in os.walk(pasta_destino):
        for file in files:
            if file.endswith(".shp"):
                return os.path.join(root, file)
    return None

if st.button("🚀 Processar"):
    if f_c and f_p:
        with st.spinner("Processando..."):
            try:
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                
                # Extração
                shp_p = extrair_e_buscar_shp(f_p, "tmp/p")
                shp_c = extrair_e_buscar_shp(f_c, "tmp/c")
                
                g_p = gpd.read_file(shp_p, engine='pyogrio').to_crs("EPSG:31982")
                
                # Identifica automaticamente a coluna de ano no PRODES
                # Procura por colunas que contenham "ano", "date", "prodes"
                cols = g_p.columns.tolist()
                col_ano = next((c for c in cols if any(x in c.lower() for x in ['ano', 'date', 'prodes'])), cols[0])
                st.write(f"Coluna de ano detectada no PRODES: **{col_ano}**")
                
                g_c = gpd.read_file(shp_c, engine='pyogrio').to_crs("EPSG:31982")
                
                inter = gpd.overlay(g_c, g_p, how='intersection')
                
                if not inter.empty:
                    res = []
                    # Agrupa por CAR se tiver múltiplos registros
                    for name, group in inter.groupby(inter.columns[0]):
                        anos = ", ".join(group[col_ano].astype(str).unique())
                        ha = group.geometry.area.sum() / 10000
                        res.append({"Identificador": name, "Anos": anos, "Area_Ha": round(ha, 2)})
                    
                    df = pd.DataFrame(res)
                    st.table(df)
                else:
                    st.write("Nenhuma intersecção encontrada.")
                
                shutil.rmtree("tmp")
            except Exception as e:
                st.error(f"Erro: {e}")
