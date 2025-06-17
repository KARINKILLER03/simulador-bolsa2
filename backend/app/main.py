from fastapi import FastAPI, HTTPException, Body, Request, Depends
from fastapi_utils.tasks import repeat_every
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from .dbHelper import *
from .priceConsultor import *


# Inicialización de la base de datos y configuración de la aplicación FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        await acciones_automaticas()
        yield
    finally:
        await close_db()

app = FastAPI(lifespan=lifespan)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de la sesión
app.add_middleware(
    SessionMiddleware, 
    secret_key=";vsW9t-G,ca@_!00m!LNmlVw",
    session_cookie="session_cookie",
    same_site="none",
    https_only=True
)

# Configuración de las acciones automáticas que se realizarán cada 10 minutos
@repeat_every(seconds=600) 
async def acciones_automaticas():
    print("Ejecutando acciones automáticas...")
    transacciones = await transacciones_automaticas()
    ventas_a_realizar = await verificar_ventas_automaticas(transacciones)
    await realizar_ventas_automaticas(ventas_a_realizar)
    print("Acciones automáticas completadas.")


#Función para realizar las acciones automáticas detectadas
async def realizar_ventas_automaticas(ventas_a_realizar):
    for venta in ventas_a_realizar:
        usuario = venta[0]
        activo = venta[1]
        num_acciones = venta[2]
        cantidad = venta[6]
        try:
            await actualizar_saldo(usuario, -cantidad) 
            precio = await obtener_valor_actual(activo)
            await registrar_venta(usuario, activo, float(cantidad), precio)
            await eliminar_todas_acciones(usuario, activo)
            print(f"Venta automática realizada para {usuario} de {num_acciones} acciones de {activo}.")
        except Exception as e:
            print(f"Error al realizar la venta automática para {usuario} de {num_acciones} acciones de {activo}: {e}")

@app.head("/keepalive")
async def keepalive():
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "message": "Simulador de bolsa activo"
    }

#Función para extraer el nombre de usuario actual de la sesión
async def get_current_user(request: Request):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="No autenticado")
    return username

#Función para comprobar si el usuario es administrador
async def check_admin(username: str = Depends(get_current_user)):
    if await es_admin(username):
        return True
    else:
        return False

#Ruta para validar el login del usuario
@app.post("/login")
async def login(request: Request, username: str = Body(...), password: str = Body(...)):
    try:
        if await validarLogin(username, password):
            request.session["username"] = username
            print(request.session["username"])
            if await check_admin(username):
                return {"ruta": "/adminPanel"}
            else:
                return {"ruta": "/market"}
        else:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


#Ruta para comprobar si el usuario ha iniciado sesión
@app.get("/session-status")
async def session_status(request: Request):
    print("Sesión actual:", request.session)
    username = request.session.get("username")
    return {
        "authenticated": bool(username),
        "username": username
    }

#Ruta para comprobar si el usuario ha iniciado sesión y es administrador
@app.get("/session-status-admin")
async def session_status(request: Request):
    username = request.session.get("username")
    if await es_admin(username):
        return{
            "es_admin": "True",
        }
    else:
        return{
            "es_admin": "False",
        }

