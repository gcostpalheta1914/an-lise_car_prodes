import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil, gc

st.set_page_config(layout="centered")

if "logado" not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🔐 Acesso")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if u.strip() == "gabriel" and p.strip() == "Gab1914.":
            st.session_state.logado = True
            st.rerun()
        else: st.error("Erro no login")
else:
    st.title("🗺️ Analisador de Passivos (Preciso)")
    f_p = st.file_uploader("PRODES (.zip)", type="zip")
    f_c = st.file_uploader("CARs (.zip)", type="zip")
    
    if st.button("Processar Dados"):
        if f_p and f_c:
            with st.spinner("Calculando interseção..."):
                try:
                    os.makedirs("tmp", exist_ok=True)
                    with zipfile.ZipFile(f_p, 'r') as z: z.extractall("tmp/prodes")
                    with zipfile.ZipFile(f_c, 'r') as z: z.extractall("tmp/cars")
                    
                    # Leitura precisa
                    p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/prodes") if f.endswith(".shp")][0]
                    g_p = gpd.read_file(p_shp)
                    
                    res = []
                    for r, _, fs in os.walk("tmp/cars"):
                        for f in fs:
                            if f.endswith(".shp"):
                                g_c = gpd.read_file(os.path.join(r, f))
                                # Garante alinhamento CRS e Geometria
                                g_c = g_c.to_crs(g_p.crs)
                                g_c['geometry'] = g_c.geometry.make_valid()
                                g_p['geometry'] = g_p.geometry.make_valid()
                                
                                inter = gpd.overlay(g_c, g_p, how='intersection')
                                if not inter.empty:
                                    # Cálculo em Hectares com projeção UTM
                                    area = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                                    res.append({"Arquivo": f, "Area_Ha": round(area, 2)})
                    
                    if res:
                        st.dataframe(pd.DataFrame(res))
                        st.success("Cruzamento finalizado com sucesso!")
                    else:
                        st.warning("Nenhuma interseção encontrada.")
                    
                    shutil.rmtree("tmp")
                    gc.collect()
                except Exception as e:
                    st.error(f"Erro no processamento: {e}")
        else:
            st.error("Suba ambos os arquivos.")
