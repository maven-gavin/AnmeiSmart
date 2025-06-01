import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.core.config import get_settings
from app.core.security import create_access_token
from app.services import user_service
from app.schemas.user import UserCreate
from app.schemas.system import SystemSettingsUpdate, AIModelConfigCreate, AIModelConfigUpdate

settings = get_settings()
SYSTEM_API_ENDPOINT = f"{settings.API_V1_STR}/system"

# Globally defined model names for consistency in tests
MODEL_NAME_CREATE = "test_create_model_001"
MODEL_NAME_OPS = "test_ops_model_001"

# Fixture to create an admin user and return an access token
@pytest_asyncio.fixture
async def admin_token(db: Session, test_admin_data: Dict[str, Any]) -> str:
    """Creates an admin user if not exists and returns an access token."""
    admin_user_email = test_admin_data["email"]
    user = await user_service.get_by_email(db, email=admin_user_email)
    if not user:
        admin_in = UserCreate(**test_admin_data)
        user = await user_service.create(db, obj_in=admin_in)
    return create_access_token(subject=str(user.id))

# Fixture to create a regular user and return an access token
@pytest_asyncio.fixture
async def user_token(db: Session, test_user_data: Dict[str, Any]) -> str:
    """Creates a regular user if not exists and returns an access token."""
    regular_user_email = test_user_data["email"]
    user = await user_service.get_by_email(db, email=regular_user_email)
    if not user:
        user_in = UserCreate(**test_user_data)
        user = await user_service.create(db, obj_in=user_in)
    return create_access_token(subject=str(user.id))

@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}

