import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import systemService from '@/service/systemService';
import { API_BASE_URL } from '@/config';

// 创建Mock适配器
const mock = new MockAdapter(axios);

// 测试数据
const mockSystemSettings = {
  siteName: '测试系统名称',
  logoUrl: '/test-logo.png',
  aiModels: [
    {
      modelName: 'Test-GPT',
      apiKey: '••••••••••••••••••••',
      baseUrl: 'https://test-api.example.com',
      maxTokens: 1500,
      temperature: 0.8,
      enabled: true
    }
  ],
  defaultModelId: 'Test-GPT',
  maintenanceMode: false,
  userRegistrationEnabled: true
};

const mockAIModels = [
  {
    modelName: 'Test-GPT',
    apiKey: '••••••••••••••••••••',
    baseUrl: 'https://test-api.example.com',
    maxTokens: 1500,
    temperature: 0.8,
    enabled: true
  },
  {
    modelName: 'Test-Claude',
    apiKey: '••••••••••••••••••••',
    baseUrl: 'https://test-claude-api.example.com',
    maxTokens: 2000,
    temperature: 0.5,
    enabled: false
  }
];

describe('系统设置服务测试', () => {
  // 每个测试后清理所有Mock
  afterEach(() => {
    mock.reset();
  });

  // 测试获取系统设置
  test('getSystemSettings 应该正确获取系统设置', async () => {
    // 设置Mock响应
    mock.onGet(`${API_BASE_URL}/system/settings`).reply(200, {
      success: true,
      data: mockSystemSettings,
      message: '获取系统设置成功'
    });

    // 调用服务方法
    const result = await systemService.getSystemSettings();
    
    // 断言返回结果
    expect(result).toEqual(mockSystemSettings);
  });

  // 测试更新系统设置
  test('updateSystemSettings 应该正确更新系统设置', async () => {
    // 更新数据
    const updateData = {
      siteName: '更新的测试系统名称',
    };
    
    const updatedSettings = {
      ...mockSystemSettings,
      ...updateData
    };
    
    // 设置Mock响应
    mock.onPut(`${API_BASE_URL}/system/settings`).reply(200, {
      success: true,
      data: updatedSettings,
      message: '更新系统设置成功'
    });

    // 调用服务方法
    const result = await systemService.updateSystemSettings(updateData);
    
    // 断言返回结果
    expect(result).toEqual(updatedSettings);
  });

  // 测试获取所有AI模型配置
  test('getAIModels 应该正确获取所有AI模型配置', async () => {
    // 设置Mock响应
    mock.onGet(`${API_BASE_URL}/system/ai-models`).reply(200, {
      success: true,
      data: mockAIModels,
      message: '获取AI模型配置成功'
    });

    // 调用服务方法
    const result = await systemService.getAIModels();
    
    // 断言返回结果
    expect(result).toEqual(mockAIModels);
    expect(result.length).toBe(2);
    expect(result[0].modelName).toBe('Test-GPT');
    expect(result[1].modelName).toBe('Test-Claude');
  });

  // 测试创建AI模型配置
  test('createAIModel 应该正确创建AI模型配置', async () => {
    // 新模型数据
    const newModel = {
      modelName: 'New-Model',
      apiKey: 'test-api-key',
      baseUrl: 'https://new-model-api.example.com',
      maxTokens: 3000,
      temperature: 0.6,
      enabled: true
    };
    
    // 设置Mock响应
    mock.onPost(`${API_BASE_URL}/system/ai-models`).reply(201, {
      success: true,
      data: {
        ...newModel,
        apiKey: '••••••••••••••••••••' // API密钥会被掩码
      },
      message: '创建AI模型配置成功'
    });

    // 调用服务方法
    const result = await systemService.createAIModel(newModel);
    
    // 断言返回结果
    expect(result.modelName).toBe('New-Model');
    expect(result.baseUrl).toBe('https://new-model-api.example.com');
    expect(result.apiKey).toBe('••••••••••••••••••••'); // API密钥应该被掩码
  });

  // 测试更新AI模型配置
  test('updateAIModel 应该正确更新AI模型配置', async () => {
    // 更新数据
    const modelName = 'Test-GPT';
    const updateData = {
      baseUrl: 'https://updated-api.example.com',
      maxTokens: 2500
    };
    
    const updatedModel = {
      ...mockAIModels[0],
      ...updateData
    };
    
    // 设置Mock响应
    mock.onPut(`${API_BASE_URL}/system/ai-models/${modelName}`).reply(200, {
      success: true,
      data: updatedModel,
      message: '更新AI模型配置成功'
    });

    // 调用服务方法
    const result = await systemService.updateAIModel(modelName, updateData);
    
    // 断言返回结果
    expect(result.modelName).toBe('Test-GPT');
    expect(result.baseUrl).toBe('https://updated-api.example.com');
    expect(result.maxTokens).toBe(2500);
  });

  // 测试删除AI模型配置
  test('deleteAIModel 应该正确删除AI模型配置', async () => {
    // 设置Mock响应
    mock.onDelete(`${API_BASE_URL}/system/ai-models/Test-GPT`).reply(200, {
      success: true,
      message: '删除AI模型配置成功'
    });

    // 调用服务方法并断言不会抛出错误
    await expect(systemService.deleteAIModel('Test-GPT')).resolves.not.toThrow();
  });

  // 测试切换AI模型状态
  test('toggleAIModelStatus 应该正确切换AI模型状态', async () => {
    const modelName = 'Test-GPT';
    const toggledModel = {
      ...mockAIModels[0],
      enabled: false // 从true切换到false
    };
    
    // 设置Mock响应
    mock.onPost(`${API_BASE_URL}/system/ai-models/${modelName}/toggle`).reply(200, {
      success: true,
      data: toggledModel,
      message: `AI模型 '${modelName}' 已停用`
    });

    // 调用服务方法
    const result = await systemService.toggleAIModelStatus(modelName);
    
    // 断言返回结果
    expect(result.modelName).toBe('Test-GPT');
    expect(result.enabled).toBe(false);
  });

  // 测试错误处理
  test('服务方法应该正确处理错误', async () => {
    // 设置Mock错误响应
    mock.onGet(`${API_BASE_URL}/system/settings`).reply(500, {
      success: false,
      message: '服务器错误'
    });

    // 断言方法会抛出错误
    await expect(systemService.getSystemSettings()).rejects.toThrow();
  });
}); 