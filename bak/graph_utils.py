from graphiti_core.graphiti_types import GraphitiClients
from graphiti_core.nodes import EntityNode
from graphiti_core.prompts.summarize_nodes import Summary
from graphiti_core.utils.maintenance.community_operations import summarize_pair

from .prompts.graph_prompts import merge_summaries


async def dedupe_nodes(
        clients: GraphitiClients
) -> None:
    llm_client = clients.llm_client
    driver = clients.driver

    # Grab all duplicate nodes
    records, _, _ = await driver.execute_query("""MATCH (n:Entity)
WITH n.name AS name, collect(n) AS nodes
WHERE size(nodes) > 1
RETURN 
  nodes[0].uuid AS primary,
  nodes[0].name AS name,
  nodes[0].summary AS summary,
  [x IN nodes[1..] | {uuid: x.uuid, name: x.name, summary: x.summary}] AS duplicates""")

    for primary in records:
        primary_uuid = primary['primary']
        primary_name = primary['name']
        primary_summary = primary['summary']
        for dupe in primary['duplicates']:
            print(f"Detected duplicate: {primary_name}({primary_uuid}) - {dupe['name']}({dupe['uuid']})")
            summary = await summarize_pair(llm_client, (primary_summary, dupe['summary']))
            print(f"Primary summary: {primary_summary}")
            print(f"Duplicate summary: {dupe['summary']}")
            print(f"Merged Summary: {summary}")

            # Merge nodes
            print("Merging Nodes.")
            result = await clients.driver.execute_query("""
MATCH (primary {uuid: $primary})
MATCH (dup {uuid: $duplicate})
CALL apoc.refactor.mergeNodes([primary, dup], {properties:"discard", mergeRels:true})
YIELD node
SET node.summary = $new_summary
RETURN node.uuid AS kept, node.name AS name
""", primary=primary_uuid, duplicate=dupe['uuid'], new_summary=summary)
