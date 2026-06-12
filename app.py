import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import re
import io
import gc

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador CAR x PRODES", page_icon="🗺️", layout="centered")

# --- FUNÇÃO DE MONTAGEM ---
def montar_base_prodes_em_tempo_real():
    bytes_totais = bytearray()
    contador_partes = 1
    while os.path.exists(f"prodes_otimizado.parquet.part{contador_partes}"):
        with open(f"prodes_otimizado.parquet.part{contador_partes}", "rb") as f_parte:
            bytes_totais.extend(f_parte.read())
        contador_partes += 1
    if len(bytes_totais) == 0: return None
    try:
        gdf_prodes = gpd.read_parquet(io.BytesIO(bytes_totais), engine='pyogrio')
    except:
        gdf_prodes = gpd.read_parquet(io.BytesIO(bytes_totais))
    coluna_ano = next((col for col in gdf_prodes.columns if 'ano' in col.lower() or 'year' in col.lower()), None)
    if gdf_prodes.crs is None: gdf_prodes.set_crs("EPSG:4674", inplace=True)
    return gdf_prodes, coluna_ano

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u == "gabriel" and p == "Gab1914.":
            st.session_state["autenticado"] = True
            st.rerun()
        else: st.error("Erro")
else:
    st.title("🗺️ Detector de Passivos: CAR vs PRODES")
    cars_file = st.file_uploader("Suba o arquivo CARS.zip", type=["zip"])
    if st.button("🚀 Rodar Cruzamento"):
        if cars_file:
            base_extracao = 'tmp_cars'
            if os.path.exists(base_extracao): shutil.rmtree(base_extracao)
            os.makedirs(base_extracao)
            with open("input.zip", "wb") as f: f.write(cars_file.getbuffer())
            with zipfile.ZipFile("input.zip", 'r') as z: z.extractall(base_extracao)
            
            gdf_prodes, col_ano = montar_base_prodes_em_tempo_real()
            shapes = [os.path.join(r, f) for r, _, fs in os.walk(base_extracao) for f in fs if f.endswith('.shp')]
            
            resultados = []
            for shp in shapes:
                try:
                    gdf_car = gpd.read_file(shp)
                    if gdf_car.crs is None: gdf_car.set_crs("EPSG:4674", inplace=True)
                    gdf_car = gdf_car.to_crs(gdf_prodes.crs)
                    inter = gpd.overlay(gdf_car, gdf_prodes, how='intersection')
                    if not inter.empty:
                        inter['area_ha'] = inter.to_crs(epsg=31982).geometry.area / 10000
                        resultados.append({'CAR': os.path.basename(shp), 'Area_Ha': inter['area_ha'].sum()})
                except: continue
            
            if resultados:
                df = pd.DataFrame(resultados)
                st.dataframe(df)
                nome_arq = "Resultado.xlsx"
                df.to_excel(nome_arq, index=False)
                with open(nome_arq, "rb") as f:
                    st.download_button("📥 Baixar Excel", f, nome_arq)
            else: st.warning("Nenhum dado encontrado.")
            shutil.rmtree(base_extracao)
