import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Analisador CAR x PRODES", layout="centered")

def carregar_prodes():
    # Carrega as partes do PRODES da raiz
    bytes_totais = bytearray()
    i = 1
    while os.path.exists(f"prodes_otimizado.parquet.part{i}"):
        with open(f"prodes_otimizado.parquet.part{i}", "rb") as f: bytes_totais.extend(f.read())
        i += 1
    if not bytes_totais: return None
    gdf = gpd.read_parquet(io.BytesIO(bytes_totais))
    # Força Geometria Válida e CRS SIRGAS 2000
    gdf['geometry'] = gdf.geometry.make_valid()
    if gdf.crs is None: gdf.set_crs("EPSG:4674", inplace=True)
    return gdf

# --- UI ---
st.title("🗺️ Detector de Passivos (Alta Precisão)")
file = st.file_uploader("Suba o CARS.zip", type=["zip"])

if st.button("🚀 Rodar Processamento"):
    if file:
        base = 'tmp_data'
        if os.path.exists(base): shutil.rmtree(base)
        os.makedirs(base)
        
        with open("input.zip", "wb") as f: f.write(file.getbuffer())
        with zipfile.ZipFile("input.zip", 'r') as z: z.extractall(base)
        
        with st.spinner("Carregando e validando dados..."):
            gdf_prodes = carregar_prodes()
        
        resultados = []
        # Procura arquivos .shp recursivamente
        for root, dirs, files in os.walk(base):
            for name in files:
                if name.endswith(".shp"):
                    try:
                        gdf_car = gpd.read_file(os.path.join(root, name))
                        gdf_car['geometry'] = gdf_car.geometry.make_valid()
                        if gdf_car.crs is None: gdf_car.set_crs("EPSG:4674", inplace=True)
                        
                        # Alinha o CRS
                        gdf_car = gdf_car.to_crs(gdf_prodes.crs)
                        
                        # Realiza o cruzamento
                        inter = gpd.overlay(gdf_car, gdf_prodes, how='intersection')
                        
                        if not inter.empty:
                            # Calcula área em Hectares usando projeção UTM local
                            # Centroide para estimativa de zona UTM
                            lon = gdf_car.geometry.centroid.x.iloc[0]
                            zona = int((lon + 180) / 6) + 1
                            epsg_utm = f"3198{zona}" # Hemisfério Sul
                            
                            area_ha = inter.to_crs(epsg=int(epsg_utm)).geometry.area.sum() / 10000
                            resultados.append({'CAR': name, 'Area_Ha': round(area_ha, 4)})
                    except: continue
        
        if resultados:
            df = pd.DataFrame(resultados)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Resultado", csv, "resultado.csv", "text/csv")
        else:
            st.warning("Nenhum dado cruzado. Verifique se os shapes estão na pasta correta ou se os polígonos se sobrepõem geograficamente.")
        
        shutil.rmtree(base)
