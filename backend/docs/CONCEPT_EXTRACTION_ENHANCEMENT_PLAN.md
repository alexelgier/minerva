# Concept Extraction Enhancement Plan

## Overview
Enhance journal concept extraction to match Zettel sync quality with three main goals:
1. Extract new concepts with rich content (like Zettel sync)
2. Find mentions of existing concepts from journal entries
3. Extract concept feelings (person-concept relations)

## Current State Analysis

### ✅ What We Have:
- Basic concept extraction in `ConceptProcessor`
- RAG system via `find_relevant_concepts()`
- Recent mentions via `get_concepts_with_recent_mentions()`
- [[Link]] parsing in `build_entity_lookup()` (ObsidianService)
- Concept merging via `MergeSummariesPrompt`
- Concept feeling extraction in `ConceptFeelingProcessor`

### ❌ What We Need:
- Enhanced context system ([[Linked]] + RAG + Recent)
- Rich concept extraction matching Zettel quality
- Concept merging for existing concepts
- Concept relation extraction
- Cleaner extraction service architecture

## Implementation Plan

### Phase 1: Enhanced Context System

#### 1.1 Move Context Logic to ConceptProcessor
- Move `get_concept_context()` from ConceptRepository to ConceptProcessor
- Use existing `build_entity_lookup()` from ObsidianService to extract [[Linked]] concepts
- Filter linked concepts to only include those with `entity_type == "Concept"`

#### 1.2 Enhanced Context Structure
```python
# Context should have 2 sections:
# 1. Explicit [[Linked]] concepts (all of them) - explaining the reference to [[link]] in journal entry
# 2. RAG + Recent concepts (10 each)

def _format_context(self, linked_concepts, rag_concepts, recent_concepts) -> str:
    """Format context with 2 sections"""
    context_parts = []
    
    # Section 1: Explicit [[Linked]] concepts
    if linked_concepts:
        context_parts.append("CONCEPTOS EXPLÍCITAMENTE MENCIONADOS:")
        for concept in linked_concepts:
            context_parts.append(f"- {concept.title} (UUID: {concept.uuid})")
            context_parts.append(f"  Concepto: {concept.concept}")
            context_parts.append(f"  Resumen: {concept.summary_short}")
        context_parts.append("")
    
    # Section 2: RAG + Recent concepts (prioritized: Extracted > RAG > Recent)
    all_related_concepts = rag_concepts + recent_concepts
    if all_related_concepts:
        context_parts.append("CONCEPTOS RELACIONADOS DE TU BASE DE CONOCIMIENTO:")
        for concept in all_related_concepts:
            context_parts.append(f"- {concept.title} (UUID: {concept.uuid})")
            context_parts.append(f"  Concepto: {concept.concept}")
            context_parts.append(f"  Resumen: {concept.summary_short}")
    
    return "\n".join(context_parts)
```

### Phase 2: Enhanced Concept Extraction

#### 2.1 Update ExtractConceptsPrompt
```python
class ConceptMention(BaseModel):
    name: str = Field(..., description="Name of the concept (same as title)")
    title: str = Field(..., description="Title of the concept (same as name)")
    concept: str = Field(..., description="Concept definition or exposition")
    analysis: str = Field(..., description="Analysis and understanding of the concept")
    source: str | None = Field(default=None, description="Source if mentioned in text")
    spans: List[str] = Field(..., description="Exact text fragments where concept appears")
    existing_uuid: str | None = Field(default=None, description="UUID if concept exists in context")
    summary_short: str = Field(..., description="Short summary (max 30 words)")
    summary: str = Field(..., description="Detailed summary (max 100 words)")

class ExtractConceptsPrompt(Prompt):
    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los conceptos e ideas mencionados en esta entrada del diario.

INSTRUCCIONES:
1. Identifica conceptos, ideas, teorías, principios, o nociones abstractas mencionados
2. Incluye conceptos tanto explícitos como implícitos
3. Para cada concepto, determina si ya existe en la base de conocimiento (existing_uuid) o es nuevo (None)
4. Proporciona spans exactos del texto donde se menciona cada concepto
5. Extrae el contenido del concepto basado en el contexto del texto
6. Crea resúmenes concisos pero informativos

FORMATO DE RESPUESTA:
- name: Nombre del concepto (usar el término más preciso)
- title: Título del concepto (mismo que name)
- concept: Definición o exposición del concepto
- analysis: Análisis y comprensión del concepto
- source: Fuente si se menciona en el texto
- spans: Fragmentos exactos del texto donde aparece
- existing_uuid: UUID si existe en la base de conocimiento, None si es nuevo
- summary_short: Resumen breve (máximo 30 palabras)
- summary: Resumen detallado (máximo 100 palabras)

IMPORTANTE:
- Solo extrae conceptos reales, no nombres propios o eventos específicos
- Si un concepto se menciona múltiples veces, inclúyelo una sola vez con todos los spans
- Usa el contexto proporcionado para determinar si un concepto ya existe
- El campo 'concept' debe contener la definición principal del concepto
- El campo 'analysis' debe contener tu análisis y comprensión del concepto"""
```

