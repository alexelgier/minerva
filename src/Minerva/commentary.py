from .llm_utils import call_llm
from .prompts import (
    IDENTIFY_COMMENTS_SYSTEM_PROMPT,
    IDENTIFY_COMMENTS_USER_PROMPT,
    GENERATE_COMMENTS_SYSTEM_PROMPT,
    GENERATE_COMMENTS_USER_PROMPT,
    GENERAL_COMMENT_SYSTEM_PROMPT,
    GENERAL_COMMENT_USER_PROMPT
)


def identify_comment_points(narrative, glossary):
    """Identify points in the narrative where comments could be made and generate questions."""
    glossary_context = ""
    if glossary:
        glossary_context = "### Glosario de conceptos (para informar tus preguntas)\n"
        for note, concept in glossary.items():
            glossary_context += f"- {note}: {concept}\n"

    message = IDENTIFY_COMMENTS_USER_PROMPT.format(
        glossary=glossary_context,
        narrative=narrative
    )
    response = call_llm(message, IDENTIFY_COMMENTS_SYSTEM_PROMPT)
    return parse_points_and_questions(response)


def parse_points_and_questions(response):
    """Parse the LLM response to extract fragments and questions."""
    lines = response.split('\n')
    points = []
    current_fragment = None
    current_question = None

    for line in lines:
        line = line.strip()
        if line.startswith('**Fragmen'):
            if current_fragment and current_question:
                points.append((current_fragment, current_question))
            current_fragment = line.replace('**Fragmento:**', '').strip().strip('"')
            current_question = None
        elif line.startswith('**Pregunta:**'):
            current_question = line.replace('**Pregunta:**', '').strip().strip('"')
        elif current_fragment and not current_question and line and not line.startswith('-'):
            current_question = line

    if current_fragment and current_question:
        points.append((current_fragment, current_question))

    return points


def interact_with_questions(points):
    """Interact with the user to answer the generated questions."""
    if not points:
        return []

    print("\n=== PREGUNTAS ESPECÍFICAS ===")
    answers = []
    for i, (fragment, question) in enumerate(points, 1):
        print(f"\nFragmento: {fragment}")
        print(f"{i}. {question}")
        answer = input("Tu respuesta (enter para omitir): ").strip()
        if answer:
            answers.append((fragment, question, answer))

    return answers


def generate_comments(narrative, points_with_answers, glossary):
    """Generate comments for the identified points using the answers."""
    system_prompt = "Eres un asistente de escritura. Sugiere comentarios breves en segunda persona ('vos') para insertar en la narrativa. Cada comentario debe ser relevante al contexto, usando elementos de la narrativa, el glosario, las respuestas del usuario y, cuando sea útil, tu conocimiento general. Usa el formato <!--categoría: comentario-->."

    glossary_context = ""
    if glossary:
        glossary_context = "Glosario de conceptos:\n"
        for note, concept in glossary.items():
            glossary_context += f"- {note}: {concept}\n"

    points_text = ""
    for fragment, question, answer in points_with_answers:
        points_text += f"- Fragmento: {fragment}\n  Pregunta: {question}\n  Respuesta: {answer}\n"

    message = GENERATE_COMMENTS_USER_PROMPT.format(
        narrative=narrative,
        points_text=points_text,
        glossary_context=glossary_context
    )

    return call_llm(message, GENERATE_COMMENTS_SYSTEM_PROMPT)


def generate_general_comment(narrative, points_with_answers, glossary):
    """Generate a general comment at the end of the entry with a fixed format."""
    answers_context = ""
    if points_with_answers:
        answers_context = "Respuestas del usuario:\n"
        for fragment, question, answer in points_with_answers.items():
            answers_context += f"- Fragmento: {fragment}\n  Pregunta: {question}\n  Respuesta: {answer}\n"

    glossary_context = ""
    if glossary:
        glossary_context = "Glosario:\n"
        for note, concept in glossary.items():
            glossary_context += f"- {note}: {concept}\n"

    message = GENERAL_COMMENT_USER_PROMPT.format(
        glossary_context=glossary_context,
        answers_context=answers_context,
        narrative=narrative
    )

    return call_llm(message, GENERAL_COMMENT_SYSTEM_PROMPT)


def insert_general_comment(narrative, general_comment):
    """Insert the general comment at the end of the narrative."""
    return narrative + f"\n\n<!--comentario_general: {general_comment}-->"


def review_comments(narrative_with_comments):
    """Allow the user to review and edit suggested comments."""
    print("\n=== REVISIÓN DE COMENTARIOS ===")
    print("A continuación se muestra la narrativa con comentarios sugeridos:")
    print(narrative_with_comments)

    print("\n¿Deseas mantener todos los comentarios? (s/n)")
    if input().lower() == 's':
        return narrative_with_comments

    print("\nPor favor, edita la narrativa con los comentarios que desees mantener:")
    print("(Pega el texto completo con tus modificaciones)")
    return input()
