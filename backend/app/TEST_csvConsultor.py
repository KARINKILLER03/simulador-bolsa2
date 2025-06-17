import os
import polars as pl
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "..", "..", "World-Stock-Prices-Dataset.csv")
print("Cargando csv...")
df = pl.read_csv(csv_path)
print(df.head())

def ver_empresas(fecha_objetivo, df):
    # Convierte la columna Date a datetime y extrae solo la fecha
    df = df.with_columns(pl.col("Date").str.slice(0, 10).alias("Date_Only"))
    
    # Filtra el DataFrame para incluir solo las filas de la fecha objetivo
    df_filtrado = df.filter(pl.col("Date_Only") == fecha_objetivo)
    
    # Selecciona las columnas Brand_Name y Ticker, elimina duplicados y ordena por Brand_Name
    empresas = df_filtrado.select(["Brand_Name", "Ticker"]).unique().sort("Brand_Name")
    
    # Convierte el resultado a una lista de diccionarios
    empresas_list = empresas.to_dicts()
    
    # Crea un diccionario donde la clave es Brand_Name y el valor es Ticker
    empresas_dict = {empresa["Brand_Name"]: empresa["Ticker"] for empresa in empresas_list}
    
    return empresas_dict

# Fecha objetivo
fecha_objetivo = "2005-03-18"

# Ejemplo de uso
empresas = ver_empresas(fecha_objetivo, df)
print(f"Empresas cotizando el {fecha_objetivo}:")

# Para imprimir de forma más legible:
for nombre, ticker in empresas.items():
    print(f"Empresa: {nombre}, Ticker: {ticker}")
