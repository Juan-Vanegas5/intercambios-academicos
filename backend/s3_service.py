<<<<<<< HEAD
"""
s3_service.py — Utilidades para subir y descargar documentos PDF desde AWS S3.

Variables de entorno requeridas:
  AWS_S3_BUCKET    Nombre del bucket (ej: intercambios-upc-docs)
  AWS_REGION       Región del bucket (ej: us-east-1)

Credenciales: en EC2 se resuelven automáticamente via IAM Role (sin ACCESS_KEY ni SECRET).
Para desarrollo local se puede usar AWS CLI (`aws configure`) o variables de entorno
AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY.
"""

import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "intercambios-upc-docs")
AWS_REGION    = os.getenv("AWS_REGION", "us-east-2")


def _client():
    """Devuelve un cliente S3. endpoint_url regional evita SignatureDoesNotMatch con IAM Role en EC2."""
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com"
    )


def subir_documento(contenido: bytes, s3_key: str, mimetype: str = "application/pdf") -> str:
    """
    Sube un archivo a S3 y devuelve el s3_key.
    El objeto se guarda como privado (sin acceso público).
    """
    client = _client()
    client.put_object(
        Bucket=AWS_S3_BUCKET,
        Key=s3_key,
        Body=contenido,
        ContentType=mimetype,
        ServerSideEncryption="AES256",  # cifrado en reposo
    )
    return s3_key


def generar_url_descarga(s3_key: str, expira_segundos: int = 300) -> str:
    """
    Genera una URL prefirmada (presigned URL) válida por `expira_segundos` segundos.
    El admin puede usarla para descargar el PDF directamente desde el navegador.
    """
    client = _client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": s3_key},
        ExpiresIn=expira_segundos,
    )
    return url


def eliminar_documento(s3_key: str) -> None:
    """Borra un objeto de S3 (se usa al reemplazar documentos)."""
    client = _client()
    try:
        client.delete_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
    except ClientError as e:
        # Si no existe, no es un error crítico
        print(f"[s3_service] No se pudo eliminar {s3_key}: {e}")
=======
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
>>>>>>> main
