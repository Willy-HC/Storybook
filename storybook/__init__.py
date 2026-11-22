"""Storybook: generación local de cuentos ilustrados con voz y ambientación sonora."""
# Importar config primero fija las variables de entorno de Hugging Face
# (carpeta local de modelos, modo offline) ANTES de importar diffusers/transformers.
from . import config  # noqa: F401

__version__ = "1.0.0"
