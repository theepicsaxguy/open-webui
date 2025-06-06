import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.constants import ERROR_MESSAGES

from open_webui.utils.git_ingest import ingest, collect_files
from open_webui.models.files import FileForm, Files
from open_webui.models.knowledge import KnowledgeForm, Knowledges
from open_webui.routers.retrieval import ProcessFileForm, process_file
from open_webui.utils.auth import get_verified_user
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()


class IngestRequest(BaseModel):
    source: str
    branch: str | None = None
    commit: str | None = None
    subpath: str | None = None
    ingest_file_content: bool | None = True


class IngestToKnowledgeRequest(IngestRequest):
    knowledge_id: str | None = None
    knowledge_name: str | None = None
    description: str | None = ""


@router.post("/ingest")
async def ingest_endpoint(req: IngestRequest, user=Depends(get_verified_user)):
    result = await ingest(
        source=req.source,
        branch=req.branch,
        commit=req.commit,
        subpath=req.subpath,
        ingest_file_content=True if req.ingest_file_content is None else req.ingest_file_content,
    )
    return result


@router.post("/knowledge")
async def ingest_to_knowledge(
    request: Request,
    req: IngestToKnowledgeRequest,
    user=Depends(get_verified_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )

    knowledge = None
    if req.knowledge_id:
        knowledge = Knowledges.get_knowledge_by_id(id=req.knowledge_id)
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )
    else:
        if not req.knowledge_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("knowledge_name"),
            )
        knowledge = Knowledges.insert_new_knowledge(
            user.id,
            KnowledgeForm(
                name=req.knowledge_name,
                description=req.description or "",
                data={"file_ids": []},
            ),
        )
        if not knowledge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("knowledge"),
            )

    result = await ingest(
        source=req.source,
        branch=req.branch,
        commit=req.commit,
        subpath=req.subpath,
        ingest_file_content=True,
    )
    root_node = result.pop("_node")
    file_nodes = collect_files(root_node)

    file_ids: list[str] = []
    for node in file_nodes:
        if node.content is None:
            continue
        file_item = Files.insert_new_file(
            user.id,
            FileForm(
                id=str(uuid.uuid4()),
                filename=node.name,
                path=node.path_str,
                data={"content": node.content},
                meta={"name": node.name, "content_type": "text/plain", "size": node.size},
            ),
        )
        if not file_item:
            continue
        try:
            process_file(
                request,
                ProcessFileForm(file_id=file_item.id, collection_name=knowledge.id),
                user=user,
            )
            file_ids.append(file_item.id)
        except Exception as e:
            log.error("Error processing file %s: %s", node.full_path, e)

    data = knowledge.data or {}
    existing = data.get("file_ids", [])
    existing.extend(file_ids)
    data["file_ids"] = existing
    knowledge = Knowledges.update_knowledge_data_by_id(id=knowledge.id, data=data)

    return {
        "knowledge_id": knowledge.id,
        "files_added": len(file_ids),
        "summary": result["Summary"],
    }

