-- ========================================
-- MIGRACIÓN: Agregar campos extendidos a itinerario_detalles
-- ========================================
-- Este script agrega las columnas necesarias para el contenido extenso
-- Ejecutar en SQLite Browser o pgAdmin
Select * from itinerario_detalles;
-- 1. Agregar columna historia_contextual (texto largo)
ALTER TABLE itinerario_detalles 
ADD COLUMN historia_contextual TEXT;

-- 2. Agregar columna datos_curiosos (JSON array)
ALTER TABLE itinerario_detalles 
ADD COLUMN datos_curiosos TEXT;

-- 3. Agregar columna que_observar (JSON array)
ALTER TABLE itinerario_detalles 
ADD COLUMN que_observar TEXT;

-- 4. Agregar columna puntos_clave (JSON array) - legacy
ALTER TABLE itinerario_detalles
ADD COLUMN puntos_clave TEXT;



