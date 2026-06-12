import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador CAR x PRODES (Fixo)", page_icon="🗺️", layout="centered")

# --- SISTEMA DE LOGIN ---
def verificar_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False
    if st.session_state["autenticado"]:
        return True

    st.title("🔒 Acesso ao Sistema")
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
    st.sidebar.title("👋 Olá, Gabriel!")
    if st.sidebar.button("Sair do Sistema"):
        st.session_state["autenticado"] = False
        st.rerun()

    st.title("🗺️ Detector de Passivos: CAR vs PRODES (Base Fixa)")
    st.markdown("Com a base estável instalada, basta subir os CARs e processar.")

    # VEJA: Agora só existe UM campo de upload! O PRODES sumiu da tela!
    cars_file = st.file_uploader("Suba o arquivo comprimido dos CARs (CARS.zip)", type=["zip"])

    if st.button("🚀 Rodar Cruzamento Espacial"):
        if cars_file is not None:
            base_extracao = 'tmp_cars_extracao'
            pasta_shapes_finais = 'tmp_shapes_prontos'
            caminho_parquet_prodes = "prodes_otimizado.parquet" # Procurado direto no repositório
            
            # Limpeza de pastas temporárias
            for p in [base_extracao, pasta_shapes_finais]:
                if os.path.exists(p): shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)
                
            # 1. Verifica se você já enviou o arquivo fixo para o GitHub
            if not os.path.exists(caminho_parquet_prodes):
                st.error("❌ Erro Crítico: A base fixa 'prodes_otimizado.parquet' não foi encontrada no GitHub. Rode o script 'converter.py' no seu computador primeiro para injetá-la aqui!")
            else:
                with st.spinner("📦 Extraindo polígonos dos CARs enviados..."):
                    with open("cars_input.zip", "wb") as f:
                        f.write(cars_file.getbuffer())
                    with zipfile.ZipFile("cars_input.zip", 'r') as z:
                        z.extractall(base_extracao)

                    # Varredura inteligente de subpastas do CAR
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
                    st.error("❌ Nenhum polígono válido do CAR foi localizado no pacote enviado.")
                else:
                    with st.spinner("⚡ Carregando Base PRODES Fixa e Cruzando Dados Espaciais..."):
                        # Lendo os CARs enviados
                        lista_gdfs = []
                        for shp in shapes_cars:
                            try: lista_gdfs.append(gpd.read_file(os.path.join(pasta_shapes_finais, shp)))
                            except: pass
                        
                        gdf_todos_cars = pd.concat(lista_gdfs, ignore_index=True)
                        if gdf_todos_cars.crs is None: gdf_todos_cars.set_crs("EPSG:4674", inplace=True)
                        
                        # MÁGICA: Abre o arquivo ultraleve Parquet direto da raiz do site
                        gdf_prodes_real = gpd.read_parquet(caminho_parquet_prodes)
                        if gdf_prodes_real.crs is None: gdf_prodes_real.set_crs("EPSG:4674", inplace=True)
                        if gdf_prodes_real.crs != gdf_todos_cars.crs:
                            gdf_prodes_real = gdf_prodes_real.to_crs(gdf_todos_cars.crs)
                        
                        linhas_brutas = []
                        coluna_ano_prodes = next((col for col in gdf_prodes_real.columns if col.lower() in ['ano', 'year', 'class_name', 'class']), None)
                        
                        # Realiza a interseção geométrica rápida
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
                        
                        # Agrupa e formata os dados para o painel
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
                        
                        st.success("🎉 Mapeamento concluído com a base fixa!")
                        st.dataframe(df_final)
                        
                        # Botão para baixar a planilha gerada
                        nome_saida = 'Relatorio_PRODES_Fixo.xlsx'
                        df_final.to_excel(nome_saida, index=False)
                        with open(nome_saida, "rb") as file:
                            st.download_button(label="📥 Baixar Planilha Excel Oficial", data=file, file_name=nome_saida, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # Limpeza final de resíduos
            for p in [base_extracao, pasta_shapes_finais, "cars_input.zip"]:
                if os.path.exists(p): shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        else:
            st.warning("⚠️ Por favor, insira o arquivo CARS.zip.")
