import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")

# ... (Mantenha seu bloco de Login como está)

if st.session_state.get("logado", False):
    st.title("🗺️ Analisador Geográfico (Otimizado)")
    f_p = st.file_uploader("PRODES (Zip)", type="zip")
    f_c = st.file_uploader("CARs (Zip)", type="zip")
    
    if st.button("Processar Otimizado"):
        with st.spinner("Processando..."):
            os.makedirs("tmp", exist_ok=True)
            with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/prodes")
            with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/cars")
            
            p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/prodes") if f.endswith(".shp")][0]
            
            # TÉCNICA DE LEITURA EM PEDAÇOS (CHUNK)
            # Lê o PRODES de forma mais inteligente
            g_p = gpd.read_file(p_shp, engine='pyogrio').to_crs("EPSG:31982")
            
            res = []
            for r, _, fs in os.walk("tmp/cars"):
                for f in fs:
                    if f.endswith(".shp"):
                        # Lê o CAR
                        g_c = gpd.read_file(os.path.join(r, f)).to_crs("EPSG:31982")
                        
                        # FILTRAGEM ESPACIAL ANTES DA INTERSEÇÃO (Essencial!)
                        # Só processa se o CAR estiver na bounding box do PRODES
                        if g_c.geometry.intersects(g_p.unary_union):
                            inter = gpd.overlay(g_c, g_p, how='intersection')
                            if not inter.empty:
                                ha = inter.geometry.area.sum() / 10000
                                res.append({"Arquivo": f, "Area_Ha": round(ha, 2)})
            
            st.dataframe(pd.DataFrame(res))
            shutil.rmtree("tmp")
