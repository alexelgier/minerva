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
import yaml
import numpy as np
import unicodedata


class ObsidianRAG:
    def __init__(self, vault_path: str, collection_name: str = "obsidian_notes"):
        self.vault_path = Path(vault_path)
        self.collection_name = collection_name

        # Initialize embedding model
        self.embedder = SentenceTransformer('jinaai/jina-embeddings-v2-base-es', trust_remote_code=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "dimension": 768,  # Explicitly set dimension for Jina model
                "ef_construction": 1000,
                "ef_search": 200
            }
        )

        # Search performance tracking
        self.search_performance = []
    def normalize_spanish_text(self, text: str) -> str:
        """Normalize Spanish text for consistent Unicode handling"""
        # Normalize unicode characters (NFD -> NFC)
        return unicodedata.normalize('NFC', text)

    def extract_semantic_content(self, content: str) -> str:
        """Extract content while preserving semantic markers - FIXED LINK PROCESSING"""
        # Normalize the text first
        content = self.normalize_spanish_text(content)

        # FIXED: Preserve wikilinks as semantic markers, ignoring aliases
        # [[Link Name|Alias]] -> LINK:Link Name (ignore the |Alias part)
        # [[Link Name#Section|Alias]] -> LINK:Link Name (ignore both #Section and |Alias)
        # [[Link Name]] -> LINK:Link Name
        content = re.sub(r'\[\[([^\]|#]+)(?:[#|][^\]]*)*\]\]', r'LINK:\1', content)

        # Preserve headers as section markers
        content = re.sub(r'^#{1,6}\s*(.+)$', r'SECTION:\1', content, flags=re.MULTILINE)

        # Preserve tags as semantic markers
        content = re.sub(r'#([a-zA-ZÀ-ÿ0-9_\-/]+)', r'TAG:\1', content)

        # Convert lists while preserving structure
        content = re.sub(r'^\s*[-*+]\s*(.+)$', r'LIST_ITEM:\1', content, flags=re.MULTILINE)

        # Remove code blocks but preserve inline code context
        content = re.sub(r'```.*?```', '[CODE_BLOCK]', content, flags=re.DOTALL)
        content = re.sub(r'`([^`]+)`', r'CODE:\1', content)

        return content

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
            content_without_fm = content
            if content.startswith('---'):
                try:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        _, fm_content, content_without_fm = parts
                        # Use proper YAML parsing
                        frontmatter = yaml.safe_load(fm_content) or {}
                except (yaml.YAMLError, ValueError) as e:
                    print(f"Error parsing frontmatter in {file_path}: {e}")
                    content_without_fm = content

            # FIXED: Extract wikilinks [[Note Name|Alias]] or [[Note Name#Heading]] - only keep the main note name
            wikilinks = re.findall(r'\[\[([^\]\|#]+)(?:[#\|][^\]])*\]\]', content_without_fm)

            # Extract tags #tag or #tag/subtag
            tags = re.findall(r'#([a-zA-ZÀ-ÿ0-9_\-/]+)', content_without_fm)

            # Use improved semantic content extraction instead of plain text conversion
            semantic_content = self.extract_semantic_content(content_without_fm)

            # Get file stats
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()

            return {
                'file_path': str(file_path),
                'file_name': file_path.stem,
                'content': content,
                'semantic_content': semantic_content,
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

    def chunk_content_improved(self, content: str, chunk_size: int = 100, overlap_ratio: float = 0.25) -> List[str]:
        """Improved chunking with better Spanish text handling and smaller chunks"""
        if not content or not content.strip():
            return []

        # Spanish sentence endings (including inverted punctuation)
        sentence_pattern = r'(?<=[.!?¡¿])\s+'
        sentences = re.split(sentence_pattern, content)

        chunks = []
        overlap_words = int(chunk_size * overlap_ratio)

        current_chunk = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            if current_word_count + sentence_words > chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)

                # Keep overlap sentences
                overlap_sentences = []
                overlap_count = 0
                for sent in reversed(current_chunk):
                    sent_words = len(sent.split())
                    if overlap_count + sent_words <= overlap_words:
                        overlap_sentences.insert(0, sent)
                        overlap_count += sent_words
                    else:
                        break

                current_chunk = overlap_sentences
                current_word_count = overlap_count

            current_chunk.append(sentence)
            current_word_count += sentence_words

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append(chunk_text)

        return chunks

    def add_with_validation(self, documents: List[str], metadatas: List[Dict], ids: List[str],
                            small_batch_size: int = 5):
        """Add documents with embedding validation and SMALL batch processing to prevent OOM"""
        if not documents:
            return

        # Process in very small batches to avoid memory issues
        total_processed = 0

        for batch_start in range(0, len(documents), small_batch_size):
            batch_end = min(batch_start + small_batch_size, len(documents))
            batch_docs = documents[batch_start:batch_end]
            batch_metas = metadatas[batch_start:batch_end]
            batch_ids = ids[batch_start:batch_end]

            try:
                # Generate embeddings for small batch
                embeddings = self.embedder.encode(batch_docs, batch_size=1, convert_to_numpy=True)

                # Validate dimensions
                expected_dim = embeddings.shape[1]

                # Check for NaN or infinite values
                invalid_embeddings = []
                for i, emb in enumerate(embeddings):
                    if np.isnan(emb).any() or np.isinf(emb).any():
                        invalid_embeddings.append(i)

                if invalid_embeddings:
                    print(f"Warning: {len(invalid_embeddings)} invalid embeddings in batch")
                    # Remove invalid entries
                    valid_indices = [i for i in range(len(batch_docs)) if i not in invalid_embeddings]
                    batch_docs = [batch_docs[i] for i in valid_indices]
                    batch_metas = [batch_metas[i] for i in valid_indices]
                    batch_ids = [batch_ids[i] for i in valid_indices]
                    embeddings = embeddings[valid_indices]

                # Add to collection with explicit embeddings
                if len(batch_docs) > 0:
                    self.collection.add(
                        documents=batch_docs,
                        metadatas=batch_metas,
                        ids=batch_ids,
                        embeddings=embeddings.tolist()
                    )
                    total_processed += len(batch_docs)

            except Exception as e:
                print(f"Error processing batch {batch_start}-{batch_end}: {e}")
                continue

        # print(f"Successfully added {total_processed} documents")

    def should_skip_folder(self, file_path: Path, skip_folders: List[str]) -> bool:
        """Check if a file is in a folder that should be skipped."""
        try:
            relative_path = file_path.relative_to(self.vault_path)
            path_parts = relative_path.parts

            # Check if any part of the path matches a skip folder
            for folder in skip_folders:
                if folder in path_parts:
                    return True

            return False
        except ValueError:
            # File is not relative to vault_path
            return True

    def validate_embeddings(self):
        """Test embedding generation and validate dimensions"""
        test_text = "Test embedding generation"
        test_embedding = self.embedder.encode([test_text])
        expected_dim = test_embedding.shape[1]

        print(f"Embedding model produces {expected_dim} dimensions")

        # Check if collection exists and has different dimensions
        try:
            existing_count = self.collection.count()
            if existing_count > 0:
                # Test query to check dimension compatibility
                self.collection.query(
                    query_embeddings=test_embedding.tolist(),
                    n_results=1
                )
                print("Embedding dimensions are compatible with existing collection")
        except Exception as e:
            if "dimension" in str(e).lower():
                print(f"Dimension mismatch detected: {e}")
                print("Consider resetting the collection or changing the embedding model")
                return False
        return True

    def reset_collection(self):
        """Reset/recreate the collection to fix any dimension or corruption issues."""
        try:
            # Delete existing collection
            self.client.delete_collection(name=self.collection_name)
            print(f"Deleted existing collection: {self.collection_name}")
        except Exception as e:
            print(f"Could not delete collection (may not exist): {e}")

        # Recreate collection with proper dimensions
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={
                "hnsw:space": "cosine",
                "dimension": 768,  # Set for Jina model
                "ef_construction": 1000,
                "ef_search": 200
            }
        )
        print(f"Created fresh collection: {self.collection_name}")

    def analyze_search_performance(self, query: str, results: List[Dict]):
        """Analyze and log search performance metrics"""
        if not results:
            print("No results found for query")
            return

        # Calculate performance metrics
        exact_matches = sum(1 for r in results if query.lower() in r['content'].lower())
        avg_distance = sum(r['distance'] for r in results) / len(results)
        min_distance = min(r['distance'] for r in results)
        max_distance = max(r['distance'] for r in results)

        # Store performance data
        performance_data = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'total_results': len(results),
            'exact_matches': exact_matches,
            'avg_distance': avg_distance,
            'min_distance': min_distance,
            'max_distance': max_distance,
            'top_result_file': results[0]['file_name'],
            'top_result_distance': results[0]['distance']
        }

        self.search_performance.append(performance_data)

        # Print performance summary
        print(f"\n=== SEARCH PERFORMANCE ===")
        print(f"Query: '{query}'")
        print(f"Total results: {len(results)}")
        print(f"Exact matches: {exact_matches}")
        print(f"Distance range: {min_distance:.4f} - {max_distance:.4f}")
        print(f"Average distance: {avg_distance:.4f}")
        print(f"Top result: {results[0]['file_name']} (distance: {results[0]['distance']:.4f})")

    def search(self, query: str, n_results: int = 5, filter_dict: Dict = None) -> List[Dict]:
        """Search the vault using semantic similarity with performance tracking."""
        search_start = datetime.now()

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
                    'tags': metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                    'wikilinks': metadata.get('wikilinks', '').split(',') if metadata.get('wikilinks') else []
                })

            # Calculate search time
            search_time = (datetime.now() - search_start).total_seconds()
            print(f"Search completed in {search_time:.3f} seconds")

            # Analyze performance
            self.analyze_search_performance(query, search_results)

            return search_results

        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def print_performance_summary(self):
        """Print a summary of all search performances"""
        if not self.search_performance:
            print("No search performance data available")
            return

        print("\n" + "=" * 50)
        print("OVERALL SEARCH PERFORMANCE SUMMARY")
        print("=" * 50)

        total_searches = len(self.search_performance)
        avg_results = sum(p['total_results'] for p in self.search_performance) / total_searches
        avg_exact_matches = sum(p['exact_matches'] for p in self.search_performance) / total_searches
        avg_distance = sum(p['avg_distance'] for p in self.search_performance) / total_searches

        print(f"Total searches performed: {total_searches}")
        print(f"Average results per search: {avg_results:.1f}")
        print(f"Average exact matches per search: {avg_exact_matches:.1f}")
        print(f"Average distance score: {avg_distance:.4f}")

        # Show most effective queries (lowest average distance)
        best_queries = sorted(self.search_performance, key=lambda x: x['avg_distance'])[:3]
        print("\nTop 3 most effective queries:")
        for i, query in enumerate(best_queries):
            print(f"{i + 1}. '{query['query']}' (avg distance: {query['avg_distance']:.4f})")

        # Show least effective queries (highest average distance)
        worst_queries = sorted(self.search_performance, key=lambda x: x['avg_distance'], reverse=True)[:3]
        print("\nTop 3 least effective queries:")
        for i, query in enumerate(worst_queries):
            print(f"{i + 1}. '{query['query']}' (avg distance: {query['avg_distance']:.4f})")

    # ... (keep all other methods the same but remove any debug logging from them)

    def index_vault(self, file_extensions: List[str] = ['.md'], chunk_notes: bool = True,
                    skip_folders: List[str] = None):
        """Index all notes in the Obsidian vault with progress tracking and MEMORY OPTIMIZATION."""
        if skip_folders is None:
            skip_folders = ['.idea', '.obsidian', '.trash', '06 - Reference', 'Attachments']

        print(f"Indexing vault: {self.vault_path}")
        print(f"Skipping folders: {skip_folders}")

        documents = []
        metadatas = []
        ids = []
        processed_files = 0
        error_files = 0
        empty_files = 0
        skipped_files = 0

        # Find all markdown files
        total_files_found = 0
        for ext in file_extensions:
            file_list = list(self.vault_path.rglob(f'*{ext}'))
            total_files_found += len(file_list)
            print(f"Found {len(file_list)} {ext} files")

            for file_path in file_list:
                if file_path.is_file():
                    # Check if file should be skipped based on folder
                    if self.should_skip_folder(file_path, skip_folders):
                        skipped_files += 1
                        continue

                    try:
                        note_data = self.parse_obsidian_note(file_path)
                        if not note_data:
                            error_files += 1
                            continue

                        # Check if this file contributes any content
                        if not note_data['semantic_content'].strip():
                            empty_files += 1
                            continue

                        if chunk_notes:
                            # Split into chunks using improved method
                            chunks = self.chunk_content_improved(note_data['semantic_content'])
                            if not chunks:  # Skip if no chunks created
                                empty_files += 1
                                continue

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
                            documents.append(note_data['semantic_content'])
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

                        # MEMORY OPTIMIZATION: Process in smaller batches during collection
                        if len(documents) >= 50:
                            # print(f"Processing batch of {len(documents)} documents...")
                            self.add_with_validation(documents, metadatas, ids, small_batch_size=5)
                            documents.clear()
                            metadatas.clear()
                            ids.clear()

                        if processed_files % 100 == 0:
                            print(f"Processed {processed_files} files...")

                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")
                        error_files += 1

        # Add any remaining documents
        if documents:
            print(f"Processing final batch of {len(documents)} documents...")
            self.add_with_validation(documents, metadatas, ids, small_batch_size=5)

        print(f"\n=== INDEXING SUMMARY ===")
        print(f"Total files found: {total_files_found}")
        print(f"Files processed: {processed_files}")
        print(f"Files skipped (excluded dirs): {skipped_files}")
        print(f"Empty/skipped files: {empty_files}")
        print(f"Error files: {error_files}")
        print(f"Indexing completed!")

    def search_by_tags(self, tags: List[str], n_results: int = 10) -> List[Dict]:
        """Search notes by tags using proper ChromaDB filtering."""
        try:
            if len(tags) == 1:
                # Single tag - use exact match with comma delimiters
                filter_condition = {"tags": {"$eq": f",{tags[0]},"}}
            else:
                # Multiple tags - use $or with exact matches
                tag_conditions = [{"tags": {"$eq": f",{tag},"}} for tag in tags]
                filter_condition = {"$or": tag_conditions}

            # Use empty query with filtering
            results = self.collection.query(
                query_texts=[""],
                n_results=n_results,
                where=filter_condition
            )

            formatted_results = []
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': metadata,
                    'file_name': metadata['file_name'],
                    'tags': metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })

            return formatted_results

        except Exception as e:
            print(f"ChromaDB filtering failed: {e}")
            # Fallback to manual filtering
            return self._manual_tag_filter(tags, n_results)

    def _manual_tag_filter(self, tags: List[str], n_results: int) -> List[Dict]:
        """Fallback manual tag filtering"""
        try:
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
        except Exception as e:
            print(f"Manual tag filtering also failed: {e}")
            return []

    def get_linked_notes(self, note_name: str) -> List[Dict]:
        """Find notes that link to a specific note using metadata filtering."""
        try:
            results = self.collection.query(
                query_texts=[""],  # Empty query to use only the filter
                n_results=20,
                where={"wikilinks": {"$eq": f",{note_name},"}}
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

                chunks = self.chunk_content_improved(note_data['semantic_content'])

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
                    self.add_with_validation(documents, metadatas, ids, small_batch_size=5)
                    print(f"✅ Updated {path.name}")
                else:
                    print(f"⚠️ No content to index in {path.name}")

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


# Example usage with proper error handling
if __name__ == "__main__":
    # Initialize RAG system
    vault_path = "D:\\yo"  # Update this to your actual vault path

    try:
        rag = ObsidianRAG(vault_path)

        # Validate embeddings first
        if not rag.validate_embeddings():
            print("Embedding validation failed. Resetting collection...")
            rag.reset_collection()

        # Index your vault with custom skip folders
        rag.index_vault(skip_folders=['.idea', '.obsidian', '.trash', '06 - Reference', 'Attachments'])

        # Example searches with performance tracking
        print("\n=== TESTING SEMANTIC SEARCH ===")

        # Test queries
        test_queries = [
            "pelea con Ana",
            "encuentro con flor",
            "sesión de terapia",
            "practicar piano",
            "sudáfrica"
        ]

        for query in test_queries:
            print(f"\nSearching for: '{query}'")
            results = rag.search(query, n_results=3)

            if results:
                print(f"Top result: {results[0]['file_name']} (distance: {results[0]['distance']:.4f})")
                print(f"Preview: {results[0]['content'][:100]}...")

        # Print overall performance summary
        rag.print_performance_summary()

    except Exception as e:
        print(f"Error in main execution: {e}")
        print("Make sure to:")
        print("1. Update the vault_path to point to your actual Obsidian vault")
        print("2. Install required dependencies: pip install chromadb sentence-transformers markdown pyyaml numpy")
        print("3. Ensure your vault directory exists and contains .md files")
