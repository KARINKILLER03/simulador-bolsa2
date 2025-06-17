# ARCHIVO EN DESUSO, SE MANTIENE COMO PRUEBA DE SU EXISTENCIA
# Este archivo contiene funciones para obtener datos de acciones desde la API de Alpha Vantage.

# import requests
# from datetime import datetime, timedelta

API_KEY_0 = 'FICUUFQ0CVFC23J3'

BASE_URL = 'https://www.alphavantage.co/query'

def obtener_datos_activo(activo, periodo):
    print("Entramos en la funcion de obtencion de datos")
    funciones_api = {
        'hora': ('TIME_SERIES_INTRADAY', '1min'),
        'dia': ('TIME_SERIES_INTRADAY', '15min'),
        'semana': ('TIME_SERIES_DAILY', None),
        'mes': ('TIME_SERIES_DAILY', None),
        'año': ('TIME_SERIES_WEEKLY', None)
    }

    if periodo not in funciones_api:
        raise ValueError("Periodo no válido. Opciones válidas: hora, dia, semana, mes, año")

    funcion, intervalo = funciones_api[periodo]

    params = {
        'function': funcion,
        'symbol': activo,
        'apikey': API_KEY_0,
        'outputsize': 'compact'
    }

    if intervalo:
        params['interval'] = intervalo

    response = requests.get(BASE_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"Error al obtener datos: {response.status_code}")

    data = response.json()

    clave_series = {
        'TIME_SERIES_INTRADAY': f'Time Series ({intervalo})',
        'TIME_SERIES_DAILY': 'Time Series (Daily)',
        'TIME_SERIES_WEEKLY': 'Weekly Time Series'
    }.get(funcion)

    if clave_series not in data:
        raise ValueError("Respuesta inválida o límite de API excedido")

    ahora = datetime.now()
    delta_periodos = {
        'hora': timedelta(hours=1),
        'dia': timedelta(days=1),
        'semana': timedelta(weeks=1),
        'mes': timedelta(days=30),
        'año': timedelta(days=365)
    }

    desde_fecha = ahora - delta_periodos[periodo]

    datos_filtrados = [
        {'fecha': fecha, 'valor': round(float(valores['4. close']), 2)}
        for fecha, valores in data[clave_series].items()
        if datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S' if intervalo else '%Y-%m-%d') >= desde_fecha
    ]

    # Ordenar cronológicamente
    datos_filtrados.sort(key=dict.get['fecha'])
    ultimos_10 = datos_filtrados[-20:]

    return ultimos_10

async def obtener_valor_actual(simbolo: str)-> float:
    
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={simbolo}&apikey={API_KEY_0}'

    response = requests.get(url)
    data = response.json()

    if "Global Quote" in data:
        current_price = data["Global Quote"]["05. price"]
        print(f"El precio actual de {simbolo} es: ${current_price}")
        return float(current_price)
    else:
        print("Error al obtener datos:", data)
        return -1


    # Ejemplo uso:
if __name__ == '__main__':
    activo_ejemplo = 'AAPL'
    periodo_ejemplo = 'año'  # opciones: hora, dia, semana, mes, año

    try:
        datos_activo = obtener_datos_activo(activo_ejemplo, periodo_ejemplo)
        print(f"Últimos valores para {activo_ejemplo} ({periodo_ejemplo}):")
        print(datos_activo)

    except Exception as e:
        print(f"Error al obtener datos: {e}")
