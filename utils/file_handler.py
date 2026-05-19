import os
import hashlib
from utils.logger_handler import logger

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_file_md5_hex(filepath: str):
    """Compute the MD5 hex digest of a file."""
    if not os.path.exists(filepath):
        logger.error(f"[MD5] File not found: {filepath}")
        return None
    if not os.path.isfile(filepath):
        logger.error(f"[MD5] Path is not a file: {filepath}")
        return None

    md5_obj = hashlib.md5()
    chunk_size = 4096
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)
        return md5_obj.hexdigest()
    except Exception as e:
        logger.error(f"[MD5] Failed to compute hash for {filepath}: {str(e)}")
        return None


def listdir_with_allowed_type(path: str, allowed_types: tuple[str]):
    """List files in a directory filtered by allowed extensions."""
    files = []
    if not os.path.isdir(path):
        logger.error(f"[listdir] Not a directory: {path}")
        return tuple(files)

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))
    return tuple(files)


def pdf_loader(filepath: str, password=None) -> list[Document]:
    return PyPDFLoader(filepath, password=password).load()


def txt_loader(filepath: str) -> list[Document]:
    return TextLoader(filepath, encoding="utf-8").load()
