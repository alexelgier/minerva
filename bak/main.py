import argparse
from backend.minerva import load_config
from backend.minerva.file_utils import find_daily_file, read_file, write_enriched_file
from backend.minerva.scoring import extract_sections, calculate_scores
from backend.minerva.linking import extract_links, build_glossary
from backend.minerva.commentary import (
    identify_comment_points,
    interact_with_questions,
    generate_comments,
    generate_general_comment,
    insert_general_comment
)
from backend.minerva.llm_utils import correct_spelling, generate_summary
from backend.minerva.metadata import suggest_metadata, interact_with_metadata


def main():
    """Main function that orchestrates the entire process."""
    # Load configuration
    config = load_config()

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Enriquece diarios con LLM')
    parser.add_argument('--date', help='Fecha específica (YYYY-MM-DD) para procesar', default=None)
    args = parser.parse_args()

    print("=== ENRIQUECIMIENTO DE DIARIO CON LLM ===\n")

    # Step 1: Find and read file
    daily_file = find_daily_file(config['journals_dir'], args.date)
    if not daily_file:
        return

    content = read_file(daily_file)

    # Step 2: Extract and calculate scores
    sections = extract_sections(content)
    scores = calculate_scores(sections)

    # Extract narrative (assuming it's before the scoring sections)
    narrative = content.split("- Imagen, Detalle:")[0].strip()

    # Step 3: Extract links and build glossary
    links = extract_links(narrative)
    glossary = build_glossary(links, config['vault_path'])

    # Step 4: Identify comment points and generate questions
    print("Identificando puntos para comentarios...")
    points = identify_comment_points(narrative, glossary)

    # Step 5: Interact with specific questions
    answers = interact_with_questions(points)

    # Step 6: Generate comments for the points
    print("Generando comentarios...")
    narrative_with_comments = generate_comments(narrative, answers, glossary)

    # Step 7: Generate general comment
    # TODO: Revisar este paso
    print("Generando comentario general...")
    general_comment = generate_general_comment(narrative, answers, glossary)

    # Step 8: Insert general comment
    final_narrative = insert_general_comment(narrative_with_comments, general_comment)

    # Step 9: Spelling correction
    print("Corrigiendo ortografía...")
    corrected_narrative = correct_spelling(final_narrative)

    if corrected_narrative:
        final_narrative = corrected_narrative

    # Step 10: Generate summary
    print("Generando resumen...")
    # TODO: Que sea en segunda/tercera persona
    summary = generate_summary(final_narrative)

    # Step 11: Suggest and confirm metadata
    print("Generando sugerencias de metadatos...")
    suggested_metadata = suggest_metadata(final_narrative)
    final_metadata = interact_with_metadata(suggested_metadata)

    # Step 12: Write final file
    # TODO: agregar respuestas a self-test (no el calculado), tambien respuestas de autoevaluacion (imegen, secuencia)
    write_enriched_file(daily_file, scores, final_metadata, summary, final_narrative)

    print("\n✅ Proceso completado. Diario enriquecido con LLM.")


if __name__ == "__main__":
    main()
