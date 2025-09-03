import os
from pathlib import Path
from typing import List, Dict

class ObsidianRAG:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.collection = None  # This would be initialized with your actual collection object
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize the collection if it's not already set."""
        if self.collection is None:
            # Replace this with your actual collection initialization logic
            print("Initializing collection...")
            self.collection = {}  # Placeholder for actual collection

    def index_vault(self):
        """Index all notes in the vault."""
        excluded_folders = ['.trash', '.idea', '.obsidian', '06 - Reference', 'Attachments']

        for file_path in self.vault_path.rglob('*'):
            if file_path.is_file() and not any(folder in str(file_path) for folder in excluded_folders):
                try:
                    note_data = self.parse_obsidian_note(file_path)
                    if not note_data:
                        continue

                    chunks = self.chunk_content(note_data['plain_content'])

                    documents = []
                    metadatas = []
                    ids = []

                    for i, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadata = {
                            'file_name': note_data['file_name'],
                            'file_path': note_data['relative_path'],
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'tags': ','.join(note_data.get('tags', [])),
                            'wikilinks': ','.join(note_data.get('wikilinks', [])),
                            'modified_time': note_data['modified_time']
                        }
                        metadatas.append(metadata)
                        ids.append(f"{note_data['relative_path']}_{i}")

                    if documents:
                        self.collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                        print(f"✅ Indexed {file_path.name}")
                except Exception as e:
                    print(f"Error indexing {file_path}: {e}")

    def parse_obsidian_note(self, file_path: Path):
        """Parse an Obsidian note and return its content."""
        # Implement your parsing logic here
        pass

    def chunk_content(self, content: str) -> List[str]:
        """Chunk the content into smaller pieces."""
        # Implement your chunking logic here
        pass

    def search(self, query: str, n_results: int = 5):
        """Search for notes matching the query."""
        try:
            results = self.collection.query(
                query_vector=self.encode_query(query),
                n_results=n_results,
                where={"wikilinks": {"$contains": note_name}}
            )

            linked_notes = []
            for i, metadata in enumerate(results['metadatas'][0]):
                linked_notes.append({
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'file_name': metadata['file_name'],
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })

            return linked_notes

        except Exception as e:
            print(f"Error finding linked notes: {e}")
            return []

    def update_note(self, file_path: str):
        """Update a single note in the index."""
        path = Path(file_path)
        if path.exists() and path.is_relative_to(self.vault_path):
            try:
                # Remove old versions
                relative_path = str(path.relative_to(self.vault_path))
                old_ids = [id for id in self.collection.get()['ids']
                           if id.startswith(relative_path)]

                if old_ids:
                    self.collection.delete(ids=old_ids)

                # Add updated version
                note_data = self.parse_obsidian_note(path)
                if not note_data:
                    return

                chunks = self.chunk_content(note_data['plain_content'])

                documents = []
                metadatas = []
                ids = []

                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadata = {
                        'file_name': note_data['file_name'],
                        'file_path': note_data['relative_path'],
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'tags': ','.join(note_data.get('tags', [])),
                        'wikilinks': ','.join(note_data.get('wikilinks', [])),
                        'modified_time': note_data['modified_time']
                    }
                    metadatas.append(metadata)
                    ids.append(f"{note_data['relative_path']}_{i}")

                if documents:
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    print(f"✅ Updated {path.name}")
                else:
                    print(f"⚠️  No content to index in {path.name}")

            except Exception as e:
                print(f"Error updating {file_path}: {e}")

    def find_text_matches(self, search_text: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Find exact text matches across all documents (bypassing vector search).
        Useful for debugging cases where semantic search doesn't find expected results.
        """
        self._initialize_collection()
        all_data = self.collection.get()
        matches = []

        for i, document in enumerate(all_data['documents']):
            content_to_search = document if case_sensitive else document.lower()
            search_text_prepared = search_text if case_sensitive else search_text.lower()

            if search_text_prepared in content_to_search:
                matches.append({
                    'content': document,
                    'metadata': all_data['metadatas'][i],
                    'id': all_data['ids'][i],
                    'file_name': all_data['metadatas'][i]['file_name']
                })

        return matches

# Example usage with enhanced debugging
if __name__ == "__main__":
    # Initialize RAG system
    vault_path = "D:\\yo"
    rag = ObsidianRAG(vault_path)

    # Index your vault
    rag.index_vault()

    # 1. First try semantic search
    print("=== Semantic Search for 'pelea con Ana' ===")
    results = rag.search("pelea con Ana", n_results=10)
    for i, r in enumerate(results):
        print(f"{i + 1}. 📄 {r['file_name']} (distance: {r['distance']:.4f})")
        print(f"   🏷️  Tags: {r['tags']}")
        print(f"   📝 {r['content'][:200]}...")
        print()

    # 2. If semantic search doesn't work, try exact text matching
    if not results:
        print("No results from semantic search, trying exact text matching...")
        exact_matches = rag.find_text_matches("pelea con Ana", case_sensitive=False)
        print(f"Found {len(exact_matches)} exact matches:")
        for i, match in enumerate(exact_matches):
            print(f"{i + 1}. 📄 {match['file_name']}")
            print(f"   📝 {match['content'][:200]}...")
            print()

    # 3. Check what's actually in the database
    print("=== Database Contents Sample ===")
    all_data = rag.collection.get()
    print(f"Total chunks in database: {len(all_data['ids'])}")

    # Show a few samples
    for i in range(min(3, len(all_data['ids']))):
        print(f"Chunk {i + 1}:")
        print(f"  ID: {all_data['ids'][i]}")
        print(f"  Content: {all_data['documents'][i][:100]}...")
        print(f"  Metadata: {json.dumps(all_data['metadatas'][i], indent=2)}")
        print()

    # 4. Search examples
    print("=== Semantic Search Examples ===")
    results = rag.search("productivity and goal setting", n_results=3)
    for r in results:
        print(f"📄 {r['file_name']} (distance: {r['distance']:.4f})")
        print(f"🏷️  Tags: {r['tags']}")
        print(f"📝 {r['content'][:200]}...")
        print("---")

    print("\n=== Tag Search ===")
    tag_results = rag.search_by_tags(["productivity", "goals"])
    for r in tag_results:
        print(f"📄 {r['file_name']} - Tags: {r['tags']}")

    print("\n=== Linked Notes ===")
    linked = rag.get_linked_notes("Daily Notes")
    for r in linked:
        print(f"📄 {r['file_name']} links to 'Daily Notes'")
