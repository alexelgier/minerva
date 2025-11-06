#!/usr/bin/env python3
"""
Test script to demonstrate entity extraction logging and identify cross-pollination issues.

This script will run entity extraction on a sample journal entry and show detailed
logging output for each processor to help identify where cross-pollination occurs.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minerva_backend.containers import Container
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.utils.logging import setup_logging


async def test_extraction_logging():
    """Test entity extraction with detailed logging."""
    
    # Setup logging
    setup_logging()
    
    # Initialize container
    container = Container()
    
    # Create a sample journal entry that might cause cross-pollination
    sample_text = """
    Hoy fui a almorzar con Ana Sorin al restaurante Chino. 
    Comí una milanesa de soja y bebí mate. 
    Ana me recomendó el libro "El Proceso" de Kafka.
    También vimos un video de YouTube sobre programación.
    Después fuimos a mi casa donde trabajamos en el proyecto Minerva.
    """
    
    journal_entry = JournalEntry(
        uuid="test-journal-001",
        entry_text=sample_text,
        entry_date="2024-01-15",
        created_at="2024-01-15T10:00:00Z"
    )
    
    print("=" * 80)
    print("TESTING ENTITY EXTRACTION WITH CROSS-POLLINATION FIX")
    print("=" * 80)
    print(f"Journal Entry: {journal_entry.uuid}")
    print(f"Text: {journal_entry.entry_text}")
    print("=" * 80)
    print("🔧 FIX APPLIED: Entity type filtering in deduplication logic")
    print("   - Each processor now only looks up entities of its own type")
    print("   - This prevents people from being overwritten as consumables/content")
    print("=" * 80)
    
    try:
        # Get the extraction service
        extraction_service = container.extraction_service()
        
        print("\nStarting entity extraction...")
        print("Watch the logs below for detailed extraction information:\n")
        
        # Run extraction
        entities = await extraction_service.extract_entities(journal_entry)
        
        print("\n" + "=" * 80)
        print("EXTRACTION RESULTS SUMMARY")
        print("=" * 80)
        
        # Group entities by type
        entities_by_type = {}
        for entity_mapping in entities:
            entity_type = entity_mapping.entity.type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity_mapping.entity.name)
        
        # Display results
        for entity_type, names in entities_by_type.items():
            print(f"\n{entity_type} ({len(names)}):")
            for name in names:
                print(f"  - {name}")
        
        print(f"\nTotal entities extracted: {len(entities)}")
        
        # Check for potential cross-pollination
        print("\n" + "=" * 80)
        print("CROSS-POLLINATION ANALYSIS")
        print("=" * 80)
        
        # Look for people names in other categories
        people_names = set(entities_by_type.get("Person", []))
        
        for entity_type in ["Consumable", "Content", "Concept"]:
            if entity_type in entities_by_type:
                other_names = set(entities_by_type[entity_type])
                cross_pollination = people_names.intersection(other_names)
                if cross_pollination:
                    print(f"⚠️  POTENTIAL CROSS-POLLINATION: {entity_type} contains people names:")
                    for name in cross_pollination:
                        print(f"   - {name} (also found in Person)")
                else:
                    print(f"✅ No cross-pollination detected in {entity_type}")
        
        print("\n" + "=" * 80)
        print("Check the logs above for detailed extraction information from each processor.")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_extraction_logging())
