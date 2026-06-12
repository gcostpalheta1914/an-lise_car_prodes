import streamlit as st
import geopandas as gpd
import pandas as pd
import zipfile, os, shutil

st.set_page_config(layout="centered")

# Login simples e direto
senha = st.text_input("Senha", type="password")
if senha == "Gab1914.":
    st.title("🗺️ Analisador CAR x PRODES")
    f_prodes = st.file_uploader("1. Suba base PRODES (Zip)", type=["zip"])
    f_cars = st.file_uploader("2. Suba base CARs (Zip)", type=["zip"])
    
    if st.button("🚀 Processar"):
        if f_prodes and f_cars:
            try:
                # Criação das pastas de forma simples
                os.makedirs("t_prodes", exist_ok=True)
                os.makedirs("t_cars", exist_ok=True)
                
                with zipfile.ZipFile(f_prodes, 'r') as z: z.extractall("t_prodes")
                with zipfile.ZipFile(f_cars, 'r') as z: z.extractall("t_cars")
                
                # Localização do SHP (a parte que causou o NameError na sua foto)
                # Adicionamos uma verificação extra para evitar o erro de lista vazia
                shp_files = [os.path.join(r, f) for r, d, fs in os.walk("t_prodes") if f.endswith(".shp")]
                if not shp_files:
                    st.error("Arquivo PRODES inválido: não encontrei .shp lá dentro.")
                else:
                    gdf_p = gpd.read_file(shp_files[0])
                    
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
                    else:
                        st.warning("Nenhum cruzamento encontrado.")
                
                shutil.rmtree("t_prodes")
                shutil.rmtree("t_cars")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")
        else:
            st.error("Suba os dois arquivos!")
elif senha != "":
    st.error("Senha incorreta.")
