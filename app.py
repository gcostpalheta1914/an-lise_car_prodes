import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

# ... (manter o bloco de login igual ao que funcionou)

    if st.button("Processar Dados"):
        if f_p and f_c:
            with st.spinner("Calculando com precisão..."):
                # ... (extração mantida)
                
                # Leitura da base PRODES
                g_p = gpd.read_file(p_shp)
                
                # IMPORTANTE: Garantir que estamos usando uma projeção métrica (ex: UTM)
                # O EPSG:31982 é ideal para a maior parte do Brasil central/norte
                if g_p.crs.is_geographic:
                    g_p = g_p.to_crs("EPSG:31982")
                
                res = []
                for root, _, files in os.walk("data/cars"):
                    for f in files:
                        if f.endswith(".shp"):
                            g_c = gpd.read_file(os.path.join(root, f))
                            
                            # Garantir que o CAR esteja na mesma projeção do PRODES
                            if g_c.crs != g_p.crs:
                                g_c = g_c.to_crs(g_p.crs)
                            
                            # Realiza a interseção
                            inter = gpd.overlay(g_c, g_p, how='intersection')
                            
                            if not inter.empty:
                                # Cálculo de área em hectares (m² / 10.000)
                                # Considera os atributos do PRODES (ano)
                                inter['ha'] = inter.geometry.area / 10000
                                
                                # Agrupa por ANO se existir a coluna 'ano' ou 'desmatamento' no PRODES
                                # Verifique se o nome da coluna de ano no seu PRODES é 'ano' ou 'ANO'
                                col_ano = 'ano' if 'ano' in inter.columns else (inter.columns[0] if 'ano' in str(inter.columns[0]).lower() else None)
                                
                                if col_ano:
                                    stats = inter.groupby(col_ano)['ha'].sum().round(2).to_dict()
                                    res.append({"Arquivo": f, "Dados": stats})
                                else:
                                    res.append({"Arquivo": f, "Total_Ha": round(inter['ha'].sum(), 2)})
                
                # Exibição dos resultados
                if res:
                    st.write("### Resultados por Ano (Ha):")
                    st.dataframe(pd.DataFrame(res))