@pytest_asyncio.fixture
async def user_headers(user_token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {user_token}"}

@pytest.mark.asyncio
async def test_get_system_settings_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str]):
    response = await async_client.get(f"{SYSTEM_API_ENDPOINT}/settings", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["success"] is True
    assert "data" in content
    data = content["data"]
    assert "siteName" in data
    assert "logoUrl" in data
    assert "defaultModelId" in data
    assert "maintenanceMode" in data
    assert "userRegistrationEnabled" in data
    assert "aiModels" in data
    assert isinstance(data["aiModels"], list)
    if data["aiModels"]:
        model = data["aiModels"][0]
        assert "modelName" in model
        assert model["apiKey"] == "••••••••••••••••••••"
        assert "baseUrl" in model
        assert "maxTokens" in model
        assert "temperature" in model
        assert "enabled" in model
        assert "provider" in model # provider and appId should be in GET /settings
        assert "appId" in model

@pytest.mark.asyncio
async def test_get_system_settings_as_user(async_client: AsyncClient, user_headers: Dict[str, str]):
    response = await async_client.get(f"{SYSTEM_API_ENDPOINT}/settings", headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_system_settings_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str], db: Session):
    update_data = SystemSettingsUpdate(
        siteName="New Site Name",
        logoUrl="https://example.com/new_logo.png",
        defaultModelId="new_default_model",
        maintenanceMode=True,
        userRegistrationEnabled=False
    )
    response = await async_client.put(
        f"{SYSTEM_API_ENDPOINT}/settings",
        headers=admin_headers,
        json=update_data.model_dump(exclude_none=True)
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["success"] is True
    data = content["data"]
    assert data["siteName"] == update_data.siteName
    assert data["logoUrl"] == update_data.logoUrl
    assert data["defaultModelId"] == update_data.defaultModelId
    assert data["maintenanceMode"] == update_data.maintenanceMode
    assert data["userRegistrationEnabled"] == update_data.userRegistrationEnabled
    if data["aiModels"]: 
        model = data["aiModels"][0]
        assert "provider" in model
        assert "appId" in model


@pytest.mark.asyncio
async def test_update_system_settings_as_user(async_client: AsyncClient, user_headers: Dict[str, str]):
    update_data = SystemSettingsUpdate(siteName="Attempted Update")
    response = await async_client.put(
        f"{SYSTEM_API_ENDPOINT}/settings",
        headers=user_headers,
        json=update_data.model_dump(exclude_none=True)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_get_ai_models_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str]):
    response = await async_client.get(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["success"] is True
    assert isinstance(content["data"], list)
    if content["data"]:
        model = content["data"][0]
        assert "modelName" in model
        assert model["apiKey"] == "••••••••••••••••••••"
        assert "provider" in model
        assert "appId" in model

@pytest.mark.asyncio
async def test_get_ai_models_as_user(async_client: AsyncClient, user_headers: Dict[str, str]):
    response = await async_client.get(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_create_ai_model_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str], db: Session):
    # 1. Define model_create_data WITH provider and appId
    model_create_data = AIModelConfigCreate(
        modelName=MODEL_NAME_CREATE,
        apiKey="test_api_key_provider_appid", # Unique key for this test run
        baseUrl="https://api.example.com/test_provider_appid",
        maxTokens=2048,
        temperature=0.7,
        enabled=True,
        provider="test_provider_exists", # Ensure this value is used
        appId="test_app_id_exists"      # Ensure this value is used
    )

    # 2. POST request to create the AI model
    response = await async_client.post(
        f"{SYSTEM_API_ENDPOINT}/ai-models",
        headers=admin_headers,
        json=model_create_data.model_dump() # Use model_dump() for Pydantic v2+
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    content = response.json()
    assert content["success"] is True
    data = content["data"] # This is an AIModelConfig schema (without raw APIKey)

    # 3. Assertions for the direct response from POST /ai-models
    # This response (as per api/app/api/v1/endpoints/system.py) returns AIModelConfig
    # which does NOT include provider and appId directly in THIS specific response schema
    # if the service system_service.create_ai_model_config returns AIModelConfig schema
    # and the endpoint wraps it. Let's verify what system_service.create_ai_model_config returns.
    #
    # api/app/services/system_service.py -> create_ai_model_config returns AIModelConfig
    # api/app/schemas/system.py -> AIModelConfig schema DOES include provider and appId.
    #
    # The endpoint POST /ai-models does:
    # created_model_data = system_service.create_ai_model_config(db, model_create) # created_model_data is AIModelConfig
    # return AIModelConfigResponse(success=True, data=created_model_data, message="...")
    # So, `data` in the response IS an AIModelConfig schema, which SHOULD have provider and appId.

    assert data["modelName"] == model_create_data.modelName
    assert data["apiKey"] == "••••••••••••••••••••" # Masked API key
    assert data["baseUrl"] == model_create_data.baseUrl
    assert data["maxTokens"] == model_create_data.maxTokens
    assert data["temperature"] == model_create_data.temperature
    assert data["enabled"] == model_create_data.enabled
    
    # **** KEY CORRECTION based on your feedback and schema review ****
    # The AIModelConfig schema *does* include provider and appId.
    # The service create_ai_model_config returns this schema.
    # The endpoint wraps this schema in AIModelConfigResponse.
    # Therefore, provider and appId SHOULD be in the `data` part of the response.
    assert data["provider"] == model_create_data.provider
    assert data["appId"] == model_create_data.appId

    # 4. Verify it's correctly stored by fetching through GET /system/settings (which also includes provider/appId)
    settings_response = await async_client.get(f"{SYSTEM_API_ENDPOINT}/settings", headers=admin_headers)
    assert settings_response.status_code == status.HTTP_200_OK
    settings_content = settings_response.json()
    assert settings_content["success"] is True
    
    found_in_settings = False
    for model_in_settings in settings_content["data"]["aiModels"]:
        if model_in_settings["modelName"] == MODEL_NAME_CREATE:
            assert model_in_settings["provider"] == model_create_data.provider
            assert model_in_settings["appId"] == model_create_data.appId
            assert model_in_settings["baseUrl"] == model_create_data.baseUrl
            found_in_settings = True
            break
    assert found_in_settings, f"Model {MODEL_NAME_CREATE} not found in GET /system/settings response or provider/appId mismatch"

@pytest.mark.asyncio
async def test_create_ai_model_duplicate_name(async_client: AsyncClient, admin_headers: Dict[str, str], db: Session):
    model_create_data = AIModelConfigCreate(modelName=MODEL_NAME_CREATE, apiKey="key1", baseUrl="url1")
    
    # First creation
    response1 = await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=model_create_data.model_dump())
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Second creation with same name
    model_create_data_dup = AIModelConfigCreate(modelName=MODEL_NAME_CREATE, apiKey="key2", baseUrl="url2")
    response2 = await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=model_create_data_dup.model_dump())
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "已存在" in response2.json()["detail"] # Based on ValueError in system.py

