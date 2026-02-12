"""
监控与质量评估完整流程测试

测试从对话到监控统计和质量评估的完整流程
"""
import pytest
from test_base import (
    BaseAPITest,
    TenantTestMixin,
    ConversationTestMixin,
    ModelConfigTestMixin,
)
from config import settings


@pytest.mark.integration
class TestMonitoringFlow(
    BaseAPITest,
    TenantTestMixin,
    ConversationTestMixin,
    ModelConfigTestMixin,
):
    """监控与质量评估完整流程测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_monitoring_flow(self):
        """
        测试监控与质量评估完整流程
        
        流程：
        1. 创建租户
        2. 创建多个对话会话
        3. 进行多轮对话
        4. 关闭会话并评价
        5. 查看对话统计
        6. 查看响应时间统计
        7. 查看满意度统计
        8. 查看Dashboard汇总
        9. 对话质量评估
        10. 质量统计汇总
        """
        # ========== 步骤1: 创建租户 ==========
        print("\n[步骤1] 创建租户...")
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])
        print(f"✓ 租户创建成功: {tenant_info['tenant_id']}")

        # 创建模型配置（如果需要）
        if settings.has_llm_config:
            jwt_token = await self.login_tenant(
                tenant_info["email"],
                tenant_info["password"]
            )
            self.client.set_jwt_token(jwt_token)
            
            await self.create_test_model_config(
                provider=settings.llm_provider
            )
            
            # 切回API Key
            self.client.clear_auth()
            self.client.set_api_key(tenant_info["api_key"])

        # ========== 步骤2: 创建多个对话会话 ==========
        print("\n[步骤2] 创建多个对话会话...")
        conversation_ids = []
        
        for i in range(5):
            conv_id = await self.create_test_conversation()
            conversation_ids.append(conv_id)
        
        print(f"✓ 创建了 {len(conversation_ids)} 个对话会话")

        # ========== 步骤3: 进行多轮对话 ==========
        print("\n[步骤3] 进行多轮对话...")
        
        messages = self.data_gen.get_conversation_messages()
        
        for i, conv_id in enumerate(conversation_ids[:3]):
            # 每个对话发送3-5条消息
            msg_count = 3 + (i % 3)
            for j in range(msg_count):
                if settings.has_llm_config and j % 2 == 0:
                    # 使用AI对话
                    await self.client.post(
                        "/ai-chat/chat",
                        json={
                            "conversation_id": conv_id,
                            "message": messages[j % len(messages)],
                            "use_rag": False
                        },
                        timeout=settings.llm_request_timeout
                    )
                else:
                    # 普通消息
                    await self.client.post(
                        f"/conversation/{conv_id}/messages",
                        json={"content": messages[j % len(messages)]}
                    )
        
        print(f"✓ 多轮对话完成")

        # ========== 步骤4: 关闭会话并评价 ==========
        print("\n[步骤4] 关闭会话并评价...")
        
        satisfaction_scores = [5, 4, 5, 3, 4]
        feedbacks = ["非常满意", "满意", "很好", "一般", "还不错"]
        
        for i, conv_id in enumerate(conversation_ids):
            await self.client.put(
                f"/conversation/{conv_id}",
                json={
                    "status": "closed",
                    "satisfaction_score": satisfaction_scores[i],
                    "feedback": feedbacks[i]
                }
            )
        
        print(f"✓ 所有会话已关闭并评价")

        # ========== 步骤5: 查看对话统计 ==========
        print("\n[步骤5] 查看对话统计...")
        conv_stat_resp = await self.client.get("/monitor/conversations")
        conv_stat_data = self.assert_success(conv_stat_resp)
        
        print(f"✓ 对话统计查询成功")
        if "total_conversations" in conv_stat_data:
            print(f"  总对话数: {conv_stat_data.get('total_conversations', 'N/A')}")

        # ========== 步骤6: 查看响应时间统计 ==========
        print("\n[步骤6] 查看响应时间统计...")
        rt_resp = await self.client.get("/monitor/response-time")
        
        if rt_resp.status_code == 200:
            rt_data = self.assert_success(rt_resp)
            print(f"✓ 响应时间统计查询成功")

        # ========== 步骤7: 查看满意度统计 ==========
        print("\n[步骤7] 查看满意度统计...")
        sat_resp = await self.client.get("/monitor/satisfaction")
        
        if sat_resp.status_code == 200:
            sat_data = self.assert_success(sat_resp)
            print(f"✓ 满意度统计查询成功")
            if "average_score" in sat_data:
                print(f"  平均满意度: {sat_data.get('average_score', 'N/A')}")

        # ========== 步骤8: 查看Dashboard汇总 ==========
        print("\n[步骤8] 查看Dashboard汇总...")
        dashboard_resp = await self.client.get("/monitor/dashboard")
        
        if dashboard_resp.status_code == 200:
            dashboard_data = self.assert_success(dashboard_resp)
            print(f"✓ Dashboard汇总查询成功")

        # ========== 步骤9: 对话质量评估 ==========
        print("\n[步骤9] 对话质量评估...")
        
        # 评估第一个对话的质量
        quality_resp = await self.client.get(
            f"/quality/conversation/{conversation_ids[0]}"
        )
        
        if quality_resp.status_code == 200:
            quality_data = self.assert_success(quality_resp)
            print(f"✓ 对话质量评估成功")
            if "score" in quality_data:
                print(f"  质量评分: {quality_data.get('score', 'N/A')}")
            elif "quality_score" in quality_data:
                print(f"  质量评分: {quality_data.get('quality_score', 'N/A')}")

        # ========== 步骤10: 质量统计汇总 ==========
        print("\n[步骤10] 质量统计汇总...")
        quality_summary_resp = await self.client.get("/quality/summary")
        
        if quality_summary_resp.status_code == 200:
            quality_summary_data = self.assert_success(quality_summary_resp)
            print(f"✓ 质量统计汇总查询成功")

        # 质量趋势
        quality_trend_resp = await self.client.get("/quality/trend")
        
        if quality_trend_resp.status_code == 200:
            quality_trend_data = self.assert_success(quality_trend_resp)
            print(f"✓ 质量趋势查询成功")

        print("\n" + "="*50)
        print("✅ 监控与质量评估完整流程测试通过！")
        print("="*50)
