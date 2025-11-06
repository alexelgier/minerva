# Arquitectura de Extracción de Entidades Refactorizada

## Visión General

La arquitectura de extracción de entidades ha sido refactorizada para mejorar la claridad, mantenibilidad y testabilidad del código. Se eliminó la herencia múltiple compleja y se implementó un patrón Strategy con servicios especializados.

## Estructura de Archivos

```
extraction/
├── README.md                           # Esta documentación
├── context.py                          # Contexto de extracción compartido
├── orchestrator.py                     # Orquestador principal
├── relationship_processor.py           # Procesador de relaciones
├── services/                          # Servicios especializados
│   ├── __init__.py
│   ├── obsidian_lookup_service.py     # Lookup de entidades Obsidian
│   └── span_processing_service.py     # Procesamiento de spans
└── processors/                        # Procesadores de entidades
    ├── __init__.py
    ├── base.py                        # Clase base y estrategia
    ├── factory.py                     # Factory para crear procesadores
    ├── people_processor.py            # Procesador de personas
    ├── emotion_processor.py           # Procesador de emociones
    └── generic_entity_processor.py    # Procesador genérico
```

## Componentes Principales

### 1. EntityExtractionOrchestrator

El orquestador principal que coordina la extracción de entidades. No contiene lógica de procesamiento específica, solo orquesta el flujo.

**Responsabilidades:**
- Preparar el contexto de extracción
- Ejecutar procesadores en el orden correcto
- Coordinar el flujo de extracción

### 2. Servicios Especializados

#### ObsidianService (build_entity_lookup method)
- Construye tablas de lookup para entidades existentes de Obsidian
- Maneja alias y resolución de enlaces

#### SpanProcessingService
- Procesa spans de texto usando coincidencias exactas y difusas
- Hidrata spans con posiciones de texto

### 3. Procesadores de Entidades

#### Patrón Strategy
Cada tipo de entidad tiene su propio procesador que implementa `EntityProcessorStrategy`:

- **PeopleProcessor**: Procesa personas con hidratación personalizada
- **EmotionProcessor**: Procesa emociones (requiere contexto de personas)
- **GenericEntityProcessor**: Procesa entidades que siguen el patrón estándar

#### BaseEntityProcessor
Clase base que proporciona funcionalidad común:
- Procesamiento y deduplicación de entidades
- Fusión de propiedades de entidades existentes
- Integración con repositorios de base de datos

### 4. ExtractionContext

Contexto compartido durante la extracción que contiene:
- Entrada del diario
- Entidades de Obsidian
- Entidades extraídas (para contexto entre procesadores)
- Métodos de utilidad para generar contexto de prompts

## Flujo de Extracción

1. **Preparación**: Se crea el contexto de extracción con lookup de Obsidian
2. **Procesamiento Secuencial**: Los procesadores se ejecutan en orden específico:
   - Personas (necesarias para emociones)
   - Emociones (requieren contexto de personas)
   - Proyectos, Consumibles, Contenido, Eventos, Lugares
3. **Contexto Compartido**: Cada procesador puede acceder a entidades extraídas por procesadores anteriores
4. **Resultado**: Lista de `EntityMapping` con entidades y sus spans

## Beneficios de la Refactorización

### ✅ Claridad
- Cada clase tiene una responsabilidad única y clara
- El flujo de extracción es fácil de seguir
- Separación clara entre orquestación y procesamiento

### ✅ Mantenibilidad
- Cambios en un tipo de entidad no afectan otros
- Fácil agregar nuevos tipos de entidades
- Código más modular y organizado

### ✅ Testabilidad
- Cada componente se puede testear independientemente
- Mocking más fácil con inyección de dependencias
- Tests unitarios más granulares

### ✅ Extensibilidad
- Agregar nuevos procesadores es trivial
- Patrón Strategy permite diferentes implementaciones
- Servicios reutilizables en otros contextos

### ✅ Reutilización
- Servicios especializados pueden usarse independientemente
- Procesadores pueden reutilizarse en otros flujos
- Contexto compartido evita duplicación

## Migración desde la Arquitectura Anterior

### Cambios en ExtractionService

**Antes:**
```python
class ExtractionService(SpanUtilsMixin, ObsidianLookupMixin, ...):
    async def extract_entities(self, journal_entry):
        # Lógica compleja con herencia múltiple
```

**Después:**
```python
class ExtractionService:
    def __init__(self, connection, llm_service, obsidian_service):
        # Configuración clara de servicios
        self.orchestrator = EntityExtractionOrchestrator(...)
    
    async def extract_entities(self, journal_entry):
        return await self.orchestrator.extract_entities(journal_entry)
```

### Compatibilidad

- La API pública de `ExtractionService` se mantiene igual
- El método `extract_relationships` se mantiene para compatibilidad
- Los tipos de retorno son idénticos

## Agregar Nuevos Tipos de Entidades

1. Crear un nuevo procesador que herede de `BaseEntityProcessor`
2. Implementar el método `process()` con lógica específica
3. Agregar el procesador a `ProcessorFactory.create_all_processors()`
4. Agregar el tipo de entidad al orden de procesamiento en `EntityExtractionOrchestrator`

## Testing

Cada componente se puede testear independientemente:

```python
# Test de procesador individual
processor = PeopleProcessor(llm_service, repos, span_service, obsidian_service)
result = await processor.process(context)

# Test de servicio especializado
entities = obsidian_service.build_entity_lookup(journal_entry)

# Test de orquestador
orchestrator = EntityExtractionOrchestrator(obsidian_service, span_service, processors)
result = await orchestrator.extract_entities(journal_entry)
```
