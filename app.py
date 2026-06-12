import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.title("Analisador")

f_p = st.file_uploader("PRODES (Zip)", type="zip")
f_c = st.file_uploader("CARs (Zip)", type="zip")

if st.button("Processar"):
    if f_p and f_c:
        # Cria pasta temporária limpa
        if os.path.exists("tmp"): shutil.rmtree("tmp")
        os.makedirs("tmp/p", exist_ok=True)
        os.makedirs("tmp/c", exist_ok=True)
        
        # Extrai
        with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
        with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
        
        # Localiza o SHP
        p_path = [os.path.join(r, f) for r, _, fs in os.walk("tmp/p") if f.endswith(".shp")][0]
        gp = gpd.read_file(p_path).to_crs("EPSG:31982")
        
        res = []
        for r, _, fs in os.walk("tmp/c"):
            for f in fs:
                if f.endswith(".shp"):
                    gc = gpd.read_file(os.path.join(r, f)).to_crs("EPSG:31982")
                    inter = gpd.overlay(gc, gp, how='intersection')
                    if not inter.empty:
                        ha = inter.geometry.area.sum() / 10000
                        res.append({"Arquivo": f, "Area_Ha": round(ha, 2)})
        
        st.dataframe(pd.DataFrame(res))
        shutil.rmtree("tmp")
    else:
        st.error("Suba os arquivos")