#### 2.2 Update ConceptProcessor with Merging Logic
```python
class ConceptProcessor(BaseEntityProcessor):
    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        # Get enhanced context
        concept_context = await self._get_enhanced_concept_context(context)
        
        # Extract concepts with LLM
        response = await self.llm_service.generate(...)
        
        # Process response
        processed_entities = []
        for concept_mention in response.concepts:
            if concept_mention.existing_uuid:
                # Merge with existing concept
                existing_concept = await self._merge_with_existing_concept(
                    concept_mention, context.kg_service.entity_repositories["Concept"]
                )
                processed_entities.append({
                    "entity": existing_concept,
                    "spans": concept_mention.spans,
                })
            else:
                # Create new concept
                concept = Concept(...)
                processed_entities.append({
                    "entity": concept,
                    "spans": concept_mention.spans,
                })
        
        return self.span_service.process_spans(processed_entities, context.journal_entry)
    
    async def _get_enhanced_concept_context(self, context: ExtractionContext) -> str:
        """Get enhanced concept context with 3 sections"""
        # 1. Extract [[Linked]] concepts
        obsidian_entities = context.obsidian_service.build_entity_lookup(context.journal_entry)
        linked_concepts = []
        for entity_data in obsidian_entities.get("db_entities", []):
            if entity_data.entity_type == "Concept":
                concept = context.kg_service.entity_repositories["Concept"].find_by_uuid(entity_data.entity_id)
                if concept:
                    linked_concepts.append(concept)
        
        # 2. Get RAG concepts
        rag_concepts = await context.kg_service.entity_repositories["Concept"].find_relevant_concepts(
            context.journal_entry.entry_text, limit=10
        )
        
        # 3. Get recent concepts
        recent_concepts = context.kg_service.entity_repositories["Concept"].get_concepts_with_recent_mentions(days=30)
        recent_concepts = recent_concepts[:10]
        
        # Format context with 2 sections
        return self._format_context(linked_concepts, rag_concepts, recent_concepts)
    
    async def _merge_with_existing_concept(self, concept_mention: ConceptMention, concept_repository) -> Concept:
        """Merge extracted concept with existing DB concept using LLM"""
        existing_concept = concept_repository.find_by_uuid(concept_mention.existing_uuid)
        
        # Prepare merge data for all fields
        merge_data = {
            "entity_name": concept_mention.name,
            "existing_title": existing_concept.title,
            "existing_concept": existing_concept.concept,
            "existing_analysis": existing_concept.analysis,
            "existing_source": existing_concept.source,
            "existing_summary": existing_concept.summary,
            "existing_short_summary": existing_concept.summary_short,
            "new_title": concept_mention.title,
            "new_concept": concept_mention.concept,
            "new_analysis": concept_mention.analysis,
            "new_source": concept_mention.source,
            "new_summary": concept_mention.summary,
            "new_short_summary": concept_mention.summary_short,
        }
        
        # Use merge prompt
        merge_prompt = MergeConceptPrompt()
        merged_concept = await self.llm_service.generate(
            prompt=merge_prompt.user_prompt(merge_data),
            system_prompt=merge_prompt.system_prompt(),
            response_model=merge_prompt.response_model(),
        )
        
        # Update existing concept
        existing_concept.title = merged_concept.title
        existing_concept.concept = merged_concept.concept
        existing_concept.analysis = merged_concept.analysis
        existing_concept.source = merged_concept.source
        existing_concept.summary = merged_concept.summary
        existing_concept.summary_short = merged_concept.summary_short
        
        return existing_concept
```

