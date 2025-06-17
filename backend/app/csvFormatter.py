import polars as pl
import os
""""USADO PARA FORMATEAR EL CSV DE ENTRADA"""
# current_dir = os.path.dirname(os.path.abspath(__file__))

# csv_path = os.path.join(current_dir, "..", "..", "World-Stock-Prices-Dataset-RAW.csv")

# df = pl.read_csv(csv_path)

# # Seleccionar las columnas deseadas
# df_filtrado = df.select(['Date', 'Open', 'Close', 'Brand_Name', 'Ticker'])

# # Guardar el nuevo DataFrame en un archivo CSV
# df_filtrado.write_csv('World-Stock-Prices-Dataset.csv')

# # Mostrar las primeras filas del DataFrame filtrado
# print(df_filtrado.head())
""""USADO PARA UNIR CSVS"""
# current_dir = os.path.dirname(os.path.abspath(__file__))

# csv_objetivo = os.path.join(current_dir, "..", "..", "World-Stock-Prices-Dataset.csv")
# csv_entrada = os.path.join(current_dir, "..", "..", "coin_Bitcoin.csv")


# # Leer los dos archivos CSV
# df_objetivo = pl.read_csv(csv_objetivo)
# df_entrada = pl.read_csv(csv_entrada)

# # Seleccionar solo las columnas del primer CSV en el segundo CSV
# columnas_objetivo = df_objetivo.columns
# df_entrada_filtrado = df_entrada.select(columnas_objetivo)

# # Concatenar los dos DataFrames verticalmente
# df_concatenado = pl.concat([df_objetivo, df_entrada_filtrado], how="vertical")

# # Guardar el resultado en un nuevo archivo CSV
# ruta_guardado = os.path.join(current_dir, "..", "..", "Stocks.csv")
# df_concatenado.write_csv(ruta_guardado)

"""USADO PARA CONCATENAR Y FILTRAR COLUMNAS DE CSVS"""
current_dir = os.path.dirname(os.path.abspath(__file__))
# files = [
#     os.path.join(current_dir, "..", "..", "coin_Cardano.csv"),
#     os.path.join(current_dir, "..", "..", "coin_Monero.csv"),
#     os.path.join(current_dir, "..", "..", "coin_Dogecoin.csv"),
#     os.path.join(current_dir, "..", "..", "coin_Ethereum.csv")
# ]


# dfs = []
# for file in files:
#     df = (
#         pl.read_csv(file)
#         .rename({"Name": "Brand_Name", "Symbol": "Ticker"})
#         .select(["Date", "Open", "Close", "Brand_Name", "Ticker"])
#     )
#     dfs.append(df)

# # Concatenar y guardar
# df_medio = pl.concat(dfs, how="vertical")

# csv_objetivo = os.path.join(current_dir, "..", "..", "Stocks.csv")
# df_objetivo = pl.read_csv(csv_objetivo)
# df_concatenado = pl.concat([df_objetivo, df_medio], how="vertical")

# output_path = os.path.join(current_dir, "..", "..", "Stocks_Final.csv")
# df_concatenado.write_csv(output_path)

"""USADO PARA SUMAR 6 AÑOS A TODAS LAS FECHAS"""
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "..", "..", "Stocks_Final.csv")
df = pl.read_csv(csv_path)

#Primero quitar las marcas de zona horaria
df = df.with_columns(
    pl.when(pl.col("Date").str.len_chars() > 19)
      .then(pl.col("Date").str.slice(0, 19))
      .otherwise(pl.col("Date"))
      .alias("Date")
)

# Ahora convierte a datetime y suma 6 años
df = df.with_columns(
    pl.col("Date").str.strptime(pl.Datetime, strict=False).dt.offset_by("6y")
)

# Guardar el DataFrame modificado en un nuevo archivo CSV
output_path = os.path.join(current_dir, "..", "..", "Stocks_Prueba.csv")
df.write_csv(output_path)