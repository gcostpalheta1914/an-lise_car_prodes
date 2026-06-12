# --- SUBSTITUA APENAS O BLOCO DO LOOP DE PROCESSAMENTO ---
            # Define projeção métrica fixa para garantir exatidão (ex: SIRGAS 2000 / UTM zone 22S - EPSG:31982)
            # Se o seu CAR estiver em outra zona UTM, altere este código para a zona correta.
            crs_metrico = "EPSG:31982" 
            
            p_shp = [os.path.join(r, f) for r, _, fs in os.walk("tmp/prodes") if f.endswith(".shp")][0]
            g_p = gpd.read_file(p_shp).to_crs(crs_metrico)
            
            res = []
            for r, _, fs in os.walk("tmp/cars"):
                for f in fs:
                    if f.endswith(".shp"):
                        g_c = gpd.read_file(os.path.join(r, f)).to_crs(crs_metrico)
                        
                        # A INTERSEÇÃO MAIS PRECISA (usando overlay com geometrias limpas)
                        g_c['geometry'] = g_c.geometry.buffer(0)
                        g_p['geometry'] = g_p.geometry.buffer(0)
                        
                        inter = gpd.overlay(g_c, g_p, how='intersection')
                        
                        if not inter.empty:
                            # Cálculo de área rigoroso em hectares
                            area_ha = inter.geometry.area.sum() / 10000
                            res.append({"Arquivo": f, "Area_Ha": round(area_ha, 4)}) # 4 casas decimais para exatidão
            
            if res:
                df_final = pd.DataFrame(res)
                st.dataframe(df_final.style.format({"Area_Ha": "{:.4f}"}))
                # Botão para baixar o resultado e conferir os dados
                st.download_button("Baixar Resultados (CSV)", df_final.to_csv(index=False), "resultados.csv")
