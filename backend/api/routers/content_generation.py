"""内容生成 API 路由"""
from fastapi import APIRouter, Query

from api.dependencies import DBDep, TenantFlexDep
from schemas.base import ApiResponse, PaginatedResponse
from schemas.generation import (
    GenerateRequest, GeneratedAssetResponse,
    GenerationTaskResponse, UploadAssetRequest,
)
from schemas.product_prompt import (
    ProductPromptCreate, ProductPromptResponse, ProductPromptUpdate,
)
from services.content_generation.generation_service import GenerationService
from services.content_generation.product_prompt_service import ProductPromptService
from services.content_generation.asset_upload_service import AssetUploadService
from tasks.generation_tasks import run_generation

router = APIRouter(prefix="/content", tags=["内容生成"])


# ===== 商品提示词 =====

@router.get("/prompts", response_model=ApiResponse[PaginatedResponse[ProductPromptResponse]])
async def list_prompts(
    tenant_id: TenantFlexDep,
    db: DBDep,
    product_id: int | None = None,
    prompt_type: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询商品提示词列表"""
    service = ProductPromptService(db, tenant_id)
    prompts, total = await service.list_prompts(
        product_id=product_id, prompt_type=prompt_type, page=page, size=size
    )
    paginated = PaginatedResponse.create(
        items=prompts, total=total, page=page, size=size
    )
    return ApiResponse(data=paginated)


@router.post("/prompts", response_model=ApiResponse[ProductPromptResponse])
async def create_prompt(
    request: ProductPromptCreate,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """创建商品提示词"""
    service = ProductPromptService(db, tenant_id)
    prompt = await service.create_prompt(
        product_id=request.product_id,
        prompt_type=request.prompt_type,
        name=request.name,
        content=request.content,
    )
    return ApiResponse(data=prompt)


@router.put("/prompts/{prompt_id}", response_model=ApiResponse[ProductPromptResponse])
async def update_prompt(
    prompt_id: int,
    request: ProductPromptUpdate,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """更新商品提示词"""
    service = ProductPromptService(db, tenant_id)
    prompt = await service.update_prompt(
        prompt_id=prompt_id,
        name=request.name,
        content=request.content,
    )
    if not prompt:
        return ApiResponse(success=False, error={"code": "NOT_FOUND", "message": "提示词不存在"})
    return ApiResponse(data=prompt)


@router.delete("/prompts/{prompt_id}", response_model=ApiResponse)
async def delete_prompt(
    prompt_id: int,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """删除商品提示词"""
    service = ProductPromptService(db, tenant_id)
    deleted = await service.delete_prompt(prompt_id)
    if not deleted:
        return ApiResponse(success=False, error={"code": "NOT_FOUND", "message": "提示词不存在"})
    return ApiResponse(data=None)


# ===== 生成任务 =====

@router.post("/generate", response_model=ApiResponse[GenerationTaskResponse])
async def create_generation(
    request: GenerateRequest,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """创建内容生成任务"""
    service = GenerationService(db, tenant_id)
    task = await service.create_task(
        task_type=request.task_type,
        prompt=request.prompt,
        product_id=request.product_id,
        prompt_id=request.prompt_id,
        model_config_id=request.model_config_id,
        params=request.params,
    )
    # 异步执行
    run_generation.delay(task.id, tenant_id)
    return ApiResponse(data=task)


@router.get("/tasks", response_model=ApiResponse[PaginatedResponse[GenerationTaskResponse]])
async def list_generation_tasks(
    tenant_id: TenantFlexDep,
    db: DBDep,
    task_type: str | None = None,
    product_id: int | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询生成任务列表"""
    service = GenerationService(db, tenant_id)
    tasks, total = await service.list_tasks(
        task_type=task_type, product_id=product_id,
        status=status, page=page, size=size,
    )
    paginated = PaginatedResponse.create(
        items=tasks, total=total, page=page, size=size
    )
    return ApiResponse(data=paginated)


@router.get("/tasks/{task_id}", response_model=ApiResponse[GenerationTaskResponse])
async def get_generation_task(
    task_id: int,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """获取生成任务详情"""
    service = GenerationService(db, tenant_id)
    task = await service.get_task(task_id)
    if not task:
        return ApiResponse(success=False, error={"code": "NOT_FOUND", "message": "任务不存在"})
    return ApiResponse(data=task)


@router.post("/tasks/{task_id}/retry", response_model=ApiResponse[GenerationTaskResponse])
async def retry_generation_task(
    task_id: int,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """重试失败的生成任务"""
    service = GenerationService(db, tenant_id)
    task = await service.retry_task(task_id)
    if not task:
        return ApiResponse(success=False, error={"code": "INVALID_STATE", "message": "任务不存在或状态不允许重试"})
    # 异步执行
    run_generation.delay(task.id, tenant_id)
    return ApiResponse(data=task)


# ===== 素材 =====

@router.get("/assets", response_model=ApiResponse[PaginatedResponse[GeneratedAssetResponse]])
async def list_assets(
    tenant_id: TenantFlexDep,
    db: DBDep,
    task_id: int | None = None,
    product_id: int | None = None,
    asset_type: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询素材列表"""
    service = GenerationService(db, tenant_id)
    assets, total = await service.list_assets(
        task_id=task_id, product_id=product_id,
        asset_type=asset_type, page=page, size=size,
    )
    paginated = PaginatedResponse.create(
        items=assets, total=total, page=page, size=size
    )
    return ApiResponse(data=paginated)


@router.post("/assets/upload", response_model=ApiResponse[dict])
async def upload_asset_to_platform(
    request: UploadAssetRequest,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """上传素材到电商平台"""
    service = AssetUploadService(db, tenant_id)
    try:
        platform_url = await service.upload_to_platform(
            asset_id=request.asset_id,
            platform_config_id=request.platform_config_id,
        )
        return ApiResponse(data={"platform_url": platform_url})
    except ValueError as e:
        return ApiResponse(success=False, error={"code": "UPLOAD_ERROR", "message": str(e)})
