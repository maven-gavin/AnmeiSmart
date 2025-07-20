import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SystemSettingsPage from '@/app/settings/page';
import systemService from '@/service/systemService';

// 模拟systemService
jest.mock('@/service/systemService', () => ({
  getSystemSettings: jest.fn(),
  updateSystemSettings: jest.fn(),
  createAIModel: jest.fn(),
  deleteAIModel: jest.fn(),
  toggleAIModelStatus: jest.fn(),
}));

// 模拟toast通知
jest.mock('react-hot-toast', () => ({
  success: jest.fn(),
  error: jest.fn(),
}));

// 测试数据
const mockSettings = {
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

describe('系统设置页面测试', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // 模拟API调用返回
    (systemService.getSystemSettings as jest.Mock).mockResolvedValue(mockSettings);
    (systemService.updateSystemSettings as jest.Mock).mockResolvedValue(mockSettings);
    (systemService.createAIModel as jest.Mock).mockResolvedValue(mockSettings.aiModels[0]);
    (systemService.deleteAIModel as jest.Mock).mockResolvedValue(undefined);
    (systemService.toggleAIModelStatus as jest.Mock).mockResolvedValue({
      ...mockSettings.aiModels[0],
      enabled: false
    });
  });

  test('应该加载并显示系统设置', async () => {
    render(<SystemSettingsPage />);
    
    // 验证加载状态
    expect(screen.getByText('加载系统设置...')).toBeInTheDocument();
    
    // 等待数据加载完成
    await waitFor(() => {
      expect(systemService.getSystemSettings).toHaveBeenCalled();
    });
    
    // 验证系统名称显示正确
    await waitFor(() => {
      expect(screen.getByDisplayValue('测试系统名称')).toBeInTheDocument();
    });
  });

  test('应该能切换标签页', async () => {
    render(<SystemSettingsPage />);
    
    // 等待数据加载完成并确保基本设置标签已显示
    await waitFor(() => {
      expect(screen.getByText('基本系统设置')).toBeInTheDocument();
    });
    
    // 使用按钮文本和类型来选择AI模型配置标签按钮
    const aiModelTabButton = screen.getByRole('button', { name: /AI模型配置/i });
    fireEvent.click(aiModelTabButton);
    
    // 验证AI模型配置标签页显示
    await waitFor(() => {
      expect(screen.getByText('已配置模型')).toBeInTheDocument();
      expect(screen.getByText('添加新模型')).toBeInTheDocument();
    });
    
    // 使用按钮文本和类型来选择安全与访问控制标签按钮
    const securityTabButton = screen.getByRole('button', { name: /安全与访问控制/i });
    fireEvent.click(securityTabButton);
    
    // 验证安全与访问控制标签页显示
    await waitFor(() => {
      expect(screen.getByText('安全与访问控制设置')).toBeInTheDocument();
    });
  });

  test('应该能更新系统设置', async () => {
    render(<SystemSettingsPage />);
    
    // 等待数据加载完成
    await waitFor(() => {
      expect(systemService.getSystemSettings).toHaveBeenCalled();
    });
    
    // 验证系统名称输入框已加载
    await waitFor(() => {
      expect(screen.getByDisplayValue('测试系统名称')).toBeInTheDocument();
    });
    
    // 修改系统名称
    const siteNameInput = screen.getByDisplayValue('测试系统名称');
    fireEvent.change(siteNameInput, { target: { value: '新系统名称' } });
    
    // 提交表单
    fireEvent.click(screen.getByText('保存设置'));
    
    // 验证更新API被调用
    await waitFor(() => {
      expect(systemService.updateSystemSettings).toHaveBeenCalled();
      expect(systemService.updateSystemSettings).toHaveBeenCalledWith(
        expect.objectContaining({
          siteName: '新系统名称'
        })
      );
    });
  });

  test('应该显示已配置的AI模型', async () => {
    render(<SystemSettingsPage />);
    
    // 等待数据加载完成
    await waitFor(() => {
      expect(screen.getByText('基本系统设置')).toBeInTheDocument();
    });
    
    // 切换到AI模型配置标签
    const aiModelTabButton = screen.getByRole('button', { name: /AI模型配置/i });
    fireEvent.click(aiModelTabButton);
    
    // 验证模型信息显示，使用更具体的选择器
    await waitFor(() => {
      // 使用父元素来定位特定的Test-GPT
      const modelHeader = screen.getAllByText('Test-GPT')[0]; // 获取第一个匹配项
      expect(modelHeader).toBeInTheDocument();
      expect(screen.getByText('https://test-api.example.com')).toBeInTheDocument();
      expect(screen.getByText('1500')).toBeInTheDocument();
    });
  });

  test('应该能切换AI模型状态', async () => {
    render(<SystemSettingsPage />);
    
    // 等待数据加载完成
    await waitFor(() => {
      expect(screen.getByText('基本系统设置')).toBeInTheDocument();
    });
    
    // 切换到AI模型配置标签
    const aiModelTabButton = screen.getByRole('button', { name: /AI模型配置/i });
    fireEvent.click(aiModelTabButton);
    
    // 等待模型信息加载
    await waitFor(() => {
      // 使用父元素来定位特定的Test-GPT
      const modelHeader = screen.getAllByText('Test-GPT')[0]; // 获取第一个匹配项
      expect(modelHeader).toBeInTheDocument();
    });
    
    // 点击停用按钮
    const disableButton = screen.getByRole('button', { name: '停用' });
    fireEvent.click(disableButton);
    
    // 验证toggleAIModelStatus被调用
    await waitFor(() => {
      expect(systemService.toggleAIModelStatus).toHaveBeenCalledWith('Test-GPT');
    });
  });

  test('处理API错误', async () => {
    // 模拟API错误
    (systemService.getSystemSettings as jest.Mock).mockRejectedValue(new Error('测试错误'));
    
    render(<SystemSettingsPage />);
    
    // 等待错误处理
    await waitFor(() => {
      expect(systemService.getSystemSettings).toHaveBeenCalled();
    });
    
    // 检查toast.error是否被调用
    const toast = require('react-hot-toast');
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('加载系统设置失败');
    });
  });
}); 