### Phase 3: Concept Relation Extraction

#### 3.1 Sequential Concept Relation Processing

**Processing Strategy:**
- Process each concept individually with one LLM call per concept
- Track relations bidirectionally as we process each concept
- Include current concept with its existing relations (populated from DB if existing, empty if new)
- Context includes: Journal entry + Extracted concepts (minus current) + RAG (10) + Recent (10)
- Hard limit: 50 total concepts in context, prioritized: Extracted > RAG > Recent

**Example Processing Flow:**
Journal entry has 3 concepts: A(new), B(existing), C(new)

1. **Process A**: A (no relations) + context(B,C + RAG + Recent) → LLM finds A→B, A→C, A→RAG concepts
2. **Process B**: B (existing relations + new A→B) + context(A,C + RAG + Recent) → LLM finds B→C, B→RAG concepts  
3. **Process C**: C (relations A→C, B→C) + context(A,B + RAG + Recent) → LLM finds C→RAG concepts

**Key Features:**
- Automatic bidirectional relation creation (A→B creates B→A with reverse type)
- Deduplication: Skip duplicate relations found in successive calls
- Relation validation: Check for invalid types and logical conflicts
- No confidence scores

#### 3.2 Create ConceptRelation Enum
```python
# Note: Use existing RELATION_MAP from ObsidianService to maintain consistency
# The 9 relation types are already defined and validated in the system:
# GENERALIZES, SPECIFIC_OF, PART_OF, HAS_PART, SUPPORTS, SUPPORTED_BY, OPPOSES, SIMILAR_TO, RELATES_TO

class ConceptRelationType(str, Enum):
    GENERALIZES = "GENERALIZES"
    SPECIFIC_OF = "SPECIFIC_OF"
    PART_OF = "PART_OF"
    HAS_PART = "HAS_PART"
    SUPPORTS = "SUPPORTS"
    SUPPORTED_BY = "SUPPORTED_BY"
    OPPOSES = "OPPOSES"
    SIMILAR_TO = "SIMILAR_TO"
    RELATES_TO = "RELATES_TO"
```

#### 3.2 Create ConceptRelation Models
```python
class ConceptRelation(BaseModel):
    relation_type: ConceptRelationType = Field(..., description="Type of relation")
    source_uuid: str = Field(..., description="UUID of the source concept")
    target_uuid: str = Field(..., description="UUID of the target concept")

class ConceptRelations(BaseModel):
    relations: List[ConceptRelation] = Field(..., description="List of concept relations")

# Note: We'll create a new ConceptRelation class that inherits from Relation
# This provides better separation of concerns and type safety

# Why create a separate ConceptRelation class?
# 1. Type Safety: ConceptRelationType enum provides compile-time type checking
# 2. Separation of Concerns: Concept relations have different validation rules than generic relations
# 3. Extensibility: Can add concept-specific fields (e.g., confidence, evidence) without affecting generic relations
# 4. Clarity: Makes it clear when we're dealing with concept relations vs other relation types
# 5. Validation: Can implement concept-specific validation logic
```

