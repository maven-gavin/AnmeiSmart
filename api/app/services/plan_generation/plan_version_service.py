"""
方案版本管理服务 - 负责方案版本的管理和控制
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models.plan_generation import PlanDraft
from app.schemas.plan_generation import (
    PlanDraftInfo,
    PlanVersionCompareResponse,
    PlanDraftStatus
)

logger = logging.getLogger(__name__)


class PlanVersionService:
    """方案版本管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_next_version(self, session_id: str) -> int:
        """获取下一个版本号"""
        max_version = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).first()
        
        if max_version:
            return max_version.version + 1
        else:
            return 1
    
    def get_version_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[PlanDraftInfo]:
        """获取版本历史"""
        logger.info(f"获取版本历史: session_id={session_id}")
        
        drafts = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).limit(limit).all()
        
        return [PlanDraftInfo.from_model(draft) for draft in drafts]
    
    def get_version_by_number(
        self,
        session_id: str,
        version: int
    ) -> Optional[PlanDraftInfo]:
        """根据版本号获取版本"""
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.version == version
        ).first()
        
        if not draft:
            return None
        
        return PlanDraftInfo.from_model(draft)
    
    def get_latest_version(self, session_id: str) -> Optional[PlanDraftInfo]:
        """获取最新版本"""
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).first()
        
        if not draft:
            return None
        
        return PlanDraftInfo.from_model(draft)
    
    def compare_versions(
        self,
        session_id: str,
        version1: int,
        version2: int
    ) -> PlanVersionCompareResponse:
        """比较两个版本"""
        logger.info(f"比较版本: {version1} vs {version2}")
        
        draft1 = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.version == version1
        ).first()
        
        draft2 = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.version == version2
        ).first()
        
        if not draft1 or not draft2:
            raise ValueError("版本不存在")
        
        differences = self._calculate_differences(draft1.content, draft2.content)
        improvement_summary = self._generate_improvement_summary(differences)
        
        return PlanVersionCompareResponse(
            draft_id=draft2.id,
            current_version=version2,
            compare_version=version1,
            differences=differences,
            improvement_summary=improvement_summary
        )
    
    def _calculate_differences(
        self,
        content1: Dict[str, Any],
        content2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """计算版本差异"""
        differences = []
        
        # 比较基础信息
        if content1.get("basic_info") != content2.get("basic_info"):
            differences.append({
                "section": "basic_info",
                "type": "modified",
                "field": "基础信息",
                "old_value": content1.get("basic_info"),
                "new_value": content2.get("basic_info"),
                "description": "基础信息已修改"
            })
        
        # 比较治疗计划
        if content1.get("treatment_plan") != content2.get("treatment_plan"):
            differences.append({
                "section": "treatment_plan",
                "type": "modified",
                "field": "治疗计划",
                "old_value": content1.get("treatment_plan"),
                "new_value": content2.get("treatment_plan"),
                "description": "治疗计划已调整"
            })
        
        # 比较费用明细
        cost1 = content1.get("cost_breakdown", {}).get("total_cost", 0)
        cost2 = content2.get("cost_breakdown", {}).get("total_cost", 0)
        
        if cost1 != cost2:
            differences.append({
                "section": "cost_breakdown",
                "type": "modified",
                "field": "总费用",
                "old_value": cost1,
                "new_value": cost2,
                "description": f"总费用从 {cost1} 调整为 {cost2}"
            })
        
        # 比较时间线
        if content1.get("timeline") != content2.get("timeline"):
            differences.append({
                "section": "timeline",
                "type": "modified",
                "field": "时间线",
                "old_value": content1.get("timeline"),
                "new_value": content2.get("timeline"),
                "description": "时间线已调整"
            })
        
        # 比较风险和注意事项
        if content1.get("risks_and_precautions") != content2.get("risks_and_precautions"):
            differences.append({
                "section": "risks_and_precautions",
                "type": "modified",
                "field": "风险和注意事项",
                "old_value": content1.get("risks_and_precautions"),
                "new_value": content2.get("risks_and_precautions"),
                "description": "风险和注意事项已更新"
            })
        
        return differences
    
    def _generate_improvement_summary(self, differences: List[Dict[str, Any]]) -> str:
        """生成改进摘要"""
        if not differences:
            return "版本之间没有差异"
        
        summary_parts = []
        
        for diff in differences:
            summary_parts.append(diff["description"])
        
        return "；".join(summary_parts)
    
    def rollback_to_version(
        self,
        session_id: str,
        target_version: int,
        operator_id: str
    ) -> PlanDraftInfo:
        """回滚到指定版本"""
        logger.info(f"回滚到版本: session_id={session_id}, version={target_version}")
        
        # 获取目标版本
        target_draft = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.version == target_version
        ).first()
        
        if not target_draft:
            raise ValueError(f"目标版本不存在: {target_version}")
        
        # 创建新版本（基于目标版本的内容）
        new_version = self.get_next_version(session_id)
        
        rollback_draft = PlanDraft(
            session_id=session_id,
            version=new_version,
            parent_version=target_version,
            content=target_draft.content,
            status=PlanDraftStatus.draft,
            generation_info={
                "generator": "rollback",
                "rollback_from": target_version,
                "operator_id": operator_id,
                "rollback_time": datetime.now().isoformat()
            }
        )
        
        self.db.add(rollback_draft)
        self.db.commit()
        self.db.refresh(rollback_draft)
        
        logger.info(f"回滚完成: new_version={new_version}")
        return PlanDraftInfo.from_model(rollback_draft)
    
    def archive_version(
        self,
        draft_id: str,
        operator_id: str
    ) -> PlanDraftInfo:
        """归档版本"""
        logger.info(f"归档版本: draft_id={draft_id}")
        
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.id == draft_id
        ).first()
        
        if not draft:
            raise ValueError(f"草稿不存在: {draft_id}")
        
        draft.status = PlanDraftStatus.archived
        draft.updated_at = datetime.now()
        
        # 更新归档信息
        if not draft.generation_info:
            draft.generation_info = {}
        
        draft.generation_info.update({
            "archived_by": operator_id,
            "archived_at": datetime.now().isoformat()
        })
        
        self.db.commit()
        self.db.refresh(draft)
        
        logger.info(f"版本归档完成: {draft_id}")
        return PlanDraftInfo.from_model(draft)
    
    def get_version_tree(self, session_id: str) -> Dict[str, Any]:
        """获取版本树结构"""
        logger.info(f"获取版本树: session_id={session_id}")
        
        # 获取所有版本
        drafts = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.asc()).all()
        
        # 构建版本树
        version_tree = {
            "session_id": session_id,
            "versions": []
        }
        
        for draft in drafts:
            version_info = {
                "id": draft.id,
                "version": draft.version,
                "parent_version": draft.parent_version,
                "status": draft.status.value,
                "created_at": draft.created_at.isoformat() if draft.created_at else None,
                "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
                "generation_info": draft.generation_info or {}
            }
            
            version_tree["versions"].append(version_info)
        
        return version_tree
    
    def get_draft_versions(self, session_id: str) -> List[PlanDraftInfo]:
        """获取草稿的所有版本"""
        logger.info(f"获取草稿版本: session_id={session_id}")
        
        drafts = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).all()
        
        return [PlanDraftInfo.from_model(draft) for draft in drafts]
    
    def get_version_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取版本统计信息"""
        logger.info(f"获取版本统计: session_id={session_id}")
        
        # 统计各种状态的版本数量
        total_versions = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).count()
        
        draft_versions = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.status == PlanDraftStatus.draft
        ).count()
        
        approved_versions = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.status == PlanDraftStatus.approved
        ).count()
        
        archived_versions = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id,
            PlanDraft.status == PlanDraftStatus.archived
        ).count()
        
        # 获取最新版本
        latest_version = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).first()
        
        return {
            "session_id": session_id,
            "total_versions": total_versions,
            "draft_versions": draft_versions,
            "approved_versions": approved_versions,
            "archived_versions": archived_versions,
            "latest_version": latest_version.version if latest_version else None,
            "latest_version_status": latest_version.status.value if latest_version else None
        } 