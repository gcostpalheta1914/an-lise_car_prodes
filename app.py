import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

# Aumentar limite de upload para o Streamlit (caso necessário)
st.set_page_config(layout="wide")
st.title("🗺️ Analisador PRODES Pará (Base Completa)")

f_c = st.file_uploader("Suba o arquivo do CAR (ZIP)", type="zip")
f_p = st.file_uploader("Suba o PRODES Pará (ZIP)", type="zip")

if st.button("🚀 Processar Base Completa"):
    if f_c and f_p:
        with st.spinner("Lendo base completa... (Isso pode demorar um pouco)"):
            try:
                # Extração
                if os.path.exists("tmp"): shutil.rmtree("tmp")
                os.makedirs("tmp", exist_ok=True)
                
                # Descompacta tudo na pasta tmp
                with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/p")
                with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/c")
                
                # Busca recursiva pelos SHPs
                def get_shp(path):
                    for r, _, fs in os.walk(path):
                        for f in fs:
                            if f.endswith(".shp"): return os.path.join(r, f)
                    return None
                
                shp_p = get_shp("tmp/p")
                shp_c = get_shp("tmp/c")
                
                # Leitura ultra-otimizada
                g_p = gpd.read_file(shp_p, engine='pyogrio')
                g_c = gpd.read_file(shp_c, engine='pyogrio').to_crs(g_p.crs)
                
                # Cruzamento Espacial (Overlay)
                resultado = gpd.overlay(g_c, g_p, how='intersection')
                
                # Exibição da tabela final
                st.table(resultado.head(20))
                
                st.success("Processamento concluído!")
                shutil.rmtree("tmp")
                
            except Exception as e:
                st.error(f"O servidor atingiu o limite de memória. Tente processar uma área menor ou verifique a estrutura do ZIP. Erro: {e}")
