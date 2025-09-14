import os
import re
import yaml
import json
import argparse
from datetime import datetime
from openai import OpenAI

# Global variables that will be set from config
VAULT_PATH = None
JOURNALS_DIR = None
LLM_ENDPOINT = None
LLM_MODEL = None
LLM_API_KEY = None

# Variable global para el caché
CACHE_VAULT = None


def cargar_configuracion():
    """Carga la configuración desde config.py."""
    global VAULT_PATH, JOURNALS_DIR, LLM_ENDPOINT, LLM_MODEL, LLM_API_KEY

    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        VAULT_PATH = config.get('vault_path', "D:\\yo")
        JOURNALS_DIR = config.get('journals_dir', "D:\\yo\\02 - Daily Notes")
        LLM_ENDPOINT = config.get('llm_endpoint', "http://127.0.0.1:11434/v1")
        LLM_MODEL = config.get('llm_model', "qwen3:4b-q4_K_M")
        # LLM_MODEL = config.get('llm_model', "qwen2.5:14b")
        LLM_API_KEY = config.get('llm_api_key', "lm-studio")

    except FileNotFoundError:
        print("Error: No se encontró config.py. Usando valores por defecto.")
        # Valores por defecto si el archivo no existe
        VAULT_PATH = "D:\\yo"
        JOURNALS_DIR = "D:\\yo\\02 - Daily Notes"
        LLM_ENDPOINT = "http://127.0.0.1:11434/v1"
        LLM_MODEL = "qwen3:4b-q4_K_M"
        # LLM_MODEL = "qwen2.5:14b"
        LLM_API_KEY = "dummy"
    except Exception as e:
        print(f"Error al cargar config.py: {e}")
        exit(1)


# Inicializar cliente OpenAI después de cargar la configuración
cargar_configuracion()
client = OpenAI(base_url=LLM_ENDPOINT, api_key=LLM_API_KEY)


def encontrar_archivo_dia(fecha=None):
    """Encuentra el archivo del día actual o de una fecha específica en la carpeta de diarios."""
    if fecha is None:
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
    else:
        fecha_actual = fecha

    archivo_dia = os.path.join(JOURNALS_DIR, f"{fecha_actual}.md")

    if not os.path.exists(archivo_dia):
        print(f"Error: No se encontró el archivo para la fecha ({fecha_actual}).md")
        return None

    return archivo_dia