#### 3.3 Create ConceptRelationProcessor (for extract_relationships)
```python
class ConceptRelationProcessor(BaseEntityProcessor):
    @property
    def entity_type(self) -> str:
        return "ConceptRelation"
    
    async def process(self, context: ExtractionContext) -> List[RelationSpanContextMapping]:
        # Get extracted concepts
        concept_entities = [
            e for e in context.extracted_entities if e.entity.type == "Concept"
        ]
        
        # Only extract relations if we have 1+ concepts
        if len(concept_entities) < 1:
            return []
        
        # Track all relations found so far (for bidirectional tracking)
        all_relations = {}  # (source_uuid, target_uuid) -> relation_type
        
        # Process each concept individually
        for concept_entity in concept_entities:
            try:
                # Get current concept with its existing relations
                current_concept = concept_entity.entity
                
                # Check if concept has existing_uuid to load relations from DB
                if hasattr(current_concept, 'existing_uuid') and current_concept.existing_uuid:
                    # This is an existing concept, load relations from database
                    existing_relations = await self._load_existing_relations_from_db(current_concept.existing_uuid)
                else:
                    # This is a new concept, no existing relations
                    existing_relations = []
                
                # Build context: Extracted concepts (minus current) + RAG + Recent
                context_concepts = await self._build_relation_context(
                    concept_entities, current_concept, context
                )
                
                # Extract relations for this concept
                new_relations = await self._extract_relations_for_concept(
                    current_concept, existing_relations, context_concepts, 
                    context.journal_entry.entry_text
                )
                
                # Add new relations to tracking (with deduplication)
                for relation in new_relations:
                    relation_key = (relation.source_uuid, relation.target_uuid)
                    if relation_key not in all_relations:
                        all_relations[relation_key] = relation.relation_type
                        
                        # Create reverse relation if needed
                        reverse_type = self._get_reverse_relation_type(relation.relation_type)
                        if reverse_type:
                            reverse_key = (relation.target_uuid, relation.source_uuid)
                            if reverse_key not in all_relations:
                                all_relations[reverse_key] = reverse_type
                
            except Exception as e:
                self.logger.error(f"Failed to process relations for concept {concept_entity.entity.name}: {e}")
                continue  # Continue with next concept
        
        # Validate all relations before creating Relation entities
        validated_relations = self._validate_all_relations(all_relations)
        
        # Convert tracked relations to RelationSpanContextMapping
        result = []
        for (source_uuid, target_uuid), relation_type in validated_relations.items():
            # Create ConceptRelation entity
            concept_relation = ConceptRelation(
                source=source_uuid,
                target=target_uuid,
                relation_type=relation_type,
                summary_short=f"Concept relation: {relation_type}",
                summary=f"Concept relation between {source_uuid} and {target_uuid}",
            )
            
            # Create spans for concept relations (find text spans where relation is mentioned)
            relation_spans = self._find_relation_spans(
                relation_type, source_uuid, target_uuid, context.journal_entry.entry_text
            )
            
            # Create RelationSpanContextMapping with populated spans
            result.append(RelationSpanContextMapping(
                relation=concept_relation,
                spans=relation_spans,
                context=None
            ))
        
        return result
    
    def _validate_all_relations(self, all_relations: Dict) -> Dict:
        """Validate all relations for logical consistency and remove invalid ones"""
        # Import validation logic from obsidian_service
        from minerva_backend.obsidian.obsidian_service import RELATION_MAP
        
        validated_relations = {}
        for (source_uuid, target_uuid), relation_type in all_relations.items():
            # Check if relation type is valid
            if relation_type not in RELATION_MAP:
                self.logger.warning(f"Invalid relation type: {relation_type}")
                continue
            
            # Check for self-connections
            if source_uuid == target_uuid:
                self.logger.warning(f"Self-connection detected: {source_uuid} -> {source_uuid}")
                continue
            
            # Additional validation logic can be added here
            # (e.g., checking for logical conflicts like SUPPORTS + OPPOSES)
            
            validated_relations[(source_uuid, target_uuid)] = relation_type
        
        return validated_relations
    
    async def _load_existing_relations_from_db(self, concept_uuid: str) -> List[Dict]:
        """Load existing relations for a concept from the database"""
        # This would query the database for existing concept relations
        # Return format: [{"target_uuid": "...", "relation_type": "..."}, ...]
        # Implementation would depend on the specific database query method
        pass
    
    def _find_relation_spans(self, relation_type: str, source_uuid: str, target_uuid: str, text: str) -> List[Span]:
        """Find text spans where the concept relation is mentioned"""
        # This would use the span service to find text spans
        # where the relation between concepts is mentioned
        # Implementation would depend on the specific span finding logic
        pass
    
    async def _build_relation_context(self, concept_entities, current_concept, context) -> List[Dict]:
        """Build context with extracted concepts (minus current) + RAG + Recent"""
        # Get other extracted concepts (excluding current)
        other_concepts = [
            {"name": e.entity.name, "uuid": e.entity.uuid, "concept": e.entity.concept, 
             "summary_short": e.entity.summary_short}
            for e in concept_entities if e.entity.uuid != current_concept.uuid
        ]
        
        # Get RAG concepts (limit 10)
        rag_concepts = await context.kg_service.entity_repositories["Concept"].find_relevant_concepts(
            context.journal_entry.entry_text, limit=10
        )
        rag_formatted = [
            {"name": c.title, "uuid": c.uuid, "concept": c.concept, "summary_short": c.summary_short}
            for c in rag_concepts
        ]
        
        # Get recent concepts (limit 10)
        recent_concepts = context.kg_service.entity_repositories["Concept"].get_concepts_with_recent_mentions(days=30)
        recent_concepts = recent_concepts[:10]
        recent_formatted = [
            {"name": c.title, "uuid": c.uuid, "concept": c.concept, "summary_short": c.summary_short}
            for c in recent_concepts
        ]
        
        # Combine and prioritize: Extracted > RAG > Recent (max 50 total)
        all_concepts = other_concepts + rag_formatted + recent_formatted
        return all_concepts[:50]
    
    async def _extract_relations_for_concept(self, current_concept, existing_relations, 
                                           context_concepts, journal_text) -> List[ConceptRelation]:
        """Extract relations for a single concept using LLM"""
        # Format current concept with its relations
        current_concept_info = {
            "name": current_concept.name,
            "uuid": current_concept.uuid,
            "concept": current_concept.concept,
            "summary_short": current_concept.summary_short,
            "existing_relations": existing_relations
        }
        
        # Extract relations
        prompt = ExtractConceptRelationsPrompt()
        response = await self.llm_service.generate(
            prompt=prompt.user_prompt(journal_text, current_concept_info, context_concepts),
            system_prompt=prompt.system_prompt(),
            response_model=prompt.response_model(),
        )
        
        # Validate relations
        validated_relations = []
        for relation in response.relations:
            if self._validate_relation(relation):
                validated_relations.append(relation)
            else:
                self.logger.warning(f"Invalid relation rejected: {relation}")
        
        return validated_relations
    
    def _validate_relation(self, relation: ConceptRelation) -> bool:
        """Validate relation for type validity and logical consistency"""
        # Check if relation type is valid
        if relation.relation_type not in ConceptRelationType:
            return False
        
        # Check for self-connections
        if relation.source_uuid == relation.target_uuid:
            return False
        
        # Additional validation logic can be added here
        # (e.g., checking for logical conflicts like SUPPORTS + OPPOSES)
        
        return True
    
    def _get_reverse_relation_type(self, relation_type: str) -> Optional[str]:
        """Get reverse relation type for bidirectional relations"""
        # Import RELATION_MAP from obsidian_service.py to avoid duplication
        from minerva_backend.obsidian.obsidian_service import RELATION_MAP
        
        if relation_type in RELATION_MAP:
            _, reverse_type = RELATION_MAP[relation_type]
            return reverse_type
        return None
```

