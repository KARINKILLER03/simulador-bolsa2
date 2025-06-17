import os
import polars as pl
from datetime import datetime
from decimal import Decimal

#Cargar el CSV de acciones
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, '..', 'csvs', 'Stocks_Definitivo.csv')
print("Cargando csv...")
df = pl.read_csv(csv_path)
print("CSV cargado correctamente.")


#Obtiene los datos de un activo en un periodo determinado
async def obtener_datos_activo(ticker, periodo):
    fecha_actual = datetime.now()
    # fecha_simulada = fecha_actual - timedelta(days=365.25 * 20) 
    # fecha_simulada_str = fecha_simulada.strftime("%Y-%m-%d")
    fecha_actual_str = fecha_actual.strftime("%Y-%m-%d")
    print(f"Fecha actual: {fecha_actual_str}")
    # print(fecha_simulada_str)
    base_query = (
        df.filter(pl.col("Ticker") == ticker)
        .filter(pl.col("Date") <= fecha_actual_str)
        .sort("Date", descending=True)
    )

    match periodo:
        case "anno":
            ticker_data = base_query.head(365)
        case "mes":
            ticker_data = base_query.head(30)
        case "semana":
            ticker_data = base_query.head(7)
        case _:
            raise ValueError("Periodo no válido. Use 'anno', 'mes' o 'semana'.")

    result = ticker_data.select([
        pl.col("Date").str.slice(0, 10).alias("fecha"),
        pl.col("Close").alias("precio")
    ])
    
    lista = result.to_dicts()
    return lista[::-1]

#Obtiene el valor actual de un activo
async def obtener_valor_actual(ticker):
    fecha_actual = datetime.now()
    # fecha_simulada = fecha_actual - timedelta(days=365.25 * 20) 
    # fecha_simulada_str = fecha_simulada.strftime("%Y-%m-%d")
    fecha_actual_str = fecha_actual.strftime("%Y-%m-%d")
    print(fecha_actual_str)
    base_query = (
        df.filter(pl.col("Ticker") == ticker)
        .filter(pl.col("Date") <= fecha_actual_str)
        .sort("Date", descending=True)
    )

    ticker_data = base_query.head(1)

    precio_actual = ticker_data.select([pl.col("Close").alias("precio")])
    precio_actual = precio_actual.to_dict()['precio'][0]
    precio_actual = round(precio_actual, 4)

    return precio_actual

# Verifica si hay que realizar alguna venta automática 
async def verificar_ventas_automaticas(transacciones):
    ventas = []
    for transaccion in transacciones:
        username = transaccion[0]
        simbolo_activo = transaccion[1]
        num_acciones = transaccion[2]
        precio_promedio = transaccion[3]
        stop_loss = transaccion[4]
        take_profit = transaccion[5]
        precio_actual = await obtener_valor_actual(simbolo_activo)
        precio_actual = Decimal.from_float(precio_actual).quantize(Decimal('0.0001'))
        precio_promedio = (precio_promedio).quantize(Decimal('0.0001'))
        porcentaje_variacion = ((precio_actual - precio_promedio) / precio_promedio * 100).quantize(Decimal('0.0001'))
        print(f"Activo: {simbolo_activo}, Porcentaje de variación: {porcentaje_variacion}%")

        # Comprobar si se cumplen las condiciones de venta
        if take_profit<=0:
            cumple_tp = False
        else:
             cumple_tp = porcentaje_variacion >= take_profit
        if stop_loss<=0:
            cumple_sl = False
        else:
            cumple_sl = porcentaje_variacion <= -stop_loss


        print(f"Cumple TP: {cumple_tp}, Cumple SL: {cumple_sl}")

        if cumple_tp or cumple_sl:
            cantidad_vendida = num_acciones * precio_actual
            transaccion.append(cantidad_vendida)
            ventas.append(transaccion)
        else:
            print(f"No se cumplen las condiciones para venta automática de {simbolo_activo}")
    print("Las ventas automáticas son las siguientes:")
    print(ventas)
    return ventas
            
    
# # Ejemplo de uso
# ticker = 'AMZN'
# ultimo_valor =  asyncio.run(obtener_valor_actual(ticker))

# print(f"Último valor de {ticker}: {ultimo_valor}")

# # Obtener datos del activo
# periodo = 'anno'  # Puede ser 'anno', 'mes' o 'semana'
# datos_activo = asyncio.run(obtener_datos_activo(ticker, periodo))
# print(f"Datos de {ticker} en el periodo '{periodo}': {datos_activo}")