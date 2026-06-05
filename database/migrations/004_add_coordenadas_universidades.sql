-- Migración 004: Agregar coordenadas geográficas a universidades
-- Ejecutar una sola vez contra la base de datos en producción (AWS RDS)

ALTER TABLE universidades
  ADD COLUMN IF NOT EXISTS latitud  DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS longitud DOUBLE PRECISION,
  ADD COLUMN IF NOT EXISTS ciudad   VARCHAR(150);

-- Actualizar coordenadas de universidades con convenio UPC
-- Argentina
UPDATE universidades SET latitud = -31.6107, longitud = -60.6970, ciudad = 'Santa Fe'
  WHERE nombre ILIKE '%Nacional del Litoral%';

-- Brasil
UPDATE universidades SET latitud = -12.9714, longitud = -38.5014, ciudad = 'Salvador'
  WHERE nombre ILIKE '%Federal da Bahia%';
UPDATE universidades SET latitud = -28.4832, longitud = -49.0063, ciudad = 'Tubarão'
  WHERE nombre ILIKE '%South Santa Catarina%' OR nombre ILIKE '%Sul de Santa Catarina%';

-- Canadá
UPDATE universidades SET latitud = 45.4215, longitud = -75.6972, ciudad = 'Ottawa'
  WHERE nombre ILIKE '%Canada Research Chair%' OR nombre ILIKE '%Architecture%Competition%';

-- Chile
UPDATE universidades SET latitud = -33.4489, longitud = -70.6693, ciudad = 'Santiago'
  WHERE nombre ILIKE '%Central de Chile%';
UPDATE universidades SET latitud = -33.4489, longitud = -70.6500, ciudad = 'Santiago'
  WHERE nombre ILIKE '%Universidad Mayor%' AND nombre NOT ILIKE '%San Marcos%';
UPDATE universidades SET latitud = -33.5199, longitud = -70.6150, ciudad = 'Santiago'
  WHERE nombre ILIKE '%Andrés Bello%';

-- España
UPDATE universidades SET latitud = 42.4650, longitud = -2.4456, ciudad = 'Logroño'
  WHERE nombre ILIKE '%La Rioja%' AND nombre NOT ILIKE '%Nacional%';
UPDATE universidades SET latitud = 37.3886, longitud = -5.9823, ciudad = 'Sevilla'
  WHERE nombre ILIKE '%Sevilla%';
UPDATE universidades SET latitud = 42.3439, longitud = -3.6969, ciudad = 'Burgos'
  WHERE nombre ILIKE '%Isabel I%';

-- Estados Unidos
UPDATE universidades SET latitud = 37.7749, longitud = -122.4194, ciudad = 'San Francisco'
  WHERE nombre ILIKE '%San Francisco%' AND nombre NOT ILIKE '%Piloto%';

-- Italia
UPDATE universidades SET latitud = 45.4654, longitud = 9.1859, ciudad = 'Milán'
  WHERE nombre ILIKE '%Marangoni%';

-- México
UPDATE universidades SET latitud = 19.4978, longitud = -99.1469, ciudad = 'Ciudad de México'
  WHERE nombre ILIKE '%Politécnico Nacional%' OR nombre ILIKE '%IPN%';
UPDATE universidades SET latitud = 19.3241, longitud = -99.1750, ciudad = 'Ciudad de México'
  WHERE nombre ILIKE '%Autónoma de México%' OR nombre ILIKE '%UNAM%';
UPDATE universidades SET latitud = 25.6866, longitud = -100.3161, ciudad = 'Monterrey'
  WHERE nombre ILIKE '%Monterrey%';
UPDATE universidades SET latitud = 19.0737, longitud = -104.3264, ciudad = 'Manzanillo'
  WHERE nombre ILIKE '%Manzanillo%';
UPDATE universidades SET latitud = 19.3639, longitud = -99.0038, ciudad = 'Ciudad de México'
  WHERE nombre ILIKE '%Autónoma Metropolitana%';
UPDATE universidades SET latitud = 19.2833, longitud = -99.6553, ciudad = 'Toluca'
  WHERE nombre ILIKE '%Estado de México%';
UPDATE universidades SET latitud = 20.6597, longitud = -103.3496, ciudad = 'Guadalajara'
  WHERE nombre ILIKE '%Guadalajara%';
UPDATE universidades SET latitud = 21.0190, longitud = -101.2574, ciudad = 'Guanajuato'
  WHERE nombre ILIKE '%Guanajuato%';
UPDATE universidades SET latitud = 22.7709, longitud = -102.5833, ciudad = 'Zacatecas'
  WHERE nombre ILIKE '%Zacatecas%';
UPDATE universidades SET latitud = 20.5236, longitud = -100.8152, ciudad = 'Celaya'
  WHERE nombre ILIKE '%Celaya%';
UPDATE universidades SET latitud = 19.4978, longitud = -99.1469, ciudad = 'Ciudad de México'
  WHERE nombre ILIKE '%Ducens%';
UPDATE universidades SET latitud = 19.4978, longitud = -99.1469, ciudad = 'Ciudad de México'
  WHERE nombre ILIKE '%INQBA%';

-- Panamá
UPDATE universidades SET latitud = 8.9936, longitud = -79.5197, ciudad = 'Ciudad de Panamá'
  WHERE nombre ILIKE '%ISTHMUS%';
UPDATE universidades SET latitud = 8.9936, longitud = -79.5197, ciudad = 'Ciudad de Panamá'
  WHERE nombre ILIKE '%ESEM%';

-- Perú
UPDATE universidades SET latitud = -12.0464, longitud = -77.0428, ciudad = 'Lima'
  WHERE nombre ILIKE '%Católica del Perú%';
UPDATE universidades SET latitud = -12.0964, longitud = -77.0234, ciudad = 'Lima'
  WHERE nombre ILIKE '%Ricardo Palma%';
UPDATE universidades SET latitud = -12.0875, longitud = -77.0553, ciudad = 'Lima'
  WHERE nombre ILIKE '%Ciencias Aplicadas%' OR nombre ILIKE '%UPC%' AND nombre ILIKE '%Perú%';
UPDATE universidades SET latitud = -12.1089, longitud = -77.0485, ciudad = 'Lima'
  WHERE nombre ILIKE '%Autónoma del Perú%';
UPDATE universidades SET latitud = -12.0566, longitud = -77.0836, ciudad = 'Lima'
  WHERE nombre ILIKE '%Mayor de San Marcos%';
UPDATE universidades SET latitud = -15.8402, longitud = -70.0219, ciudad = 'Puno'
  WHERE nombre ILIKE '%Altiplano%';

-- República Dominicana
UPDATE universidades SET latitud = 18.4861, longitud = -69.9312, ciudad = 'Santo Domingo'
  WHERE nombre ILIKE '%Iberoamericana%' OR nombre ILIKE '%UNIBE%';

-- Taiwán
UPDATE universidades SET latitud = 24.2580, longitud = 120.6944, ciudad = 'Taichung'
  WHERE nombre ILIKE '%Providence%';

-- Israel
UPDATE universidades SET latitud = 32.0853, longitud = 34.7818, ciudad = 'Tel Aviv'
  WHERE nombre ILIKE '%Check Point%';

-- Portugal
UPDATE universidades SET latitud = 40.2033, longitud = -8.4103, ciudad = 'Coimbra'
  WHERE nombre ILIKE '%Coimbra%';

-- Venezuela
UPDATE universidades SET latitud = 10.4806, longitud = -66.9036, ciudad = 'Caracas'
  WHERE nombre ILIKE '%Andrés Bello%' AND nombre ILIKE '%Católica%';