#### 3.4 Update ExtractConceptRelationsPrompt
```python
class ExtractConceptRelationsPrompt(Prompt):
    @staticmethod
    def system_prompt() -> str:
        return """Extrae relaciones para un concepto específico basándote en el texto del diario y el contexto de conceptos relacionados.

INSTRUCCIONES:
1. Analiza el concepto actual y encuentra sus relaciones con otros conceptos
2. Usa ÚNICAMENTE los tipos de relación definidos en ConceptRelationType
3. Puedes inferir relaciones implícitas si están claramente sugeridas en el texto
4. Considera tanto el texto del diario como el contexto de conceptos relacionados
5. No inventes relaciones que no estén justificadas por el contenido

TIPOS DE RELACIÓN DISPONIBLES:
- GENERALIZES: A generaliza B (A es más general que B)
- SPECIFIC_OF: A es específico de B (A es más específico que B)
- PART_OF: A es parte de B
- HAS_PART: A tiene parte B
- SUPPORTS: A apoya B
- SUPPORTED_BY: A es apoyado por B
- OPPOSES: A se opone a B (simétrico)
- SIMILAR_TO: A es similar a B (simétrico)
- RELATES_TO: A se relaciona con B (simétrico)

FORMATO DE RESPUESTA:
- relation_type: Tipo de relación de la lista anterior
- source_uuid: UUID del concepto origen (siempre el concepto actual)
- target_uuid: UUID del concepto objetivo

IMPORTANTE:
- source_uuid debe ser siempre el UUID del concepto actual
- Usa los UUIDs de los conceptos proporcionados en el contexto
- Solo sugiere relaciones que estén justificadas por el contenido"""

    @staticmethod
    def user_prompt(journal_text: str, current_concept: Dict, context_concepts: List[Dict]) -> str:
        # Format current concept
        current_info = f"""
CONCEPTO ACTUAL:
- Nombre: {current_concept['name']} (UUID: {current_concept['uuid']})
- Concepto: {current_concept['concept']}
- Resumen: {current_concept['summary_short']}
- Relaciones existentes: {current_concept.get('existing_relations', [])}
"""
        
        # Format context concepts
        context_str = "\n".join([
            f"- {c['name']} (UUID: {c['uuid']})\n  Concepto: {c['concept']}\n  Resumen: {c['summary_short']}"
            for c in context_concepts
        ])
        
        return f"""Analiza el siguiente texto del diario y encuentra relaciones para el concepto actual:

TEXTO DEL DIARIO:
{journal_text}

{current_info}

CONCEPTOS EN CONTEXTO:
{context_str}

Encuentra relaciones entre el concepto actual y los conceptos en contexto basándote en el texto del diario."""
```

