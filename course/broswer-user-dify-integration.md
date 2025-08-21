# Dify集成Browser-Use插件开发教案

## 教案概述

### 课程目标
- 掌握Dify插件开发的完整流程
- 学会集成第三方AI库到Dify平台
- 理解Dify的工具提供者架构
- 实现browser-use的AI浏览器自动化功能

### 教学对象
- 具备Python基础的开发者
- 了解AI/LLM基本概念的技术人员
- 希望扩展Dify功能的开发者

### 课程时长
4-6小时（理论2小时 + 实践3-4小时）

---

## 第一章：理论基础

### 1.1 项目背景介绍

#### Browser-Use项目概述
[Browser-Use](https://github.com/browser-use/browser-use) 是一个革命性的AI代理库，主要功能包括：

- 🌐 **网站自动化操作**：让AI代理能够像人类一样操作网页
- 🤖 **智能任务执行**：通过自然语言描述任务，AI自动完成复杂的网页操作
- 🖥️ **跨平台支持**：支持Chrome、Firefox等主流浏览器
- 📊 **数据提取能力**：自动从网页中提取结构化数据

#### Dify平台架构
Dify是一个开源的LLM应用开发平台，具有以下特点：

- **插件化架构**：支持通过插件扩展功能
- **多模型支持**：兼容OpenAI、Anthropic等多种LLM提供商
- **工具生态**：内置丰富的工具，支持自定义工具开发

### 1.2 技术架构分析

#### Dify插件系统架构
```
Dify Plugin System
├── Built-in Tools (内置工具)
│   ├── Provider Controller (提供者控制器)
│   ├── Tool Implementation (工具实现)
│   └── Configuration Files (配置文件)
├── Custom API Tools (自定义API工具)
├── MCP Tools (模型上下文协议工具)
└── Plugin Tools (插件工具)
```

#### Browser-Use集成策略
我们选择**Built-in Tool Provider**方案，因为：
- ✅ 性能最优：直接集成，无需额外通信开销
- ✅ 用户体验好：无需复杂配置
- ✅ 维护简单：统一在Dify代码库中管理

---

## 第二章：环境准备

### 2.1 开发环境搭建

#### 系统要求
```bash
# 操作系统：macOS/Linux/Windows
# Python版本：3.10+
# Node.js版本：16+
```

#### 克隆Dify项目
```bash
# 克隆Dify源码
git clone https://github.com/langgenius/dify.git
cd dify

# 设置开发环境
cp .env.example .env
```

#### 安装依赖
```bash
# 后端依赖
cd api
pip install -r requirements.txt
pip install browser-use

# 前端依赖
cd ../web
npm install
```

### 2.2 Browser-Use环境配置

#### 安装浏览器驱动
```bash
# 安装Playwright（推荐）
playwright install chromium

# 或使用Chrome浏览器
# 确保系统已安装Chrome
```

#### 验证安装
```python
# test_browser_use.py
from browser_use import Agent
from langchain_openai import ChatOpenAI

# 基础功能测试
llm = ChatOpenAI(model="gpt-4o-mini", api_key="your-api-key")
agent = Agent(task="Go to google.com and search for 'Dify'", llm=llm)
result = agent.run()
print(result)
```

---

## 第三章：插件架构设计

### 3.1 目录结构规划

```
api/core/tools/builtin_tool/providers/browser_use/
├── browser_use.yaml              # 提供者配置
├── browser_use.py               # 提供者实现
├── _assets/
│   ├── icon.svg                 # 工具图标
│   └── icon_dark.svg            # 深色主题图标
└── tools/                       # 工具集合
    ├── browse_and_act.yaml      # 浏览器操作工具配置
    ├── browse_and_act.py        # 浏览器操作工具实现
    ├── screenshot.yaml          # 截图工具配置
    ├── screenshot.py            # 截图工具实现
    ├── extract_data.yaml        # 数据提取工具配置
    └── extract_data.py          # 数据提取工具实现
```

### 3.2 功能模块设计

#### 核心工具分类
1. **browse_and_act**：通用浏览器操作工具
2. **screenshot**：网页截图工具
3. **extract_data**：数据提取工具

#### API Key管理策略
- **优先级1**：工具级别配置的API Key
- **优先级2**：系统默认模型的API Key
- **优先级3**：环境变量中的API Key

---

## 第四章：核心代码实现

### 4.1 提供者配置文件

#### browser_use.yaml
```yaml
identity:
  author: Dify
  name: browser_use
  label:
    en_US: Browser Use
    zh_Hans: 浏览器操作
    pt_BR: Browser Use
  description:
    en_US: AI-powered browser automation tools for web interaction and data extraction
    zh_Hans: 基于AI的浏览器自动化工具，用于网页交互和数据提取
    pt_BR: Ferramentas de automação de navegador alimentadas por IA
  icon: icon.svg
  tags:
    - productivity
    - automation
    - web
    - ai-agent

# 可选的API Key配置（支持fallback到系统默认模型）
credentials_for_provider:
  openai_api_key:
    type: secret-input
    required: false
    label:
      en_US: OpenAI API Key (Optional)
      zh_Hans: OpenAI API密钥（可选）
      pt_BR: Chave da API OpenAI (Opcional)
    placeholder:
      en_US: Leave empty to use system default model API key
      zh_Hans: 留空将使用系统默认模型的API密钥
      pt_BR: Deixe vazio para usar a chave da API do modelo padrão do sistema
    help:
      en_US: If not provided, will use the API key from system default LLM model
      zh_Hans: 如果未提供，将使用系统默认LLM模型的API密钥
      pt_BR: Se não fornecido, usará a chave da API do modelo LLM padrão do sistema
  browser_type:
    type: select
    required: false
    default: "chromium"
    label:
      en_US: Browser Type
      zh_Hans: 浏览器类型
      pt_BR: Tipo de Navegador
    options:
      - value: "chromium"
        label:
          en_US: Chromium
          zh_Hans: Chromium
      - value: "firefox"
        label:
          en_US: Firefox
          zh_Hans: Firefox
      - value: "webkit"
        label:
          en_US: WebKit
          zh_Hans: WebKit
  headless:
    type: boolean
    required: false
    default: true
    label:
      en_US: Headless Mode
      zh_Hans: 无头模式
      pt_BR: Modo Headless
    help:
      en_US: Run browser in headless mode (no GUI)
      zh_Hans: 在无头模式下运行浏览器（无图形界面）
      pt_BR: Executar navegador em modo headless (sem GUI)
```

### 4.2 提供者实现类

#### browser_use.py
```python
from typing import Any
from core.tools.builtin_tool.provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError

class BrowserUseProvider(BuiltinToolProviderController):
    """
    Browser Use工具提供者
    支持AI驱动的浏览器自动化操作
    """
    
    def _validate_credentials(self, user_id: str, credentials: dict[str, Any]) -> None:
        """
        验证凭据配置
        
        Args:
            user_id: 用户ID
            credentials: 凭据字典
            
        Raises:
            ToolProviderCredentialValidationError: 凭据验证失败时抛出
        """
        try:
            # 验证browser-use是否已安装
            import browser_use
            
            # 如果提供了OpenAI API Key，验证其格式
            api_key = credentials.get("openai_api_key")
            if api_key:
                if not isinstance(api_key, str) or len(api_key.strip()) < 10:
                    raise ToolProviderCredentialValidationError(
                        "Invalid OpenAI API Key format"
                    )
            
            # 验证浏览器类型配置
            browser_type = credentials.get("browser_type", "chromium")
            valid_browsers = ["chromium", "firefox", "webkit"]
            if browser_type not in valid_browsers:
                raise ToolProviderCredentialValidationError(
                    f"Invalid browser type. Must be one of: {valid_browsers}"
                )
                
        except ImportError:
            raise ToolProviderCredentialValidationError(
                "browser-use package is not installed. Please install it with: pip install browser-use"
            )
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
```

### 4.3 核心工具实现

#### browse_and_act.yaml
```yaml
identity:
  name: browse_and_act
  author: Dify
  label:
    en_US: Browse and Act
    zh_Hans: 浏览器操作
    pt_BR: Navegar e Agir

description:
  human:
    en_US: Automate browser actions using AI. Can navigate websites, click elements, fill forms, and extract data.
    zh_Hans: 使用AI自动化浏览器操作。可以导航网站、点击元素、填写表单和提取数据。
    pt_BR: Automatize ações do navegador usando IA. Pode navegar em sites, clicar em elementos, preencher formulários e extrair dados.
  llm: |
    A powerful AI-driven browser automation tool that can:
    - Navigate to websites and interact with web elements
    - Fill out forms and submit data
    - Click buttons, links, and other interactive elements
    - Extract specific information from web pages
    - Take screenshots of web pages
    - Handle complex multi-step web workflows

parameters:
  - name: task
    type: string
    required: true
    label:
      en_US: Task Description
      zh_Hans: 任务描述
      pt_BR: Descrição da Tarefa
    human_description:
      en_US: Describe what you want the browser to do in natural language
      zh_Hans: 用自然语言描述你希望浏览器执行的操作
      pt_BR: Descreva o que você quer que o navegador faça em linguagem natural
    llm_description: |
      Detailed description of the browser automation task to perform. 
      Examples:
      - "Go to google.com and search for 'Dify AI platform'"
      - "Navigate to amazon.com, search for 'wireless headphones', and find the top 3 products with their prices"
      - "Go to linkedin.com, find the profile of John Doe, and extract his work experience"
    form: llm

  - name: start_url
    type: string
    required: false
    label:
      en_US: Starting URL
      zh_Hans: 起始网址
      pt_BR: URL Inicial
    human_description:
      en_US: The URL to start browsing from (optional, can be included in task description)
      zh_Hans: 开始浏览的网址（可选，可以包含在任务描述中）
      pt_BR: A URL para começar a navegar (opcional, pode ser incluída na descrição da tarefa)
    llm_description: Optional starting URL for the browser automation task. If not provided, the URL should be mentioned in the task description.
    form: llm

  - name: max_steps
    type: number
    required: false
    label:
      en_US: Max Steps
      zh_Hans: 最大步数
      pt_BR: Máximo de Passos
    human_description:
      en_US: Maximum number of actions the AI can perform (default: 10)
      zh_Hans: AI可以执行的最大操作数（默认：10）
      pt_BR: Número máximo de ações que a IA pode realizar (padrão: 10)
    form: form
    default: 10
    min: 1
    max: 50

  - name: include_screenshot
    type: boolean
    required: false
    label:
      en_US: Include Screenshot
      zh_Hans: 包含截图
      pt_BR: Incluir Captura de Tela
    human_description:
      en_US: Whether to include a screenshot of the final result
      zh_Hans: 是否包含最终结果的截图
      pt_BR: Se deve incluir uma captura de tela do resultado final
    form: form
    default: true

  - name: wait_time
    type: number
    required: false
    label:
      en_US: Wait Time (seconds)
      zh_Hans: 等待时间（秒）
      pt_BR: Tempo de Espera (segundos)
    human_description:
      en_US: Time to wait between actions for page loading (default: 2)
      zh_Hans: 操作之间等待页面加载的时间（默认：2）
      pt_BR: Tempo para aguardar entre ações para carregamento da página (padrão: 2)
    form: form
    default: 2
    min: 0.5
    max: 10
```

#### browse_and_act.py
```python
import asyncio
import base64
import json
import tempfile
from collections.abc import Generator
from typing import Any, Optional, Tuple
from pathlib import Path

from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from core.tools.builtin_tool.tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.errors import ToolInvokeError

class BrowseAndActTool(BuiltinTool):
    """
    Browser-Use AI驱动的浏览器自动化工具
    
    该工具可以执行复杂的网页操作任务，包括：
    - 网页导航和元素交互
    - 表单填写和提交
    - 数据提取和截图
    - 多步骤工作流程自动化
    """

    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        执行浏览器自动化任务
        
        Args:
            user_id: 用户ID
            tool_parameters: 工具参数
            conversation_id: 对话ID
            app_id: 应用ID
            message_id: 消息ID
            
        Yields:
            ToolInvokeMessage: 工具执行消息
        """
        try:
            # 导入browser-use（延迟导入避免启动时错误）
            from browser_use import Agent
            
            # 获取和验证参数
            task = tool_parameters.get("task", "").strip()
            if not task:
                yield self.create_text_message("❌ 任务描述不能为空")
                return

            start_url = tool_parameters.get("start_url", "").strip()
            max_steps = int(tool_parameters.get("max_steps", 10))
            include_screenshot = tool_parameters.get("include_screenshot", True)
            wait_time = float(tool_parameters.get("wait_time", 2))

            # 获取LLM实例
            llm = self._get_llm_instance()
            
            # 获取浏览器配置
            browser_config = self._get_browser_config()
            
            yield self.create_text_message("🚀 正在启动AI浏览器代理...")

            # 构建完整任务描述
            full_task = self._build_full_task(task, start_url)
            
            # 创建并运行browser-use代理
            result = self._run_browser_agent(
                llm=llm,
                task=full_task,
                max_steps=max_steps,
                wait_time=wait_time,
                browser_config=browser_config
            )
            
            # 处理和返回结果
            yield from self._process_results(result, include_screenshot)
            
        except ImportError as e:
            yield self.create_text_message(
                "❌ browser-use未安装。请运行: pip install browser-use"
            )
        except Exception as e:
            raise ToolInvokeError(f"浏览器自动化失败: {str(e)}")

    def _get_llm_instance(self):
        """
        获取LLM实例，支持从系统默认模型获取API Key
        
        Returns:
            LLM实例
        """
        # 优先使用工具配置的API Key
        tool_api_key = self.runtime.credentials.get("openai_api_key")
        
        if tool_api_key:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=tool_api_key,
                temperature=0.1
            )
        
        # Fallback到系统默认模型
        api_key, provider = self._get_api_key_from_default_model()
        
        if not api_key:
            raise ToolInvokeError(
                "未找到可用的API Key。请在模型设置中配置默认LLM，或在工具设置中提供OpenAI API Key"
            )
        
        # 根据提供商创建相应的LLM实例
        if provider.startswith('openai') or provider.startswith('azure_openai'):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=api_key,
                temperature=0.1
            )
        elif provider.startswith('anthropic'):
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-3-sonnet-20240229",
                api_key=api_key,
                temperature=0.1
            )
        else:
            # 尝试使用OpenAI兼容的接口
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=api_key,
                temperature=0.1
            )

    def _get_api_key_from_default_model(self) -> Tuple[Optional[str], str]:
        """
        从系统默认LLM模型配置中获取API Key
        
        Returns:
            Tuple[Optional[str], str]: (api_key, provider_name)
        """
        try:
            model_manager = ModelManager()
            model_instance = model_manager.get_default_model_instance(
                tenant_id=self.runtime.tenant_id or "",
                model_type=ModelType.LLM
            )
            
            credentials = model_instance.credentials
            provider = model_instance.provider
            
            # 根据不同提供商获取相应的API Key
            if provider.startswith('openai'):
                api_key = credentials.get("openai_api_key") or credentials.get("api_key")
                return api_key, "openai"
            elif provider.startswith('anthropic'):
                api_key = credentials.get("anthropic_api_key") or credentials.get("api_key")
                return api_key, "anthropic"
            elif provider.startswith('azure_openai'):
                api_key = credentials.get("api_key")
                return api_key, "azure_openai"
            else:
                # 对于其他提供商，尝试通用字段
                api_key = credentials.get("api_key")
                return api_key, provider
                
        except Exception as e:
            return None, "unknown"

    def _get_browser_config(self) -> dict:
        """
        获取浏览器配置
        
        Returns:
            dict: 浏览器配置字典
        """
        browser_type = self.runtime.credentials.get("browser_type", "chromium")
        headless = self.runtime.credentials.get("headless", True)
        
        return {
            "browser_type": browser_type,
            "headless": headless,
        }

    def _build_full_task(self, task: str, start_url: str) -> str:
        """
        构建完整的任务描述
        
        Args:
            task: 基础任务描述
            start_url: 起始URL
            
        Returns:
            str: 完整的任务描述
        """
        if start_url:
            return f"First, navigate to {start_url}. Then, {task}"
        return task

    def _run_browser_agent(
        self, 
        llm, 
        task: str, 
        max_steps: int,
        wait_time: float,
        browser_config: dict
    ) -> dict:
        """
        运行browser-use代理
        
        Args:
            llm: LLM实例
            task: 任务描述
            max_steps: 最大步数
            wait_time: 等待时间
            browser_config: 浏览器配置
            
        Returns:
            dict: 执行结果
        """
        try:
            from browser_use import Agent
            
            # 创建代理
            agent = Agent(
                task=task,
                llm=llm,
                max_actions=max_steps,
                # 可以根据需要添加更多配置
            )
            
            # 同步运行（browser-use支持同步调用）
            result = agent.run()
            
            return {
                "success": True,
                "result": result,
                "task": task,
                "steps_taken": getattr(result, 'action_count', 0),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "task": task,
            }

    def _process_results(
        self, 
        result: dict, 
        include_screenshot: bool
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        处理和返回执行结果
        
        Args:
            result: 执行结果
            include_screenshot: 是否包含截图
            
        Yields:
            ToolInvokeMessage: 处理后的消息
        """
        if not result["success"]:
            yield self.create_text_message(f"❌ 执行失败: {result['error']}")
            return

        browser_result = result["result"]
        
        # 返回主要结果
        if hasattr(browser_result, 'final_result') and browser_result.final_result:
            yield self.create_text_message(f"✅ 任务完成: {browser_result.final_result}")
        else:
            yield self.create_text_message("✅ 浏览器操作已完成")

        # 返回操作历史摘要
        if hasattr(browser_result, 'action_history') and browser_result.action_history:
            self._yield_action_summary(browser_result.action_history)

        # 返回截图（如果有且用户要求）
        if include_screenshot and hasattr(browser_result, 'screenshots'):
            yield from self._yield_screenshot(browser_result.screenshots)

        # 返回提取的数据（如果有）
        if hasattr(browser_result, 'extracted_data') and browser_result.extracted_data:
            yield from self._yield_extracted_data(browser_result.extracted_data)

    def _yield_action_summary(self, action_history: list) -> Generator[ToolInvokeMessage, None, None]:
        """
        返回操作历史摘要
        
        Args:
            action_history: 操作历史列表
            
        Yields:
            ToolInvokeMessage: 操作摘要消息
        """
        if not action_history:
            return
            
        # 显示最后5个操作
        recent_actions = action_history[-5:]
        action_summary = []
        
        for i, action in enumerate(recent_actions, 1):
            action_desc = str(action) if hasattr(action, '__str__') else repr(action)
            action_summary.append(f"{i}. {action_desc}")
        
        summary_text = "📋 最近执行的操作:\n" + "\n".join(action_summary)
        yield self.create_text_message(summary_text)

    def _yield_screenshot(self, screenshots) -> Generator[ToolInvokeMessage, None, None]:
        """
        返回截图
        
        Args:
            screenshots: 截图数据
            
        Yields:
            ToolInvokeMessage: 截图消息
        """
        if not screenshots:
            return
            
        try:
            # 获取最后一张截图
            last_screenshot = screenshots[-1] if isinstance(screenshots, list) else screenshots
            
            if isinstance(last_screenshot, str):
                # 如果是base64编码的字符串
                screenshot_data = base64.b64decode(last_screenshot)
            elif isinstance(last_screenshot, bytes):
                # 如果是字节数据
                screenshot_data = last_screenshot
            elif isinstance(last_screenshot, Path):
                # 如果是文件路径
                with open(last_screenshot, 'rb') as f:
                    screenshot_data = f.read()
            else:
                return
            
            yield self.create_blob_message(
                blob=screenshot_data,
                meta={"mime_type": "image/png"}
            )
            
        except Exception as e:
            yield self.create_text_message(f"⚠️ 截图处理失败: {str(e)}")

    def _yield_extracted_data(self, extracted_data) -> Generator[ToolInvokeMessage, None, None]:
        """
        返回提取的数据
        
        Args:
            extracted_data: 提取的数据
            
        Yields:
            ToolInvokeMessage: 数据消息
        """
        try:
            if isinstance(extracted_data, dict):
                yield self.create_json_message(extracted_data)
            elif isinstance(extracted_data, list):
                for item in extracted_data:
                    if isinstance(item, dict):
                        yield self.create_json_message(item)
                    else:
                        yield self.create_text_message(f"📊 提取的数据: {str(item)}")
            else:
                yield self.create_text_message(f"📊 提取的数据: {str(extracted_data)}")
                
        except Exception as e:
            yield self.create_text_message(f"⚠️ 数据处理失败: {str(e)}")
```

---

## 第五章：辅助工具实现

### 5.1 截图工具

#### screenshot.yaml
```yaml
identity:
  name: screenshot
  author: Dify
  label:
    en_US: Web Screenshot
    zh_Hans: 网页截图
    pt_BR: Captura de Tela Web

description:
  human:
    en_US: Take a screenshot of a web page
    zh_Hans: 对网页进行截图
    pt_BR: Tire uma captura de tela de uma página web
  llm: Take a screenshot of a specified web page URL and return the image

parameters:
  - name: url
    type: string
    required: true
    label:
      en_US: URL
      zh_Hans: 网址
      pt_BR: URL
    human_description:
      en_US: The URL of the web page to screenshot
      zh_Hans: 要截图的网页URL
      pt_BR: A URL da página web para capturar
    llm_description: The complete URL of the web page to take a screenshot of
    form: llm

  - name: full_page
    type: boolean
    required: false
    label:
      en_US: Full Page
      zh_Hans: 完整页面
      pt_BR: Página Completa
    human_description:
      en_US: Whether to capture the full page or just the visible area
      zh_Hans: 是否捕获完整页面或仅可见区域
      pt_BR: Se deve capturar a página completa ou apenas a área visível
    form: form
    default: false

  - name: width
    type: number
    required: false
    label:
      en_US: Viewport Width
      zh_Hans: 视口宽度
      pt_BR: Largura da Janela
    human_description:
      en_US: Browser viewport width in pixels (default: 1280)
      zh_Hans: 浏览器视口宽度（像素）（默认：1280）
      pt_BR: Largura da janela do navegador em pixels (padrão: 1280)
    form: form
    default: 1280
    min: 320
    max: 3840

  - name: height
    type: number
    required: false
    label:
      en_US: Viewport Height
      zh_Hans: 视口高度
      pt_BR: Altura da Janela
    human_description:
      en_US: Browser viewport height in pixels (default: 720)
      zh_Hans: 浏览器视口高度（像素）（默认：720）
      pt_BR: Altura da janela do navegador em pixels (padrão: 720)
    form: form
    default: 720
    min: 240
    max: 2160
```

#### screenshot.py
```python
import asyncio
import base64
from collections.abc import Generator
from typing import Any, Optional

from core.tools.builtin_tool.tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.errors import ToolInvokeError

class ScreenshotTool(BuiltinTool):
    """
    网页截图工具
    """

    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        执行网页截图
        """
        try:
            from playwright.async_api import async_playwright
            
            url = tool_parameters.get("url", "").strip()
            if not url:
                yield self.create_text_message("❌ URL不能为空")
                return

            # 确保URL格式正确
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            full_page = tool_parameters.get("full_page", False)
            width = int(tool_parameters.get("width", 1280))
            height = int(tool_parameters.get("height", 720))

            yield self.create_text_message(f"📸 正在截图: {url}")

            # 获取浏览器配置
            browser_type = self.runtime.credentials.get("browser_type", "chromium")
            headless = self.runtime.credentials.get("headless", True)

            # 执行截图
            screenshot_data = asyncio.run(self._take_screenshot(
                url=url,
                full_page=full_page,
                width=width,
                height=height,
                browser_type=browser_type,
                headless=headless
            ))

            if screenshot_data:
                yield self.create_blob_message(
                    blob=screenshot_data,
                    meta={"mime_type": "image/png"}
                )
                yield self.create_text_message("✅ 截图完成")
            else:
                yield self.create_text_message("❌ 截图失败")

        except ImportError:
            yield self.create_text_message(
                "❌ Playwright未安装。请运行: pip install playwright && playwright install"
            )
        except Exception as e:
            raise ToolInvokeError(f"截图失败: {str(e)}")

    async def _take_screenshot(
        self, 
        url: str, 
        full_page: bool, 
        width: int, 
        height: int,
        browser_type: str,
        headless: bool
    ) -> Optional[bytes]:
        """
        异步截图函数
        """
        async with async_playwright() as p:
            # 根据配置启动浏览器
            if browser_type == "firefox":
                browser = await p.firefox.launch(headless=headless)
            elif browser_type == "webkit":
                browser = await p.webkit.launch(headless=headless)
            else:  # chromium (default)
                browser = await p.chromium.launch(headless=headless)

            try:
                context = await browser.new_context(
                    viewport={"width": width, "height": height}
                )
                page = await context.new_page()
                
                # 访问页面
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # 截图
                screenshot_bytes = await page.screenshot(
                    full_page=full_page,
                    type="png"
                )
                
                return screenshot_bytes
                
            finally:
                await browser.close()
```

### 5.2 数据提取工具

#### extract_data.yaml
```yaml
identity:
  name: extract_data
  author: Dify
  label:
    en_US: Extract Web Data
    zh_Hans: 提取网页数据
    pt_BR: Extrair Dados Web

description:
  human:
    en_US: Extract structured data from web pages using AI
    zh_Hans: 使用AI从网页中提取结构化数据
    pt_BR: Extrair dados estruturados de páginas web usando IA
  llm: |
    Extract specific structured data from web pages using AI. Can extract:
    - Product information (name, price, description, etc.)
    - Contact information (email, phone, address)
    - Article content (title, author, publish date, content)
    - Table data and lists
    - Any structured information based on user requirements

parameters:
  - name: url
    type: string
    required: true
    label:
      en_US: URL
      zh_Hans: 网址
      pt_BR: URL
    human_description:
      en_US: The URL of the web page to extract data from
      zh_Hans: 要提取数据的网页URL
      pt_BR: A URL da página web para extrair dados
    llm_description: The complete URL of the web page to extract data from
    form: llm

  - name: data_schema
    type: string
    required: true
    label:
      en_US: Data Schema
      zh_Hans: 数据结构
      pt_BR: Esquema de Dados
    human_description:
      en_US: |
        Describe the structure of data you want to extract. 
        Example: "Extract product name, price, and description from each product listing"
      zh_Hans: |
        描述你想要提取的数据结构。
        例如："从每个产品列表中提取产品名称、价格和描述"
      pt_BR: |
        Descreva a estrutura dos dados que você quer extrair.
        Exemplo: "Extrair nome do produto, preço e descrição de cada listagem de produto"
    llm_description: |
      Detailed description of the data structure to extract from the web page.
      Be specific about what fields you need and their expected format.
    form: llm

  - name: max_items
    type: number
    required: false
    label:
      en_US: Max Items
      zh_Hans: 最大条目数
      pt_BR: Máximo de Itens
    human_description:
      en_US: Maximum number of items to extract (default: 10)
      zh_Hans: 要提取的最大条目数（默认：10）
      pt_BR: Número máximo de itens para extrair (padrão: 10)
    form: form
    default: 10
    min: 1
    max: 100

  - name: include_screenshot
    type: boolean
    required: false
    label:
      en_US: Include Screenshot
      zh_Hans: 包含截图
      pt_BR: Incluir Captura de Tela
    human_description:
      en_US: Whether to include a screenshot for reference
      zh_Hans: 是否包含截图作为参考
      pt_BR: Se deve incluir uma captura de tela para referência
    form: form
    default: false
```

#### extract_data.py
```python
import asyncio
import json
from collections.abc import Generator
from typing import Any, Optional

from core.tools.builtin_tool.tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.errors import ToolInvokeError

class ExtractDataTool(BuiltinTool):
    """
    AI驱动的网页数据提取工具
    """

    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
        conversation_id: Optional[str] = None,
        app_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        执行数据提取任务
        """
        try:
            from browser_use import Agent
            
            url = tool_parameters.get("url", "").strip()
            data_schema = tool_parameters.get("data_schema", "").strip()
            
            if not url or not data_schema:
                yield self.create_text_message("❌ URL和数据结构描述不能为空")
                return

            # 确保URL格式正确
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            max_items = int(tool_parameters.get("max_items", 10))
            include_screenshot = tool_parameters.get("include_screenshot", False)

            yield self.create_text_message(f"🔍 正在从 {url} 提取数据...")

            # 获取LLM实例（复用browse_and_act的逻辑）
            llm = self._get_llm_instance()

            # 构建数据提取任务
            extraction_task = self._build_extraction_task(url, data_schema, max_items)
            
            # 创建browser-use代理进行数据提取
            agent = Agent(
                task=extraction_task,
                llm=llm,
                max_actions=20,  # 数据提取可能需要更多步骤
            )

            result = agent.run()

            # 处理提取结果
            yield from self._process_extraction_results(
                result, 
                include_screenshot,
                data_schema
            )

        except ImportError:
            yield self.create_text_message(
                "❌ browser-use未安装。请运行: pip install browser-use"
            )
        except Exception as e:
            raise ToolInvokeError(f"数据提取失败: {str(e)}")

    def _get_llm_instance(self):
        """
        获取LLM实例（与browse_and_act工具相同的逻辑）
        """
        # 这里复用browse_and_act.py中的_get_llm_instance方法
        # 为简化示例，这里省略具体实现
        # 实际开发中可以将此方法提取到基类或工具类中
        pass

    def _build_extraction_task(self, url: str, data_schema: str, max_items: int) -> str:
        """
        构建数据提取任务描述
        """
        task = f"""
        Navigate to {url} and extract structured data according to the following schema:
        
        Data Schema: {data_schema}
        
        Requirements:
        1. Extract up to {max_items} items
        2. Return the data in JSON format
        3. Be precise and accurate in data extraction
        4. If the page has pagination, extract from the current page only
        5. Return the final extracted data as a structured JSON object
        
        Focus on extracting clean, accurate data that matches the specified schema.
        """
        
        return task

    def _process_extraction_results(
        self, 
        result, 
        include_screenshot: bool,
        data_schema: str
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        处理数据提取结果
        """
        if not result or not hasattr(result, 'final_result'):
            yield self.create_text_message("❌ 数据提取失败，未获得有效结果")
            return

        # 尝试解析JSON数据
        extracted_text = result.final_result
        
        try:
            # 尝试从结果中提取JSON数据
            extracted_data = self._parse_json_from_result(extracted_text)
            
            if extracted_data:
                yield self.create_text_message(f"✅ 成功提取数据（基于: {data_schema}）")
                yield self.create_json_message(extracted_data)
            else:
                # 如果无法解析为JSON，返回原始文本
                yield self.create_text_message("📊 提取的数据:")
                yield self.create_text_message(extracted_text)
                
        except Exception as e:
            yield self.create_text_message(f"⚠️ 数据解析失败: {str(e)}")
            yield self.create_text_message("原始提取结果:")
            yield self.create_text_message(extracted_text)

        # 返回截图（如果需要）
        if include_screenshot and hasattr(result, 'screenshots') and result.screenshots:
            try:
                last_screenshot = result.screenshots[-1]
                if isinstance(last_screenshot, bytes):
                    yield self.create_blob_message(
                        blob=last_screenshot,
                        meta={"mime_type": "image/png"}
                    )
            except Exception as e:
                yield self.create_text_message(f"⚠️ 截图处理失败: {str(e)}")

    def _parse_json_from_result(self, text: str) -> Optional[dict]:
        """
        从结果文本中解析JSON数据
        """
        try:
            # 直接尝试解析整个文本
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                # 尝试找到JSON部分
                import re
                json_pattern = r'\{.*\}'
                match = re.search(json_pattern, text, re.DOTALL)
                if match:
                    return json.loads(match.group())
                
                # 尝试数组格式
                array_pattern = r'\[.*\]'
                match = re.search(array_pattern, text, re.DOTALL)
                if match:
                    return json.loads(match.group())
                    
            except json.JSONDecodeError:
                pass
                
        return None
```

---

## 第六章：系统集成与配置

### 6.1 注册工具提供者

#### 更新_positions.py
```python
# api/core/tools/builtin_tool/providers/_positions.py

class BuiltinToolProviderSort:
    SEARCHAPI = "searchapi"
    SERPAPI = "serpapi"
    WEBSCRAPER = "webscraper"
    BROWSER_USE = "browser_use"  # 新增
    # ... 其他工具
```

### 6.2 添加依赖

#### requirements.txt
```txt
# 在api/requirements.txt中添加
browser-use>=1.0.0
playwright>=1.40.0
langchain-openai>=0.1.0
langchain-anthropic>=0.1.0
```

### 6.3 Docker配置（可选）

#### Dockerfile修改
```dockerfile
# 如果使用Docker部署，在api/Dockerfile中添加
RUN pip install browser-use playwright
RUN playwright install chromium
```

---

## 第七章：测试与调试

### 7.1 单元测试

#### test_browser_use.py
```python
# api/tests/unit_tests/tools/builtin_tool/test_browser_use.py

import pytest
from unittest.mock import Mock, patch
from core.tools.builtin_tool.providers.browser_use.tools.browse_and_act import BrowseAndActTool
from core.tools.entities.tool_entities import ToolEntity, ToolIdentity
from core.tools.__base.tool_runtime import ToolRuntime

class TestBrowserUseTool:
    
    @pytest.fixture
    def tool_entity(self):
        return ToolEntity(
            identity=ToolIdentity(
                author="Dify",
                name="browse_and_act",
                provider="browser_use"
            ),
            parameters=[],
            description="Test browser automation tool"
        )
    
    @pytest.fixture
    def tool_runtime(self):
        return ToolRuntime(
            tenant_id="test_tenant",
            credentials={
                "openai_api_key": "sk-test",
                "browser_type": "chromium",
                "headless": True
            }
        )
    
    @pytest.fixture
    def browse_tool(self, tool_entity, tool_runtime):
        return BrowseAndActTool(
            entity=tool_entity,
            runtime=tool_runtime
        )
    
    def test_get_llm_instance_with_tool_credentials(self, browse_tool):
        """测试使用工具凭据创建LLM实例"""
        with patch('langchain_openai.ChatOpenAI') as mock_llm:
            llm = browse_tool._get_llm_instance()
            mock_llm.assert_called_once()
    
    @patch('core.model_manager.ModelManager')
    def test_get_api_key_from_default_model(self, mock_manager, browse_tool):
        """测试从默认模型获取API Key"""
        # 模拟模型实例
        mock_instance = Mock()
        mock_instance.credentials = {"openai_api_key": "sk-default"}
        mock_instance.provider = "openai"
        
        mock_manager.return_value.get_default_model_instance.return_value = mock_instance
        
        api_key, provider = browse_tool._get_api_key_from_default_model()
        
        assert api_key == "sk-default"
        assert provider == "openai"
    
    def test_build_full_task(self, browse_tool):
        """测试任务描述构建"""
        task = "Search for information"
        start_url = "https://google.com"
        
        full_task = browse_tool._build_full_task(task, start_url)
        
        assert "https://google.com" in full_task
        assert "Search for information" in full_task
    
    @patch('browser_use.Agent')
    def test_run_browser_agent_success(self, mock_agent, browse_tool):
        """测试成功运行浏览器代理"""
        # 模拟成功结果
        mock_result = Mock()
        mock_result.final_result = "Task completed successfully"
        mock_agent.return_value.run.return_value = mock_result
        
        llm = Mock()
        result = browse_tool._run_browser_agent(
            llm=llm,
            task="Test task",
            max_steps=5,
            wait_time=1.0,
            browser_config={"browser_type": "chromium", "headless": True}
        )
        
        assert result["success"] is True
        assert "result" in result
    
    @patch('browser_use.Agent')
    def test_run_browser_agent_failure(self, mock_agent, browse_tool):
        """测试浏览器代理运行失败"""
        mock_agent.return_value.run.side_effect = Exception("Browser error")
        
        llm = Mock()
        result = browse_tool._run_browser_agent(
            llm=llm,
            task="Test task",
            max_steps=5,
            wait_time=1.0,
            browser_config={"browser_type": "chromium", "headless": True}
        )
        
        assert result["success"] is False
        assert "error" in result
```

### 7.2 集成测试

#### test_integration.py
```python
# api/tests/integration_tests/tools/test_browser_use_integration.py

import pytest
from core.tools.tool_manager import ToolManager

class TestBrowserUseIntegration:
    
    def test_provider_registration(self):
        """测试提供者是否正确注册"""
        tool_manager = ToolManager()
        
        # 检查browser_use提供者是否存在
        providers = tool_manager.get_builtin_tool_provider_controllers()
        provider_names = [p.entity.identity.name for p in providers]
        
        assert "browser_use" in provider_names
    
    def test_tools_available(self):
        """测试工具是否可用"""
        tool_manager = ToolManager()
        
        try:
            provider = tool_manager.get_builtin_tool_provider_controller("browser_use")
            tools = provider.get_tools()
            tool_names = [tool.identity.name for tool in tools]
            
            assert "browse_and_act" in tool_names
            assert "screenshot" in tool_names
            assert "extract_data" in tool_names
            
        except Exception as e:
            pytest.fail(f"Failed to get browser_use tools: {e}")
```

### 7.3 手动测试

#### 测试脚本
```python
# test_manual.py - 手动测试脚本

from core.tools.builtin_tool.providers.browser_use.tools.browse_and_act import BrowseAndActTool
from core.tools.entities.tool_entities import ToolEntity, ToolIdentity
from core.tools.__base.tool_runtime import ToolRuntime

def test_browser_use_manual():
    """手动测试browser-use工具"""
    
    # 创建工具实例
    tool_entity = ToolEntity(
        identity=ToolIdentity(
            author="Dify",
            name="browse_and_act",
            provider="browser_use"
        ),
        parameters=[],
        description="Test browser automation tool"
    )
    
    tool_runtime = ToolRuntime(
        tenant_id="test_tenant",
        credentials={
            "openai_api_key": "your-openai-api-key",  # 替换为真实API Key
            "browser_type": "chromium",
            "headless": True
        }
    )
    
    tool = BrowseAndActTool(entity=tool_entity, runtime=tool_runtime)
    
    # 执行简单的搜索任务
    tool_parameters = {
        "task": "Go to google.com and search for 'Dify AI platform'",
        "max_steps": 5,
        "include_screenshot": True,
        "wait_time": 2
    }
    
    print("开始执行浏览器自动化任务...")
    
    try:
        results = list(tool._invoke(
            user_id="test_user",
            tool_parameters=tool_parameters
        ))
        
        for result in results:
            if result.type == "text":
                print(f"文本消息: {result.message}")
            elif result.type == "blob":
                print(f"接收到图片，大小: {len(result.message)} bytes")
            elif result.type == "json":
                print(f"JSON数据: {result.message}")
                
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    test_browser_use_manual()
```

---

## 第八章：部署与发布

### 8.1 本地部署

#### 启动开发环境
```bash
# 启动后端
cd api
python app.py

# 启动前端
cd ../web
npm run dev
```

#### 验证安装
1. 打开Dify界面
2. 进入工作流编辑器
3. 查看工具列表中是否有"Browser Use"
4. 测试创建简单的浏览器自动化工作流

### 8.2 生产部署

#### Docker部署
```bash
# 构建包含browser-use的镜像
docker build -t dify-with-browser-use .

# 启动服务
docker-compose up -d
```

#### 环境变量配置
```bash
# .env文件中添加
BROWSER_USE_ENABLED=true
BROWSER_USE_HEADLESS=true
BROWSER_USE_DEFAULT_BROWSER=chromium
```

### 8.3 性能优化

#### 浏览器资源管理
```python
# 在browser_use工具中添加资源管理
class BrowserResourceManager:
    def __init__(self):
        self.active_browsers = {}
        self.max_concurrent = 3
    
    async def get_browser(self, browser_type: str):
        # 实现浏览器实例复用逻辑
        pass
    
    async def cleanup_idle_browsers(self):
        # 清理空闲浏览器
        pass
```

#### 缓存策略
```python
# 实现结果缓存
from functools import lru_cache
import hashlib

class BrowserResultCache:
    @staticmethod
    @lru_cache(maxsize=100)
    def get_cached_result(task_hash: str):
        # 缓存频繁访问的页面结果
        pass
```

---

## 第九章：故障排除

### 9.1 常见问题

#### 问题1：browser-use安装失败
**症状**：ImportError: No module named 'browser_use'
**解决方案**：
```bash
pip install browser-use
# 如果网络问题，使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple browser-use
```

#### 问题2：浏览器驱动问题
**症状**：Playwright浏览器未安装
**解决方案**：
```bash
playwright install
# 或安装特定浏览器
playwright install chromium
```

#### 问题3：API Key未找到
**症状**：工具报告无法获取API Key
**解决方案**：
1. 检查Dify模型设置中是否配置了默认LLM
2. 确认API Key格式正确
3. 验证工具凭据配置

#### 问题4：浏览器操作超时
**症状**：任务执行时间过长或超时
**解决方案**：
1. 增加max_steps参数
2. 调整wait_time参数
3. 简化任务描述

### 9.2 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 在工具中添加调试信息
yield self.create_text_message(f"🐛 调试信息: {debug_info}")
```

#### 浏览器调试模式
```python
# 临时启用非headless模式查看浏览器操作
browser_config = {
    "browser_type": "chromium",
    "headless": False,  # 设置为False以查看浏览器界面
}
```

### 9.3 监控与日志

#### 添加性能监控
```python
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.2f}秒")
        return result
    return wrapper
