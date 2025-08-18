"""OAuth2服务模块，处理MCP客户端认证"""
import secrets
import time
from typing import Dict, Any, Optional
from urllib.parse import urlencode, urljoin
from fastapi import HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.core.config import get_settings
from app.mcp.utils import base64url_sha256, generate_token, is_token_expired
from app.mcp.types import OAuthMetadata, OAuthResourceMetadata, OAuthClientMetadata, OAuthClientInformationFull, OAuthTokens

settings = get_settings()

class OAuth2Manager:
    """OAuth2管理器，处理客户端注册、授权和令牌管理"""
    
    def __init__(self):
        self.registered_clients: Dict[str, OAuthClientInformationFull] = {}
        self.auth_codes: Dict[str, Dict[str, Any]] = {}
        self.access_tokens: Dict[str, Dict[str, Any]] = {}
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
    def get_oauth_metadata(self) -> OAuthMetadata:
        """获取OAuth发现元数据"""
        base_url = settings.MCP_SERVER_BASE_URL
        return OAuthMetadata(
            # RFC 8414 必需字段
            issuer=base_url,
            authorization_endpoint=f"{base_url}/api/v1/oauth/authorize",
            token_endpoint=f"{base_url}/api/v1/oauth/token",
            jwks_uri=None,  # 我们不使用JWT，所以不需要JWKS
            response_types_supported=["code"],
            subject_types_supported=["public"],  # 我们使用public subject type
            id_token_signing_alg_values_supported=None,  # 不使用ID token
            
            # RFC 8414 可选字段
            registration_endpoint=f"{base_url}/api/v1/oauth/register",
            grant_types_supported=["authorization_code", "refresh_token"],
            code_challenge_methods_supported=["S256"],
            scopes_supported=None, 
            token_endpoint_auth_methods_supported=["none"],  # 使用PKCE，不需要客户端认证
            claims_supported=None
        )
    
    def get_oauth_resource_metadata(self) -> OAuthResourceMetadata:
        """获取OAuth资源服务器元数据"""
        base_url = settings.MCP_SERVER_BASE_URL
        return OAuthResourceMetadata(
            resource=f"{base_url}/api/v1/mcp/server/default/mcp",
            authorization_servers=[base_url],
            scopes_supported=["mcp:read", "mcp:write"],
            bearer_methods_supported=["header"],
            resource_documentation=f"{base_url}/api/v1/docs",
        )
    
    def register_client(self, client_metadata: OAuthClientMetadata) -> OAuthClientInformationFull:
        """注册新的OAuth客户端"""
        client_id = generate_token("client", 16)
        
        client_info = OAuthClientInformationFull(
            client_id=client_id,
            client_secret="",  # MCP使用PKCE，不需要客户端密钥
            client_name=client_metadata.client_name,
            redirect_uris=client_metadata.redirect_uris,
            grant_types=client_metadata.grant_types or ["authorization_code", "refresh_token"],
            response_types=client_metadata.response_types or ["code"],
            token_endpoint_auth_method=client_metadata.token_endpoint_auth_method or "none",
            scope=client_metadata.scope
        )
        
        self.registered_clients[client_id] = client_info
        return client_info
    
    def get_authorization_page(
        self,
        response_type: str,
        client_id: str,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        code_challenge_method: str = "S256"
    ) -> HTMLResponse:
        """显示授权页面"""
        # 验证参数
        if response_type != "code":
            raise HTTPException(
                status_code=400,
                detail={"error": "unsupported_response_type", "error_description": "Only 'code' response type is supported"}
            )
        
        if client_id not in self.registered_clients:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_client", "error_description": "Unknown client ID"}
            )
        
        if code_challenge_method != "S256":
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_request", "error_description": "Only 'S256' code challenge method is supported"}
            )
        
        # 渲染授权页面
        html_content = f"""
<!doctype html>
<html>
  <head>
    <title>授权MCP服务器</title>
    <meta charset="utf-8">
    <style>
      body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui; padding: 48px; max-width: 500px; margin: 0 auto; }}
      .form-group {{ margin-bottom: 24px; }}
      label {{ display: block; margin-bottom: 8px; font-weight: 500; }}
      input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }}
      button {{ background: #007AFF; color: white; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }}
      button:hover {{ background: #0051D0; }}
      .client-info {{ background: #f8f9fa; padding: 16px; border-radius: 6px; margin-bottom: 24px; }}
    </style>
  </head>
  <body>
    <h2>授权MCP服务器访问</h2>
    <div class="client-info">
      <strong>应用名称:</strong> {self.registered_clients[client_id].client_name or "未知应用"}<br>
      <strong>客户端ID:</strong> {client_id}
    </div>
    
    <form method="post" action="/api/v1/oauth/authorize">
      <div class="form-group">
        <label for="api_key">API密钥:</label>
        <input name="api_key" type="password" id="api_key" required placeholder="请输入您的API密钥" />
      </div>
      <input type="hidden" name="client_id" value="{client_id}" />
      <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
      <input type="hidden" name="state" value="{state}" />
      <input type="hidden" name="code_challenge" value="{code_challenge}" />
      <button type="submit">授权访问</button>
    </form>
  </body>
</html>
"""
        return HTMLResponse(content=html_content)
    
    def process_authorization(
        self,
        api_key: str,
        client_id: str,
        redirect_uri: str,
        state: str,
        code_challenge: str
    ) -> RedirectResponse:
        """处理授权提交"""
        if client_id not in self.registered_clients:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_client", "error_description": "Unknown client ID"}
            )
        
        # 生成授权码
        code = generate_token("code", 16)
        
        # 处理重定向URI
        client = self.registered_clients[client_id]
        abs_redirect = redirect_uri
        
        if redirect_uri.startswith("/"):
            base = (client.client_uri or "").rstrip("/") + "/"
            if not base.strip("/"):
                raise HTTPException(
                    status_code=400,
                    detail={"error": "invalid_request", "error_description": "redirect_uri must be absolute or client_uri must be provided"}
                )
            abs_redirect = urljoin(base, redirect_uri.lstrip("/"))
        
        # 存储授权码信息
        self.auth_codes[code] = {
            "api_key": api_key,
            "client_id": client_id,
            "redirect_uri": abs_redirect,
            "code_challenge": code_challenge,
            "created_at": int(time.time()),
        }
        
        # 重定向回客户端
        params = {"code": code, "state": state}
        return RedirectResponse(url=f"{abs_redirect}?{urlencode(params)}", status_code=302)
    
    def exchange_token(self, request_data: Dict[str, Any]) -> OAuthTokens:
        """交换令牌"""
        grant_type = request_data.get("grant_type")
        client_id = request_data.get("client_id")
        
        if client_id not in self.registered_clients:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_client", "error_description": "Unknown client ID"}
            )
        
        if grant_type == "authorization_code":
            return self._handle_authorization_code_grant(request_data)
        elif grant_type == "refresh_token":
            return self._handle_refresh_token_grant(request_data)
        else:
            raise HTTPException(
                status_code=400,
                detail={"error": "unsupported_grant_type", "error_description": "Unsupported grant type"}
            )
    
    def _handle_authorization_code_grant(self, request_data: Dict[str, Any]) -> OAuthTokens:
        """处理授权码授权"""
        code = request_data.get("code")
        code_verifier = request_data.get("code_verifier")
        redirect_uri = request_data.get("redirect_uri")
        client_id = request_data.get("client_id")
        
        if code not in self.auth_codes:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_grant", "error_description": "Invalid or expired authorization code"}
            )
        
        auth_data = self.auth_codes.pop(code)
        
        # 验证客户端和重定向URI
        if auth_data["client_id"] != client_id or auth_data["redirect_uri"] != redirect_uri:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_grant", "error_description": "Invalid client or redirect URI"}
            )
        
        # PKCE验证
        if not code_verifier or base64url_sha256(code_verifier) != auth_data["code_challenge"]:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_grant", "error_description": "Invalid code verifier"}
            )
        
        # 生成令牌
        api_key = auth_data["api_key"]
        access_token = generate_token("atk", 24)
        refresh_token = generate_token("rt", 24)
        
        # 存储令牌
        self.access_tokens[access_token] = {"api_key": api_key, "created_at": int(time.time())}
        self.refresh_tokens[refresh_token] = {"api_key": api_key, "created_at": int(time.time())}
        
        return OAuthTokens(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_token
        )
    
    def _handle_refresh_token_grant(self, request_data: Dict[str, Any]) -> OAuthTokens:
        """处理刷新令牌授权"""
        refresh_token = request_data.get("refresh_token")
        
        if not refresh_token or refresh_token not in self.refresh_tokens:
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_grant", "error_description": "Invalid refresh token"}
            )
        
        # 生成新的访问令牌
        api_key = self.refresh_tokens[refresh_token]["api_key"]
        access_token = generate_token("atk", 24)
        self.access_tokens[access_token] = {"api_key": api_key, "created_at": int(time.time())}
        
        return OAuthTokens(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,
            refresh_token=refresh_token
        )
    
    def get_api_key_by_token(self, token: str) -> Optional[str]:
        """验证Bearer令牌并返回API密钥"""
        if not token or token not in self.access_tokens:
            return None
        
        token_data = self.access_tokens[token]
        
        # 检查令牌是否过期
        if is_token_expired(token_data["created_at"], 3600):
            self.access_tokens.pop(token, None)
            return None
        
        return token_data["api_key"]


# 全局OAuth2管理器实例
oauth2_manager = OAuth2Manager()
