"""Temporal workflow for classifying Obsidian inbox notes and moving them after human approval."""

import asyncio
import os
import shutil
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from pydantic import BaseModel, Field
from temporalio import activity, workflow
from temporalio.common import RetryPolicy



# ===== ACTIVITIES =====


class InboxClassificationActivities:
    @activity.defn
    async def emit_notification(
        workflow_id: str,
        workflow_type: str,
        notification_type: str,
        title: str,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write a notification to the curation DB (for UI display)."""
        from minerva_backend.containers import Container

        container = Container()
        await container.curation_manager().create_notification(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            notification_type=notification_type,
            title=title,
            message=message,
            payload=payload,
        )

    @activity.defn
    async def scan_inbox(inbox_path: str, vault_path: str) -> List[Dict[str, Any]]:
        """List all markdown files in the inbox folder. Returns list of {source_path, note_title}."""
        root = Path(vault_path).resolve()
        inbox = (root / inbox_path.lstrip("/")).resolve()
        if not inbox.is_dir():
            return []
        if not str(inbox).startswith(str(root)):
            return []
        result = []
        for path in sorted(inbox.rglob("*.md")):
            if not path.is_file():
                continue
            try:
                rel = path.relative_to(root)
                source_path = str(rel).replace("\\", "/")
                title = path.stem
                result.append({"source_path": source_path, "note_title": title})
            except ValueError:
                continue
        return result

    @activity.defn
    async def classify_notes_llm(
        files: List[Dict[str, Any]],
        vault_path: str,
        folder_structure: str,
    ) -> List[Dict[str, Any]]:
        """Use LLM to suggest target folder for each note. Returns list of {uuid, source_path, target_folder, note_title, reason}."""
        from langchain.chat_models import init_chat_model
        from langchain_core.messages import HumanMessage, SystemMessage

        class ClassificationResult(BaseModel):
            target_folder: str = Field(description="Folder path relative to vault, e.g. 03 - Projects/MyProject")
            reason: str = Field(description="Brief reason for this classification")

        model_name = os.getenv("MINERVA_INBOX_CLASSIFY_MODEL", "gemini-2.5-flash-lite")
        model_provider = os.getenv("MINERVA_INBOX_CLASSIFY_PROVIDER", "google-genai")
        try:
            llm = init_chat_model(
                model=model_name,
                model_provider=model_provider,
                temperature=0,
            )
            llm_structured = llm.with_structured_output(ClassificationResult, method="json_schema")
        except Exception as e:
            activity.logger.warning(f"init_chat_model failed: {e}, using default folder")
            return [
                {
                    "uuid": str(uuid4()),
                    "source_path": f["source_path"],
                    "target_folder": "02 - Daily Notes",
                    "note_title": f.get("note_title", ""),
                    "reason": "LLM unavailable; defaulting to Daily Notes",
                }
                for f in files
            ]

        system = """You classify Obsidian notes into the right folder. Given the vault folder structure and the note content (or title), suggest the best target folder. Return only valid folder paths that exist in the structure (or a sensible new subfolder). Use the same path style as the structure (e.g. "03 - Projects/ProjectName")."""
        results = []
        for f in files:
            source_path = f["source_path"]
            note_title = f.get("note_title", Path(source_path).stem)
            # Read first 500 chars of note for context
            full_path = Path(vault_path) / source_path
            content_preview = ""
            if full_path.is_file():
                try:
                    content_preview = full_path.read_text(encoding="utf-8", errors="replace")[:500]
                except OSError:
                    pass
            user_content = f"""Vault folder structure:\n{folder_structure}\n\nNote: {note_title}\nPath: {source_path}\nContent preview:\n{content_preview}\n\nSuggest target_folder and reason."""
            try:
                out = await llm_structured.ainvoke(
                    [SystemMessage(content=system), HumanMessage(content=user_content)]
                )
                results.append({
                    "uuid": str(uuid4()),
                    "source_path": source_path,
                    "target_folder": out.target_folder,
                    "note_title": note_title,
                    "reason": out.reason,
                })
            except Exception as e:
                activity.logger.warning(f"LLM classification failed for {source_path}: {e}")
                results.append({
                    "uuid": str(uuid4()),
                    "source_path": source_path,
                    "target_folder": "02 - Daily Notes",
                    "note_title": note_title,
                    "reason": f"Fallback: {e!s}"[:200],
                })
        return results

    @activity.defn
    async def get_vault_folder_structure(vault_path: str, max_depth: int = 2) -> str:
        """Return a text listing of vault folders (for LLM context)."""
        root = Path(vault_path).resolve()
        lines = []
        for path in sorted(root.rglob("*")):
            if path.is_file():
                continue
            try:
                rel = path.relative_to(root)
                if len(rel.parts) > max_depth:
                    continue
                lines.append(str(rel).replace("\\", "/"))
            except ValueError:
                continue
        return "\n".join(sorted(set(lines))[:200]) if lines else ""

    @activity.defn
    async def submit_classification_curation(
        workflow_id: str, classifications: List[Dict[str, Any]]
    ) -> None:
        """Write classification suggestions to curation DB."""
        from minerva_backend.containers import Container

        container = Container()
        await container.curation_manager().queue_inbox_classification_items(
            workflow_id, classifications
        )

    @activity.defn
    async def wait_for_classification_curation(workflow_id: str) -> List[Dict[str, Any]]:
        """Poll until all items are approved/rejected; return approved moves."""
        from minerva_backend.containers import Container

        container = Container()
        while True:
            pending = await container.curation_manager().get_inbox_classification_pending_count(
                workflow_id
            )
            if pending == 0:
                return await container.curation_manager().get_approved_inbox_classification_items(
                    workflow_id
                )
            activity.heartbeat()
            await asyncio.sleep(30)

    @activity.defn
    async def execute_moves(
        approved_moves: List[Dict[str, Any]], vault_path: str, workflow_id: Optional[str] = None
    ) -> None:
        """Move files from inbox to target folders. Creates target dirs if needed."""
        root = Path(vault_path).resolve()
        for move in approved_moves:
            src = root / move["source_path"]
            target_dir = root / move["target_folder"]
            target_dir.mkdir(parents=True, exist_ok=True)
            dest = target_dir / src.name
            if src.is_file():
                shutil.move(str(src), str(dest))
                activity.logger.info(f"Moved {move['source_path']} -> {move['target_folder']}/{src.name}")
        if workflow_id:
            from minerva_backend.containers import Container
            container = Container()
            await container.curation_manager().create_notification(
                workflow_id=workflow_id,
                workflow_type="inbox_classification",
                notification_type="workflow_completed",
                title="Inbox classification completed",
                message=f"Moved {len(approved_moves)} notes",
                payload={"moved": len(approved_moves)},
            )


# ===== WORKFLOW =====


@workflow.defn(name="InboxClassification")
class InboxClassificationWorkflow:
    """Classify notes in the Obsidian inbox and move them after human approval."""

    @workflow.run
    async def run(self, inbox_path: str) -> Dict[str, Any]:
        from minerva_backend.config import settings

        vault_path = settings.OBSIDIAN_VAULT_PATH
        workflow_id = f"inbox-{int(time.time())}"

        # 1. Scan inbox
        files = await workflow.execute_activity(
            InboxClassificationActivities.scan_inbox,
            args=[inbox_path, vault_path],
            start_to_close_timeout=timedelta(minutes=5),
        )
        if not files:
            return {"workflow_id": workflow_id, "status": "completed", "moved": 0, "message": "No markdown files in inbox"}

        # 2. Get folder structure for LLM context
        folder_structure = await workflow.execute_activity(
            InboxClassificationActivities.get_vault_folder_structure,
            args=[vault_path],
            start_to_close_timeout=timedelta(minutes=2),
        )

        # 3. Classify with LLM
        llm_retry = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_attempts=3,
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
        )
        classifications = await workflow.execute_activity(
            InboxClassificationActivities.classify_notes_llm,
            args=[files, vault_path, folder_structure],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=llm_retry,
        )

        # 4. Submit to curation and wait for human approval
        await workflow.execute_activity(
            InboxClassificationActivities.submit_classification_curation,
            args=[workflow_id, classifications],
            start_to_close_timeout=timedelta(minutes=2),
        )
        approved = await workflow.execute_activity(
            InboxClassificationActivities.wait_for_classification_curation,
            args=[workflow_id],
            schedule_to_close_timeout=timedelta(days=7),
            heartbeat_timeout=timedelta(minutes=2),
        )

        # 5. Execute moves
        if approved:
            await workflow.execute_activity(
                InboxClassificationActivities.execute_moves,
                args=[approved, vault_path, workflow_id],
                start_to_close_timeout=timedelta(minutes=10),
            )

        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "moved": len(approved),
            "total_classified": len(classifications),
        }