```

---

## 第十章：进阶特性

### 10.1 自定义浏览器配置

#### 高级浏览器设置
```python
def _get_advanced_browser_config(self) -> dict:
    """获取高级浏览器配置"""
    return {
        "browser_type": self.runtime.credentials.get("browser_type", "chromium"),
        "headless": self.runtime.credentials.get("headless", True),
        "viewport": {
            "width": self.runtime.credentials.get("viewport_width", 1280),
            "height": self.runtime.credentials.get("viewport_height", 720)
        },
        "user_agent": self.runtime.credentials.get("user_agent", ""),
        "proxy": self.runtime.credentials.get("proxy_url", ""),
        "timeout": self.runtime.credentials.get("timeout", 30000),
        "locale": self.runtime.credentials.get("locale", "en-US"),
    }
```

### 10.2 多步骤工作流

#### 复杂任务分解
```python
def _execute_multi_step_workflow(self, steps: list) -> dict:
    """执行多步骤工作流"""
    results = []
    
    for i, step in enumerate(steps, 1):
        yield self.create_text_message(f"🔄 执行步骤 {i}/{len(steps)}: {step['description']}")
        
        step_result = self._execute_single_step(step)
        results.append(step_result)
        
        # 步骤间等待
        if step.get("wait_after", 0) > 0:
            time.sleep(step["wait_after"])
    
    return {"steps_completed": len(results), "results": results}