@pytest.mark.asyncio
async def test_create_ai_model_as_user(async_client: AsyncClient, user_headers: Dict[str, str]):
    model_create_data = AIModelConfigCreate(modelName="user_test_model", apiKey="key", baseUrl="url")
    response = await async_client.post(
        f"{SYSTEM_API_ENDPOINT}/ai-models",
        headers=user_headers,
        json=model_create_data.model_dump()
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_ai_model_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str], db: Session):
    # First, create a model to update
    initial_data = AIModelConfigCreate(modelName=MODEL_NAME_OPS, apiKey="initial_key", baseUrl="initial_url", temperature=0.5)
    await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=initial_data.model_dump())

    update_data = AIModelConfigUpdate(baseUrl="updated_url", temperature=0.8, enabled=False)
    response = await async_client.put(
        f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}",
        headers=admin_headers,
        json=update_data.model_dump(exclude_none=True)
    )
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["success"] is True
    data = content["data"]
    assert data["modelName"] == MODEL_NAME_OPS
    assert data["baseUrl"] == update_data.baseUrl
    assert data["temperature"] == update_data.temperature
    assert data["enabled"] == update_data.enabled
    # The update response should include provider and appId fields, just like create and get operations
    assert "provider" in data  # Should be in response
    assert "appId" in data     # Should be in response

@pytest.mark.asyncio
async def test_update_ai_model_not_found(async_client: AsyncClient, admin_headers: Dict[str, str]):
    update_data = AIModelConfigUpdate(baseUrl="updated_url")
    response = await async_client.put(
        f"{SYSTEM_API_ENDPOINT}/ai-models/non_existent_model",
        headers=admin_headers,
        json=update_data.model_dump(exclude_none=True)
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_ai_model_as_user(async_client: AsyncClient, admin_headers: Dict[str, str], user_headers: Dict[str, str], db: Session):
    initial_data = AIModelConfigCreate(modelName=MODEL_NAME_OPS, apiKey="key", baseUrl="url")
    await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=initial_data.model_dump())

    update_data = AIModelConfigUpdate(baseUrl="user_attempt_update")
    response = await async_client.put(
        f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}",
        headers=user_headers,
        json=update_data.model_dump(exclude_none=True)
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_delete_ai_model_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str], db: Session):
    initial_data = AIModelConfigCreate(modelName=MODEL_NAME_OPS, apiKey="key_to_delete", baseUrl="url_to_delete")
    await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=initial_data.model_dump())

    response = await async_client.delete(f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    content = response.json()
    assert content["success"] is True
    assert "删除AI模型配置成功" in content["message"]

    # Verify it's gone
    get_response = await async_client.put(f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}", headers=admin_headers, json={}) # Update a non-existent should 404
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_ai_model_not_found(async_client: AsyncClient, admin_headers: Dict[str, str]):
    response = await async_client.delete(f"{SYSTEM_API_ENDPOINT}/ai-models/non_existent_model_for_delete", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_ai_model_as_user(async_client: AsyncClient, admin_headers: Dict[str, str], user_headers: Dict[str, str], db: Session):
    initial_data = AIModelConfigCreate(modelName=MODEL_NAME_OPS, apiKey="key", baseUrl="url")
    await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=initial_data.model_dump())

    response = await async_client.delete(f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}", headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_toggle_ai_model_status_as_admin(async_client: AsyncClient, admin_headers: Dict[str, str], db: Session):
    initial_data = AIModelConfigCreate(modelName=MODEL_NAME_OPS, apiKey="toggle_key", baseUrl="toggle_url", enabled=True)
    await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=initial_data.model_dump())

    # Toggle to disabled
    response1 = await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}/toggle", headers=admin_headers)
    assert response1.status_code == status.HTTP_200_OK
    content1 = response1.json()
    assert content1["success"] is True
    assert content1["data"]["enabled"] is False
    assert f"AI模型 '{MODEL_NAME_OPS}' 已停用" in content1["message"]

    # Toggle back to enabled
    response2 = await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}/toggle", headers=admin_headers)
    assert response2.status_code == status.HTTP_200_OK
    content2 = response2.json()
    assert content2["success"] is True
    assert content2["data"]["enabled"] is True
    assert f"AI模型 '{MODEL_NAME_OPS}' 已启用" in content2["message"]

@pytest.mark.asyncio
async def test_toggle_ai_model_status_not_found(async_client: AsyncClient, admin_headers: Dict[str, str]):
    response = await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models/non_existent_model_for_toggle/toggle", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_toggle_ai_model_status_as_user(async_client: AsyncClient, admin_headers: Dict[str, str], user_headers: Dict[str, str], db: Session):
    initial_data = AIModelConfigCreate(modelName=MODEL_NAME_OPS, apiKey="key", baseUrl="url")
    await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models", headers=admin_headers, json=initial_data.model_dump())

    response = await async_client.post(f"{SYSTEM_API_ENDPOINT}/ai-models/{MODEL_NAME_OPS}/toggle", headers=user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN 