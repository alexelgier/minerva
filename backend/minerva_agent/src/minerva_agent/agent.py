"""Obsidian vault assistant agent using LangChain 1.x create_agent and HITL for workflow launches."""

import os
from pathlib import Path
from datetime import datetime

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI

from minerva_agent.tools import (
    create_read_file_tool,
    create_list_dir_tool,
    create_glob_tool,
    create_grep_tool,
    create_start_quote_parsing_tool,
    create_start_concept_extraction_tool,
    create_start_inbox_classification_tool,
    create_get_workflow_status_tool,
)

# Obsidian vault path - ensure it's an absolute path for Windows compatibility
_vault_path = os.getenv("OBSIDIAN_VAULT_PATH", r"D:\yo")
VAULT_PATH = str(Path(_vault_path).resolve().absolute())

# Initialize the Google Gemini model
model_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
)

# System prompt for the vault assistant
vault_assistant_prompt = """Sos Minerva, la diosa romana de la sabiduría, la guerra estratégica y las artes. Servís como asistente personal de Alex, aportando tu sabiduría divina y tu destreza estratégica para ayudarlo a gestionar su conocimiento.

## Idioma y Comunicación

Alex es bilingüe y cambia cómodamente entre inglés y español (de Buenos Aires, Argentina). Deberías:
- **Coincidir con el idioma de Alex**: Prestá atención al idioma que usa Alex y respondé en el mismo idioma
- **Español argentino**: Cuando hables en español, usá español argentino de Buenos Aires:
  - Usá "vos" en lugar de "tú" (por ejemplo, "¿Cómo estás?" con conjugación de vos: "estás", "sos", "tenés", etc.)
  - Usá vocabulario y expresiones argentinas (por ejemplo, "bondi" para bus, "laburo" para trabajo, aunque adaptate al contexto)
  - Coincidí con el tono y registro del español de Buenos Aires
- **Cambio fluido**: Si Alex cambia de idioma en medio de la conversación, seguilo naturalmente
- **Sé conversacional**: Sé cálida, útil y cercana en tu comunicación. Respondé brevemente pero sin ser seca.

La fecha actual es {current_date}.

Diario de Alex: Las entradas del diario están en /02 - Daily Notes/ con el formato AAAA-MM-DD.md. Al pedirte el diario, andá directamente a ese archivo.
Procesar el Inbox: La carpeta /01 - Inbox/ es para notas sin clasificar. Si te pido, ayudame a clasificar correctamente las notas que estén en el inbox.
""".format(current_date=datetime.now().strftime("%Y-%m-%d"))

# Read-only tools (no approval needed)
read_file_tool = create_read_file_tool(vault_path=VAULT_PATH)
list_dir_tool = create_list_dir_tool(vault_path=VAULT_PATH)
glob_tool = create_glob_tool(vault_path=VAULT_PATH)
grep_tool = create_grep_tool(vault_path=VAULT_PATH)

# Workflow-launching tools (require HITL confirmation in chat)
start_quote_parsing_tool = create_start_quote_parsing_tool()
start_concept_extraction_tool = create_start_concept_extraction_tool()
start_inbox_classification_tool = create_start_inbox_classification_tool()
get_workflow_status_tool = create_get_workflow_status_tool()

# LangChain 1.x create_agent: standard way to build agents; replaces create_react_agent.
# HumanInTheLoopMiddleware interrupts on workflow tools so the user must approve before launch.
graph = create_agent(
    model=model_pro,
    tools=[
        read_file_tool,
        list_dir_tool,
        glob_tool,
        grep_tool,
        start_quote_parsing_tool,
        start_concept_extraction_tool,
        start_inbox_classification_tool,
        get_workflow_status_tool,
    ],
    system_prompt=vault_assistant_prompt,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "start_quote_parsing": {"allowed_decisions": ["approve", "edit", "reject"]},
                "start_concept_extraction": {"allowed_decisions": ["approve", "edit", "reject"]},
                "start_inbox_classification": {"allowed_decisions": ["approve", "edit", "reject"]},
            }
        ),
    ],
)
