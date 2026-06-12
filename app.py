import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")

st.title("🗺️ Analisador Geográfico")
f_p = st.file_uploader("PRODES (Zip)", type="zip")
f_c = st.file_uploader("CARs (Zip)", type="zip")

if st.button("Processar"):
    if f_p and f_c:
        with st.spinner("Processando..."):
            try:
                # Limpeza
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                os.makedirs("tmp/p", exist_ok=True)
                os.makedirs("tmp/c", exist_ok=True)
                
                # Extração
                with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
                with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
                
                # Busca recursiva mais robusta
                p_shp = None
                for root, dirs, files in os.walk("tmp/p"):
                    for file in files:
                        if file.endswith(".shp"):
                            p_shp = os.path.join(root, file)
                            break
                
                if not p_shp:
                    st.error("Não achei nenhum arquivo .shp dentro do ZIP do PRODES. Verifique se o arquivo está na raiz do ZIP.")
                else:
                    # Leitura
                    gp = gpd.read_file(p_shp, engine='pyogrio').to_crs("EPSG:31982")
                    res = []
                    
                    for root, dirs, files in os.walk("tmp/c"):
                        for file in files:
                            if file.endswith(".shp"):
                                gc = gpd.read_file(os.path.join(root, file), engine='pyogrio').to_crs("EPSG:31982")
                                inter = gpd.overlay(gc, gp, how='intersection')
                                if not inter.empty:
                                    ha = inter.geometry.area.sum() / 10000
                                    res.append({"Arquivo": file, "Area_Ha": round(ha, 2)})
                    
                    if res:
                        st.dataframe(pd.DataFrame(res))
                    else:
                        st.warning("Nenhuma interseção encontrada.")
                
                shutil.rmtree("tmp")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")
    else:
        st.error("Por favor, suba ambos os arquivos.")
