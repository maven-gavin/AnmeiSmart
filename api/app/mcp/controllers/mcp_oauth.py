"""MCP Server端点实现"""
import logging
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.mcp.oauth import oauth2_manager
from app.mcp import types

logger = logging.getLogger(__name__)
router = APIRouter()


# ===== Dynamic Client Registration =====
@router.post("/register")
async def register_client(request: Request):
    """动态客户端注册"""
    try:
        body = await request.json()
        client_metadata = types.OAuthClientMetadata.model_validate(body)
        client_info = oauth2_manager.register_client(client_metadata)
        
        return JSONResponse(content=client_info.model_dump(by_alias=True, exclude_none=True))
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_request", "error_description": f"Invalid client metadata: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"客户端注册失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": "Internal server error"}
        )


# ===== Authorization Page (API Key input) =====
@router.get("/authorize")
async def authorize_page(
    response_type: str,
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str = "S256",
):
    """显示授权页面"""
    try:
        return oauth2_manager.get_authorization_page(
            response_type=response_type,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"显示授权页面失败: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/authorize")
async def authorize_submit(
    api_key: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(...),
    code_challenge: str = Form(...),
):
    """处理授权提交"""
    try:
        return oauth2_manager.process_authorization(
            api_key=api_key,
            client_id=client_id,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理授权提交失败: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ===== Token Exchange =====
@router.post("/token")
async def token_exchange(request: Request):
    """令牌交换端点"""
    try:
        form = await request.form()
        request_data = dict(form)
        tokens = oauth2_manager.exchange_token(request_data)
        
        return JSONResponse(content=tokens.model_dump(by_alias=True, exclude_none=True))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌交换失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": "Internal server error"}
        )


# ===== OAuth Metadata Discovery =====
async def oauth_metadata():
    """OAuth授权服务器元数据发现端点 (RFC 8414)"""
    try:
        metadata = oauth2_manager.get_oauth_metadata()
        return JSONResponse(content=metadata.model_dump(by_alias=True, exclude_none=True))
    except Exception as e:
        logger.error(f"获取OAuth元数据失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "error_description": "Internal server error"}
        )


async def oauth_metadata_options():
    """OAuth元数据发现端点的OPTIONS方法支持"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )
