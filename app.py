import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

# Configuração simples
st.set_page_config(layout="wide")
st.title("🗺️ Analisador Geográfico")

# Uploads
f_p = st.file_uploader("Upload PRODES (Zip)", type="zip")
f_c = st.file_uploader("Upload CARs (Zip)", type="zip")

if st.button("Processar"):
    if f_p and f_c:
        try:
            # Limpeza e preparação de pastas
            if os.path.exists("tmp"): shutil.rmtree("tmp")
            os.makedirs("tmp/prodes", exist_ok=True)
            os.makedirs("tmp/cars", exist_ok=True)
            
            # Extração
            with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/prodes")
            with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/cars")
            
            # Encontrar ficheiro PRODES
            prodes_path = ""
            for r, d, files in os.walk("tmp/prodes"):
                for file in files:
                    if file.endswith(".shp"):
                        prodes_path = os.path.join(r, file)
            
            if prodes_path:
                g_p = gpd.read_file(prodes_path).to_crs("EPSG:31982")
                res = []
                # Processar cada CAR
                for r, d, files in os.walk("tmp/cars"):
                    for file in files:
                        if file.endswith(".shp"):
                            g_c = gpd.read_file(os.path.join(r, file)).to_crs("EPSG:31982")
                            # Interseção
                            inter = gpd.overlay(g_c, g_p, how='intersection')
                            if not inter.empty:
                                area_ha = inter.geometry.area.sum() / 10000
                                res.append({"Ficheiro": file, "Area_Ha": round(area_ha, 2)})
                
                if res:
                    st.dataframe(pd.DataFrame(res))
                else:
                    st.warning("Nenhuma interseção encontrada.")
            else:
                st.error("Ficheiro .shp do PRODES não encontrado dentro do ZIP.")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")
    else:
        st.error("Por favor, suba ambos os ficheiros.")
