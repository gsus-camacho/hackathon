"""Product approval + catalog API."""
from fastapi import APIRouter, HTTPException
from typing import Optional
from modules.approvals import service as svc
from modules.approvals.schemas import ApprovalResolve, CatalogProductCreate
from modules.approvals.errors import ApprovalsError

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/pending")
async def pending(
    identificacion_padre: Optional[str] = None,
    nit_colegio: Optional[str] = None,
    limit: int = 100,
):
    return await svc.list_pending(identificacion_padre, nit_colegio, limit)


@router.post("/{approval_id}/resolve")
async def resolve_approval(approval_id: str, body: ApprovalResolve):
    try:
        return await svc.resolve(approval_id, body.decision)
    except ApprovalsError as e:
        raise HTTPException(404, str(e))


@router.post("/process-expired")
async def process_expired(limit: int = 30):
    processed = await svc.process_expired(limit=limit)
    return {"processed": len(processed), "items": processed}


@router.post("/catalog/products")
async def add_catalog_product(req: CatalogProductCreate):
    return await svc.register_catalog_product(req)


@router.get("/catalog/products")
async def list_catalog(nit_colegio: Optional[str] = None, limit: int = 100):
    from modules.approvals import repository as repo

    return await repo.list_catalog(nit_colegio, limit)
