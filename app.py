import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")

# Inicializa o estado de login
if "logado" not in st.session_state:
    st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "gabriel" and p == "Gab1914.":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")
else:
    st.title("🗺️ Analisador Geográfico")
    f_p = st.file_uploader("Upload PRODES (Zip)", type="zip")
    f_c = st.file_uploader("Upload CARs (Zip)", type="zip")
    
    if st.button("Processar"):
        if f_p and f_c:
            with st.spinner("Processando..."):
                try:
                    # Limpeza total de pastas temporárias
                    if os.path.exists("tmp"): shutil.rmtree("tmp")
                    os.makedirs("tmp/prodes", exist_ok=True)
                    os.makedirs("tmp/cars", exist_ok=True)
                    
                    with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/prodes")
                    with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/cars")
                    
                    # Identificar o .shp do PRODES
                    shp_path = None
                    for root, _, files in os.walk("tmp/prodes"):
                        for file in files:
                            if file.endswith(".shp"):
                                shp_path = os.path.join(root, file)
                                break
                    
                    if not shp_path:
                        st.error("Arquivo .shp do PRODES não encontrado.")
                    else:
                        # LEITURA OTIMIZADA: Lê apenas a geometria do PRODES
                        g_p = gpd.read_file(shp_path, engine='pyogrio').to_crs("EPSG:31982")
                        
                        res = []
                        # Processar CARs um por um
                        for root, _, files in os.walk("tmp/cars"):
                            for file in files:
                                if file.endswith(".shp"):
                                    g_c = gpd.read_file(os.path.join(root, file)).to_crs("EPSG:31982")
                                    # Interseção
                                    inter = gpd.overlay(g_c, g_p, how='intersection')
                                    if not inter.empty:
                                        ha = inter.geometry.area.sum() / 10000
                                        res.append({"Arquivo": file, "Area_Ha": round(ha, 2)})
                        
                        if res:
                            st.dataframe(pd.DataFrame(res))
                        else:
                            st.warning("Nenhuma interseção encontrada.")
                    
                    shutil.rmtree("tmp")
                except Exception as e:
                    st.error(f"Erro crítico: {e}")
        else:
            st.error("Por favor, suba ambos os arquivos!")
