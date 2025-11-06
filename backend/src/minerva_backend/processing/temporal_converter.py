"""Custom Temporal data converter for EntityMapping and RelationSpanContextMapping serialization."""

import json
from datetime import date, datetime
from typing import Any, Dict, Optional, Type

from temporalio.api.common.v1 import Payload
from temporalio.converter import EncodingPayloadConverter


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


from minerva_models import (
    ConceptRelation,
    ConceptRelationType,
    EntityType,
    FeelingConcept,
    FeelingEmotion,
    Relation,
    RelationshipType,
)
from minerva_backend.processing.curation_manager import ENTITY_TYPE_MAP
from minerva_backend.processing.models import CuratableMapping, EntityMapping


class EntityMappingPayloadConverter(EncodingPayloadConverter):
    """Custom converter for EntityMapping dataclass with polymorphic entity types."""

    @property
    def encoding(self) -> str:
        return "json/entity-mapping"

    def to_payload(self, value: Any) -> Optional[Payload]:
        if isinstance(value, EntityMapping):
            data = {
                "entity": self._serialize_entity(value.entity),
                "spans": [self._serialize_span(span) for span in value.spans],
            }
            return Payload(
                metadata={"encoding": self.encoding.encode()},
                data=json.dumps(data, cls=DateTimeEncoder).encode(),
            )
        return None

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        if payload.metadata.get("encoding") == self.encoding.encode():
            data = json.loads(payload.data.decode())
            return EntityMapping(
                entity=self._deserialize_entity(data["entity"]),
                spans=[self._deserialize_span(span) for span in data["spans"]],
            )
        return None

    def _serialize_entity(self, entity: Any) -> Dict[str, Any]:
        """Serialize entity using existing type field."""
        if hasattr(entity, "model_dump"):  # Pydantic model
            data = entity.model_dump()
            # Convert datetime and date objects to ISO format for JSON serialization
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, date):
                    data[key] = value.isoformat()
            return data
        elif isinstance(entity, dict):
            return entity
        else:
            raise RuntimeError(f"Cannot serialize entity of type {type(entity)}")

    def _deserialize_entity(self, data: Dict[str, Any]) -> Any:
        """Deserialize entity using existing type field and ENTITY_TYPE_MAP."""
        entity_type_value = data.get("type")
        if not entity_type_value:
            raise RuntimeError("Entity missing 'type' field")

        if entity_type_value not in ENTITY_TYPE_MAP:
            raise RuntimeError(f"Unknown entity type: {entity_type_value}")

        entity_class = ENTITY_TYPE_MAP[entity_type_value]
        return entity_class(**data)

    def _serialize_span(self, span: Any) -> Dict[str, Any]:
        """Serialize span."""
        if hasattr(span, "model_dump"):  # Pydantic model
            data = span.model_dump()
            # Convert datetime and date objects to ISO format for JSON serialization
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, date):
                    data[key] = value.isoformat()
            return data
        elif isinstance(span, dict):
            return span
        else:
            raise RuntimeError(f"Cannot serialize span of type {type(span)}")

    def _deserialize_span(self, data: Dict[str, Any]) -> Any:
        """Deserialize span."""
        from minerva_models import LexicalType, Span

        # Ensure type field is correct
        if "type" in data and data["type"] != LexicalType.SPAN.value:
            data["type"] = LexicalType.SPAN.value

        return Span(**data)

    def _serialize_entity_mapping(
        self, entity_mapping: EntityMapping
    ) -> Dict[str, Any]:
        """Serialize EntityMapping for use in list converter."""
        return {
            "entity": self._serialize_entity(entity_mapping.entity),
            "spans": [self._serialize_span(span) for span in entity_mapping.spans],
        }

    def _deserialize_entity_mapping(self, data: Dict[str, Any]) -> EntityMapping:
        """Deserialize EntityMapping for use in list converter."""
        return EntityMapping(
            entity=self._deserialize_entity(data["entity"]),
            spans=[self._deserialize_span(span) for span in data["spans"]],
        )


class ListEntityMappingPayloadConverter(EncodingPayloadConverter):
    """Custom converter for List[EntityMapping]."""

    @property
    def encoding(self) -> str:
        return "json/entity-mapping-list"

    def to_payload(self, value: Any) -> Optional[Payload]:
        if isinstance(value, list) and all(
            isinstance(item, EntityMapping) for item in value
        ):
            # Use the existing EntityMappingPayloadConverter for each item
            entity_converter = EntityMappingPayloadConverter()
            data = {
                "items": [
                    entity_converter._serialize_entity_mapping(item) for item in value
                ]
            }
            return Payload(
                metadata={"encoding": self.encoding.encode()},
                data=json.dumps(data, cls=DateTimeEncoder).encode(),
            )
        return None

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        if payload.metadata.get("encoding") == self.encoding.encode():
            data = json.loads(payload.data.decode())
            entity_converter = EntityMappingPayloadConverter()
            return [
                entity_converter._deserialize_entity_mapping(item_data)
                for item_data in data["items"]
            ]
        return None