def leer_archivo(ruta_archivo):
    """Lee el contenido del archivo y devuelve el texto."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error al leer el archivo {ruta_archivo}: {e}")
        return ""


def extraer_secciones(texto):
    """Extrae las secciones PANAS, BPNS y Flourishing del texto."""
    secciones = {}

    # Extraer PANAS Positive
    panas_pos_match = re.search(
        r"## PANAS.*?Positive Affect.*?Interested::\s*(\d+).*?Excited::\s*(\d+).*?Strong::\s*(\d+).*?Enthusiastic::\s*(\d+).*?Proud::\s*(\d+).*?Alert::\s*(\d+).*?Inspired::\s*(\d+).*?Determined::\s*(\d+).*?Attentive::\s*(\d+).*?Active::\s*(\d+)",
        texto, re.DOTALL)
    if panas_pos_match:
        secciones['panas_pos'] = [int(val) for val in panas_pos_match.groups()]

    # Extraer PANAS Negative
    panas_neg_match = re.search(
        r"Negative Affect.*?Distressed::\s*(\d+).*?Upset::\s*(\d+).*?Guilty::\s*(\d+).*?Scared::\s*(\d+).*?Hostile::\s*(\d+).*?Irritable::\s*(\d+).*?Ashamed::\s*(\d+).*?Nervous::\s*(\d+).*?Jittery::\s*(\d+).*?Afraid::\s*(\d+)",
        texto, re.DOTALL)
    if panas_neg_match:
        secciones['panas_neg'] = [int(val) for val in panas_neg_match.groups()]

    # Extraer BPNS
    bpns_match = re.search(
        r"## BPNS.*?Autonomy.*?I feel like I can make choices about the things I do::\s*(\d+).*?I feel free to decide how I do my daily tasks::\s*(\d+).*?Competence.*?I feel capable at the things I do::\s*(\d+).*?I can successfully complete challenging tasks::\s*(\d+).*?Relatedness.*?I feel close and connected with the people around me::\s*(\d+).*?I get along well with the people I interact with daily::\s*(\d+).*?I feel supported by others in my life::\s*(\d+)",
        texto, re.DOTALL)
    if bpns_match:
        secciones['bpns'] = [int(val) for val in bpns_match.groups()]

    # Extraer Flourishing
    flour_match = re.search(
        r"## Flourishing Scale.*?I lead a purposeful and meaningful life::\s*(\d+).*?My social relationships are supportive and rewarding::\s*(\d+).*?I am engaged and interested in my daily activities::\s*(\d+).*?I actively contribute to the happiness and well-being of others::\s*(\d+).*?I am competent and capable in the activities that are important to me::\s*(\d+).*?I am a good person and live a good life::\s*(\d+).*?I am optimistic about my future::\s*(\d+).*?People respect me::\s*(\d+)",
        texto, re.DOTALL)
    if flour_match:
        secciones['flourishing'] = [int(val) for val in flour_match.groups()]

    return secciones


def calcular_scores(secciones):
    """Calcula los scores basados en las secciones extraídas."""
    scores = {}

    if 'panas_pos' in secciones:
        scores['panas_pos'] = sum(secciones['panas_pos'])
        scores['panas_pos_percent'] = (scores['panas_pos'] - 10) / 40 * 100  # Escala de 10-50 a 0-100%

    if 'panas_neg' in secciones:
        scores['panas_neg'] = sum(secciones['panas_neg'])
        scores['panas_neg_percent'] = (scores['panas_neg'] - 10) / 40 * 100

    if 'bpns' in secciones:
        autonomy = sum(secciones['bpns'][0:2])
        competence = sum(secciones['bpns'][2:4])
        relatedness = sum(secciones['bpns'][4:7])
        bpns_total = autonomy + competence + relatedness

        scores['bpns_autonomy'] = (autonomy - 2) / 12 * 100  # 2 items, min 2, max 14
        scores['bpns_competence'] = (competence - 2) / 12 * 100
        scores['bpns_relatedness'] = (relatedness - 3) / 18 * 100  # 3 items, min 3, max 21
        scores['bpns_total'] = (bpns_total - 7) / 42 * 100  # 7 items total, min 7, max 49

    if 'flourishing' in secciones:
        flourishing_total = sum(secciones['flourishing'])
        scores['flourishing'] = (flourishing_total - 8) / 48 * 100  # 8 items, min 8, max 56

    return scores


def extraer_enlaces(texto):
    """Extrae todos los enlaces wiki del texto."""
    return set(re.findall(r"\[\[(.*?)\]\]", texto))


def tiene_seccion_concepto(contenido):
    """Verifica si la nota tiene una sección ## Concepto."""
    return re.search(r"## Concepto", contenido) is not None


def extraer_seccion_concepto(contenido):
    """Extrae el contenido de la sección ## Concepto."""
    concepto_match = re.search(r"## Concepto\s*(.*?)(?=##|$)", contenido, re.DOTALL)
    return concepto_match.group(1).strip() if concepto_match else None


def tiene_resumen_frontmatter(frontmatter):
    """Verifica si el frontmatter tiene un campo 'resumen'."""
    return frontmatter and 'resumen' in frontmatter


def generar_resumen_con_instruccion(nombre_nota, contenido="", instruccion_usuario=""):
    """Genera un resumen conceptual conciso con instrucciones específicas del usuario."""
    system_prompt = "Eres un asistente para resúmenes conceptuales. Genera una descripción MUY BREVE (máximo 10-15 palabras) del concepto representado por la nota. Responde siempre en español, con una sola línea sin saltos de línea. Sé factual y evita agregar información no proporcionada explícitamente."

    base_prompt = f"Genera una descripción extremadamente concisa y factual para: {nombre_nota}"

    if contenido.strip() and len(contenido) > 50:
        base_prompt += f". Contexto: {contenido[:300]}"  # Limitar contexto a 300 caracteres

    if instruccion_usuario.strip():
        base_prompt += f". Instrucción adicional: {instruccion_usuario}"

    mensaje = f"{base_prompt}. Descripción concisa:"

    respuesta = llamar_llm(mensaje, system_prompt)

    # Limpiar la respuesta
    respuesta_limpia = respuesta.replace('\n', ' ').strip()
    respuesta_limpia = re.sub(r'\s+', ' ', respuesta_limpia)

    # Si la respuesta es demasiado larga, pedir una versión más corta
    palabras = respuesta_limpia.split()
    if len(palabras) > 20:
        mensaje_corto = f"La siguiente descripción es demasiado larga. Acórtala a máximo 15 palabras: {respuesta_limpia}. Descripción corta:"
        respuesta_corta = llamar_llm(mensaje_corto, system_prompt)
        respuesta_limpia = respuesta_corta.replace('\n', ' ').strip()
        respuesta_limpia = re.sub(r'\s+', ' ', respuesta_limpia)

    return respuesta_limpia


