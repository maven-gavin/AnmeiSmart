"""创建测试用的MCP工具数据"""
import uuid
import hashlib
from sqlalchemy.orm import Session
from app.db.models.mcp import MCPToolGroup, MCPTool
from app.core.config import get_settings
from app.db.base import SessionLocal

settings = get_settings()


def create_test_tools():
    """创建测试用的MCP工具数据"""
    db: Session = SessionLocal()
    
    try:
        # 检查是否已存在default工具分组
        existing_group = db.query(MCPToolGroup).filter(
            MCPToolGroup.server_code == "default"
        ).first()
        
        if existing_group:
            print("默认工具分组已存在，跳过创建")
            return
        
        # 创建默认工具分组
        test_api_key = "test_api_key_123"
        hashed_api_key = hashlib.sha256(test_api_key.encode()).hexdigest()
        
        group = MCPToolGroup(
            id=str(uuid.uuid4()),
            name="默认测试工具组",
            description="用于测试MCP服务器的默认工具组",
            api_key=test_api_key,  # 会被自动加密
            hashed_api_key=hashed_api_key,
            server_code="default",
            user_tier_access=["internal", "premium"],
            allowed_roles=["admin", "consultant", "customer"],
            enabled=True,
            created_by="system"
        )
        
        db.add(group)
        db.flush()  # 获取分组ID
        
        # 创建测试工具
        tools = [
            {
                "tool_name": "echo_tool",
                "description": "简单的回显工具，返回用户输入的内容",
                "config_data": {
                    "parameters": {
                        "message": {
                            "type": "string",
                            "description": "要回显的消息",
                            "required": True
                        }
                    }
                }
            },
            {
                "tool_name": "user_profile",
                "description": "获取用户档案信息",
                "config_data": {
                    "parameters": {
                        "user_id": {
                            "type": "string",
                            "description": "用户ID",
                            "required": True
                        }
                    }
                }
            },
            {
                "tool_name": "customer_analysis",
                "description": "分析客户信息和需求",
                "config_data": {
                    "parameters": {
                        "customer_id": {
                            "type": "string",
                            "description": "客户ID",
                            "required": True
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "分析类型",
                            "enum": ["basic", "detailed", "preferences"],
                            "required": False
                        }
                    }
                }
            },
            {
                "tool_name": "treatment_plan_generation",
                "description": "生成个性化治疗方案",
                "config_data": {
                    "parameters": {
                        "customer_id": {
                            "type": "string",
                            "description": "客户ID",
                            "required": True
                        },
                        "treatment_category": {
                            "type": "string",
                            "description": "治疗类别",
                            "enum": ["facial", "body", "skin", "anti_aging"],
                            "required": True
                        },
                        "budget_range": {
                            "type": "string",
                            "description": "预算范围",
                            "enum": ["low", "medium", "high", "premium"],
                            "required": False
                        }
                    }
                }
            }
        ]
        
        for tool_config in tools:
            tool = MCPTool(
                id=str(uuid.uuid4()),
                group_id=group.id,
                tool_name=tool_config["tool_name"],
                description=tool_config["description"],
                version="1.0.0",
                enabled=True,
                timeout_seconds=30,
                config_data=tool_config["config_data"]
            )
            db.add(tool)
        
        db.commit()
        print(f"成功创建工具分组: {group.name} (server_code: {group.server_code})")
        print(f"创建了 {len(tools)} 个测试工具")
        
        # 列出创建的工具
        for tool_config in tools:
            print(f"  - {tool_config['tool_name']}: {tool_config['description']}")
        
    except Exception as e:
        db.rollback()
        print(f"创建测试工具失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("正在创建测试用的MCP工具...")
    create_test_tools()
    print("完成！")