### Phase 4: Clean Up Extraction Service

#### 4.1 Integrate Concept Relations into extract_relationships
```python
async def extract_relationships(
    self, journal_entry: JournalEntry, entities: List[EntityMapping]
) -> List[RelationSpanContextMapping]:
    """Extract relationships between entities including concept relations."""
    start_time = time.time()

    self.logger.info(
        "Starting relationship extraction",
        context={
            "journal_id": journal_entry.uuid,
            "entity_count": len(entities),
            "stage": "relationship_extraction",
        },
    )

    try:
        # Create context with extracted entities
        obsidian_entities = self.obsidian_service.build_entity_lookup(journal_entry)
        context = ExtractionContext(
            journal_entry=journal_entry,
            obsidian_entities=obsidian_entities,
            kg_service=self.kg_service,
        )
        context.add_entities(entities)

        all_relationships = []

        # 1. Extract general relationships (existing logic)
        relationship_processor = RelationshipProcessor(
            llm_service=self.llm_service,
            entity_repositories=self.entity_repositories,
            span_service=self.span_processing_service,
            obsidian_service=self.obsidian_service,
        )
        general_relationships = await relationship_processor.process(context)
        all_relationships.extend(general_relationships)

        # 2. Extract concept relations (new logic)
        concept_relation_processor = ConceptRelationProcessor(
            llm_service=self.llm_service,
            entity_repositories=self.entity_repositories,
            span_service=self.span_processing_service,
            obsidian_service=self.obsidian_service,
        )
        concept_relationships = await concept_relation_processor.process(context)
        all_relationships.extend(concept_relationships)

        duration_ms = (time.time() - start_time) * 1000

        self.performance_logger.log_processing_time(
            "relationship_extraction",
            duration_ms,
            journal_id=journal_entry.uuid,
            entity_count=len(entities),
            relationship_count=len(all_relationships),
        )

        self.logger.info(
            "Relationship extraction completed",
            context={
                "journal_id": journal_entry.uuid,
                "relationship_count": len(all_relationships),
                "concept_relations": len(concept_relationships),
                "duration_ms": duration_ms,
                "stage": "relationship_extraction",
            },
        )

        return all_relationships

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        self.logger.error(
            "Relationship extraction failed",
            context={
                "journal_id": journal_entry.uuid,
                "error": str(e),
                "duration_ms": duration_ms,
                "stage": "relationship_extraction",
            },
        )
        raise
```

#### 4.2 Update Processing Flow
```python
# In orchestrator.py - entity extraction
processing_order = [
    "Person",  # People first
    "Concept",  # Enhanced concept extraction (existing + new)
    "Feeling",  # Emotions
    "FeelingConcept",  # Concept feelings
    "Project",  # Projects
    "Consumable",  # Consumables
    "Content",  # Content
    "Event",  # Events
    "Place",  # Places
]

# In extract_relationships - concept relations are processed here
# ConceptRelationProcessor will be called during relationship extraction
```

