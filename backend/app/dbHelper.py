import asyncpg
from .pwEncrypt import *
from .priceConsultor import *
from decimal import Decimal

# Configuración para Neon con SSL
NEON_DATABASE_CONFIG = {
    "host": "ep-super-bush-a9o5isnp-pooler.gwc.azure.neon.tech",
    "port": 5432,
    "user": "neondb_owner", 
    "password": "npg_IwZC2FBgU7GS",
    "database": "neondb",
    "ssl": "require"
}

DATABASE_CONFIG = {
    "user": "postgres",
    "password": "postgres",
    "database": "tfg",
    "host": "localhost",
    "port": 5432,
}

connection_pool = None

# # Inicia la conexión a la base de datos
# async def init_db():
#     global connection_pool
#     try:
#         print("Inicializando la base de datos...")
#         connection_pool = await asyncpg.create_pool(**DATABASE_CONFIG)
#         print("Base de datos inicializada correctamente.")
#     except Exception as e:
#         print(f"Error al inicializar la base de datos: {e}")
#         raise

async def init_db():
    global connection_pool
    try:
        print("Inicializando la base de datos...")
        connection_pool = await asyncpg.create_pool(**NEON_DATABASE_CONFIG)
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise


# Cierra la conexión a la base de datos
async def close_db():
    if connection_pool:
        print("Cerrando la conexión a la base de datos...")
        await connection_pool.close()
        print("Conexión a la base de datos cerrada correctamente.")

# Valida el login del usuario
async def validarLogin(username: str, password: str) -> bool:
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")
    
    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT contrasenna FROM usuarios WHERE nombre_usuario = $1"
            stored_password = await connection.fetchval(query, username)
            if (stored_password is not None and verify_password(password, stored_password)):
                return True
            
            return False
    except Exception as e:
        print(f"Error en loginValidation: {e}")
        return False

