import os
import yaml
from datetime import datetime


def find_daily_file(journals_dir, date=None):
    """Find today's journal file or a specific date's file."""
    if date is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = date

    file_path = os.path.join(journals_dir, f"{date_str}.md")

    if not os.path.exists(file_path):
        print(f"Error: No se encontró el archivo para la fecha ({date_str}).md")
        return None

    return file_path


def read_file(file_path):
    """Read file content and return text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error al leer el archivo {file_path}: {e}")
        return ""


def extract_frontmatter(content):
    """Extract YAML frontmatter from note content."""
    if not content.startswith('---'):
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None

    frontmatter_text = parts[1].strip()
    try:
        return yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return None


def update_frontmatter_with_summary(file_path, frontmatter, content):
    """Update note frontmatter adding a 'resumen' field."""
    yaml_text = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            new_content = f"---\n{yaml_text}---\n{parts[2]}"
        else:
            new_content = f"---\n{yaml_text}---\n"
    else:
        new_content = f"---\n{yaml_text}---\n{content}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


def write_enriched_file(file_path, scores, metadata, summary, final_narrative):
    """Write the final file with YAML frontmatter and enriched narrative."""
    frontmatter = {
        'fecha': datetime.now().strftime("%Y-%m-%d"),
        'tags': ['daily'],
        'scores': scores
    }

    frontmatter.update(metadata)

    if summary:
        frontmatter['resumen_llm'] = summary

    yaml_text = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"---\n{yaml_text}---\n\n{final_narrative}\n")

    print(f"\n✅ Diario enriquecido guardado en: {file_path}")
