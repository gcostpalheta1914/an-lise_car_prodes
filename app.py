import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")
st.title("🗺️ Detector de Passivos: CAR vs PRODES")

f_c = st.file_uploader("1. Suba o arquivo dos CARs (CARS.zip)", type="zip")
f_p = st.file_uploader("2. Suba o arquivo do PRODES (PRODES_2008_A_2023.zip)", type="zip")

def extrair_tudo(caminho_zip, pasta_destino):
    """Extrai arquivos ZIP e descompacta qualquer ZIP interno encontrado."""
    os.makedirs(pasta_destino, exist_ok=True)
    with zipfile.ZipFile(caminho_zip, 'r') as z:
        z.extractall(pasta_destino)
    
    # Verifica se existem sub-zips e extrai
    for root, _, files in os.walk(pasta_destino):
        for file in files:
            if file.endswith(".zip"):
                caminho_subzip = os.path.join(root, file)
                try:
                    with zipfile.ZipFile(caminho_subzip, 'r') as z:
                        z.extractall(root)
                except:
                    pass

if st.button("🚀 Processar"):
    if f_c and f_p:
        with st.spinner("Descompactando e analisando..."):
            try:
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                
                # Extração profunda
                extrair_tudo(f_p, "tmp/p")
                extrair_tudo(f_c, "tmp/c")
                
                # Acha o PRODES
                p_path = None
                for r, _, fs in os.walk("tmp/p"):
                    for f in fs:
                        if f.endswith(".shp"):
                            p_path = os.path.join(r, f)
                            break
                
                g_p = gpd.read_file(p_path, engine='pyogrio').to_crs("EPSG:31982")
                
                res = []
                # Processa CARs
                for r, _, fs in os.walk("tmp/c"):
                    for f in fs:
                        if f.endswith(".shp"):
                            g_c = gpd.read_file(os.path.join(r, f), engine='pyogrio').to_crs("EPSG:31982")
                            inter = gpd.overlay(g_c, g_p, how='intersection')
                            
                            if not inter.empty:
                                anos = ", ".join(inter['view_date'].astype(str).unique())
                                ha = inter.geometry.area.sum() / 10000
                                res.append({"Identificador": f, "Anos": anos, "Area_Ha": round(ha, 2)})
                            else:
                                res.append({"Identificador": f, "Anos": "Sem PRODES", "Area_Ha": 0})
                
                st.table(pd.DataFrame(res))
                shutil.rmtree("tmp")
            except Exception as e:
                st.error(f"Erro: {e}")
    else:
        st.warning("Suba os arquivos.")
