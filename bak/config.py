import json
import os


def load_config():
    """Load configuration from config.json file."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        return {
            'vault_path': config.get('vault_path', "D:\\yo"),
            'journals_dir': config.get('journals_dir', "D:\\yo\\02 - Daily Notes"),
            'llm_endpoint': config.get('llm_endpoint', "http://localhost:1234/v1"),
            'llm_model': config.get('llm_model', "openai/gpt-oss-20b"),
            'llm_api_key': config.get('llm_api_key', "lm-studio")
        }
    except FileNotFoundError:
        print("Error: No se encontró config.json. Usando valores por defecto.")
        return {
            'vault_path': "D:\\yo",
            'journals_dir': "D:\\yo\\02 - Daily Notes",
            'llm_endpoint': "http://127.0.0.1:11434/v1",
            'llm_model': "qwen2.5:7b",
            'llm_api_key': "dummy"
        }
    except Exception as e:
        print(f"Error al cargar config.json: {e}")
        exit(1)