```

### 10.3 错误处理与重试

#### 智能重试机制
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class BrowserOperationWithRetry:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _execute_with_retry(self, operation):
        """带重试的操作执行"""
        try:
            return operation()
        except Exception as e:
            print(f"操作失败，准备重试: {e}")
            raise
```

---

## 课程总结

### 学习成果
通过本教案，你已经掌握了：

1. ✅ **Dify插件架构理解**：深入了解Built-in Tool Provider的工作机制
2. ✅ **Browser-Use集成**：成功将AI浏览器自动化功能集成到Dify
3. ✅ **多工具开发**：实现了浏览器操作、截图、数据提取三个核心工具
4. ✅ **系统级集成**：支持从系统默认模型获取API Key
5. ✅ **完整测试**：包含单元测试、集成测试和手动测试
6. ✅ **生产部署**：具备生产环境部署的完整方案

### 技术亮点
- 🎯 **智能API Key管理**：自动从系统默认模型获取凭据
- 🔧 **灵活配置**：支持多种浏览器和自定义设置
- 🛡️ **健壮错误处理**：完善的异常处理和重试机制
- 📊 **丰富输出格式**：支持文本、JSON、图片等多种输出
- 🚀 **高性能设计**：支持并发和资源复用

### 扩展建议
1. **添加更多浏览器操作**：表单自动填写、文件上传等
2. **增强数据提取**：支持更复杂的数据结构和格式
3. **集成代理支持**：添加HTTP代理和IP轮换
4. **实现结果缓存**：提高重复任务的执行效率
5. **添加监控告警**：实时监控工具使用情况

这个完整的集成方案为Dify平台带来了强大的AI浏览器自动化能力，让用户可以通过自然语言描述来完成复杂的网页操作任务，极大地扩展了Dify的应用场景和实用性。