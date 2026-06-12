import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")

st.title("🗺️ Analisador Geográfico")

f_p = st.file_uploader("Upload PRODES (Zip)", type="zip")
f_c = st.file_uploader("Upload CARs (Zip)", type="zip")

if st.button("Processar"):
    if f_p and f_c:
        with st.spinner("Processando..."):
            os.makedirs("tmp", exist_ok=True)
            with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/prodes")
            with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/cars")
            
            # Localizar shapefile
            p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/prodes") if f.endswith(".shp")][0]
            g_p = gpd.read_file(p_shp)
            
            res = []
            for r, _, fs in os.walk("tmp/cars"):
                for f in fs:
                    if f.endswith(".shp"):
                        g_c = gpd.read_file(os.path.join(r, f))
                        
                        # Alinhamento obrigatório de CRS
                        if g_c.crs != g_p.crs:
                            g_c = g_c.to_crs(g_p.crs)
                            
                        # Interseção
                        inter = gpd.overlay(g_c, g_p, how='intersection')
                        
                        if not inter.empty:
                            area = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                            res.append({"Arquivo": f, "Area_Ha": round(area, 2)})
            
            if res:
                st.dataframe(pd.DataFrame(res))
            else:
                st.warning("Nenhuma interseção encontrada.")
            shutil.rmtree("tmp")
    else:
        st.error("Por favor, suba ambos os arquivos!")
