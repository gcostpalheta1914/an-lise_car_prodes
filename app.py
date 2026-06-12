import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")

# Login simples para evitar problemas
if "logado" not in st.session_state: st.session_state.logado = False
if not st.session_state.logado:
    u = st.text_input("Usuário"); p = st.text_input("Senha", type="password")
    if st.button("Entrar") and u == "gabriel" and p == "Gab1914.":
        st.session_state.logado = True; st.rerun()
else:
    st.title("🗺️ Analisador Geográfico")
    f_p = st.file_uploader("PRODES (Zip)", type="zip")
    f_c = st.file_uploader("CARs (Zip)", type="zip")
    
    if st.button("Processar") and f_p and f_c:
        try:
            # 1. Limpeza radical
            if os.path.exists("tmp"): shutil.rmtree("tmp")
            os.makedirs("tmp/p", exist_ok=True); os.makedirs("tmp/c", exist_ok=True)
            
            # 2. Extração
            with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
            with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
            
            # 3. Leitura com tratamento de erro
            p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/p") if f.endswith(".shp")][0]
            gp = gpd.read_file(p_shp).to_crs("EPSG:31982")
            
            res = []
            for r, _, fs in os.walk("tmp/c"):
                for f in fs:
                    if f.endswith(".shp"):
                        gc = gpd.read_file(os.path.join(r, f)).to_crs("EPSG:31982")
                        # Interseção
                        inter = gpd.overlay(gc, gp, how='intersection')
                        if not inter.empty:
                            ha = inter.geometry.area.sum() / 10000
                            res.append({"Arquivo": f, "Area_Ha": round(ha, 2)})
            
            st.dataframe(pd.DataFrame(res))
            shutil.rmtree("tmp")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")