class CuratableMappingPayloadConverter(EncodingPayloadConverter):
    """Custom converter for CuratableMapping dataclass."""

    @property
    def encoding(self) -> str:
        return "json/curatable-mapping"

    def to_payload(self, value: Any) -> Optional[Payload]:
        if isinstance(value, CuratableMapping):
            data = {
                "kind": value.kind,
                "data": self._serialize_data(value.data),
                "spans": [self._serialize_span(span) for span in value.spans],
                "context": [
                    self._serialize_context(ctx) for ctx in (value.context or [])
                ],
            }
            return Payload(
                metadata={"encoding": self.encoding.encode()},
                data=json.dumps(data, cls=DateTimeEncoder).encode(),
            )
        return None

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        if payload.metadata.get("encoding") == self.encoding.encode():
            data = json.loads(payload.data.decode())
            return CuratableMapping(
                kind=data["kind"],
                data=self._deserialize_data(data["data"], data["kind"]),
                spans=[self._deserialize_span(span) for span in data["spans"]],
                context=[
                    self._deserialize_context(ctx)
                    for ctx in (data.get("context") or [])
                ],
            )
        return None

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """Serialize data based on its type."""
        if hasattr(data, "model_dump"):  # Pydantic model
            data_dict = data.model_dump()
            # Convert datetime and date objects to ISO format for JSON serialization
            for key, value in data_dict.items():
                if isinstance(value, datetime):
                    data_dict[key] = value.isoformat()
                elif isinstance(value, date):
                    data_dict[key] = value.isoformat()
            return data_dict
        elif isinstance(data, dict):
            return data
        else:
            raise RuntimeError(f"Cannot serialize data of type {type(data)}")

    def _deserialize_data(self, data: Dict[str, Any], kind: str) -> Any:
        """Deserialize data based on kind."""
        if kind == "relation":
            return Relation(**data)
        elif kind == "concept_relation":
            return ConceptRelation(**data)
        elif kind == "feeling_emotion":
            return FeelingEmotion(**data)
        elif kind == "feeling_concept":
            return FeelingConcept(**data)
        else:
            raise RuntimeError(f"Unknown kind: {kind}")

    def _serialize_span(self, span: Any) -> Dict[str, Any]:
        """Serialize span."""
        if hasattr(span, "model_dump"):
            return span.model_dump()
        elif isinstance(span, dict):
            return span
        else:
            raise RuntimeError(f"Cannot serialize span of type {type(span)}")

    def _deserialize_span(self, data: Dict[str, Any]) -> Any:
        """Deserialize span."""
        from minerva_models import LexicalType, Span

        # Ensure type field is correct
        if "type" in data and data["type"] != LexicalType.SPAN.value:
            data["type"] = LexicalType.SPAN.value

        return Span(**data)

    def _serialize_context(self, context: Any) -> Dict[str, Any]:
        """Serialize context."""
        if hasattr(context, "model_dump"):
            data = context.model_dump()
            # Convert datetime and date objects to ISO format for JSON serialization
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, date):
                    data[key] = value.isoformat()
            return data
        elif isinstance(context, dict):
            return context
        else:
            raise RuntimeError(f"Cannot serialize context of type {type(context)}")

    def _deserialize_context(self, data: Dict[str, Any]) -> Any:
        """Deserialize context."""
        from minerva_backend.prompt.extract_relationships import RelationshipContext

        return RelationshipContext(**data)


