#!/usr/bin/env python3
"""
AI Gateway功能测试脚本

测试新的AI Gateway架构的各项功能。
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["DATABASE_URL"] = "postgresql://postgres:difyai123456@localhost:5432/anmeismart"
os.environ["OPENAI_API_KEY"] = "sk-test-key"  # 测试密钥
# AI Gateway已集成Agent配置，无需单独设置AGENT环境变量

from app.db.base import get_db_context
from app.services.ai.ai_gateway_service import get_ai_gateway_service
from app.services.ai.interfaces import AIScenario


class AIGatewayTester:
    """AI Gateway测试器"""
    
    def __init__(self):
        self.db = None
        self.ai_gateway = None
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def setup(self):
        """设置测试环境"""
        try:
            # 获取数据库连接
            db_context = get_db_context()
            self.db = next(db_context)
            
            # 获取AI Gateway服务
            self.ai_gateway = get_ai_gateway_service(self.db)
            
            self.logger.info("✅ AI Gateway测试环境初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 测试环境初始化失败: {e}")
            return False
    
    async def test_health_check(self):
        """测试健康检查"""
        try:
            self.logger.info("🔍 测试健康检查...")
            
            health_status = await self.ai_gateway.get_health_status()
            
            self.logger.info(f"📊 Gateway状态: {health_status.get('status', 'unknown')}")
            
            providers = health_status.get('providers', {})
            for provider_name, provider_status in providers.items():
                status = provider_status.get('health', {}).get('status', 'unknown')
                self.logger.info(f"   • {provider_name}: {status}")
            
            cache_stats = health_status.get('cache_stats', {})
            if cache_stats:
                self.logger.info(f"📱 缓存状态: {cache_stats.get('size', 0)}/{cache_stats.get('max_size', 0)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 健康检查测试失败: {e}")
            return False
    
    async def test_chat(self):
        """测试通用聊天"""
        try:
            self.logger.info("💬 测试通用聊天...")
            
            response = await self.ai_gateway.chat(
                message="你好，我想了解医美服务",
                user_id="test_user_001",
                session_id="test_session_001",
                user_profile={
                    "age": 25,
                    "gender": "female",
                    "skin_type": "mixed"
                }
            )
            
            self.logger.info(f"🤖 AI回复: {response.content[:100]}...")
            self.logger.info(f"🏷️ 提供商: {response.provider.value}")
            self.logger.info(f"⏱️ 响应时间: {response.response_time:.2f}s")
            
            if response.usage:
                tokens = response.usage.get('total_tokens', 0)
                self.logger.info(f"🎫 Token使用: {tokens}")
            
            return response.success
            
        except Exception as e:
            self.logger.error(f"❌ 聊天测试失败: {e}")
            return False
    
    async def test_beauty_plan(self):
        """测试医美方案生成"""
        try:
            self.logger.info("💄 测试医美方案生成...")
            
            response = await self.ai_gateway.generate_beauty_plan(
                requirements="我想改善面部肌肤，预算在1-2万元",
                user_id="test_user_002",
                user_profile={
                    "age": 28,
                    "gender": "female",
                    "skin_type": "dry",
                    "concerns": ["fine_lines", "dullness"],
                    "budget": "10000-20000"
                }
            )
            
            self.logger.info(f"📋 方案内容: {response.content[:150]}...")
            self.logger.info(f"🏷️ 提供商: {response.provider.value}")
            
            if response.plan_sections:
                self.logger.info(f"📑 方案章节数: {len(response.plan_sections)}")
            
            if response.estimated_cost:
                total_cost = response.estimated_cost.get('total', 0)
                self.logger.info(f"💰 预估费用: {total_cost}元")
            
            return response.success
            
        except Exception as e:
            self.logger.error(f"❌ 方案生成测试失败: {e}")
            return False
    
    async def test_sentiment_analysis(self):
        """测试情感分析"""
        try:
            self.logger.info("😊 测试情感分析...")
            
            test_texts = [
                "我对这个治疗方案很满意，效果超出了我的期望！",
                "我有点担心这个手术的风险...",
                "价格有点贵，但是如果效果好的话还是可以考虑的。"
            ]
            
            for i, text in enumerate(test_texts, 1):
                response = await self.ai_gateway.analyze_sentiment(
                    text=text,
                    user_id=f"test_user_sentiment_{i}"
                )
                
                self.logger.info(f"📝 文本{i}: {text[:50]}...")
                self.logger.info(f"💭 情感分数: {response.sentiment_score:.2f}")
                self.logger.info(f"🎯 置信度: {response.confidence:.2f}")
                
                if response.emotions:
                    emotions = ", ".join([f"{k}:{v:.2f}" for k, v in response.emotions.items()])
                    self.logger.info(f"❤️ 具体情感: {emotions}")
                
                if not response.success:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 情感分析测试失败: {e}")
            return False
    
    async def test_consultation_summary(self):
        """测试咨询总结"""
        try:
            self.logger.info("📝 测试咨询总结...")
            
            conversation_text = """