def construir_cache_vault():
    """Construye un caché de todas las notas en el vault, indexado por nombre de archivo."""
    global CACHE_VAULT
    if CACHE_VAULT is not None:
        return CACHE_VAULT

    print("Construyendo caché del vault...")
    CACHE_VAULT = {}

    for root, dirs, files in os.walk(VAULT_PATH):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                # Usar el nombre del archivo (sin extensión) como clave
                nombre_archivo = file[:-3]
                CACHE_VAULT[nombre_archivo] = full_path

                # También almacenar por nombre completo con ruta relativa
                rel_path = os.path.relpath(full_path, VAULT_PATH)
                rel_path_key = rel_path.replace('\\', '/')[:-3]  # Normalizar y quitar .md
                if rel_path_key != nombre_archivo:  # Solo si es diferente
                    CACHE_VAULT[rel_path_key] = full_path

    print(f"Caché construido con {len(CACHE_VAULT)} entradas\n")
    return CACHE_VAULT


def extraer_frontmatter(contenido):
    """Extrae el frontmatter YAML del contenido de una nota."""
    if not contenido.startswith('---'):
        return None

    # Buscar el cierre del frontmatter
    partes = contenido.split('---', 2)
    if len(partes) < 3:
        return None

    frontmatter_text = partes[1].strip()
    try:
        return yaml.safe_load(frontmatter_text)
    except yaml.YAMLError:
        return None


def actualizar_frontmatter_con_resumen(ruta_nota, frontmatter, contenido):
    """Actualiza el frontmatter de la nota añadiendo un campo 'resumen'."""
    # Reconstruir el contenido con el nuevo frontmatter
    yaml_text = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)

    if contenido.startswith('---'):
        # Si ya tenía frontmatter, reemplazarlo
        partes = contenido.split('---', 2)
        if len(partes) >= 3:
            nuevo_contenido = f"---\n{yaml_text}---\n{partes[2]}"
        else:
            nuevo_contenido = f"---\n{yaml_text}---\n"
    else:
        # Si no tenía frontmatter, añadirlo
        nuevo_contenido = f"---\n{yaml_text}---\n{contenido}"

    # Escribir el archivo actualizado
    with open(ruta_nota, 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)


