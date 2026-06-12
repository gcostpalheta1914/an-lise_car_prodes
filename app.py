import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import io
import gc

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Analisador CAR x PRODES", layout="centered")

def montar_base_prodes():
    bytes_totais = bytearray()
    i = 1
    while os.path.exists(f"prodes_otimizado.parquet.part{i}"):
        with open(f"prodes_otimizado.parquet.part{i}", "rb") as f: bytes_totais.extend(f.read())
        i += 1
    if not bytes_totais: return None
    gdf = gpd.read_parquet(io.BytesIO(bytes_totais))
    if gdf.crs is None: gdf.set_crs("EPSG:4674", inplace=True)
    return gdf

# --- UI ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "gabriel" and p == "Gab1914.":
            st.session_state["autenticado"] = True
            st.rerun()
else:
    st.title("🗺️ Detector de Passivos (Alta Precisão)")
    file = st.file_uploader("Suba o CARS.zip", type=["zip"])
    
    if st.button("🚀 Rodar Processamento"):
        if file:
            base = 'tmp_data'
            if os.path.exists(base): shutil.rmtree(base)
            os.makedirs(base)
            
            with open("input.zip", "wb") as f: f.write(file.getbuffer())
            with zipfile.ZipFile("input.zip", 'r') as z: z.extractall(base)
            
            with st.spinner("Carregando PRODES..."):
                gdf_prodes = montar_base_prodes()
            
            resultados = []
            # Varredura recursiva para achar todos os .shp
            for root, dirs, files in os.walk(base):
                for name in files:
                    if name.endswith(".shp"):
                        path = os.path.join(root, name)
                        try:
                            gdf_car = gpd.read_file(path)
                            if gdf_car.crs is None: gdf_car.set_crs("EPSG:4674", inplace=True)
                            gdf_car = gdf_car.to_crs(gdf_prodes.crs)
                            
                            inter = gpd.overlay(gdf_car, gdf_prodes, how='intersection')
                            if not inter.empty:
                                inter['area_ha'] = inter.to_crs(epsg=31982).geometry.area / 10000
                                resultados.append({'CAR': name, 'Area_Ha': round(inter['area_ha'].sum(), 4)})
                        except Exception as e:
                            continue
            
            if resultados:
                df = pd.DataFrame(resultados)
                st.dataframe(df)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar CSV", csv, "resultado.csv", "text/csv")
            else:
                st.warning("Nenhum dado cruzado. Verifique se os polígonos coincidem.")
            
            shutil.rmtree(base)
            os.remove("input.zip")
