\c postgres;

DROP DATABASE IF EXISTS tfg;

CREATE DATABASE tfg;

\c tfg;

CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,         
    nombre_usuario VARCHAR(50) UNIQUE NOT NULL,  
    correo_electronico VARCHAR(100) UNIQUE NOT NULL, 
    contrasenna VARCHAR(255) NOT NULL,   
    es_admin BOOLEAN DEFAULT FALSE,
    saldo_virtual NUMERIC(15, 2)
);

CREATE TABLE cartera (
    id_cartera SERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuarios(id_usuario) ON DELETE CASCADE, 
    simbolo_activo VARCHAR(10) NOT NULL,    
    stop_loss NUMERIC(15, 4),
    take_profit NUMERIC(15,4), 
    numero_acciones NUMERIC(30, 15) NOT NULL,        
    precio_promedio_compra NUMERIC(30, 15) NOT NULL
);

CREATE TABLE transacciones (
    id_transaccion SERIAL PRIMARY KEY,  
    id_usuario INT REFERENCES usuarios(id_usuario) ON DELETE CASCADE,  
    simbolo_activo VARCHAR(10) NOT NULL,     
    tipo_transaccion VARCHAR(10) NOT NULL CHECK (tipo_transaccion IN ('compra', 'venta')), 
    monto_total NUMERIC(15, 4) NOT NULL,       
    precio NUMERIC(30, 15) NOT NULL,          
    numero_acciones NUMERIC(30, 15)NOT NULL,     
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
);
