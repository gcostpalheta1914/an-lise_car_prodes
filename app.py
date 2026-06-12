import streamlit as st
import os, zipfile, shutil, geopandas as gpd, pandas as pd, io

st.set_page_config(page_title="Detector CAR", layout="centered")

def carregar_prodes():
    b = bytearray()
    i = 1
    while os.path.exists(f"prodes_otimizado.parquet.part{i}"):
        with open(f"prodes_otimizado.parquet.part{i}", "rb") as f: b.extend(f.read())
        i += 1
    return gpd.read_parquet(io.BytesIO(b)) if b else None

if "login" not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    if st.text_input("Senha", type="password") == "Gab1914.":
        st.session_state.login = True
        st.rerun()
else:
    file = st.file_uploader("Suba o CARS.zip")
    if file and st.button("Processar"):
        base = 'tmp'
        if os.path.exists(base): shutil.rmtree(base)
        os.makedirs(base)
        with zipfile.ZipFile(file, 'r') as z: z.extractall(base)
        
        prodes = carregar_prodes()
        prodes = prodes.to_crs("EPSG:4674") # Garante SIRGAS 2000
        
        res = []
        for root, _, files in os.walk(base):
            for f in files:
                if f.endswith(".shp"):
                    try:
                        car = gpd.read_file(os.path.join(root, f))
                        car = car.to_crs("EPSG:4674")
                        # Cruzamento forçado
                        inter = gpd.overlay(car, prodes, how='intersection')
                        if not inter.empty:
                            area = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                            res.append({'Arquivo': f, 'Hectares': round(area, 2)})
                    except: continue
        
        if res:
            st.dataframe(pd.DataFrame(res))
        else:
            st.error("Nenhuma intersecção encontrada. Verifique se os arquivos estão na mesma zona geográfica.")
        shutil.rmtree(base)