def construir_glosario(enlaces):
    """Construye un glosario de contexto buscando resúmenes en las notas enlazadas."""
    glosario = {}
    cache = construir_cache_vault()
    notas_sin_resumen = []

    # Primera pasada: recolectar notas que necesitan resumen
    for enlace in enlaces:
        if "|" in enlace:
            nota, alias = enlace.split("|", 1)
        else:
            nota = enlace
            alias = None

        ruta_nota = None
        if nota in cache:
            ruta_nota = cache[nota]
        else:
            nombre_base = os.path.basename(nota)
            if nombre_base in cache:
                ruta_nota = cache[nombre_base]

        if not ruta_nota or not os.path.exists(ruta_nota):
            print(f"Advertencia: No se encontró la nota '{nota}' en el vault")
            continue

        with open(ruta_nota, 'r', encoding='utf-8') as f:
            contenido = f.read()

        frontmatter = extraer_frontmatter(contenido)

        # Verificar si ya tiene resumen en frontmatter
        if frontmatter and 'resumen' in frontmatter:
            glosario[enlace] = frontmatter['resumen']
            continue

        # Verificar si tiene sección Concepto
        concepto = extraer_seccion_concepto(contenido)
        if concepto:
            glosario[enlace] = concepto
            # Guardar en frontmatter para futuras ocasiones
            if frontmatter is None:
                frontmatter = {}
            frontmatter['resumen'] = concepto
            actualizar_frontmatter_con_resumen(ruta_nota, frontmatter, contenido)
            continue

        # Si no tiene nada, agregar a la lista de notas sin resumen
        notas_sin_resumen.append((enlace, ruta_nota, contenido, frontmatter))

    # Segunda pasada: procesar notas sin resumen
    if notas_sin_resumen:
        print(f"\n=== NOTAS SIN RESUMEN ===")
        print(f"Se encontraron {len(notas_sin_resumen)} notas sin resumen.")

        for i, (enlace, ruta_nota, contenido, frontmatter) in enumerate(notas_sin_resumen, 1):
            print(f"\n[{i}/{len(notas_sin_resumen)}] Nota: {enlace}")
            print("Opciones:")
            print("1. Escribir resumen manualmente")
            print("2. Generar resumen con LLM")
            print("3. Omitir esta nota")
            print("4. Omitir todas las notas restantes")

            opcion = input("Elige una opción (1/2/3/4): ").strip()

            if opcion == '4':
                break
            elif opcion == '3':
                continue
            elif opcion == '1':
                resumen = input("Escribe el resumen: ").strip()
            elif opcion == '2':
                # pedir instrucción directamente, si está vacía será como "N"
                instruccion = input("Instrucciones para el LLM (opcional, presiona Enter para omitir): ").strip()

                print("Generando resumen con LLM...")
                resumen = generar_resumen_con_instruccion(enlace, contenido, instruccion)
                print(f"Resumen generado: {resumen}")
            else:
                continue

            if resumen:
                glosario[enlace] = resumen
                if frontmatter is None:
                    frontmatter = {}
                frontmatter['resumen'] = resumen
                actualizar_frontmatter_con_resumen(ruta_nota, frontmatter, contenido)

    return glosario


def llamar_llm(mensaje, system_prompt=None):
    """Realiza una llamada al LLM local."""
    try:
        mensajes = []
        if system_prompt:
            mensajes.append({"role": "system", "content": system_prompt})
        mensajes.append({"role": "user", "content": mensaje})

        respuesta = client.chat.completions.create(
            model=LLM_MODEL,
            messages=mensajes,
            temperature=0.7
        )

        return respuesta.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error al llamar al LLM: {e}")
        return None


def identificar_puntos_comentario(narrativa, glosario):
    """Identifica puntos en la narrativa donde se podrían hacer comentarios y genera preguntas para cada punto."""
    system_prompt = """Eres un asistente especializado en analizar narrativas diarias escritas en español.  
Tu tarea es identificar fragmentos que puedan enriquecerse con más detalle y generar preguntas específicas en español sobre esos fragmentos.  

Reglas generales:  
- Siempre responde en español.  
- Para cada fragmento: cita el fragmento y luego formula una sola pregunta clara y específica.  
- Lee la narrativa completa antes de generar las preguntas. Evita formular preguntas cuya respuesta ya aparezca en otra parte del texto.  
- Sigue el orden cronológico de la narrativa original.  
- Mantén la densidad: las preguntas deben ser menos densas que el texto fuente (como máximo la mitad de palabras).  
- Usa el glosario provisto como conocimiento de fondo:  
  - Si un fragmento incluye un término del glosario, utiliza la información del glosario para hacer la pregunta más precisa o contextualizada.  
  - No inventes ni preguntes sobre términos del glosario que no aparezcan en la narrativa.  
- Prioriza en este orden: 1) Detalle fáctico, 2) Emociones, 3) Matices narrativos.  
- Evita preguntas vagas, repetitivas o sin relación con el fragmento.  
"""
    contexto_glosario = ""
    if glosario:
        contexto_glosario = "### Glosario de conceptos (para informar tus preguntas)\n"
        for nota, concepto in glosario.items():
            contexto_glosario += f"- {nota}: {concepto}\n"

    mensaje = f"""Analiza la siguiente narrativa diaria e identifica fragmentos que podrían enriquecerse con más detalle.  

Para cada fragmento:  
1. Cita textualmente el fragmento (aprox. 1 oración, más o menos según el flujo).  
2. Formula **una pregunta clara y específica en español** que permita ampliar el texto.  

⚠️ Importante: Antes de formular cada pregunta, revisa la narrativa completa para asegurarte de que la información no esté ya presente en otro fragmento. Solo haz preguntas que aporten información nueva o un ángulo distinto.  

### Ejemplos  
- Fragmento: “Desperté 1215, snooze, pesado.”  
  Pregunta: “¿Qué hizo que despertaras tan tarde hoy?”  

- Fragmento: “Almorcé [[Sandwich de Milanesa]], leí [[Lenin]].”  
  Pregunta: “¿Cómo estaba el sándwich de milanesa, lo preparaste vos o lo compraste?”  

- Fragmento: “Ana decidió no ir al GLED y hacer virtual, así está más tranquila.”  
  Pregunta: “¿Qué ventajas le dio a Ana la opción virtual en el GLED?”  

---

{contexto_glosario}

---

### Narrativa
{narrativa}
"""

    respuesta = llamar_llm(mensaje, system_prompt)
    return parsear_puntos_y_preguntas(respuesta)


