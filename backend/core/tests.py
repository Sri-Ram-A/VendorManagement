# python -m core.tests
import os
import django
# from backend.clients.cohere import call_cohere
# from docling.document_converter import DocumentConverter
# from pprint import pprint
# from pathlib import Path
# import re
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from loguru import logger

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()



# # 1. Docling Testing
# PDF_FILE_PATH = Path(
#     "/home/srirama/Documents/sr_proj/VendorManagement/data/PCI_DSS.pdf"
# )
# if not PDF_FILE_PATH.exists():
#     raise FileNotFoundError(f"Double check this path, file not found: {PDF_FILE_PATH}")

# converter = DocumentConverter()
# result = converter.convert(PDF_FILE_PATH)
# markdown = result.document.export_to_markdown()
# print(markdown)

# # 2. Model Testing with JSON
# system_prompt = """
# You are a JSON extraction engine.
# Return exactly
# {
#     "company": "...",
#     "compliant": true,
#     "year": 2026
# }
# """
# user_message = """
# NimbusPay LLC completed PCI DSS v4.0 assessment in February 2026.
# """
# response = call_cohere(
#     system_prompt=system_prompt,
#     user_message=user_message,
#     force_json=True,
# )

# print(type(response))
# print("*" * 70)
# print(response)
# print("*" * 70)

# # 3. Model Testing without JSON
# system_prompt = """
# You are a PCI-DSS compliance expert.
# Read the user's input and provide a concise professional summary in plain English.
# Do not return JSON.
# """

# user_message = """
# NimbusPay LLC completed a PCI DSS v4.0 assessment in February 2026.
# The assessment found the company compliant with all applicable requirements.
# The attestation is valid until February 2027.
# """

# response = call_cohere(
#     system_prompt=system_prompt,
#     user_message=user_message,
#     force_json=False,
# )

# print(type(response))
# print("*" * 70)
# print(response)
# print("*" * 70)


# # 4. Download chromaDB model
logger.info("Initializing ChromaDB default transformer model download workflow...")
try:
    # Invoking this class triggers the automatic download with visible streaming output
    embedding_engine = DefaultEmbeddingFunction()
    logger.success("Model successfully downloaded and saved to: ~/.cache/chroma/onnx_models/")
except Exception as e:
    logger.error(f"Download sequence failed: {e}")