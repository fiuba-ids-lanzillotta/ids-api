"""
Config compartida de pytest.

Fija credenciales dummy de Supabase antes de importar la app, para que el
cliente se pueda construir sin depender del entorno real. Los tests cubren
funciones puras (validaciones, parser de CSV, lógica de calendario) y no
hacen llamadas de red.
"""
import os

os.environ.setdefault('SUPABASE_URL', 'http://localhost:54321')
os.environ.setdefault('SUPABASE_KEY', 'test-key')
