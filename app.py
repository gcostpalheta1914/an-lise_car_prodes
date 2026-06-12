import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

# Login
usuario = st.text_input("Usuário")
senha = st.text_input("Senha", type="password")

if st.button("Entrar"):
    if usuario == "gabriel" and senha == "Gab1914.":
        st.session_state.logado = True
        st.rerun()

if st.session_state.get("logado", False):
    st.title("Analisador")
    f_p = st.file_uploader("PRODES", type="zip")
    f_c = st.file_uploader("CARs", type="zip")
    
    if st.button("Processar"):
        os.makedirs("tmp", exist_ok=True)
        with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/prodes")
        with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/cars")
        
        p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/prodes") if f.endswith(".shp")][0]
        g_p = gpd.read_file(p_shp)
        
        res = []
        for r, _, fs in os.walk("tmp/cars"):
            for f in fs:
                if f.endswith(".shp"):
                    g_c = gpd.read_file(os.path.join(r, f))
                    if g_c.crs != g_p.crs: g_c = g_c.to_crs(g_p.crs)
                    inter = gpd.overlay(g_c, g_p, how='intersection')
                    if not inter.empty:
                        ha = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                        res.append({"Arquivo": f, "Area_Ha": round(ha, 2)})
        
        st.dataframe(pd.DataFrame(res))
        shutil.rmtree("tmp")
