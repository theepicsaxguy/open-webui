import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from open_webui.utils.git_ingest import ingest
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
    max_depth: int | None = 20
    ingest_file_content: bool | None = True


@router.post("/ingest")
async def ingest_endpoint(req: IngestRequest, user=Depends(get_verified_user)):
    result = ingest(
        source=req.source,
        branch=req.branch,
        commit=req.commit,
        subpath=req.subpath,
        max_depth=req.max_depth or 20,
        ingest_file_content=True if req.ingest_file_content is None else req.ingest_file_content,
    )
    return result
