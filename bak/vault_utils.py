import os

import yaml

from backend.minerva.enriquecer_diario import construir_cache_vault


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


def actualizar_frontmatter_con_resumen(ruta_nota, frontmatter):
    """Actualiza el frontmatter de la nota añadiendo un campo 'resumen'."""
    # Reconstruir el contenido con el nuevo frontmatter
    yaml_text = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)
    with open(ruta_nota, 'r', encoding='utf-8') as f:
        contenido = f.read()

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


def actualizar_entradas(entradas):
    cache = construir_cache_vault()
    # Primera pasada: recolectar notas que necesitan resumen
    for entrada in entradas:
        ruta_nota = None
        enlace = entrada.name
        print(f'Procesando "{enlace}"')
        if enlace in cache:
            ruta_nota = cache[enlace]
        else:
            nombre_base = os.path.basename(enlace)
            if nombre_base in cache:
                ruta_nota = cache[nombre_base]

        if not ruta_nota or not os.path.exists(ruta_nota):
            print(f"Advertencia: No se encontró la nota '{enlace}' en el vault")
            continue

        with open(ruta_nota, 'r', encoding='utf-8') as f:
            contenido = f.read()

            frontmatter = extraer_frontmatter(contenido)

            # Verificar si ya tiene resumen en frontmatter
            if frontmatter and 'resumen' in frontmatter:
                resumen = frontmatter['resumen']
                print(f'Resumen viejo: "{resumen}"')
                print(f'Resumen nuevo: "{entrada.summary}"')
                opcion = input("Aceptar nuevo resumen? Y/N: ").strip()
                if opcion == 'N':
                    continue
            if frontmatter is None:
                frontmatter = {}
            frontmatter['resumen'] = entrada.summary
            actualizar_frontmatter_con_resumen(ruta_nota, frontmatter)
