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
        with st.spinner("Alinhando base cartográfica do PRODES..."):
            try:
                # Limpeza de segurança
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                os.makedirs("tmp/p", exist_ok=True)
                os.makedirs("tmp/c", exist_ok=True)
                
                # Extração
                with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
                with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
                
                # Leitura inteligente do PRODES
                p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/p") if f.endswith(".shp")][0]
                g_p = gpd.read_file(p_shp, engine='pyogrio').to_crs("EPSG:31982")
                
                res = []
                for r, _, fs in os.walk("tmp/c"):
                    for f in fs:
                        if f.endswith(".shp"):
                            g_c = gpd.read_file(os.path.join(r, f), engine='pyogrio').to_crs("EPSG:31982")
                            inter = gpd.overlay(g_c, g_p, how='intersection')
                            
                            if not inter.empty:
                                anos = ", ".join(inter['view_date'].astype(str).unique())
                                ha = inter.geometry.area.sum() / 10000
                                res.append({"Identificador_do_CAR": f, "Anos_com_Incidência": anos, "Area_Total_Ha": round(ha, 2)})
                            else:
                                res.append({"Identificador_do_CAR": f, "Anos_com_Incidência": "Sem PRODES", "Area_Total_Ha": 0})
                
                df_final = pd.DataFrame(res)
                st.table(df_final)
                
                # Botão de download
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Baixar Planilha Oficial", csv, "resultado.csv", "text/csv")
                
                shutil.rmtree("tmp")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
    else:
        st.warning("Por favor, suba os dois arquivos.")