def parsear_puntos_y_preguntas(respuesta):
    """Parsea la respuesta del LLM para extraer fragmentos y preguntas."""
    lineas = respuesta.split('\n')
    puntos = []
    current_fragmento = None
    current_pregunta = None

    for linea in lineas:
        linea = linea.strip()
        if linea.startswith('**Fragmento:**'):
            if current_fragmento and current_pregunta:
                puntos.append((current_fragmento, current_pregunta))
            current_fragmento = linea.replace('**Fragmento:**', '').strip().strip('"')
            current_pregunta = None
        elif linea.startswith('**Pregunta:**'):
            current_pregunta = linea.replace('**Pregunta:**', '').strip().strip('"')
        elif current_fragmento and not current_pregunta and linea and not linea.startswith('-'):
            # Si no hay pregunta definida pero hay fragmento, podríamos tomar la línea como pregunta
            current_pregunta = linea

    if current_fragmento and current_pregunta:
        puntos.append((current_fragmento, current_pregunta))

    return puntos


def interactuar_con_preguntas(puntos):
    """Interactúa con el usuario para responder las preguntas generadas."""
    if not puntos:
        return {}

    print("\n=== PREGUNTAS ESPECÍFICAS ===")
    respuestas = {}
    for i, (fragmento, pregunta) in enumerate(puntos, 1):
        print(f"\nFragmento: {fragmento}")
        print(f"{i}. {pregunta}")
        respuesta = input("Tu respuesta (enter para omitir): ").strip()
        if respuesta:
            respuestas[pregunta] = respuesta

    return respuestas


def generar_comentarios(narrativa, puntos, respuestas, glosario):
    """Genera comentarios para los puntos identificados, usando las respuestas."""
    system_prompt = "Eres un asistente de escritura. Sugiere comentarios breves en segunda persona ('vos') para insertar en la narrativa. Cada comentario debe ser relevante al contexto, usando elementos de la narrativa, el glosario, las respuestas del usuario y, cuando sea útil, tu conocimiento general. Usa el formato <!--categoría: comentario-->."
    # Preparar contexto de respuestas
    contexto_respuestas = ""
    for pregunta, respuesta in respuestas.items():
        contexto_respuestas += f"P: {pregunta}\nR: {respuesta}\n\n"

    contexto_glosario = ""
    if glosario:
        contexto_glosario = "Glosario de conceptos:\n"
        for nota, concepto in glosario.items():
            contexto_glosario += f"- {nota}: {concepto}\n"

    # Preparar lista de puntos identificados
    puntos_texto = ""
    for fragmento, pregunta in puntos:
        puntos_texto += f"- Fragmento: {fragmento}\n  Pregunta: {pregunta}\n"

    mensaje = f"""Dada la narrativa original, los puntos identificados con sus preguntas y respuestas, y el glosario de conceptos, genera comentarios breves para cada punto e insertalos directamente en la narrativa, justo después del fragmento correspondiente.

## Secciones incluidas
### Narrativa original
{narrativa}

### Puntos identificados con preguntas y respuestas:
{puntos_texto}
{contexto_respuestas}

### Glosario de conceptos:
{contexto_glosario}

## Reglas:
- Usar segunda persona ('vos').
- Máximo 15 palabras por comentario.
- Solo observaciones; no incluir sugerencias.
- Los comentarios deben ser relevantes al contexto и pueden integrar narrativa, respuestas, glosario y conocimiento general del modelo.
- Categorías disponibles: emocion, contexto, detalle, reflexion, relacion, proyecto, salud.

## Formato de salida:
La salida debe ser la narrativa completa con comentarios insertados en el lugar correcto, en el formato:
<!--categoría: comentario-->

Ejemplo de fragmento:
Desperte 1215, snooze, pesado. <!--salud: dormiste poco por la actividad de Lila durante la noche-->

Generá la narrativa completa con todos los comentarios insertados siguiendo este patrón.
"""

    return llamar_llm(mensaje, system_prompt)


