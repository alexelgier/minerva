import os
import re
from .file_utils import extract_frontmatter, update_frontmatter_with_summary
from .llm_utils import generate_summary_with_instruction

# Global cache
CACHE_VAULT = None


def extract_links(text):
    """Extract all wiki links from text."""
    return set(re.findall(r"\[\[(.*?)\]\]", text))


def has_concept_section(content):
    """Check if note has a ## Concept section."""
    return re.search(r"## Concepto", content) is not None


def extract_concept_section(content):
    """Extract content from ## Concept section."""
    concept_match = re.search(r"## Concepto\s*(.*?)(?=##|$)", content, re.DOTALL)
    return concept_match.group(1).strip() if concept_match else None


def has_summary_in_frontmatter(frontmatter):
    """Check if frontmatter has a 'resumen' field."""
    return frontmatter and 'resumen' in frontmatter


def build_vault_cache(vault_path):
    """Build a cache of all notes in the vault, indexed by filename."""
    global CACHE_VAULT
    if CACHE_VAULT is not None:
        return CACHE_VAULT

    print("Construyendo caché del vault...")
    CACHE_VAULT = {}

    for root, dirs, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                filename = file[:-3]
                CACHE_VAULT[filename] = full_path

                rel_path = os.path.relpath(full_path, vault_path)
                rel_path_key = rel_path.replace('\\', '/')[:-3]
                if rel_path_key != filename:
                    CACHE_VAULT[rel_path_key] = full_path

    print(f"Caché construido con {len(CACHE_VAULT)} entradas\n")
    return CACHE_VAULT


def build_glossary(links, vault_path):
    """Build a context glossary by searching for summaries in linked notes."""
    glossary = {}
    cache = build_vault_cache(vault_path)
    notes_without_summary = []

    # First pass: collect notes that need summary
    for link in links:
        if "|" in link:
            note, alias = link.split("|", 1)
        else:
            note = link
            alias = None

        note_path = None
        if note in cache:
            note_path = cache[note]
        else:
            base_name = os.path.basename(note)
            if base_name in cache:
                note_path = cache[base_name]

        if not note_path or not os.path.exists(note_path):
            print(f"Advertencia: No se encontró la nota '{note}' en el vault")
            continue

        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter = extract_frontmatter(content)

        # Check if already has summary in frontmatter
        if frontmatter and 'resumen' in frontmatter:
            glossary[link] = frontmatter['resumen']
            continue

        # Check if has Concept section
        concept = extract_concept_section(content)
        if concept:
            glossary[link] = concept
            # Save in frontmatter for future
            if frontmatter is None:
                frontmatter = {}
            frontmatter['resumen'] = concept
            update_frontmatter_with_summary(note_path, frontmatter, content)
            continue

        # If nothing, add to list of notes without summary
        notes_without_summary.append((link, note_path, content, frontmatter))

    # Second pass: process notes without summary
    if notes_without_summary:
        print(f"\n=== NOTAS SIN RESUMEN ===")
        print(f"Se encontraron {len(notes_without_summary)} notas sin resumen.")

        for i, (link, note_path, content, frontmatter) in enumerate(notes_without_summary, 1):
            print(f"\n[{i}/{len(notes_without_summary)}] Nota: {link}")
            print("Opciones:")
            print("1. Escribir resumen manualmente")
            print("2. Generar resumen con LLM")
            print("3. Omitir esta nota")
            print("4. Omitir todas las notas restantes")

            option = input("Elige una opción (1/2/3/4): ").strip()

            if option == '4':
                break
            elif option == '3':
                continue
            elif option == '1':
                summary = input("Escribe el resumen: ").strip()
            elif option == '2':
                instruction = input("Instrucciones para el LLM (opcional, presiona Enter para omitir): ").strip()
                print("Generando resumen con LLM...")
                summary = generate_summary_with_instruction(link, content, instruction)
                print(f"Resumen generado: {summary}")
            else:
                continue

            if summary:
                glossary[link] = summary
                if frontmatter is None:
                    frontmatter = {}
                frontmatter['resumen'] = summary
                update_frontmatter_with_summary(note_path, frontmatter, content)

    return glossary
