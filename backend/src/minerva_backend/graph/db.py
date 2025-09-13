"""
Minerva Neo4j CRUD Operations
Comprehensive database operations for all entity types in the Minerva knowledge graph.
"""

from neo4j import GraphDatabase, Query
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date, time
import uuid
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from minerva_backend.graph.model import Person, Feeling, Event, Project, Concept, Resource, JournalEntry, \
    RelationshipType, EntityType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinervaDatabase:
    """
    Main database interface for Minerva knowledge graph operations.
    Provides comprehensive CRUD operations for all entity types.
    """

    def __init__(self, uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "Alxe342!"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connection()

    def _verify_connection(self):
        """Verify database connection and schema."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record and record["test"] == 1:
                    logger.info("Neo4j connection established successfully")
                else:
                    raise Exception("Connection test failed")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    # =============================================================================
    # PERSON CRUD OPERATIONS
    # =============================================================================

    def create_person(self, person: Person) -> str:
        """Create a new Person entity."""
        with self.driver.session() as session:
            query = """
            CREATE (p:Person $properties)
            RETURN p.id as id
            """
            properties = asdict(person)
            properties['last_updated'] = datetime.now()
            properties['first_mentioned'] = properties.get('first_mentioned', datetime.now())
            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created Person: {person.full_name} (ID: {person.id})")
            return record["id"]

    def get_person(self, person_id: str) -> Optional[Person]:
        """Retrieve a Person by ID."""
        with self.driver.session() as session:
            query = "MATCH (p:Person {id: $id}) RETURN p"
            result = session.run(query, id=person_id)
            record = result.single()

            if record:
                properties = dict(record["p"])
                return Person(**properties)
            return None

    def update_person(self, person_id: str, updates: Dict[str, Any]) -> bool:
        """Update Person properties."""
        with self.driver.session() as session:
            updates['last_updated'] = datetime.now()
            query = """
            MATCH (p:Person {id: $id})
            SET p += $updates
            RETURN p.id as id
            """
            result = session.run(query, id=person_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated Person: {person_id}")
            return success

    def delete_person(self, person_id: str) -> bool:
        """Delete a Person and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (p:Person {id: $id})
            DETACH DELETE p
            RETURN count(p) as deleted
            """
            result = session.run(query, id=person_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted Person: {person_id}")
            return success

    def list_persons(self, limit: int = 100, offset: int = 0) -> List[Person]:
        """List all Person entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (p:Person)
            RETURN p
            ORDER BY p.last_updated DESC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            persons = []
            for record in result:
                properties = dict(record["p"])
                persons.append(Person(**properties))
            return persons

    # =============================================================================
    # FEELING CRUD OPERATIONS
    # =============================================================================

    def create_feeling(self, feeling: Feeling) -> str:
        """Create a new Feeling entity."""
        with self.driver.session() as session:
            query = """
            CREATE (f:Feeling $properties)
            RETURN f.id as id
            """
            properties = asdict(feeling)

            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created Feeling: {feeling.emotion_type} (ID: {feeling.id})")
            return record["id"]

    def get_feeling(self, feeling_id: str) -> Optional[Feeling]:
        """Retrieve a Feeling by ID."""
        with self.driver.session() as session:
            query = "MATCH (f:Feeling {id: $id}) RETURN f"
            result = session.run(query, id=feeling_id)
            record = result.single()

            if record:
                properties = dict(record["f"])
                return Feeling(**properties)
            return None

    def update_feeling(self, feeling_id: str, updates: Dict[str, Any]) -> bool:
        """Update Feeling properties."""
        with self.driver.session() as session:
            query = """
            MATCH (f:Feeling {id: $id})
            SET f += $updates
            RETURN f.id as id
            """
            result = session.run(query, id=feeling_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated Feeling: {feeling_id}")
            return success

    def delete_feeling(self, feeling_id: str) -> bool:
        """Delete a Feeling and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (f:Feeling {id: $id})
            DETACH DELETE f
            RETURN count(f) as deleted
            """
            result = session.run(query, id=feeling_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted Feeling: {feeling_id}")
            return success

    def list_feelings(self, limit: int = 100, offset: int = 0) -> List[Feeling]:
        """List all Feeling entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (f:Feeling)
            RETURN f
            ORDER BY f.timestamp DESC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            feelings = []
            for record in result:
                properties = dict(record["f"])
                feelings.append(Feeling(**properties))
            return feelings

    # =============================================================================
    # EVENT CRUD OPERATIONS
    # =============================================================================

    def create_event(self, event: Event) -> str:
        """Create a new Event entity."""
        with self.driver.session() as session:
            query = """
            CREATE (e:Event $properties)
            RETURN e.id as id
            """
            properties = asdict(event)

            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created Event: {event.title} (ID: {event.id})")
            return record["id"]

    def get_event(self, event_id: str) -> Optional[Event]:
        """Retrieve an Event by ID."""
        with self.driver.session() as session:
            query = "MATCH (e:Event {id: $id}) RETURN e"
            result = session.run(query, id=event_id)
            record = result.single()

            if record:
                properties = dict(record["e"])
                return Event(**properties)
            return None

    def update_event(self, event_id: str, updates: Dict[str, Any]) -> bool:
        """Update Event properties."""
        with self.driver.session() as session:
            query = """
            MATCH (e:Event {id: $id})
            SET e += $updates
            RETURN e.id as id
            """
            result = session.run(query, id=event_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated Event: {event_id}")
            return success

    def delete_event(self, event_id: str) -> bool:
        """Delete an Event and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (e:Event {id: $id})
            DETACH DELETE e
            RETURN count(e) as deleted
            """
            result = session.run(query, id=event_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted Event: {event_id}")
            return success

    def list_events(self, limit: int = 100, offset: int = 0) -> List[Event]:
        """List all Event entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (e:Event)
            RETURN e
            ORDER BY e.start_date DESC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            events = []
            for record in result:
                properties = dict(record["e"])
                events.append(Event(**properties))
            return events

    # =============================================================================
    # PROJECT CRUD OPERATIONS
    # =============================================================================

    def create_project(self, project: Project) -> str:
        """Create a new Project entity."""
        with self.driver.session() as session:
            query = """
            CREATE (pr:Project $properties)
            RETURN pr.id as id
            """
            properties = asdict(project)

            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created Project: {project.name} (ID: {project.id})")
            return record["id"]

    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a Project by ID."""
        with self.driver.session() as session:
            query = "MATCH (pr:Project {id: $id}) RETURN pr"
            result = session.run(query, id=project_id)
            record = result.single()

            if record:
                properties = dict(record["pr"])
                return Project(**properties)
            return None

    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """Update Project properties."""
        with self.driver.session() as session:
            query = """
            MATCH (pr:Project {id: $id})
            SET pr += $updates
            RETURN pr.id as id
            """
            result = session.run(query, id=project_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated Project: {project_id}")
            return success

    def delete_project(self, project_id: str) -> bool:
        """Delete a Project and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (pr:Project {id: $id})
            DETACH DELETE pr
            RETURN count(pr) as deleted
            """
            result = session.run(query, id=project_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted Project: {project_id}")
            return success

    def list_projects(self, limit: int = 100, offset: int = 0) -> List[Project]:
        """List all Project entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (pr:Project)
            RETURN pr
            ORDER BY pr.priority DESC, pr.start_date DESC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            projects = []
            for record in result:
                properties = dict(record["pr"])
                projects.append(Project(**properties))
            return projects

    # =============================================================================
    # CONCEPT CRUD OPERATIONS
    # =============================================================================

    def create_concept(self, concept: Concept) -> str:
        """Create a new Concept entity."""
        with self.driver.session() as session:
            query = """
            CREATE (c:Concept $properties)
            RETURN c.id as id
            """
            properties = asdict(concept)

            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created Concept: {concept.title} (ID: {concept.id})")
            return record["id"]

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Retrieve a Concept by ID."""
        with self.driver.session() as session:
            query = "MATCH (c:Concept {id: $id}) RETURN c"
            result = session.run(query, id=concept_id)
            record = result.single()

            if record:
                properties = dict(record["c"])
                return Concept(**properties)
            return None

    def update_concept(self, concept_id: str, updates: Dict[str, Any]) -> bool:
        """Update Concept properties."""
        with self.driver.session() as session:
            query = """
            MATCH (c:Concept {id: $id})
            SET c += $updates
            RETURN c.id as id
            """
            result = session.run(query, id=concept_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated Concept: {concept_id}")
            return success

    def delete_concept(self, concept_id: str) -> bool:
        """Delete a Concept and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (c:Concept {id: $id})
            DETACH DELETE c
            RETURN count(c) as deleted
            """
            result = session.run(query, id=concept_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted Concept: {concept_id}")
            return success

    def list_concepts(self, limit: int = 100, offset: int = 0) -> List[Concept]:
        """List all Concept entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (c:Concept)
            RETURN c
            ORDER BY c.understanding_level DESC, c.title ASC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            concepts = []
            for record in result:
                properties = dict(record["c"])
                concepts.append(Concept(**properties))
            return concepts

    # =============================================================================
    # RESOURCE CRUD OPERATIONS
    # =============================================================================

    def create_resource(self, resource: Resource) -> str:
        """Create a new Resource entity."""
        with self.driver.session() as session:
            query = """
            CREATE (r:Resource $properties)
            RETURN r.id as id
            """
            properties = asdict(resource)

            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created Resource: {resource.title} (ID: {resource.id})")
            return record["id"]

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Retrieve a Resource by ID."""
        with self.driver.session() as session:
            query = "MATCH (r:Resource {id: $id}) RETURN r"
            result = session.run(query, id=resource_id)
            record = result.single()

            if record:
                properties = dict(record["r"])
                return Resource(**properties)
            return None

    def update_resource(self, resource_id: str, updates: Dict[str, Any]) -> bool:
        """Update Resource properties."""
        with self.driver.session() as session:
            query = """
            MATCH (r:Resource {id: $id})
            SET r += $updates
            RETURN r.id as id
            """
            result = session.run(query, id=resource_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated Resource: {resource_id}")
            return success

    def delete_resource(self, resource_id: str) -> bool:
        """Delete a Resource and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (r:Resource {id: $id})
            DETACH DELETE r
            RETURN count(r) as deleted
            """
            result = session.run(query, id=resource_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted Resource: {resource_id}")
            return success

    def list_resources(self, limit: int = 100, offset: int = 0) -> List[Resource]:
        """List all Resource entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (r:Resource)
            RETURN r
            ORDER BY r.rating DESC, r.consumption_date DESC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            resources = []
            for record in result:
                properties = dict(record["r"])
                resources.append(Resource(**properties))
            return resources

    # =============================================================================
    # JOURNAL ENTRY CRUD OPERATIONS
    # =============================================================================

    def create_journal_entry(self, journal_entry: JournalEntry) -> str:
        """Create a new JournalEntry entity."""
        with self.driver.session() as session:
            query = """
            CREATE (j:JournalEntry $properties)
            RETURN j.id as id
            """
            properties = asdict(journal_entry)

            result = session.run(query, properties=properties)
            record = result.single()
            logger.info(f"Created JournalEntry: {journal_entry.date} (ID: {journal_entry.id})")
            return record["id"]

    def get_journal_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Retrieve a JournalEntry by ID."""
        with self.driver.session() as session:
            query = "MATCH (j:JournalEntry {id: $id}) RETURN j"
            result = session.run(query, id=entry_id)
            record = result.single()

            if record:
                properties = dict(record["j"])
                return JournalEntry(**properties)
            return None

    def update_journal_entry(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update JournalEntry properties."""
        with self.driver.session() as session:
            query = """
            MATCH (j:JournalEntry {id: $id})
            SET j += $updates
            RETURN j.id as id
            """
            result = session.run(query, id=entry_id, updates=updates)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Updated JournalEntry: {entry_id}")
            return success

    def delete_journal_entry(self, entry_id: str) -> bool:
        """Delete a JournalEntry and all relationships."""
        with self.driver.session() as session:
            query = """
            MATCH (j:JournalEntry {id: $id})
            DETACH DELETE j
            RETURN count(j) as deleted
            """
            result = session.run(query, id=entry_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted JournalEntry: {entry_id}")
            return success

    def list_journal_entries(self, limit: int = 100, offset: int = 0) -> List[JournalEntry]:
        """List all JournalEntry entities with pagination."""
        with self.driver.session() as session:
            query = """
            MATCH (j:JournalEntry)
            RETURN j
            ORDER BY j.date DESC
            SKIP $offset LIMIT $limit
            """
            result = session.run(query, offset=offset, limit=limit)
            entries = []
            for record in result:
                properties = dict(record["j"])
                entries.append(JournalEntry(**properties))
            return entries

    # =============================================================================
    # RELATIONSHIP OPERATIONS
    # =============================================================================

    def create_relationship(self, from_id: str, to_id: str,
                            relationship_type: RelationshipType,
                            properties: Dict[str, Any] = None) -> bool:
        """Create a relationship between two entities."""
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
            CREATE (a)-[r:{relationship_type.value} $properties]->(b)
            RETURN r
            """
            properties = properties or {}
            result = session.run(query, from_id=from_id, to_id=to_id, properties=properties)
            record = result.single()
            success = record is not None
            if success:
                logger.info(f"Created relationship: {from_id} -{relationship_type.value}-> {to_id}")
            return success

    def delete_relationship(self, from_id: str, to_id: str,
                            relationship_type: RelationshipType) -> bool:
        """Delete a specific relationship between two entities."""
        with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $from_id}})-[r:{relationship_type.value}]->(b {{id: $to_id}})
            DELETE r
            RETURN count(r) as deleted
            """
            result = session.run(query, from_id=from_id, to_id=to_id)
            record = result.single()
            success = record["deleted"] > 0
            if success:
                logger.info(f"Deleted relationship: {from_id} -{relationship_type.value}-> {to_id}")
            return success

    def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for an entity."""
        with self.driver.session() as session:
            query = """
            MATCH (a {id: $entity_id})-[r]-(b)
            RETURN a, r, b, type(r) as relationship_type, 
                   startNode(r).id as from_id, endNode(r).id as to_id
            """
            result = session.run(query, entity_id=entity_id)
            relationships = []
            for record in result:
                relationships.append({
                    "from_id": record["from_id"],
                    "to_id": record["to_id"],
                    "relationship_type": record["relationship_type"],
                    "properties": dict(record["r"]),
                    "from_entity": dict(record["a"]),
                    "to_entity": dict(record["b"])
                })
            return relationships

    # =============================================================================
    # UTILITY OPERATIONS
    # =============================================================================

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        with self.driver.session() as session:
            # Count entities by type
            entity_query = """
            MATCH (n)
            RETURN labels(n)[0] as entity_type, count(n) as count
            ORDER BY count DESC
            """
            entity_result = session.run(entity_query)
            entity_counts = {record["entity_type"]: record["count"] for record in entity_result}

            # Count relationships by type
            relationship_query = """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
            relationship_result = session.run(relationship_query)
            relationship_counts = {record["relationship_type"]: record["count"] for record in relationship_result}

            # Total counts
            total_query = """
            MATCH (n) RETURN count(n) as total_nodes
            UNION ALL
            MATCH ()-[r]->() RETURN count(r) as total_relationships
            """
            total_result = session.run(total_query)
            totals = [record.values()[0] for record in total_result]

            return {
                "total_nodes": totals[0] if len(totals) > 0 else 0,
                "total_relationships": totals[1] if len(totals) > 1 else 0,
                "entity_counts": entity_counts,
                "relationship_counts": relationship_counts
            }

    def search_entities(self, search_term: str, entity_types: List[EntityType] = None) -> List[Dict[str, Any]]:
        """Search entities by text across all properties."""
        with self.driver.session() as session:
            if entity_types:
                labels_filter = " OR ".join([f"n:{et.value}" for et in entity_types])
                where_clause = f"({labels_filter}) AND "
            else:
                where_clause = ""

            query = f"""
            MATCH (n)
            WHERE {where_clause}
                  any(prop in keys(n) WHERE toString(n[prop]) CONTAINS $search_term)
            RETURN n, labels(n) as entity_types
            LIMIT 50
            """

            result = session.run(query, search_term=search_term)
            entities = []
            for record in result:
                entity_data = dict(record["n"])
                entity_data["entity_types"] = record["entity_types"]
                entities.append(entity_data)
            return entities


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

def main():
    """Example usage of the Minerva database operations."""

    # Initialize database connection
    db = MinervaDatabase()

    try:
        # Test Person operations
        print("=== Testing Person Operations ===")
        person = Person(
            id=str(uuid.uuid4()),
            full_name="Ana Martínez",
            aliases=["Ana", "Anita"],
            occupation="Data Scientist",
            relationship_type="colleague",
            mention_count=1,
            emotional_valence=0.8
        )

        # Create
        person_id = db.create_person(person)
        print(f"Created person with ID: {person_id}")

        # Read
        retrieved_person = db.get_person(person_id)
        print(f"Retrieved person: {retrieved_person.full_name}")

        # Update
        db.update_person(person_id, {"mention_count": 5, "emotional_valence": 0.9})
        print("Updated person mention count and emotional valence")

        # List
        persons = db.list_persons(limit=5)
        print(f"Found {len(persons)} persons in database")

        # Test Feeling operations
        print("\n=== Testing Feeling Operations ===")
        feeling = Feeling(
            id=str(uuid.uuid4()),
            emotion_type="excitement",
            intensity=9,
            timestamp=datetime.now(),
            duration_minutes=60,
            context="New project kickoff meeting"
        )

        feeling_id = db.create_feeling(feeling)
        print(f"Created feeling with ID: {feeling_id}")

        # Test relationships
        print("\n=== Testing Relationship Operations ===")
        success = db.create_relationship(
            person_id, feeling_id,
            RelationshipType.FEELS,
            {"intensity": 9, "context": "work excitement"}
        )
        print(f"Created relationship: {success}")

        # Get relationships
        relationships = db.get_entity_relationships(person_id)
        print(f"Person has {len(relationships)} relationships")

        # Database statistics
        print("\n=== Database Statistics ===")
        stats = db.get_database_stats()
        print(f"Total nodes: {stats['total_nodes']}")
        print(f"Total relationships: {stats['total_relationships']}")
        print(f"Entity counts: {stats['entity_counts']}")
        print(f"Relationship counts: {stats['relationship_counts']}")

        # Search test
        print("\n=== Search Test ===")
        search_results = db.search_entities("Ana", [EntityType.PERSON])
        print(f"Search for 'Ana' found {len(search_results)} results")

    except Exception as e:
        logger.error(f"Error during testing: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