def generar_comentario_general(narrativa, respuestas, glosario):
    """Genera un comentario general al final de la entrada, con formato fijo."""
    system_prompt = "Eres un asistente para reflexión personal. Genera un comentario general sobre el día, en segunda persona ('vos'), que resuma las emociones, eventos clave y aspectos destacados. Usa un formato fijo que facilite comparaciones diarias."

    contexto_respuestas = ""
    if respuestas:
        contexto_respuestas = "Respuestas del usuario:\n"
        for pregunta, respuesta in respuestas.items():
            contexto_respuestas += f"- {pregunta}: {respuesta}\n"

    contexto_glosario = ""
    if glosario:
        contexto_glosario = "Glosario:\n"
        for nota, concepto in glosario.items():
            contexto_glosario += f"- {nota}: {concepto}\n"

    mensaje = f"""Genera un comentario general sobre el día, basado en la narrativa y respuestas proporcionadas. El comentario debe ser en segunda persona ('vos') y seguir el siguiente formato:

[Emociones predominantes]: [descripción breve]
[Eventos clave]: [lista de eventos]
[Aspectos destacados]: [aspectos relevantes]

Ejemplo:
Emociones predominantes: alegría por el partido ganado y preocupación por Ana
Eventos clave: escape de gas, clase de canto, partido de fútbol
Aspectos destacados: buena performance en el fútbol, conversación con Ana sobre su padre

{contexto_glosario}
{contexto_respuestas}

Narrativa:
{narrativa}

Comentario general:"""

    return llamar_llm(mensaje, system_prompt)


def insertar_comentario_general(narrativa, comentario_general):
    """Inserta el comentario general al final de la narrativa."""
    return narrativa + f"\n\n<!--comentario_general: {comentario_general}-->"


def revisar_comentarios(narrativa_con_comentarios):
    """Permite al usuario revisar y editar los comentarios sugeridos."""
    print("\n=== REVISIÓN DE COMENTARIOS ===")
    print("A continuación se muestra la narrativa con comentarios sugeridos:")
    print(narrativa_con_comentarios)

    print("\n¿Deseas mantener todos los comentarios? (s/n)")
    if input().lower() == 's':
        return narrativa_con_comentarios

    # Si no quiere mantener todos, permitir edición manual
    print("\nPor favor, edita la narrativa con los comentarios que desees mantener:")
    print("(Pega el texto completo con tus modificaciones)")
    return input()


def corregir_ortografia(texto):
    """Corrige ortografía y gramática sin cambiar el contenido sustancial."""
    system_prompt = "Eres un corrector ortográfico y gramatical. Corrige solo errores de ortografía y gramática, sin cambiar el estilo o contenido sustancial."

    mensaje = f"""Corrige los errores ortográficos y gramaticales en el siguiente texto, pero mantén el estilo y contenido originales:

{texto}

Texto corregido:"""

    return llamar_llm(mensaje, system_prompt)


def generar_resumen(narrativa):
    """Genera un resumen conciso de la narrativa."""
    system_prompt = "Eres un asistente para resúmenes. Genera resúmenes concisos que capturen la esencia de un texto."

    mensaje = f"""Genera un resumen conciso en español de la siguiente entrada de diario:

{narrativa}

Resumen:"""

    return llamar_llm(mensaje, system_prompt)


