import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import io
import gc

# Configuração de performance
st.set_page_config(page_title="Detector de Passivos", layout="wide")

# Função Otimizada para carregar PRODES em partes
def carregar_prodes():
    bytes_totais = bytearray()
    i = 1
    while os.path.exists(f"prodes_otimizado.parquet.part{i}"):
        with open(f"prodes_otimizado.parquet.part{i}", "rb") as f:
            bytes_totais.extend(f.read())
        i += 1
    if not bytes_totais: return None
    gdf = gpd.read_parquet(io.BytesIO(bytes_totais))
    if gdf.crs is None: gdf.set_crs("EPSG:4674", inplace=True)
    return gdf

# Controle de Acesso
if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    senha = st.text_input("Senha", type="password")
    if senha == "Gab1914.":
        st.session_state.auth = True
        st.rerun()
else:
    st.title("🗺️ Detector de Passivos: CAR vs PRODES")
    arquivo = st.file_uploader("Suba o arquivo CARS.zip", type=["zip"])
    
    if arquivo and st.button("🚀 Rodar Cruzamento"):
        try:
            # Limpeza inicial
            if os.path.exists("tmp"): shutil.rmtree("tmp")
            os.makedirs("tmp")
            
            with open("temp.zip", "wb") as f: f.write(arquivo.getbuffer())
            with zipfile.ZipFile("temp.zip", "r") as z: z.extractall("tmp")
            
            with st.spinner("Carregando bases..."):
                prodes = carregar_prodes()
            
            resultados = []
            for root, _, files in os.walk("tmp"):
                for file in files:
                    if file.endswith(".shp"):
                        try:
                            car = gpd.read_file(os.path.join(root, file))
                            if car.crs is None: car.set_crs("EPSG:4674", inplace=True)
                            car = car.to_crs(prodes.crs)
                            
                            # Interseção
                            inter = gpd.overlay(car, prodes, how='intersection')
                            if not inter.empty:
                                area = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                                resultados.append({"Arquivo": file, "Area_Ha": round(area, 2)})
                        except: continue
            
            if resultados:
                df = pd.DataFrame(resultados)
                st.dataframe(df)
                st.download_button("📥 Baixar CSV", df.to_csv(index=False), "resultado.csv", "text/csv")
            else:
                st.warning("Nenhum cruzamento encontrado. Verifique a compatibilidade geográfica.")
        
        finally:
            if os.path.exists("tmp"): shutil.rmtree("tmp")
            if os.path.exists("temp.zip"): os.remove("temp.zip")
            gc.collect()