class ListCuratableMappingPayloadConverter(EncodingPayloadConverter):
    """Custom converter for List[CuratableMapping]."""

    @property
    def encoding(self) -> str:
        return "json/curatable-mapping-list"

    def to_payload(self, value: Any) -> Optional[Payload]:
        if isinstance(value, list) and all(
            isinstance(item, CuratableMapping) for item in value
        ):
            # Use the existing CuratableMappingPayloadConverter for each item
            curatable_converter = CuratableMappingPayloadConverter()
            data = {
                "items": [
                    {
                        "kind": item.kind,
                        "data": curatable_converter._serialize_data(item.data),
                        "spans": [
                            curatable_converter._serialize_span(span)
                            for span in item.spans
                        ],
                        "context": [
                            curatable_converter._serialize_context(ctx)
                            for ctx in (item.context or [])
                        ],
                    }
                    for item in value
                ]
            }
            return Payload(
                metadata={"encoding": self.encoding.encode()},
                data=json.dumps(data, cls=DateTimeEncoder).encode(),
            )
        return None

    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        if payload.metadata.get("encoding") == self.encoding.encode():
            data = json.loads(payload.data.decode())
            curatable_converter = CuratableMappingPayloadConverter()
            return [
                curatable_converter.from_payload(
                    Payload(
                        metadata={"encoding": b"json/curatable-mapping"},
                        data=json.dumps(item_data).encode(),
                    )
                )
                for item_data in data["items"]
            ]
        return None

    def _serialize_curatable_mapping(self, mapping: CuratableMapping) -> Dict[str, Any]:
        """Serialize CuratableMapping for use in list converter."""
        return {
            "kind": mapping.kind,
            "data": self._serialize_data(mapping.data),
            "spans": [self._serialize_span(span) for span in mapping.spans],
            "context": [
                self._serialize_context(ctx) for ctx in (mapping.context or [])
            ],
        }

    def _deserialize_curatable_mapping(self, data: Dict[str, Any]) -> CuratableMapping:
        """Deserialize CuratableMapping for use in list converter."""
        return CuratableMapping(
            kind=data["kind"],
            data=self._deserialize_data(data["data"], data["kind"]),
            spans=[self._deserialize_span(span) for span in data["spans"]],
            context=[
                self._deserialize_context(ctx) for ctx in (data.get("context") or [])
            ],
        )

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """Serialize data based on its type."""
        if hasattr(data, "model_dump"):  # Pydantic model
            data_dict = data.model_dump()
            # Convert datetime and date objects to ISO format for JSON serialization
            for key, value in data_dict.items():
                if isinstance(value, datetime):
                    data_dict[key] = value.isoformat()
                elif isinstance(value, date):
                    data_dict[key] = value.isoformat()
            return data_dict
        elif isinstance(data, dict):
            return data
        else:
            raise RuntimeError(f"Cannot serialize data of type {type(data)}")

    def _deserialize_data(self, data: Dict[str, Any], kind: str) -> Any:
        """Deserialize data based on kind."""
        if kind == "relation":
            return Relation(**data)
        elif kind == "concept_relation":
            return ConceptRelation(**data)
        elif kind == "feeling_emotion":
            return FeelingEmotion(**data)
        elif kind == "feeling_concept":
            return FeelingConcept(**data)
        else:
            raise RuntimeError(f"Unknown kind: {kind}")

    def _serialize_span(self, span: Any) -> Dict[str, Any]:
        """Serialize span."""
        if hasattr(span, "model_dump"):
            return span.model_dump()
        elif isinstance(span, dict):
            return span
        else:
            raise RuntimeError(f"Cannot serialize span of type {type(span)}")

    def _deserialize_span(self, data: Dict[str, Any]) -> Any:
        """Deserialize span."""
        from minerva_models import LexicalType, Span

        # Ensure type field is correct
        if "type" in data and data["type"] != LexicalType.SPAN.value:
            data["type"] = LexicalType.SPAN.value

        return Span(**data)

    def _serialize_context(self, context: Any) -> Dict[str, Any]:
        """Serialize context."""
        if hasattr(context, "model_dump"):
            data = context.model_dump()
            # Convert datetime and date objects to ISO format for JSON serialization
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, date):
                    data[key] = value.isoformat()
            return data
        elif isinstance(context, dict):
            return context
        else:
            raise RuntimeError(f"Cannot serialize context of type {type(context)}")

    def _deserialize_context(self, data: Dict[str, Any]) -> Any:
        """Deserialize context."""
        from minerva_backend.prompt.extract_relationships import RelationshipContext

        return RelationshipContext(**data)


def create_custom_data_converter():
    """Create a custom data converter that handles EntityMapping and CuratableMapping properly."""
    from temporalio.contrib.pydantic import pydantic_data_converter
    from temporalio.converter import (
        CompositePayloadConverter,
        DataConverter,
        DefaultPayloadConverter,
    )

    # Create composite payload converter with our custom converters first, then pydantic, then defaults
    # List converters must come before individual converters to match first
    payload_converter = CompositePayloadConverter(
        ListEntityMappingPayloadConverter(),
        ListCuratableMappingPayloadConverter(),
        EntityMappingPayloadConverter(),
        CuratableMappingPayloadConverter(),
        *pydantic_data_converter.payload_converter.converters.values(),
        *DefaultPayloadConverter.default_encoding_payload_converters,
    )

    # Create a custom DataConverter that uses our composite payload converter
    return DataConverter(payload_converter_class=lambda: payload_converter)