### Phase 5: Enhanced Merge Prompt

#### 5.1 Create MergeConceptPrompt
```python
class MergedConcept(BaseModel):
    title: str = Field(..., description="Merged title")
    concept: str = Field(..., description="Merged concept definition")
    analysis: str = Field(..., description="Merged analysis")
    source: str | None = Field(default=None, description="Merged source")
    summary_short: str = Field(..., description="Merged short summary (max 30 words)")
    summary: str = Field(..., description="Merged detailed summary (max 100 words)")

class MergeConceptPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[MergedConcept]:
        return MergedConcept

    @staticmethod
    def system_prompt() -> str:
        return """Eres un experto en fusionar información de conceptos de manera inteligente.

Tu tarea es tomar un concepto existente y un concepto extraído de un journal, y crear un concepto fusionado que combine la información de ambos de manera coherente.

REGLAS IMPORTANTES:
- La información más reciente NO siempre es más correcta - usa tu juicio
- Si hay contradicciones, prefiere la información más específica/detallada
- No inventes información que no esté en los conceptos originales
- Si un campo está vacío o es genérico, prioriza el otro
- Combina información complementaria de ambos conceptos

LÍMITES ESTRICTOS:
- summary (resumen largo): MÁXIMO 100 palabras
- summary_short (resumen corto): MÁXIMO 30 palabras

El resumen corto debe ser la versión más condensada del resumen largo."""

    @staticmethod
    def user_prompt(data: dict) -> str:
        return f"""Fusiona la información sobre: {data['entity_name']}

CONCEPTO EXISTENTE:
Título: {data['existing_title']}
Concepto: {data['existing_concept']}
Análisis: {data['existing_analysis']}
Fuente: {data['existing_source']}
Resumen corto: {data['existing_short_summary']}
Resumen: {data['existing_summary']}

CONCEPTO EXTRAÍDO:
Título: {data['new_title']}
Concepto: {data['new_concept']}
Análisis: {data['new_analysis']}
Fuente: {data['new_source']}
Resumen corto: {data['new_short_summary']}
Resumen: {data['new_summary']}

Crea un concepto fusionado que combine lo mejor de ambos, eliminando redundancia pero preservando detalles importantes."""
```

## Implementation Steps

### Step 1: Create Enhanced Context System
- Move `get_concept_context()` to ConceptProcessor
- Use existing `build_entity_lookup()` for [[Linked]] concepts
- Implement 3-section context formatting
- **Note**: Leverage existing vector search infrastructure (1024-dim embeddings, cosine similarity)

### Step 2: Update Concept Extraction
- Update `ExtractConceptsPrompt` with new fields and descriptions
- Update `ConceptProcessor` with merging logic
- Create `MergeConceptPrompt`
- **Note**: Ensure extraction matches Zettel template structure (Concepto, Análisis, Fuente sections)

### Step 3: Add Concept Relation Extraction
- Create `ConceptRelationType` enum (reuse existing 9 types from `RELATION_MAP`)
- Create `ConceptRelation` class (inheriting from `Relation`)
- Create `ConceptRelationProcessor` (for extract_relationships)
- Update `ExtractConceptRelationsPrompt`
- Integrate with `extract_relationships` method
- **Note**: Use existing bidirectional relation logic and validation from `RELATION_MAP`

### Step 4: Clean Up Extraction Service
- Clean up `extract_relationships` method
- Update processing flow
- Test and validate
- **Note**: Ensure integration with existing 5-stage processing pipeline

## Documentation Analysis

### Key Insights from Existing Documentation

1. **Zettel Template Structure**: The existing Zettel template shows the expected structure:
   - `## Concepto` section for concept definition
   - `## Análisis` section for personal analysis
   - `## Fuente` section for source attribution
   - `## Conexiones` section for concept relations

2. **Concept Relations Already Defined**: The system already has a comprehensive concept relations system:
   - 9 relation types: GENERALIZES, SPECIFIC_OF, PART_OF, HAS_PART, SUPPORTS, SUPPORTED_BY, OPPOSES, SIMILAR_TO, RELATES_TO
   - Bidirectional relation creation logic exists in `RELATION_MAP`
   - Validation and cleanup logic already implemented

