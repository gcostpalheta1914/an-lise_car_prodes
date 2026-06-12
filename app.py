import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="wide")
st.title("🗺️ Detector de Passivos: CAR vs PRODES")

f_c = st.file_uploader("1. Suba o arquivo dos CARs (CARS.zip)", type="zip")
f_p = st.file_uploader("2. Suba o arquivo do PRODES (PRODES_2008_A_2023.zip)", type="zip")

if st.button("🚀 Processar Cruzamento Espacial"):
    if f_c and f_p:
        with st.spinner("Buscando e processando arquivos..."):
            try:
                # 1. Limpeza radical
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                os.makedirs("tmp/p", exist_ok=True)
                os.makedirs("tmp/c", exist_ok=True)
                
                # 2. Extração
                with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
                with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
                
                # 3. Função para achar o primeiro .shp em qualquer lugar
                def achar_shp(pasta):
                    for raiz, _, arquivos in os.walk(pasta):
                        for file in arquivos:
                            if file.endswith(".shp"):
                                return os.path.join(raiz, file)
                    return None

                p_path = achar_shp("tmp/p")
                g_p = gpd.read_file(p_path, engine='pyogrio').to_crs("EPSG:31982")
                
                res = []
                # 4. Achar TODOS os .shp de CAR dentro das subpastas
                for raiz, _, arquivos in os.walk("tmp/c"):
                    for file in arquivos:
                        if file.endswith(".shp"):
                            caminho_c = os.path.join(raiz, file)
                            g_c = gpd.read_file(caminho_c, engine='pyogrio').to_crs("EPSG:31982")
                            
                            inter = gpd.overlay(g_c, g_p, how='intersection')
                            
                            if not inter.empty:
                                anos = ", ".join(inter['view_date'].astype(str).unique())
                                ha = inter.geometry.area.sum() / 10000
                                res.append({"Identificador_do_CAR": file, "Anos_com_Incidência_PRODES": anos, "Area_Total_PRODES_Ha": round(ha, 2)})
                            else:
                                res.append({"Identificador_do_CAR": file, "Anos_com_Incidência_PRODES": "Sem PRODES", "Area_Total_PRODES_Ha": 0})
                
                # 5. Exibição
                df_final = pd.DataFrame(res)
                st.table(df_final)
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar Planilha Excel Oficial", csv, "resultado.csv", "text/csv")
                
                shutil.rmtree("tmp")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
    else:
        st.warning("Por favor, suba os dois arquivos.")
