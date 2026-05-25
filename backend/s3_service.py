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
    """Devuelve un cliente S3. En EC2 usa el IAM Role automáticamente."""
    return boto3.client("s3", region_name=AWS_REGION)


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