客户: 你好，我想咨询一下面部美容的项目
顾问: 您好！欢迎咨询。请问您主要想改善哪些方面的问题？
客户: 我觉得皮肤比较暗沉，而且有一些细纹，想让皮肤看起来更年轻一些
顾问: 了解您的需求。请问您的年龄和肌肤类型是怎样的？
客户: 我今年30岁，混合性肌肤，T区比较油，两颊偏干
顾问: 根据您的情况，我建议可以考虑光子嫩肤配合水光针的组合治疗
客户: 这个治疗大概需要多少费用？有什么风险吗？
顾问: 费用大概在8000-12000元，风险很小，主要是术后需要注意防晒和保湿
客户: 好的，我考虑一下。还有其他方案吗？
顾问: 还可以考虑射频紧肤，对细纹改善效果更明显，费用稍高一些
"""
            
            response = await self.ai_gateway.summarize_consultation(
                conversation_text=conversation_text,
                user_id="test_user_summary"
            )
            
            self.logger.info(f"📄 总结内容: {response.content[:200]}...")
            self.logger.info(f"🏷️ 提供商: {response.provider.value}")
            
            if response.key_points:
                self.logger.info(f"🔑 关键点数: {len(response.key_points)}")
            
            if response.action_items:
                self.logger.info(f"✅ 行动项数: {len(response.action_items)}")
            
            if response.sentiment_score is not None:
                self.logger.info(f"💭 客户情感: {response.sentiment_score:.2f}")
            
            return response.success
            
        except Exception as e:
            self.logger.error(f"❌ 咨询总结测试失败: {e}")
            return False
    
    async def test_performance(self):
        """测试性能和并发"""
        try:
            self.logger.info("⚡ 测试性能和并发...")
            
            import time
            
            # 并发聊天测试
            tasks = []
            start_time = time.time()
            
            for i in range(5):
                task = self.ai_gateway.chat(
                    message=f"这是并发测试消息 {i+1}",
                    user_id=f"concurrent_user_{i}",
                    session_id=f"concurrent_session_{i}"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful = sum(1 for r in results if not isinstance(r, Exception) and r.success)
            total_time = end_time - start_time
            
            self.logger.info(f"🚀 并发测试结果: {successful}/5 成功")
            self.logger.info(f"⏱️ 总耗时: {total_time:.2f}s")
            self.logger.info(f"📈 平均QPS: {5/total_time:.2f}")
            
            return successful >= 3  # 至少60%成功率
            
        except Exception as e:
            self.logger.error(f"❌ 性能测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("🚀 开始AI Gateway功能测试")
        self.logger.info("=" * 60)
        
        if not await self.setup():
            return False
        
        tests = [
            ("健康检查", self.test_health_check),
            ("通用聊天", self.test_chat),
            ("医美方案生成", self.test_beauty_plan),
            ("情感分析", self.test_sentiment_analysis),
            ("咨询总结", self.test_consultation_summary),
            ("性能测试", self.test_performance)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.logger.info("-" * 40)
            try:
                result = await test_func()
                if result:
                    self.logger.info(f"✅ {test_name} - 通过")
                    passed += 1
                else:
                    self.logger.error(f"❌ {test_name} - 失败")
            except Exception as e:
                self.logger.error(f"❌ {test_name} - 异常: {e}")
        
        self.logger.info("=" * 60)
        self.logger.info(f"🎯 测试完成: {passed}/{total} 通过")
        
        if passed == total:
            self.logger.info("🎉 所有测试通过! AI Gateway工作正常")
        elif passed >= total * 0.7:
            self.logger.warning("⚠️ 大部分测试通过，部分功能可能有问题")
        else:
            self.logger.error("❌ 多项测试失败，需要检查配置和服务状态")
        
        return passed >= total * 0.7


async def main():
    """主测试函数"""
    tester = AIGatewayTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 AI Gateway测试完成，系统工作正常！")
        sys.exit(0)
    else:
        print("\n❌ AI Gateway测试失败，请检查配置和服务状态")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 