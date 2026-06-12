import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="centered")

if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u.strip() == "gabriel" and p.strip() == "Gab1914.":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    st.title("🗺️ Analisador Geográfico")
    f_p = st.file_uploader("Upload PRODES (Zip)", type="zip")
    f_c = st.file_uploader("Upload CARs (Zip)", type="zip")
    
    # A LÓGICA DE PROCESSAMENTO ESTÁ AQUI
    if st.button("Processar"):
        if f_p and f_c:
            with st.spinner("Calculando interseções... aguarde."):
                try:
                    os.makedirs("data", exist_ok=True)
                    with zipfile.ZipFile(f_p, 'r') as z: z.extractall("data/prodes")
                    with zipfile.ZipFile(f_c, 'r') as z: z.extractall("data/cars")
                    
                    # Carrega PRODES
                    p_shp = [os.path.join(r, f) for r, _, fs in os.walk("data/prodes") if f.endswith(".shp")][0]
                    g_p = gpd.read_file(p_shp)
                    
                    # Carrega e cruza CARs
                    res = []
                    for r, _, fs in os.walk("data/cars"):
                        for f in fs:
                            if f.endswith(".shp"):
                                g_c = gpd.read_file(os.path.join(r, f))
                                if g_c.crs != g_p.crs: g_c = g_c.to_crs(g_p.crs)
                                int_ = gpd.overlay(g_c, g_p, how='intersection')
                                if not int_.empty:
                                    ha = int_.to_crs("EPSG:31982").geometry.area.sum() / 10000
                                    res.append({"Arquivo": f, "Ha": round(ha, 2)})
                    
                    if res:
                        st.dataframe(pd.DataFrame(res))
                        st.success("Cálculo finalizado!")
                    else:
                        st.warning("Nenhuma interseção encontrada.")
                    
                    shutil.rmtree("data")
                except Exception as e:
                    st.error(f"Erro técnico: {e}")
        else:
            st.error("Por favor, suba os dois arquivos primeiro!")
