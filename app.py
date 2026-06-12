import streamlit as st
import os
import zipfile
import shutil
import geopandas as gpd
import pandas as pd
import re
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Analisador CAR x PRODES (Alta Precisão)", page_icon="🗺️", layout="centered")

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

    st.title("🗺️ Detector de Passivos: CAR vs PRODES (Alta Precisão)")
    st.markdown("Base carregada com sucesso. Pronto para processamento com correção de distorção UTM.")

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

                    # Varredura inteligente de qualquer arquivo zip ou pasta aninhada
                    for raiz, _, arquivos in os.walk(base_extracao):
                        # Tenta pegar o código do CAR pelo nome da pasta ou usa o nome do arquivo zip encontrado
                        match_car = re.search(r'(PA-\d{7}-[A-F0-9]+)', raiz, re.IGNORECASE)
                        codigo_car = match_car.group(1) if match_car else None
                        
                        for arquivo in arquivos:
                            caminho_completo = os.path.join(raiz, arquivo)
                            if arquivo.endswith('.zip'):
                                try:
                                    if not codigo_car:
                                        match_sub = re.search(r'(PA-\d{7}-[A-F0-9]+)', arquivo, re.IGNORECASE)
                                        codigo_car = match_sub.group(1) if match_sub else os.path.splitext(arquivo)[0]
                                        
                                    with zipfile.ZipFile(caminho_completo, 'r') as sub_zip:
                                        for f_interno in sub_zip.namelist():
                                            ext = os.path.splitext(f_interno)[1].lower()
                                            if ext in ['.shp', '.shx', '.dbf', '.prj']:
                                                nome_final = f"{codigo_car}{ext}"
                                                with sub_zip.open(f_interno) as z_in, open(os.path.join(pasta_shapes_finais, nome_final), 'wb') as f_out:
                                                    shutil.copyfileobj(z_in, f_out)
                                except: pass
                            elif arquivo.endswith('.shp'):
                                try:
                                    if not codigo_car:
                                        match_sub = re.search(r'(PA-\d{7}-[A-F0-9]+)', arquivo, re.IGNORECASE)
                                        codigo_car = match_sub.group(1) if match_sub else os.path.splitext(arquivo)[0]
                                    
                                    nome_base = os.path.splitext(arquivo)[0]
                                    for ext in ['.shp', '.shx', '.dbf', '.prj']:
                                        arq_origem = os.path.join(raiz, f"{nome_base}{ext}")
                                        if os.path.exists(arq_origem):
                                            shutil.copy(arq_origem, os.path.join(pasta_shapes_finais, f"{codigo_car}{ext}"))
                                except: pass

                shapes_cars = [f for f in os.listdir(pasta_shapes_finais) if f.endswith('.shp')]
                
                if not shapes_cars:
                    st.error("❌ Nenhum polígono válido do CAR foi localizado no pacote enviado.")
                else:
                    with st.spinner("⚔️ Executando Cruzamento Geográfico de Alta Precisão..."):
                        coluna_ano_prodes = next((col for col in gdf_prodes_real.columns if col.lower() in ['ano', 'year', 'class_name', 'class']), None)
                        linhas_finais = []
                        
                        for shp in shapes_cars:
                            car_id_limpo = shp.replace('.shp', '')
                            try:
                                gdf_imovel = gpd.read_file(os.path.join(pasta_shapes_finais, shp))
                                if gdf_imovel.empty: continue
                                
                                if gdf_imovel.crs is None: gdf_imovel.set_crs("EPSG:4674", inplace=True)
                                
                                if gdf_prodes_real.crs != gdf_imovel.crs:
                                    gdf_imovel = gdf_imovel.to_crs(gdf_prodes_real.crs)
                                
                                prodes_concorrentes = gpd.sjoin(gdf_prodes_real, gdf_imovel, how="inner", predicate="intersects")
                                
                                if not prodes_concorrentes.empty:
                                    prodes_concorrentes = prodes_concorrentes.drop(columns=['index_right'], errors='ignore')
                                    intersecao_real = gpd.overlay(gdf_imovel, prodes_concorrentes, how='intersection')
                                    
                                    if not intersecao_real.empty:
                                        # Descobre zona UTM dinamicamente com fallback de segurança se falhar
                                        try:
                                            lon_centro = gdf_imovel.geometry.centroid.x.iloc[0]
                                            lat_centro = gdf_imovel.geometry.centroid.y.iloc[0]
                                            zona_utm = int((lon_centro + 180) / 6) + 1
                                            epsg_utm = f"3198{zona_utm}" if lat_centro < 0 else f"3197{zona_utm}"
                                            epsg_final = int(epsg_utm)
                                        except:
                                            epsg_final = 31981 # Fallback padrão Pará Zona 21S
                                        
                                        intersecao_utm = intersecao_real.to_crs(num=epsg_final)
                                        intersecao_real['area_calculada_ha'] = intersecao_utm.geometry.area / 10000
                                        
                                        anos_detectados = set()
                                        area_acumulada_prodes = 0.0
                                        
                                        for _, row in intersecao_real.iterrows():
                                            area_linha = row['area_calculada_ha']
                                            area_acumulada_prodes += area_linha
                                            if coluna_ano_prodes:
                                                numeros = re.findall(r'\d+', str(row[coluna_ano_prodes]))
                                                if numeros:
                                                    anos_detectados.add(str(numeros[0]))
                                        
                                        if list(anos_detectados):
                                            texto_anos = ", ".join(sorted(list(anos_detectados)))
                                            area_final_ha = round(area_acumulada_prodes, 2)
                                        else:
                                            texto_anos = "Sem PRODES"
                                            area_final_ha = 0.0
                                    else:
                                        texto_anos = "Sem PRODES"
                                        area_final_ha = 0.0
                                else:
                                    texto_anos = "Sem PRODES"
                                    area_final_ha = 0.0
                                    
                                linhas_finais.append({
                                    'Identificador_do_CAR': car_id_limpo, 
                                    'Anos_com_Incidencia_PRODES': texto_anos, 
                                    'Area_Total_PRODES_HA': area_final_ha
                                })
                                
                            except Exception as e:
                                linhas_finais.append({
                                    'Identificador_do_CAR': car_id_limpo, 
                                    'Anos_com_Incidencia_PRODES': 'Erro na análise', 
                                    'Area_Total_PRODES_HA': 0.0
                                })
                        
                        df_final = pd.DataFrame(linhas_finais).sort_values(by='Identificador_do_CAR')
                        
                        st.success("🎉 Mapeamento de alta precisão concluído!")
                        st.dataframe(df_final)
                        
                        nome_saida = 'Relatorio_PRODES_Fixo.xlsx'
                        df_final.to_excel(nome_saida, index=False)
                        with open(nome_saida, "rb") as file:
                            st.download_button(label="📥 Baixar Planilha Excel Oficial", data=file, file_name=nome_saida, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            for p in [base_extracao, pasta_shapes_finais, "cars_input.zip"]:
                if os.path.exists(p): shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        else:
            st.warning("⚠️ Por favor, insira o arquivo CARS.zip.")
