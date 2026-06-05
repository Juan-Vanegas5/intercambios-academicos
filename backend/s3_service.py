import os
import boto3
from fastapi import HTTPException, UploadFile
from botocore.exceptions import NoCredentialsError

# --- Configuración S3 ---
S3_CLIENT = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-2")
)
BUCKET_NAME = os.getenv("AWS_S3_BUCKET", "intercambios-upc-docs")

def subir_a_s3(file: UploadFile, folder: str) -> str:
    """Sube un archivo a S3 y devuelve su URL pública."""
    s3_key = f"uploads/{folder}/{file.filename}"
    try:
        # Asegurarse de que el puntero del archivo esté al inicio
        file.file.seek(0)
        S3_CLIENT.upload_fileobj(
            file.file, 
            BUCKET_NAME, 
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        region = os.getenv("AWS_REGION", "us-east-2")
        return f"https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{s3_key}"
    except Exception as e:
        print(f"Error subiendo a S3: {e}")
        raise HTTPException(status_code=500, detail="Error al subir archivo a la nube")

def descargar_de_s3(s3_url: str) -> bytes:
    """Descarga el contenido de un archivo de S3 a partir de su URL."""
    # Extraer el key de la URL: https://bucket.s3.region.amazonaws.com/uploads/folder/file.pdf
    # O simplemente usar la URL si es pública
    import requests
    try:
        response = requests.get(s3_url)
        response.raise_for_status()
        return response.content
    except Exception as e:
        # Si falla el GET, intentar vía boto3 por si no es público
        try:
            # key es la parte después del dominio
            # Ejemplo: https://intercambios-upc-docs.s3.us-east-2.amazonaws.com/uploads/1/archivo.pdf
            # El key sería uploads/1/archivo.pdf
            key = s3_url.split(".com/")[-1]
            obj = S3_CLIENT.get_object(Bucket=BUCKET_NAME, Key=key)
            return obj['Body'].read()
        except Exception as e2:
            print(f"Error descargando de S3: {e2}")
            return None
