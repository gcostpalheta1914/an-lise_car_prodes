import streamlit as st
import geopandas as gpd
import pandas as pd
import os, zipfile, shutil

# --- CÓDIGO DE FORÇAGEM ESPACIAL ---
# ... (manter o login igual)

                # FORÇAR ALINHAMENTO
                # Se o CRS for diferente, vamos padronizar para o CRS do PRODES
                if g_c.crs != g_p.crs:
                    g_c = g_c.to_crs(g_p.crs)
                
                # Se ainda assim não cruzar, o problema é a geometria
                # Vamos converter tudo para uma geometria "buffer 0" (corrige falhas minúsculas)
                g_c['geometry'] = g_c.geometry.buffer(0)
                g_p['geometry'] = g_p.geometry.buffer(0)
                
                inter = gpd.overlay(g_c, g_p, how='intersection')
# ...