3. **Processing Pipeline Integration**: The enhancement fits perfectly into the existing 5-stage pipeline:
   - Stage 1: Entity Extraction (where enhanced concept extraction happens)
   - Stage 3: Relationship Extraction (where concept relations would be extracted)

4. **LLM Service Requirements**: Documentation confirms LLM service is required for:
   - Summary generation (no fallbacks allowed)
   - Concept merging
   - Relation extraction

5. **Vector Search Infrastructure**: Existing RAG system uses:
   - 1024-dimensional embeddings
   - Cosine similarity search
   - Neo4j native vector indexes
   - Auto-created indexes for all entity types

## Questions for Refinement

1. **Relation Source/Target Determination**: ✅ Confirmed - Automatic bidirectional relation creation (A→B creates B→A with reverse type)

2. **Context Limits**: ✅ Confirmed - Hard limit of 50 concepts, prioritized: Extracted > RAG > Recent

3. **Concept Merging Strategy**: ✅ Confirmed - merge title, concept, analysis, source, summary_short, summary

4. **Relation Validation**: ✅ Confirmed - Validate relation types and logical consistency (using validation logic from sync_zettels_to_db)

5. **Processing Order**: ✅ Confirmed - Sequential processing of each concept individually during `extract_relationships`

6. **Error Handling**: ✅ Confirmed - Continue with next concept if one fails, similar to entity extraction

7. **Context Formatting**: ✅ Confirmed - Include name, uuid, concept, and summary_short for every concept

8. **Relation Updates**: ✅ Confirmed - Not handled during extraction, happens at later stage

9. **Performance**: ✅ Confirmed - Use local LLM, patient with processing time

10. **Deduplication**: ✅ Confirmed - Skip duplicate relations found in successive calls

11. **Zettel Integration**: ✅ Confirmed - Enhanced extraction should match Zettel sync quality and structure

12. **Relation Type Consistency**: ✅ Confirmed - Use existing 9 relation types from `RELATION_MAP` in ObsidianService

## Next Steps

1. ✅ Review and refine this plan
2. ✅ Documentation analysis complete - plan validated against existing system
3. Start with Step 1 (Enhanced Context System)
4. Implement fully, then write/run tests
5. After fully tested, update documentation

## Implementation Readiness Assessment

### ✅ **READY TO IMPLEMENT** - The plan is well-structured and mostly ready for implementation

**Key Strengths:**
- Leverages existing infrastructure (vector search, relation types, validation logic)
- Aligns with current Zettel template structure
- Fits perfectly into existing 5-stage processing pipeline
- Reuses proven patterns from Zettel sync functionality

**Implementation Order (Recommended):**
1. **Phase 1** (Enhanced Context) - Low risk, high impact
2. **Phase 2** (Enhanced Extraction) - Low risk, core functionality  
3. **Phase 5** (Enhanced Merge) - Low risk, supports Phase 2
4. **Phase 3** (Concept Relations) - Moderate complexity, new feature
5. **Phase 4** (Clean Up) - Low risk, integration work

**Estimated Timeline:** 7-9 days total

## Files to Modify

- `backend/src/minerva_backend/processing/extraction/processors/concept_processor.py`
- `backend/src/minerva_backend/prompt/extract_concepts.py`
- `backend/src/minerva_backend/prompt/merge_summaries.py` (enhance to MergeConceptPrompt)
- `backend/src/minerva_backend/processing/extraction/orchestrator.py`
- `backend/src/minerva_backend/processing/extraction_service.py`
- `backend/src/minerva_backend/graph/repositories/concept_repository.py`
- `backend/src/minerva_backend/graph/models/entities.py` (add ConceptRelationType enum)
- `backend/src/minerva_backend/graph/models/relations.py` (create ConceptRelation class)
- `backend/src/minerva_backend/processing/extraction/processors/factory.py`

## New Files to Create

- `backend/src/minerva_backend/processing/extraction/processors/concept_relation_processor.py`
- `backend/src/minerva_backend/prompt/extract_concept_relations.py`
- `backend/src/minerva_backend/prompt/merge_concept.py`
