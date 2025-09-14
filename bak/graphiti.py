"""
Copyright 2025, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime, timezone
from logging import DEBUG

from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.cross_encoder import OpenAIRerankerClient
from graphiti_core.llm_client import LLMConfig, OpenAIClient
from graphiti_core.llm_client.ollama_client import MinervaClient, MinervaEmbeddingClient
from backend.minerva.config import load_config
from backend.minerva.enriquecer_diario import construir_glosario, extraer_enlaces
from backend.minerva.graph.episodes.diario import DIARIO3DIAS
from backend.minerva.graph.models import entity_types
from backend.minerva.vault_utils import actualizar_entradas

#################################################
# CONFIGURATION
#################################################
# Set up logging and environment variables for
# connecting to Neo4j database
#################################################

# Configure logging
logging.basicConfig(
    level=DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]  # Output to console
)
logger = logging.getLogger(__name__)

logging.getLogger('graphiti_core').setLevel(logging.DEBUG)
logging.getLogger('AlexLogs').setLevel(logging.DEBUG)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Database configuration
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Alxe342!")

# LLM Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "http://127.0.0.1:1234/v1")


async def initialize_graphiti():
    """Initialize Graphiti with proper configuration."""
    # Configure LLM client with more conservative settings
    llm_config = LLMConfig(
        api_key="ollama",  # Ollama doesn't require a real API key
        # model="qwen2.5:14b",
        # small_model="qwen2.5:14b",
        model="qwen3:14b-q4_K_M",
        small_model="qwen3:4b-q4_K_M",
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,  # Small temperature for more consistent results
        max_tokens=4096,  # Reasonable token limit
    )

    # Create LLM clients
    # llm_client = OpenAIGenericClient(config=llm_config)
    llm_client = MinervaClient(config=llm_config, cache=True)

    # Initialize Graphiti
    graphiti = Graphiti(
        NEO4J_URL,
        NEO4J_USERNAME,
        NEO4J_PASSWORD,
        llm_client=llm_client,
        embedder=MinervaEmbeddingClient(),
        cross_encoder=OpenAIRerankerClient(client=OpenAIClient(config=llm_config), config=llm_config),
        store_raw_episode_content=False,
        ensure_ascii=True
    )

    return graphiti


async def add_episodes_safely(graphiti, episodes):
    """Add episodes with proper error handling and delays."""
    successful_episodes = []
    failed_episodes = []

    for i, episode in enumerate(episodes):
        try:
            print(f"Adding episode {i + 1}/{len(episodes)}: {episode['description']}")

            # Prepare episode content
            episode_content = (
                episode['content']
                if isinstance(episode['content'], str)
                else json.dumps(episode['content'], indent=2)
            )

            episode_date = datetime.strptime(episode['date'], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            load_config()
            glosario = construir_glosario(extraer_enlaces(episode_content))

            # Add episode
            result = await graphiti.add_diary_entry(
                name=episode['description'],
                episode_body=episode_content,
                reference_time=episode_date,
                glossary=glosario,
                entity_types=entity_types,
                edge_types=None,
                edge_type_map=None
            )
            successful_episodes.append(i + 1)
            print(f'✓ Successfully added episode: {episode['description']} ({episode["type"].value})')

            print(f'Updating {len(result.nodes)} obsidian summaries.')
            actualizar_entradas(result.nodes)
            #    result
            # episode: EpisodicNode
            # episodic_edges: list[EpisodicEdge]
            # nodes: list[EntityNode]
            # edges: list[EntityEdge]
            # communities: list[CommunityNode]
            # community_edges: list[CommunityEdge]

            # Add delay between episodes to prevent overwhelming the system
            if i < len(episodes) - 1:  # Don't sleep after the last episode
                await asyncio.sleep(10)
        except Exception as e:
            print(f'✗ Error adding episode {i + 1}: {str(e)}')
            print("Full traceback:")
            traceback.print_exc()
            failed_episodes.append(i + 1)

            # If we get multiple failures, something might be seriously wrong
            # if len(failed_episodes) >= 2:
            #    print("Multiple episodes failed. Stopping to prevent further issues.")
            #    break

    print(f"\nEpisode Summary:")
    print(f"  Successful: {len(successful_episodes)} episodes")
    print(f"  Failed: {len(failed_episodes)} episodes")

    return successful_episodes, failed_episodes


async def main():
    """Main function with comprehensive error handling."""
    graphiti = None

    try:
        print("=" * 50)
        print("INITIALIZING GRAPHITI")
        print("=" * 50)

        # Initialize Graphiti
        graphiti = await initialize_graphiti()
        print("✓ Graphiti client created successfully.")

        # Initialize database schema
        print("\nInitializing database schema...")
        await graphiti.build_indices_and_constraints()
        print("✓ Database schema initialized.")

        # Add episodes safely
        print("\n" + "=" * 50)
        print("ADDING EPISODES")
        print("=" * 50)

        episodes = DIARIO3DIAS
        successful, failed = await add_episodes_safely(graphiti, episodes)

        # dedupe
        # await dedupe_nodes(graphiti.clients)

        # await find_entity(graphiti, "Alex Elgier")
        # await find_entity(graphiti, "Ana Sorin")
        print("Done")

    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        print(f"Unexpected error in main: {str(e)}")
        logger.exception("Main function error details:")
    finally:
        # Always close the connection
        if graphiti:
            try:
                await graphiti.close()
                print('\n✓ Connection closed successfully.')
            except Exception as e:
                print(f'Warning: Error closing connection: {e}')


if __name__ == '__main__':
    # Set up proper event loop handling for Windows


    if os.name == 'nt':  # Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.exception("Fatal error details:")
