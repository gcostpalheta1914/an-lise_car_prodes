import streamlit as st
import geopandas as gpd
import pandas as pd
import zipfile, os, shutil, io

st.set_page_config(layout="centered")

if "auth" not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    senha = st.text_input("Senha", type="password")
    if senha == "Gab1914.":
        st.session_state.auth = True
        st.rerun()
else:
    st.title("🗺️ Analisador CAR x PRODES")
    f_prodes = st.file_uploader("1. Suba base PRODES (Zip)", type=["zip"])
    f_cars = st.file_uploader("2. Suba base CARs (Zip)", type=["zip"])
    
    if st.button("🚀 Processar"):
        if f_prodes and f_cars:
            try:
                # Criar pastas temporárias
                os.makedirs("t_prodes", exist_ok=True)
                os.makedirs("t_cars", exist_ok=True)
                
                with zipfile.ZipFile(f_prodes, 'r') as z: z.extractall("t_prodes")
                with zipfile.ZipFile(f_cars, 'r') as z: z.extractall("t_cars")
                
                # Achar o arquivo .shp do PRODES
                shp_p = [os.path.join(r, f) for r, d, fs in os.walk("t_prodes") if f.endswith(".shp")][0]
                gdf_p = gpd.read_file(shp_p)
                
                res = []
                for root, _, files in os.walk("t_cars"):
                    for f in files:
                        if f.endswith(".shp"):
                            gdf_c = gpd.read_file(os.path.join(root, f))
                            if gdf_c.crs != gdf_p.crs: gdf_c = gdf_c.to_crs(gdf_p.crs)
                            
                            inter = gpd.overlay(gdf_c, gdf_p, how='intersection')
                            if not inter.empty:
                                area = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                                res.append({"Arquivo": f, "Area_Ha": round(area, 2)})
                
                if res:
                    df = pd.DataFrame(res)
                    st.dataframe(df)
                    st.download_button("📥 Baixar CSV", df.to_csv(index=False), "resultado.csv")
                else:
                    st.warning("Nenhum cruzamento encontrado. Verifique se os arquivos estão na mesma região.")
                
                shutil.rmtree("t_prodes")
                shutil.rmtree("t_cars")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")
        else:
            st.error("Suba os dois arquivos!")
