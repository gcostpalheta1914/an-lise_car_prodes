import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import re
from shapely.geometry import box

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador CAR x PRODES", page_icon="🗺️", layout="centered")

# --- SISTEMA DE LOGIN DIRETO E SEGURO ---
def verificar_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if st.session_state["autenticado"]:
        return True

    st.title("🔒 Acesso ao Sistema")
    st.markdown("Por favor, insira suas credenciais de administrador para acessar a ferramenta.")
    usuario_input = st.text_input("Usuário", key="user_input")
    senha_input = st.text_input("Senha", type="password", key="password_input")
    
    if st.button("Entrar"):
        if usuario_input == "gabriel" and senha_input == "Gab1914.":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")
    return False

# --- VERIFICAÇÃO DE ACESSO ---
if verificar_login():
    st.sidebar.title("👋 Bem-vindo, Gabriel!")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["autenticado"] = False
        st.rerun()

    st.title("🗺️ Detector de Passivos: CAR vs PRODES")
    st.markdown("Preencha os campos para rodar o cruzamento automático espacial.")

    # Exibe os dois campos na tela de forma otimizada
    cars_file = st.file_uploader("1. Suba o arquivo dos CARs (CARS.zip)", type=["zip"])
    prodes_file = st.file_uploader("2. Suba o arquivo do PRODES (PRODES_2008_A_2023.zip) — Apenas se for a primeira vez na sessão", type=["zip"])

    if st.button("🚀 Processar Cruzamento Espacial"):
        if cars_file is not None:
            base_extracao = 'tmp_cars_extracao'
            pasta_shapes_finais = 'tmp_shapes_prontos'
            pasta_prodes_memoria = 'tmp_prodes_memoria'
            
            for p in [base_extracao, pasta_shapes_finais]:
                if os.path.exists(p): shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)
                
            with st.spinner("📦 Extraindo arquivos dos CARs..."):
                with open("cars_input.zip", "wb") as f:
                    f.write(cars_file.getbuffer())
                with zipfile.ZipFile("cars_input.zip", 'r') as z:
                    z.extractall(base_extracao)

                for raiz, _, arquivos in os.walk(base_extracao):
                    match_car = re.search(r'(PA-\d{7}-[A-F0-9]+)', raiz, re.IGNORECASE)
                    if match_car:
                        codigo_car = match_car.group(1)
                        for arquivo in arquivos:
                            if "área do imóvel" in arquivo.lower() or arquivo.endswith('.zip'):
                                try:
                                    with zipfile.ZipFile(os.path.join(raiz, arquivo), 'r') as sub_zip:
                                        for f_interno in sub_zip.namelist():
                                            ext = os.path.splitext(f_interno)[1].lower()
                                            if ext in ['.shp', '.shx', '.dbf', '.prj']:
                                                nome_final = f"{codigo_car}{ext}"
                                                with sub_zip.open(f_interno) as z_in, open(os.path.join(pasta_shapes_finais, nome_final), 'wb') as f_out:
                                                    shutil.copyfileobj(z_in, f_out)
                                except: pass

            shapes_cars = [f for f in os.listdir(pasta_shapes_finais) if f.endswith('.shp')]
            
            if not shapes_cars:
                st.error("❌ Nenhum polígono de CAR válido foi encontrado dentro do ZIP.")
            else:
                with st.spinner("🗺️ Alinhando base cartográfica do PRODES..."):
                    
                    # Se o usuário subiu o PRODES agora, salva na pasta persistente do servidor
                    if prodes_file is not None:
                        if os.path.exists(pasta_prodes_memoria): shutil.rmtree(pasta_prodes_memoria)
                        os.makedirs(pasta_prodes_memoria, exist_ok=True)
                        with open("prodes_temp.zip", "wb") as f:
                            f.write(prodes_file.getbuffer())
                        with zipfile.ZipFile("prodes_temp.zip", 'r') as z:
                            z.extractall(pasta_prodes_memoria)
                        if os.path.exists("prodes_temp.zip"): os.remove("prodes_temp.zip")

                    caminho_shp_prodes = os.path.join(pasta_prodes_memoria, 'PRODES_2008_A_2023.shp')

                    if not os.path.exists(caminho_shp_prodes):
                        st.error("⚠️ O arquivo do PRODES não está carregado. Por favor, faça o upload do 'PRODES_2008_A_2023.zip' neste primeiro cruzamento.")
                    else:
                        lista_gdfs = []
                        for shp in shapes_cars:
                            try: lista_gdfs.append(gpd.read_file(os.path.join(pasta_shapes_finais, shp)))
                            except: pass
                        
                        gdf_todos_cars = pd.concat(lista_gdfs, ignore_index=True)
                        if gdf_todos_cars.crs is None: gdf_todos_cars.set_crs("EPSG:4674", inplace=True)
                        
                        gdf_prodes_real = gpd.read_file(caminho_shp_prodes, bbox=box(*gdf_todos_cars.total_bounds))
                        if gdf_prodes_real.crs is None: gdf_prodes_real.set_crs("EPSG:4674", inplace=True)
                        if gdf_prodes_real.crs != gdf_todos_cars.crs:
                            gdf_prodes_real = gdf_prodes_real.to_crs(gdf_todos_cars.crs)
                        
                        linhas_brutas = []
                        coluna_ano_prodes = next((col for col in gdf_prodes_real.columns if col.lower() in ['ano', 'year', 'class_name', 'class']), None)
                        
                        for shp in shapes_cars:
                            car_id_limpo = shp.replace('.shp', '')
                            try:
                                gdf_imovel = gpd.read_file(os.path.join(pasta_shapes_finais, shp))
                                if gdf_imovel.crs is None: gdf_imovel.set_crs("EPSG:4674", inplace=True)
                                
                                intersecao = gpd.overlay(gdf_imovel, gdf_prodes_real, how='intersection')
                                if not intersecao.empty:
                                    intersecao_utm = intersecao.to_crs(epsg=31981)
                                    intersecao['area_ha'] = intersecao_utm.geometry.area / 10000
                                    for _, row in intersecao.iterrows():
                                        ano_val = int(re.findall(r'\d+', str(row[coluna_ano_prodes]))[0]) if coluna_ano_prodes and re.findall(r'\d+', str(row[coluna_ano_prodes])) else "Inconclusivo"
                                        linhas_brutas.append({'Identificador_do_CAR': car_id_limpo, 'Ano': ano_val, 'Area': row['area_ha']})
                                else:
                                    linhas_brutas.append({'Identificador_do_CAR': car_id_limpo, 'Ano': 'Sem PRODES', 'Area': 0.0})
                            except: pass
                        
                        df_bruto = pd.DataFrame(linhas_brutas)
                        linhas_finais = []
                        for car_id, group in df_bruto.groupby('Identificador_do_CAR'):
                            anos_validos = group[~group['Ano'].isin(['Sem PRODES', 'Erro na análise'])]
                            if not anos_validos.empty:
                                texto_anos = ", ".join(sorted(list(set(anos_validos['Ano'].astype(str)))))
                                area_total = round(anos_validos['Area'].sum(), 2)
                            else:
                                texto_anos = 'Sem PRODES'
                                area_total = 0.0
                            linhas_finais.append({'Identificador_do_CAR': car_id, 'Anos_com_Incidencia_PRODES': texto_anos, 'Area_Total_PRODES_HA': area_total})
                        
                        df_final = pd.DataFrame(linhas_finais).sort_values(by='Identificador_do_CAR')
                        
                        st.success("🎉 Processamento concluído!")
                        st.dataframe(df_final)
                        
                        nome_saida = 'Relatorio_PRODES_Automatico.xlsx'
                        df_final.to_excel(nome_saida, index=False)
                        with open(nome_saida, "rb") as file:
                            st.download_button(label="📥 Baixar Planilha Excel Oficial", data=file, file_name=nome_saida, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            for p in [base_extracao, pasta_shapes_finais, "cars_input.zip"]:
                if os.path.exists(p): shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        else:
            st.warning("⚠️ Por favor, insira o arquivo CARS.zip.")
