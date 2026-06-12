import streamlit as st
import os, zipfile, shutil, geopandas as gpd, pandas as pd, io

st.set_page_config(page_title="Mapeamento CAR x PRODES", layout="wide")

# --- LOGIN ---
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Acesso")
    if st.text_input("Senha", type="password") == "Gab1914.":
        st.session_state.auth = True
        st.rerun()
else:
    st.title("🗺️ Analisador Geográfico: CAR vs PRODES")
    st.markdown("Nesta versão, você faz o upload de ambas as bases para garantir precisão total.")

    col1, col2 = st.columns(2)
    with col1:
        prodes_file = st.file_uploader("1. Suba a base PRODES (.zip ou .parquet)", type=["zip", "parquet"])
    with col2:
        cars_file = st.file_uploader("2. Suba os CARs (.zip)", type=["zip"])

    if st.button("🚀 Iniciar Cruzamento de Dados"):
        if prodes_file and cars_file:
            try:
                # 1. Preparação de pastas
                for p in ['tmp_prodes', 'tmp_cars']:
                    if os.path.exists(p): shutil.rmtree(p)
                    os.makedirs(p)

                # 2. Carregando PRODES
                with st.spinner("Lendo base PRODES..."):
                    if prodes_file.name.endswith(".parquet"):
                        gdf_prodes = gpd.read_parquet(prodes_file)
                    else:
                        with zipfile.ZipFile(prodes_file, 'r') as z: z.extractall('tmp_prodes')
                        # Acha o .shp dentro do zip do prodes
                        shp_prodes = [os.path.join(r, f) for r,d,fs in os.walk('tmp_prodes') if f.endswith('.shp')][0]
                        gdf_prodes = gpd.read_file(shp_prodes)
                    
                    if gdf_prodes.crs is None: gdf_prodes.set_crs("EPSG:4674", inplace=True)
                    gdf_prodes = gdf_prodes.to_crs("EPSG:4674")
                    gdf_prodes['geometry'] = gdf_prodes.geometry.make_valid()

                # 3. Carregando e Cruzando CARs
                with zipfile.ZipFile(cars_file, 'r') as z: z.extractall('tmp_cars')
                shapes_cars = [os.path.join(r, f) for r,d,fs in os.walk('tmp_cars') if f.endswith('.shp')]
                
                resultados = []
                progresso = st.progress(0)
                
                for idx, shp_path in enumerate(shapes_cars):
                    try:
                        gdf_car = gpd.read_file(shp_path)
                        if gdf_car.crs is None: gdf_car.set_crs("EPSG:4674", inplace=True)
                        gdf_car = gdf_car.to_
