"""
测试数据清理工具
"""
from typing import List
from rich.console import Console

console = Console()


class TestDataCleaner:
    """测试数据清理器"""

    def __init__(self):
        self.tenant_ids: List[str] = []
        self.conversation_ids: List[str] = []
        self.knowledge_ids: List[str] = []
        self.model_config_ids: List[str] = []

    def register_tenant(self, tenant_id: str):
        """注册需要清理的租户"""
        if tenant_id not in self.tenant_ids:
            self.tenant_ids.append(tenant_id)
            console.print(f"[yellow]📝 注册清理: 租户 {tenant_id}[/yellow]")

    def register_conversation(self, conversation_id: str):
        """注册需要清理的对话"""
        if conversation_id not in self.conversation_ids:
            self.conversation_ids.append(conversation_id)
            console.print(f"[yellow]📝 注册清理: 对话 {conversation_id}[/yellow]")

    def register_knowledge(self, knowledge_id: str):
        """注册需要清理的知识条目"""
        if knowledge_id not in self.knowledge_ids:
            self.knowledge_ids.append(knowledge_id)
            console.print(f"[yellow]📝 注册清理: 知识 {knowledge_id}[/yellow]")

    def register_model_config(self, config_id: str):
        """注册需要清理的模型配置"""
        if config_id not in self.model_config_ids:
            self.model_config_ids.append(config_id)
            console.print(f"[yellow]📝 注册清理: 模型配置 {config_id}[/yellow]")

    async def cleanup_all(self, client):
        """清理所有注册的测试数据"""
        console.print("\n[cyan]🧹 开始清理测试数据...[/cyan]")

        # 清理模型配置
        for config_id in self.model_config_ids:
            try:
                await client.delete(f"/models/{config_id}")
                console.print(f"[green]✓ 已删除模型配置: {config_id}[/green]")
            except Exception as e:
                console.print(f"[red]✗ 删除模型配置失败: {str(e)}[/red]")

        # 清理知识条目
        for knowledge_id in self.knowledge_ids:
            try:
                await client.delete(f"/knowledge/{knowledge_id}")
                console.print(f"[green]✓ 已删除知识: {knowledge_id}[/green]")
            except Exception as e:
                console.print(f"[red]✗ 删除知识失败: {str(e)}[/red]")

        # 清理对话
        for conversation_id in self.conversation_ids:
            try:
                # 对话可能需要先关闭再删除
                # 这里假设关闭即可
                await client.put(
                    f"/conversation/{conversation_id}",
                    json={"status": "closed"}
                )
                console.print(f"[green]✓ 已关闭对话: {conversation_id}[/green]")
            except Exception as e:
                console.print(f"[red]✗ 关闭对话失败: {str(e)}[/red]")

        # 注意：租户数据通常不建议在测试中删除，因为可能有外键约束
        # 可以通过管理员接口禁用租户
        if self.tenant_ids:
            console.print(
                f"[yellow]⚠ 需要手动清理 {len(self.tenant_ids)} 个测试租户[/yellow]"
            )

        console.print("[cyan]✓ 清理完成[/cyan]\n")

    def clear_registry(self):
        """清空注册列表"""
        self.tenant_ids.clear()
        self.conversation_ids.clear()
        self.knowledge_ids.clear()
        self.model_config_ids.clear()


# 全局清理器实例
cleaner = TestDataCleaner()