# Registra un nuevo usuario en la base de datos si no existe y el email no está en uso
async def registrarUsuario(email: str, username: str, password: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    async with connection_pool.acquire() as connection:
        query = "INSERT INTO usuarios (nombre_usuario, correo_electronico, contrasenna, saldo_virtual) VALUES ($1, $2, $3, 1000)"
        password_hash = hash_password(password)
        await connection.execute(query, username, email, password_hash)

# Verifica si el usuario es administrador    
async def es_admin(username: str) -> bool:
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT es_admin FROM usuarios WHERE nombre_usuario = $1"
            es_admin = await connection.fetchval(query, username)
            return es_admin
    except Exception as e:
        print(f"Error al verificar si es admin: {e}")
        raise

# Consulta el saldo virtual disponible del usuario
async def consultar_saldo_disponible(username: str) -> float:
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT saldo_virtual FROM usuarios WHERE nombre_usuario = $1"
            saldo = await connection.fetchval(query, username)
            if saldo is None:
                raise ValueError(f"No se encontró el usuario: {username}")
            print("El saldo obtenido es de:", saldo)
            return float(saldo)
    except Exception as e:
        print(f"Error al consultar saldo: {e}")
        raise

# Actualiza el saldo virtual del usuario restando la cantidad especificada
async def actualizar_saldo(username: str, cantidad: float):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "UPDATE usuarios SET saldo_virtual = saldo_virtual - $1 WHERE nombre_usuario = $2"
            await connection.execute(query, cantidad, username)
    except Exception as e:
        print(f"Error al actualizar saldo: {e}")
        raise

# Registra una compra en la base de datos en la tabla de transacciones
async def registrar_compra(username: str, activo: str, cantidad: float, precio: float):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            idUsuario = await connection.fetchval("SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1", username)
            query = "INSERT INTO transacciones (id_usuario, simbolo_activo, tipo_transaccion, monto_total, precio, numero_acciones) VALUES ($1, $2, 'compra', $3, $4, $5)"
            await connection.execute(query, idUsuario, activo, cantidad, precio, cantidad/precio)

    except Exception as e:
        print(f"Error al registrar compra: {e}")

# Actualiza la cartera del usuario con el activo comprado, cantidad, precio promedio, stop loss y take profit        
async def actualizar_cartera(username: str, activo: str, cantidad: float, precio: float, stopLoss: float, takeProfit: float):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            async with connection.transaction(): 
                query = "SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1"
                idUsuario = await connection.fetchval(query, username)
                
                numAcciones = Decimal.from_float(cantidad / precio).quantize(Decimal('0.00000000000001'))  # Redondear a 13 decimales
                # Verificamos si el usuario ya tiene un registro para este activo
                query_registro = "SELECT numero_acciones, precio_promedio_compra FROM cartera WHERE id_usuario = $1 AND simbolo_activo = $2"
                registro_actual = await connection.fetchrow(query_registro, idUsuario, activo)
                
                # Si ya existe un registro para este activo, actualizamos la cantidad y el precio promedio
                if registro_actual:
                    num_acciones_actual = float(registro_actual['numero_acciones'])
                    precio_actual = float(registro_actual['precio_promedio_compra'])
                    
                    nuevo_num_acciones_total = float(numAcciones) + float(num_acciones_actual)
                    nuevo_precio_promedio = (float(num_acciones_actual * precio_actual) + float(float(numAcciones) * precio)) / nuevo_num_acciones_total
                    
                    nuevo_num_acciones_total = Decimal.from_float(nuevo_num_acciones_total).quantize(Decimal('0.00000000000001'))
                    query_actualizar = "UPDATE cartera SET numero_acciones = $1, precio_promedio_compra = $2, stop_loss = $3, take_profit = $4 WHERE id_usuario = $5 AND simbolo_activo = $6"
                    await connection.execute(query_actualizar, nuevo_num_acciones_total, nuevo_precio_promedio, stopLoss, takeProfit, idUsuario, activo)
                else:
                    query_insertar = "INSERT INTO cartera (id_usuario, simbolo_activo, numero_acciones, precio_promedio_compra, stop_loss, take_profit) VALUES ($1, $2, $3, $4, $5, $6)"
                    await connection.execute(query_insertar, idUsuario, activo, numAcciones, precio, stopLoss, takeProfit)
                    
    except Exception as e:
        print(f"Error al actualizar cartera: {e}")
        raise

# Reinicia los datos del usuario, eliminando transacciones, vaciando cartera y restableciendo el saldo a 1000
async def reiniciar(username: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            async with connection.transaction():
                query_usuario = "SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1"
                id_usuario = await connection.fetchval(query_usuario,username)
                
                if id_usuario:

                    query_transacciones = "DELETE FROM transacciones WHERE id_usuario = $1"
                    await connection.execute(query_transacciones, id_usuario)
                    
                    query_cartera = "DELETE FROM cartera WHERE id_usuario = $1"
                    await connection.execute(query_cartera, id_usuario)

                    query_saldo = "UPDATE usuarios SET saldo_virtual = 1000 WHERE id_usuario = $1"
                    await connection.execute(query_saldo, id_usuario)
                    return True
                return False

    except Exception as e:
        print(f"Error al eliminar datos y restablecer saldo: {e}")
        raise

# Consulta los datos para el perfil del usuario, incluyendo saldo y activos en cartera
async def cargarPerfil(username: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT saldo_virtual FROM usuarios WHERE nombre_usuario = $1"
            saldo = await connection.fetchrow(query, username)
            query_id = "SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1"
            id_usuario = await connection.fetchval(query_id, username)
            
            query_activos = """
                SELECT simbolo_activo, numero_acciones, precio_promedio_compra, stop_loss, take_profit
                FROM cartera 
                WHERE id_usuario = $1
            """
            activos = await connection.fetch(query_activos, id_usuario)
            datos_activos = []
            if (float(saldo['saldo_virtual']) >0):
                datos_activos = [
                    {"activo": "Saldo", "valor": float(saldo['saldo_virtual']), "stop_loss": 0, "take_profit": 0}
                ]
            
            # Para cada activo, calculamos su valor actual total
            for activo in activos:
                simbolo = activo['simbolo_activo']
                cantidad_invertida = float(activo['numero_acciones'] * activo['precio_promedio_compra'])
                cantidad_invertida = round(cantidad_invertida,4)
                precio_promedio = float(activo['precio_promedio_compra'])
                
                num_acciones = float(activo['numero_acciones'])
                
                # Obtenemos el precio actual del mercado
                precio_actual = await obtener_valor_actual(simbolo)
                
                # Calculamos el valor total actual (num_acciones * precio_actual)
                valor_total_actual = round(num_acciones * precio_actual,4)

                
                
                datos_activos.append({
                    "activo": simbolo,
                    "valor": valor_total_actual,
                    "cantidad_invertida": cantidad_invertida,
                    "precio_actual": precio_actual,
                    "precio_inicial": precio_promedio,
                    "stop_loss": activo['stop_loss'],
                    "take_profit": activo['take_profit']
                })
            
            return datos_activos

    except Exception as e:
        print(f"Error al consultar datos de perfil: {e}")
        raise


# Carga las últimas 3 transacciones del usuario para mostrar en su perfil
async def cargarTransaccionesPerfil(username: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query_id = "SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1"
            id_usuario = await connection.fetchval(query_id, username)
            query = "SELECT simbolo_activo, tipo_transaccion, monto_total, precio, numero_acciones, creado_en FROM transacciones WHERE id_usuario = $1 ORDER BY creado_en DESC LIMIT 3"
            transacciones = await connection.fetch(query, id_usuario)
            lista_transacciones = [dict(transaccion) for transaccion in transacciones]
            return lista_transacciones
    except Exception as e:
        print(f"Error al consultar transacciones: {e}")
        raise

# Carga todas las transacciones del usuario
async def cargarTodasLasTransacciones(username: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query_id = "SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1"
            id_usuario = await connection.fetchval(query_id, username)
            query = "SELECT simbolo_activo, tipo_transaccion, monto_total, precio, numero_acciones, creado_en FROM transacciones WHERE id_usuario = $1 ORDER BY creado_en DESC"
            transacciones = await connection.fetch(query, id_usuario)
            lista_transacciones = [dict(transaccion) for transaccion in transacciones]
            return lista_transacciones
    except Exception as e:
        print(f"Error al consultar transacciones: {e}")
        raise

# Consulta el número de acciones que el usuario tiene en su cartera para un activo específico
async def consultar_cantidad_acciones(username: str, activo: str) -> float:
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT numero_acciones FROM cartera WHERE id_usuario = (SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1) AND simbolo_activo = $2"
            #dividir cantidad entre precio promedio para obtener el número real de acciones
            resultado = await connection.fetchrow(query, username, activo)
            if resultado is None:
                return -1
            numAcciones = resultado['numero_acciones']
            
            return numAcciones
    except Exception as e:
        print(f"Error al consultar cantidad de acciones: {e}")
        raise

#EN DESUSO
async def consultar_cantidad_disponible(username: str, activo: str) -> float:
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT cantidad FROM cartera WHERE id_usuario = (SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1) AND simbolo_activo = $2"
            resultado = await connection.fetchrow(query, username, activo)
            if resultado is None:
                return -1
            numAcciones = round(resultado['cantidad'],4)
            
            return numAcciones
    except Exception as e:
        print(f"Error al consultar cantidad de acciones: {e}")
        raise

# Registra una venta en la base de datos
async def registrar_venta(username: str, activo: str, cantidad: float, precio: float):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            cantidad_decimal = Decimal.from_float(cantidad)
            precio_decimal =  Decimal.from_float(precio)
            num_acciones = float(cantidad_decimal/precio_decimal)
            idUsuario = await connection.fetchval("SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1", username)
            query = "INSERT INTO transacciones (id_usuario, simbolo_activo, tipo_transaccion, monto_total, precio, numero_acciones) VALUES ($1, $2, 'venta', $3, $4, $5)"
            await connection.execute(query, idUsuario, activo, cantidad, precio, num_acciones)

    except Exception as e:
        print(f"Error al registrar venta: {e}")

# Elimina acciones de la cartera del usuario, actualizando el número de acciones y eliminando el activo si es necesario
async def eliminar_acciones(username: str, activo: str, cantidad: float):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        # Primero, obtenemos la cantidad actual de acciones del usuario para el activo

        numero_acciones = await consultar_cantidad_acciones(username, activo)
        numero_acciones = float(numero_acciones)  # Asegurarse de que sea un número flotante
        precio = await obtener_valor_actual(activo)
        cantidad = float(cantidad)  # Asegurarse de que sea un número flotante
        porcentaje_venta = round(cantidad/(numero_acciones * precio), 4)
        print("El porcentaje de venta es: " + str(porcentaje_venta))
        acciones_restantes = numero_acciones - (numero_acciones * porcentaje_venta)
        async with connection_pool.acquire() as connection:
            query = "UPDATE cartera SET numero_acciones = $1 WHERE id_usuario = (SELECT id_usuario FROM usuarios WHERE nombre_usuario = $2) AND simbolo_activo = $3"
            await connection.execute(query, acciones_restantes, username, activo)
            #si se queda sin acciones de este activo lo eliminamos de la base de datos
            query = "DELETE FROM cartera WHERE id_usuario = (SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1) AND simbolo_activo = $2 AND numero_acciones <= 0"
            await connection.execute(query, username, activo)
    except Exception as e:
        print(f"Error al eliminar acciones: {e}")
        raise

# Selecciona aquellas transacciones automáticas cuyo Stop Loss o Take Profit sean mayores que 0
async def transacciones_automaticas():
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = """SELECT usuarios.nombre_usuario, cartera.simbolo_activo, cartera.numero_acciones, cartera.precio_promedio_compra, cartera.stop_loss, cartera.take_profit
            FROM cartera JOIN usuarios ON cartera.id_usuario = usuarios.id_usuario
            WHERE  (cartera.stop_loss IS NOT NULL AND cartera.stop_loss > 0) 
            OR (cartera.take_profit IS NOT NULL AND cartera.take_profit > 0)
            """

            resultados = await connection.fetch(query)
            #transformar los resultados a una lista de listas
            resultados = [list(resultado) for resultado in resultados]
            print(resultados)
            return resultados
    except Exception as e:
        print(f"Error en transacciones automáticas: {e}")
        raise    

# Ejecuta una venta automática, lo que significa eliminar el activo de la cartera del usuario
async def venta_automatica(id_cartera: int, simbolo_activo: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            # Obtener el precio actual del activo
            precio_actual = await obtener_valor_actual(simbolo_activo)
            
            # Aquí iría la lógica para ejecutar la venta automática
            query = "DELETE FROM cartera WHERE id_cartera = $1"
            await connection.execute(query, id_cartera)
            
            return True
    except Exception as e:
        print(f"Error en venta automática: {e}")
        raise

# Elimina todas las acciones de un activo específico del usuario
async def eliminar_todas_acciones(usuario: str, activo: str):
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "DELETE FROM cartera WHERE id_usuario = (SELECT id_usuario FROM usuarios WHERE nombre_usuario = $1) AND simbolo_activo = $2"
            await connection.execute(query, usuario, activo)
    except Exception as e:
        print(f"Error al eliminar todas las acciones: {e}")
        raise

# Carga los usuarios de la base de datos, excluyendo administradores, ordenados por saldo virtual
async def cargar_usuarios():
    if not connection_pool:
        raise Exception("La conexión a la base de datos no ha sido inicializada")

    try:
        async with connection_pool.acquire() as connection:
            query = "SELECT nombre_usuario, saldo_virtual FROM usuarios WHERE es_admin = false ORDER BY saldo_virtual DESC"
            usuarios = await connection.fetch(query)
            lista_usuarios = [dict(usuario) for usuario in usuarios]
            return lista_usuarios
    except Exception as e:
        print(f"Error al cargar usuarios: {e}")
        raise