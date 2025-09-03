import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import chromadb
from sentence_transformers import SentenceTransformer
import markdown
from datetime import datetime
import html
import yaml  # Added for proper YAML parsing


class ObsidianRAG:
    def __init__(self, vault_path: str, collection_name: str = "obsidian_notes"):
        self.vault_path = Path(vault_path)
        self.collection_name = collection_name

        # Initialize embedding model
        self.embedder = SentenceTransformer('jinaai/jina-embeddings-v2-base-es', trust_remote_code=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def debug_search(self, query: str):
        """Debug search by showing exact matches and embedding details."""
        # Check for exact text matches
        exact_matches = self.find_text_matches(query, case_sensitive=False)
        print(f"Exact text matches for '{query}': {len(exact_matches)}")
        for match in exact_matches[:3]:
            print(f"File: {match['file_name']}")
            print(f"Content snippet: {match['content'][:100]}...")
            print()

        # Check the query embedding
        query_embedding = self.embedder.encode([query])
        print(f"Query embedding shape: {query_embedding.shape}")
        print(f"Query embedding sample: {query_embedding[0][:5]}")

    def parse_obsidian_note(self, file_path: Path) -> Optional[Dict]:
        """Parse an Obsidian markdown file and extract metadata with better error handling."""
        try:
            # Try multiple encodings to handle different file formats
            encodings = ['utf-8', 'latin-1', 'cp1252']
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                print(f"Could not read {file_path} with any encoding")
                return None

            # Extract frontmatter (YAML metadata)
            frontmatter = {}
            if content.startswith('---'):
                try:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        _, fm_content, content = parts
                        # Use proper YAML parsing
                        frontmatter = yaml.safe_load(fm_content) or {}
                except (yaml.YAMLError, ValueError) as e:
                    print(f"Error parsing frontmatter in {file_path}: {e}")
                    # Continue without frontmatter

            # Extract wikilinks [[Note Name|Alias]] or [[Note Name#Heading]]
            wikilinks = re.findall(r'\[\[([^\]\|#]+)(?:[#\|][^\]])*\]\]', content)

            # Extract tags #tag or #tag/subtag
            tags = re.findall(r'#([a-zA-ZÀ-ÿ0-9_\-/]+)', content)

            # Convert markdown to plain text for better embedding
            # First remove code blocks to avoid processing them as markdown
            content_no_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
            content_no_code = re.sub(r'`.*?`', '', content_no_code)

            # Convert markdown to HTML then to plain text
            html_content = markdown.markdown(content_no_code, extensions=['extra'])
            plain_content = html.unescape(re.sub('<[^<]+?>', '', html_content)).strip()

            # Get file stats
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()

            return {
                'file_path': str(file_path),
                'file_name': file_path.stem,
                'content': content,
                'plain_content': plain_content,
                'frontmatter': frontmatter,
                'wikilinks': wikilinks,
                'tags': tags,
                'modified_time': modified_time,
                'created_time': frontmatter.get('created', created_time),
                'relative_path': str(file_path.relative_to(self.vault_path))
            }

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None

    def chunk_content(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split content into overlapping chunks for better retrieval."""
        if not content or not content.strip():
            return []

        # Split into sentences first for better chunk boundaries
        sentences = re.split(r'(?<=[.!?])\s+', content)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_length + sentence_length > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                # Keep overlap sentences for next chunk
                if overlap > 0:
                    # Calculate how many sentences to keep for overlap
                    overlap_count = 0
                    overlap_length = 0
                    for i in range(len(current_chunk) - 1, -1, -1):
                        sent = current_chunk[i]
                        sent_length = len(sent.split())
                        if overlap_length + sent_length <= overlap:
                            overlap_length += sent_length
                            overlap_count += 1
                        else:
                            break
                    current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def index_vault(self, file_extensions: List[str] = ['.md'], chunk_notes: bool = True):
        """Index all notes in the Obsidian vault with progress tracking."""
        print(f"Indexing vault: {self.vault_path}")

        documents = []
        metadatas = []
        ids = []
        processed_files = 0
        error_files = 0

        # Find all markdown files
        for ext in file_extensions:
            file_list = list(self.vault_path.rglob(f'*{ext}'))
            print(f"Found {len(file_list)} {ext} files")

            for file_path in file_list:
                if file_path.is_file():
                    try:
                        note_data = self.parse_obsidian_note(file_path)
                        if not note_data:
                            error_files += 1
                            continue

                        if chunk_notes:
                            # Split into chunks
                            chunks = self.chunk_content(note_data['plain_content'])
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
                        else:
                            # Store whole note
                            documents.append(note_data['plain_content'])
                            metadata = {
                                'file_name': note_data['file_name'],
                                'file_path': note_data['relative_path'],
                                'tags': ','.join(note_data.get('tags', [])),
                                'wikilinks': ','.join(note_data.get('wikilinks', [])),
                                'modified_time': note_data['modified_time']
                            }
                            metadatas.append(metadata)
                            ids.append(note_data['relative_path'])

                        processed_files += 1
                        if processed_files % 100 == 0:
                            print(f"Processed {processed_files} files...")

                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        error_files += 1

        # Add to vector store
        if documents:
            print(f"Adding {len(documents)} document chunks to vector store...")
            # Add in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end_idx = min(i + batch_size, len(documents))
                self.collection.add(
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx],
                    ids=ids[i:end_idx]
                )
                print(f"Added batch {i // batch_size + 1}/{(len(documents) - 1) // batch_size + 1}")

            print(f"✅ Successfully indexed {processed_files} files with {len(documents)} chunks")
            if error_files > 0:
                print(f"❌ Failed to process {error_files} files")
        else:
            print("No documents found to index")

    def search(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """Search the vault using semantic similarity."""
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode([query]).tolist()

            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=filter_dict
            )

            # Format results
            search_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                search_results.append({
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'distance': results['distances'][0][i],
                    'file_name': metadata['file_name'],
                    'file_path': metadata.get('file_path', ''),
                    'tags': metadata.get('tags', '').split(','),
                    'wikilinks': metadata.get('wikilinks', '').split(',')
                })

            return search_results

        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def search_by_tags(self, tags: List[str], n_results: int = 10) -> List[Dict]:
        """Search notes by tags using ChromaDB's filtering capabilities."""
        try:
            # ChromaDB supports filtering with the "where" parameter
            tag_filters = [{"tags": {"$contains": tag}} for tag in tags]

            results = self.collection.query(
                query_texts=[""],  # Empty query to get all documents that match the filter
                n_results=n_results,
                where={"$or": tag_filters} if len(tags) > 1 else tag_filters[0]
            )

            formatted_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'file_name': metadata['file_name'],
                    'tags': metadata.get('tags', '').split(','),
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })

            return formatted_results

        except Exception as e:
            print(f"Error during tag search: {e}")
            # Fallback to manual filtering if ChromaDB query fails
            all_results = self.collection.get()
            matching_results = []

            for i, metadata in enumerate(all_results['metadatas']):
                note_tags = metadata.get('tags', '').split(',')
                if any(tag in note_tags for tag in tags):
                    matching_results.append({
                        'content': all_results['documents'][i],
                        'metadata': metadata,
                        'file_name': metadata['file_name'],
                        'tags': note_tags
                    })

            return matching_results[:n_results]

    def get_linked_notes(self, note_name: str) -> List[Dict]:
        """Find notes that link to a specific note using metadata filtering."""
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query to use only the filter
                n_results=20,
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

    rag.debug_search("pelea con Ana")