def sugerir_metadatos(narrativa):
    """Sugiere metadatos semánticos basados en la narrativa."""
    system_prompt = "Eres un asistente para organización de información. Sugiere metadatos relevantes para categorizar contenido."

    mensaje = f"""Sugiere valores para los siguientes metadatos basados en la narrativa: clima, actividad_principal, lugar_principal, personas, proyectos, estado_predominante, sensacion_corporal.

Devuelve la respuesta en formato JSON con las claves mencionadas.

Narrativa:
{narrativa}

JSON:"""

    respuesta = llamar_llm(mensaje, system_prompt)

    try:
        # Intentar extraer JSON de la respuesta
        json_match = re.search(r'\{.*\}', respuesta, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except:
        return {}


def interactuar_metadatos(metadatos_sugeridos):
    """Permite al usuario confirmar o editar los metadatos sugeridos."""
    print("\n=== METADATOS SUGERIDOS ===")
    metadatos_finales = {}

    campos = [
        'clima', 'actividad_principal', 'lugar_principal',
        'personas', 'proyectos', 'estado_predominante', 'sensacion_corporal'
    ]

    for campo in campos:
        valor_sugerido = metadatos_sugeridos.get(campo, '')
        print(f"{campo}: {valor_sugerido}")

        respuesta = input(f"Ingresa valor para {campo} (enter para mantener, 'none' para omitir): ").strip()

        if respuesta.lower() == 'none':
            continue
        elif respuesta:
            # Convertir a lista si contiene comas
            if ',' in respuesta:
                metadatos_finales[campo] = [item.strip() for item in respuesta.split(',')]
            else:
                metadatos_finales[campo] = respuesta
        elif valor_sugerido:
            metadatos_finales[campo] = valor_sugerido

    return metadatos_finales


def escribir_archivo(ruta_archivo, scores, metadatos, resumen, narrativa_final):
    """Escribe el archivo final con frontmatter YAML y narrativa enriquecida."""
    # Preparar frontmatter
    frontmatter = {
        'fecha': datetime.now().strftime("%Y-%m-%d"),
        'tags': ['daily'],
        'scores': scores
    }

    # Agregar metadatos
    frontmatter.update(metadatos)

    # Agregar resumen si existe
    if resumen:
        frontmatter['resumen_llm'] = resumen

    # Convertir a YAML
    yaml_text = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)

    # Escribir archivo
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write(f"---\n{yaml_text}---\n\n{narrativa_final}\n")

    print(f"\n✅ Diario enriquecido guardado en: {ruta_archivo}")


def main():
    """Función principal que orquesta todo el proceso."""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description='Enriquece diarios con LLM')
    parser.add_argument('--date', help='Fecha específica (YYYY-MM-DD) para procesar', default=None)
    args = parser.parse_args()

    print("=== ENRIQUECIMIENTO DE DIARIO CON LLM ===\n")

    # Paso 1: Encontrar y leer archivo
    archivo_dia = encontrar_archivo_dia(args.date)
    if not archivo_dia:
        return

    contenido = leer_archivo(archivo_dia)

    # Paso 2: Extraer y calcular scores
    secciones = extraer_secciones(contenido)
    scores = calcular_scores(secciones)

    # Extraer narrativa (asumiendo que está antes de las secciones de scoring)
    narrativa = contenido.split("- Imagen, Detalle:")[0].strip()

    # Paso 3: Extraer enlaces y construir glosario
    enlaces = extraer_enlaces(narrativa)
    glosario = construir_glosario(enlaces)

    # Paso 4: Identificar puntos de comentario y generar preguntas
    print("Identificando puntos para comentarios...")
    puntos = identificar_puntos_comentario(narrativa, glosario)

    # Paso 5: Interactuar con preguntas específicas
    respuestas = interactuar_con_preguntas(puntos)

    # Paso 6: Generar comentarios para los puntos
    print("Generando comentarios...")
    narrativa_con_comentarios = generar_comentarios(narrativa, puntos, respuestas, glosario)

    # Paso 7: Generar comentario general
    print("Generando comentario general...")
    comentario_general = generar_comentario_general(narrativa, respuestas, glosario)

    # Paso 8: Insertar comentario general
    narrativa_final = insertar_comentario_general(narrativa_con_comentarios, comentario_general)

    # Paso 8: Corrección ortográfica
    print("Corrigiendo ortografía...")
    narrativa_corregida = corregir_ortografia(narrativa_final)

    if narrativa_corregida:
        narrativa_final = narrativa_corregida

    # Paso 9: Generar resumen
    print("Generando resumen...")
    resumen = generar_resumen(narrativa_final)

    # Paso 10: Sugerir y confirmar metadatos
    print("Generando sugerencias de metadatos...")
    metadatos_sugeridos = sugerir_metadatos(narrativa_final)
    metadatos_finales = interactuar_metadatos(metadatos_sugeridos)

    # Paso 11: Escribir archivo final
    escribir_archivo(archivo_dia, scores, metadatos_finales, resumen, narrativa_final)

    print("\n✅ Proceso completado. Diario enriquecido con LLM.")


if __name__ == "__main__":
    main()
