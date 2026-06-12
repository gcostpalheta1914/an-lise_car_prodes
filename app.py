import streamlit as st
import os, zipfile, shutil, geopandas as gpd, pandas as pd, io

st.set_page_config(page_title="Detector de Passivos", layout="centered")

if "auth" not in st.session_state: st.session_state.auth = False

# --- FUNÇÃO DE CARGA DO PRODES ---
def carregar_prodes():
    bytes_totais = bytearray()
    i = 1
    while os.path.exists(f"prodes_otimizado.parquet.part{i}"):
        with open(f"prodes_otimizado.parquet.part{i}", "rb") as f: bytes_totais.extend(f.read())
        i += 1
    if not bytes_totais: return None
    gdf = gpd.read_parquet(io.BytesIO(bytes_totais))
    # Força o CRS para SIRGAS 2000
    if gdf.crs is None: gdf.set_crs("EPSG:4674", inplace=True)
    return gdf

# --- TELA DE LOGIN ---
if not st.session_state.auth:
    st.title("🔒 Acesso ao Sistema")
    if st.text_input("Senha", type="password") == "Gab1914.":
        st.session_state.auth = True
        st.rerun()
else:
    st.title("🗺️ Detector de Passivos: CAR vs PRODES")
    arquivo = st.file_uploader("Suba o arquivo CARS.zip", type=["zip"])
    
    if arquivo and st.button("🚀 Rodar Processamento"):
        st.write("Iniciando processamento...")
        base = 'tmp_data'
        if os.path.exists(base): shutil.rmtree(base)
        os.makedirs(base)
        
        with zipfile.ZipFile(arquivo, 'r') as z: z.extractall(base)
        
        prodes = carregar_prodes()
        resultados = []
        
        # Procura arquivos SHP em qualquer subpasta
        for root, dirs, files in os.walk(base):
            for file in files:
                if file.endswith(".shp"):
                    try:
                        caminho = os.path.join(root, file)
                        car = gpd.read_file(caminho)
                        
                        # Padroniza CRS
                        if car.crs is None: car.set_crs("EPSG:4674", inplace=True)
                        car = car.to_crs(prodes.crs)
                        
                        # Interseção
                        inter = gpd.overlay(car, prodes, how='intersection')
                        
                        if not inter.empty:
                            area_ha = inter.to_crs("EPSG:31982").geometry.area.sum() / 10000
                            resultados.append({"CAR": file, "Area_Ha": round(area_ha, 2)})
                    except Exception as e:
                        st.write(f"Erro no arquivo {file}: {e}")
                        continue
        
        if resultados:
            df = pd.DataFrame(resultados)
            st.dataframe(df)
            st.download_button("📥 Baixar Resultados", df.to_csv(index=False), "resultado.csv", "text/csv")
            st.success("Cruzamento concluído com sucesso!")
        else:
            st.warning("⚠️ O processamento rodou, mas nenhuma interseção foi encontrada. Verifique se os polígonos dos arquivos CAR realmente ocupam as mesmas áreas da sua base PRODES.")
            
        shutil.rmtree(base)
