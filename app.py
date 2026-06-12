import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

st.set_page_config(layout="centered")

# Inicializa o estado de login
if "logado" not in st.session_state:
    st.session_state.logado = False

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("🔐 Login no Sistema")
    st.subheader("Por favor, insira suas credenciais abaixo")
    
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if usuario == "gabriel" and senha == "Gab1914.":
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos!")
else:
    # --- TELA PRINCIPAL ---
    st.title("🗺️ Analisador Geográfico CAR x PRODES")
    st.write(f"Bem-vindo, gabriel!") # Aqui aparece o nome do usuário
    
    f_p = st.file_uploader("Upload PRODES (Zip)", type="zip")
    f_c = st.file_uploader("Upload CARs (Zip)", type="zip")
    
    if st.button("Processar"):
        if f_p and f_c:
            with st.spinner("Processando dados..."):
                os.makedirs("data", exist_ok=True)
                with zipfile.ZipFile(f_p, 'r') as z: z.extractall("data/prodes")
                with zipfile.ZipFile(f_c, 'r') as z: z.extractall("data/cars")
                
                # Acha o arquivo SHP do PRODES
                try:
                    p_shp = [os.path.join(r, f) for r, _, fs in os.walk("data/prodes") if f.endswith(".shp")][0]
                    g_p = gpd.read_file(p_shp)
                    
                    res = []
                    for r, _, fs in os.walk("data/cars"):
                        for f in fs:
                            if f.endswith(".shp"):
                                g_c = gpd.read_file(os.path.join(r, f))
                                if g_c.crs != g_p.crs: g_c = g_c.to_crs(g_p.crs)
                                int_ = gpd.overlay(g_c, g_p, how='intersection')
                                if not int_.empty:
                                    ha = int_.to_crs("EPSG:31982").geometry.area.sum() / 10000
                                    res.append({"Arquivo": f, "Ha": round(ha, 2)})
                    
                    if res:
                        st.dataframe(pd.DataFrame(res))
                    else:
                        st.warning("Nenhuma interseção encontrada.")
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")
                
                shutil.rmtree("data")
        else:
            st.error("Suba os dois arquivos!")
