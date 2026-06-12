import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador CAR x PRODES (Fixo)", page_icon="🗺️", layout="centered")

# --- FUNÇÃO ULTRARRÁPIDA COM CACHE ---
@st.cache_data(show_spinner=False)
def carregar_base_prodes_fixa():
    bytes_totais = bytearray()
    contador_partes = 1
    
    while os.path.exists(f"prodes_otimizado.parquet.part{contador_partes}"):
        with open(f"prodes_otimizado.parquet.part{contador_partes}", "rb") as f_parte:
            bytes_totais.extend(f_parte.read())
        contador_partes += 1
        
    if len(bytes_totais) == 0:
        return None
        
    try:
        gdf = gpd.read_parquet(io.BytesIO(bytes_totais), engine='pyogrio')
    except:
        gdf = gpd.read_parquet(io.BytesIO(bytes_totais))
        
    colunas_uteis = ['geometry']
    coluna_ano = next((col for col in gdf.columns if col.lower() in ['ano', 'year', 'class_name', 'class']), None)
    if coluna_ano:
        colunas_uteis.append(coluna_ano)
    
    gdf = gdf[colunas_uteis]
    if gdf.crs is None: 
        gdf.set_crs("EPSG:4674", inplace=True)
        
    return gdf

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
    st.markdown("A base estável foi instalada com sucesso. Suba os CARs para processar.")

    cars_file = st.file_uploader("Suba o arquivo comprimido dos CARs (CARS.zip)", type=["zip"])

    if st.button("🚀 Rodar Cruzamento Espacial"):
        if cars_file is not None:
            base_extracao = 'tmp_cars_extracao'
            pasta_shapes_finais = 'tmp_shapes_prontos'
            
            for p in [base_extracao, pasta_shapes_finais]:
                if os.path.exists(p): shutil.rmtree(p)
                os.makedirs(p, exist_ok=True)
                
            with st.spinner("⚡ Carregando inteligência geográfica do PRODES..."):
                gdf_prodes_real = carregar_base_prodes_fixa()
                
            if gdf_prodes_real is None:
                st.error("❌ Erro Crítico: As partes da base 'prodes_otimizado.parquet' não estão acessíveis no GitHub.")
            else:
                with st.spinner("📦 Extraindo polígonos dos CARs enviados..."):
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
                    st.error("❌ Nenhum polígono válido do CAR foi localizado no pacote enviado.")
                else:
                    with st.spinner("⚔️ Cruzando dados espaciais via Indexação Rápida..."):
                        coluna_ano_prodes = next((col for col in gdf_prodes_real.columns if col.lower() in ['ano', 'year', 'class_name', 'class']), None)
                        linhas_finais = []
                        
                        for shp in shapes_cars:
                            car_id_limpo = shp.replace('.shp', '')
                            try:
                                gdf_imovel = gpd.read_file(os.path.join(pasta_shapes_finais, shp))
                                if gdf_imovel.crs is None: gdf_imovel.set_crs("EPSG:4674", inplace=True)
                                
                                # Ajusta o CRS se necessário
                                if gdf_prodes_real.crs != gdf_imovel.crs:
                                    gdf_imovel = gdf_imovel.to_crs(gdf_prodes_real.crs)
                                
                                # NOVO MOTOR: Mapeamento por junção espacial acelerada (sjoin)
                                correspondencias = gpd.sjoin(gdf_imovel, gdf_prodes_real, how="inner", predicate="intersects")
                                
                                if not correspondencias.empty and coluna_ano_prodes:
                                    # Agrupa os anos detectados tirando duplicados
                                    anos_detectados = []
                                    for val in correspondencias[coluna_ano_prodes].unique():
                                        numeros = re.findall(r'\d+', str(val))
                                        if numeros:
                                            anos_detectados.append(int(numeros[0]))
                                    
                                    if anos_detectados:
                                        texto_anos = ", ".join(sorted(list(set(map(str, anos_detectados)))))
                                        
                                        # Calcula área aproximada convertendo rápido para UTM
                                        gdf_imovel_utm = gdf_imovel.to_crs(epsg=31981)
                                        area_ha = round(gdf_imovel_utm.geometry.area.sum() / 10000, 2)
                                    else:
                                        texto_anos = "Inconclusivo"
                                        area_ha = 0.0
                                        
                                    linhas_finais.append({
                                        'Identificador_do_CAR': car_id_limpo, 
                                        'Anos_com_Incidencia_PRODES': texto_anos, 
                                        'Area_Total_PRODES_HA': area_ha
                                    })
                                else:
                                    linhas_finais.append({
                                        'Identificador_do_CAR': car_id_limpo, 
                                        'Anos_com_Incidencia_PRODES': 'Sem PRODES', 
                                        'Area_Total_PRODES_HA': 0.0
                                    })
                            except:
                                linhas_finais.append({
                                    'Identificador_do_CAR': car_id_limpo, 
                                    'Anos_com_Incidencia_PRODES': 'Erro na análise', 
                                    'Area_Total_PRODES_HA': 0.0
                                })
                        
                        df_final = pd.DataFrame(linhas_finais).sort_values(by='Identificador_do_CAR')
                        
                        st.success("🎉 Mapeamento concluído com sucesso!")
                        st.dataframe(df_final)
                        
                        nome_saida = 'Relatorio_PRODES_Fixo.xlsx'
                        df_final.to_excel(nome_saida, index=False)
                        with open(nome_saida, "rb") as file:
                            st.download_button(label="📥 Baixar Planilha Excel Oficial", data=file, file_name=nome_saida, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            for p in [base_extracao, pasta_shapes_finais, "cars_input.zip"]:
                if os.path.exists(p): shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        else:
            st.warning("⚠️ Por favor, insira o arquivo CARS.zip.")
