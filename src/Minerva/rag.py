import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
import chromadb
from sentence_transformers import SentenceTransformer
import markdown
from datetime import datetime


class ObsidianRAG:
    def __init__(self, vault_path: str, collection_name: str = "obsidian_notes"):
        self.vault_path = Path(vault_path)
        self.collection_name = collection_name

        # Initialize embedding model (runs locally)
        self.embedder = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

        # Initialize ChromaDB (local vector store)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def parse_obsidian_note(self, file_path: Path) -> Dict:
        """Parse an Obsidian markdown file and extract metadata."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract frontmatter (YAML metadata)
        frontmatter = {}
        if content.startswith('---'):
            try:
                _, fm_content, content = content.split('---', 2)
                # Simple YAML parsing (you might want to use proper yaml library)
                for line in fm_content.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
            except ValueError:
                pass

        # Extract wikilinks [[Note Name]]
        wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)

        # Extract tags #tag
        tags = re.findall(r'#(\w+)', content)

        # Convert markdown to plain text for better embedding
        plain_content = markdown.markdown(content, extensions=['extra'])
        plain_content = re.sub('<[^<]+?>', '', plain_content)  # Strip HTML

        return {
            'file_path': str(file_path),
            'file_name': file_path.stem,
            'content': content,
            'plain_content': plain_content.strip(),
            'frontmatter': frontmatter,
            'wikilinks': wikilinks,
            'tags': tags,
            'modified_time': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'created_time': frontmatter.get('created', ''),
            'relative_path': str(file_path.relative_to(self.vault_path))
        }

    def chunk_content(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split content into overlapping chunks for better retrieval."""
        words = content.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks

    def index_vault(self, file_extensions: List[str] = ['.md'], chunk_notes: bool = True):
        """Index all notes in the Obsidian vault."""
        print(f"Indexing vault: {self.vault_path}")

        documents = []
        metadatas = []
        ids = []

        # Find all markdown files
        for ext in file_extensions:
            for file_path in self.vault_path.rglob(f'*{ext}'):
                if file_path.is_file():
                    try:
                        note_data = self.parse_obsidian_note(file_path)

                        if chunk_notes:
                            # Split into chunks
                            chunks = self.chunk_content(note_data['plain_content'])
                            for i, chunk in enumerate(chunks):
                                documents.append(chunk)
                                metadata = note_data.copy()
                                metadata['chunk_index'] = i
                                metadata['total_chunks'] = len(chunks)
                                metadatas.append(metadata)
                                ids.append(f"{note_data['relative_path']}_{i}")
                        else:
                            # Store whole note
                            documents.append(note_data['plain_content'])
                            metadatas.append(note_data)
                            ids.append(note_data['relative_path'])

                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

        # Add to vector store
        if documents:
            print(f"Adding {len(documents)} documents to vector store...")
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ Indexed {len(documents)} document chunks")
        else:
            print("No documents found to index")

    def search(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """Search the vault using semantic similarity."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict
        )

        # Format results
        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i],
                'file_name': results['metadatas'][0][i]['file_name'],
                'file_path': results['metadatas'][0][i]['file_path'],
                'tags': results['metadatas'][0][i].get('tags', []),
                'wikilinks': results['metadatas'][0][i].get('wikilinks', [])
            })

        return search_results

    def search_by_tags(self, tags: List[str], n_results: int = 10) -> List[Dict]:
        """Search notes by tags."""
        # ChromaDB doesn't support array contains, so we'll do post-filtering
        all_results = self.collection.get()
        matching_results = []

        for i, metadata in enumerate(all_results['metadatas']):
            note_tags = metadata.get('tags', [])
            if any(tag in note_tags for tag in tags):
                matching_results.append({
                    'content': all_results['documents'][i],
                    'metadata': metadata,
                    'file_name': metadata['file_name'],
                    'tags': note_tags
                })

        return matching_results[:n_results]

    def get_linked_notes(self, note_name: str) -> List[Dict]:
        """Find notes that link to a specific note."""
        # Search for notes containing [[note_name]]
        results = self.collection.query(
            query_texts=[f"[[{note_name}]]"],
            n_results=20
        )

        linked_notes = []
        for i, metadata in enumerate(results['metadatas'][0]):
            if note_name in metadata.get('wikilinks', []):
                linked_notes.append({
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'file_name': metadata['file_name']
                })

        return linked_notes

    def update_note(self, file_path: str):
        """Update a single note in the index (useful for real-time updates)."""
        path = Path(file_path)
        if path.exists():
            try:
                # Remove old versions
                old_ids = [id for id in self.collection.get()['ids']
                           if id.startswith(str(path.relative_to(self.vault_path)))]
                if old_ids:
                    self.collection.delete(ids=old_ids)

                # Add updated version
                note_data = self.parse_obsidian_note(path)
                chunks = self.chunk_content(note_data['plain_content'])

                documents = []
                metadatas = []
                ids = []

                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadata = note_data.copy()
                    metadata['chunk_index'] = i
                    metadata['total_chunks'] = len(chunks)
                    metadatas.append(metadata)
                    ids.append(f"{note_data['relative_path']}_{i}")

                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"✅ Updated {path.name}")

            except Exception as e:
                print(f"Error updating {file_path}: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize RAG system
    vault_path = "D:\\yo"  # Change this!
    rag = ObsidianRAG(vault_path)

    # Index your vault (run this once, or when you want to refresh)
    rag.index_vault()

    # Search examples
    print("=== Semantic Search ===")
    results = rag.search("productivity and goal setting", n_results=3)
    for r in results:
        print(f"📄 {r['file_name']}")
        print(f"🏷️  Tags: {r['tags']}")
        print(f"📝 {r['content'][:200]}...")
        print(f"🔗 Links: {r['wikilinks']}")
        print("---")

    print("\n=== Tag Search ===")
    tag_results = rag.search_by_tags(["productivity", "goals"])
    for r in tag_results:
        print(f"📄 {r['file_name']} - Tags: {r['tags']}")

    print("\n=== Linked Notes ===")
    linked = rag.get_linked_notes("Daily Notes")
    for r in linked:
        print(f"📄 {r['file_name']} links to 'Daily Notes'")