# Ruta para registrar un nuevo usuario
@app.post("/register")
async def register(email: str = Body(...), username: str = Body(...), password: str = Body(...)):
    try:
        await registrarUsuario(email, username, password)
        return {"message": "Usuario registrado correctamente", "username": username}
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="El nombre de usuario o correo ya están en uso")
    except Exception as e:
        print(f"Error en la ruta /register: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Ruta para consultar datos de un activo
@app.get("/consult")
async def consult(activo: str, periodo: str):
    print("Entramos en el endpoint de consult")
    try:
        datos_activo = await obtener_datos_activo(activo, periodo)
        return {"datos": datos_activo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ruta para obtener el valor actual de un activo y el saldo disponible del usuario
@app.get("/datos-pre-transaccion-compra")
async def datos_pre_transaccion(
    activo: str, 
    usuario: str = Depends(get_current_user)
):
    try:
        precio_activo = await obtener_valor_actual(activo)
        saldo_disponible = await consultar_saldo_disponible(usuario)
        return {
            "precioActivo": precio_activo,
            "saldoDisponible": saldo_disponible
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# Ruta para comprar acciones
@app.post("/comprar-acciones")
async def comprar_acciones(activo: str = Body(...), cantidad: float = Body(...), stopLoss: float = Body(0), takeProfit: float = Body(0), usuario: str = Depends(get_current_user)):
    try:
        
        precio = await obtener_valor_actual(activo)
        saldo = await consultar_saldo_disponible(usuario)
        print("Estamos comprando acciones")
        if saldo < cantidad:
            raise HTTPException(400, "Saldo insuficiente")
            
        await actualizar_cartera(usuario, activo, cantidad, precio, stopLoss, takeProfit)
        await actualizar_saldo(usuario, cantidad)
        await registrar_compra(usuario, activo, cantidad, precio)


        return {"message": "Compra realizada exitosamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")

# Ruta para obtener datos previos a la transacción de venta
@app.get("/datos-pre-transaccion-venta")
async def datos_pre_transaccion_venta(
    activo: str, 
    usuario: str = Depends(get_current_user)
):
    try:
        precio_activo = await obtener_valor_actual(activo)
        print("el precio del activo es: "+ str(precio_activo))
        numAcciones = await consultar_cantidad_acciones(usuario, activo)
        numAcciones = float(numAcciones)  
        print("El número de acciones que tiene es: " + str(numAcciones))
        cantidadDisponible = (numAcciones * precio_activo)
        print("La multiplicación es el saldo total del activo, que es: " + str(cantidadDisponible))
        return {
            "precioActivo": precio_activo,
            "numAcciones": numAcciones,
            "cantidadDisponible": cantidadDisponible
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    
# Ruta para vender acciones
@app.post("/vender-acciones")
async def vender_acciones(activo: str,cantidad: float,usuario: str = Depends(get_current_user)):
    try:
        precio = await obtener_valor_actual(activo)
        
        if cantidad <= 0:
            raise HTTPException(400, "Cantidad no válida")
            
        # Comprobar si el usuario tiene suficientes acciones para vender
        precio_activo = await obtener_valor_actual(activo)
        #Consultar cuantas acciones tiene el usuario de este activo y devolver 
        numAcciones = await consultar_cantidad_acciones(usuario, activo)
        numAcciones = float(numAcciones)  # Asegurarse de que sea un número flotante
        cantidadDisponible = round(numAcciones * precio_activo, 4)

        if cantidadDisponible < cantidad:
            raise HTTPException(400, "No tienes suficientes acciones para vender")
            
        await actualizar_saldo(usuario, -cantidad)  # Vender implica sumar al saldo
        await registrar_venta(usuario, activo, cantidad, precio)
        await eliminar_acciones(usuario, activo, cantidad)
        
        return {"message": "Venta realizada exitosamente"}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error interno: {str(e)}")   

#Ruta para cargar los activos del perfil del usuario
@app.get("/cargar-activos-perfil")
async def cargar_perfil(usuario: str = Depends(get_current_user)):
    try:
        return await cargarPerfil(usuario)
    except Exception as e:
        raise HTTPException(500, str(e))

# Ruta para cargar las transacciones del perfil del usuario
@app.get("/cargar-transacciones-perfil")
async def cargar_transacciones_perfil(usuario: str = Depends(get_current_user)):
    try:
        return await cargarTransaccionesPerfil(usuario)
    except Exception as e:
        raise HTTPException(500, str(e))
    
# Ruta para reiniciar un usuario
@app.post("/reinicio")
async def reinicio(usuario: str = Depends(get_current_user)):
    try:
        await reiniciar(usuario)
        return {"message": "Cartera reiniciada correctamente"}
    except Exception as e:
        raise HTTPException(500, str(e))
    
# Ruta para cerrar sesión
@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Sesión cerrada"}

# Ruta para cargar todas las transacciones de un usuario
@app.get("/cargar-todas-transacciones")
async def cargar_todas_transacciones(usuario: str = Depends(get_current_user)):
    try:
        return await cargarTodasLasTransacciones(usuario)
    except Exception as e:
        raise HTTPException(500, str(e))


# Ruta para cargar la página del administrador
@app.get('/cargar-pagina-admin')
async def cargar_pagina_admin(usuario: str = Depends(get_current_user)):
    try:
        if await es_admin(usuario):
            usuariosYSaldos = await cargar_usuarios()
            return {"usuariosYSaldos" : usuariosYSaldos}

            
        else:
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ruta para reiniciar a un usuario forzadamente
@app.post('/reiniciar-forzado')
async def reiniciar_forzado(admin: str = Depends(get_current_user), nombre_usuario: str = Body(...)):
    try:
        if await es_admin(admin):
            await reiniciar(nombre_usuario)
            return {"message": "Cartera del usuario " + nombre_usuario + " reiniciada correctamente"}
        else:
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))