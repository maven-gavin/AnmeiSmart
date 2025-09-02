#!/usr/bin/env python3
"""
初始化顾问相关的测试数据
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy.orm import Session
from app.common.infrastructure.db.base import get_db
from app.consultation.infrastructure.db.consultant import ProjectTemplate, ProjectType, PersonalizedPlan, PlanStatusEnum
from app.common.infrastructure.db.uuid_utils import generate_uuid


def init_project_templates(db: Session):
    """初始化项目模板数据"""
    templates = [
        {
            "name": "全切双眼皮",
            "description": "通过手术方式创建持久自然的双眼皮褶皱",
            "category": "眼部整形",
            "base_cost": 8000.0,
            "duration": "1-2小时",
            "recovery_time": "7-10天",
            "expected_results": "更加明亮有神的眼睛",
            "risks": ["术后肿胀", "疤痕", "感染风险"],
            "suitable_age_min": 18,
            "suitable_age_max": 50,
            "suitable_concerns": ["眼睛单眼皮", "眼部无神"]
        },
        {
            "name": "鼻部整形",
            "description": "通过植入物提升鼻梁，精细化鼻尖",
            "category": "鼻部整形",
            "base_cost": 12000.0,
            "duration": "2-3小时",
            "recovery_time": "10-14天",
            "expected_results": "鼻梁更高挺，鼻尖更加精致",
            "risks": ["感染", "位移", "色素沉着"],
            "suitable_age_min": 18,
            "suitable_age_max": 45,
            "suitable_concerns": ["鼻子不够挺", "鼻尖钝圆"]
        },
        {
            "name": "玻尿酸填充",
            "description": "使用玻尿酸填充面部凹陷区域",
            "category": "面部填充",
            "base_cost": 6000.0,
            "duration": "30分钟",
            "recovery_time": "1-2天",
            "expected_results": "面部更加饱满年轻",
            "risks": ["淤青", "不对称", "过敏反应"],
            "suitable_age_min": 25,
            "suitable_age_max": 60,
            "suitable_concerns": ["面部凹陷", "苹果肌下垂"]
        },
        {
            "name": "下巴轮廓注射",
            "description": "通过注射方式强化下巴轮廓",
            "category": "面部轮廓",
            "base_cost": 8000.0,
            "duration": "45分钟",
            "recovery_time": "3-5天",
            "expected_results": "更加分明的下巴轮廓线",
            "risks": ["淤青", "不对称", "感染"],
            "suitable_age_min": 20,
            "suitable_age_max": 50,
            "suitable_concerns": ["下巴轮廓不明显", "双下巴"]
        },
        {
            "name": "瘦脸针",
            "description": "注射肉毒素放松咬肌，达到瘦脸效果",
            "category": "面部轮廓",
            "base_cost": 3000.0,
            "duration": "20分钟",
            "recovery_time": "0-1天",
            "expected_results": "面部线条更加柔和精致",
            "risks": ["肌肉无力", "不对称", "效果持续时间有限"],
            "suitable_age_min": 20,
            "suitable_age_max": 55,
            "suitable_concerns": ["脸部过宽", "咬肌肥大"]
        }
    ]
    
    for template_data in templates:
        existing = db.query(ProjectTemplate).filter(
            ProjectTemplate.name == template_data["name"]
        ).first()
        
        if not existing:
            template = ProjectTemplate(**template_data)
            db.add(template)
            print(f"创建项目模板: {template_data['name']}")
    
    db.commit()


def init_project_types(db: Session):
    """初始化项目类型数据"""
    project_types = [
        {
            "name": "double-eyelid",
            "label": "双眼皮",
            "description": "通过手术方式改变上眼睑形态，形成美观的双眼皮褶皱",
            "category": "眼部整形",
            "parameters": [
                {
                    "id": "param-001",
                    "name": "foldWidth",
                    "label": "褶皱宽度",
                    "type": "slider",
                    "min": 4,
                    "max": 10,
                    "step": 0.5,
                    "default_value": 6
                },
                {
                    "id": "param-002",
                    "name": "foldShape",
                    "label": "褶皱形状",
                    "type": "select",
                    "options": [
                        {"value": "parallel", "label": "平行型"},
                        {"value": "crescent", "label": "新月型"},
                        {"value": "natural", "label": "自然型"}
                    ],
                    "default_value": "natural"
                }
            ]
        },
        {
            "name": "nose-augmentation",
            "label": "鼻部整形",
            "description": "通过填充或手术方式改善鼻子形态，提升面部立体感",
            "category": "鼻部整形",
            "parameters": [
                {
                    "id": "param-003",
                    "name": "heightIncrease",
                    "label": "鼻梁高度",
                    "type": "slider",
                    "min": 1,
                    "max": 5,
                    "step": 0.5,
                    "default_value": 2.5
                },
                {
                    "id": "param-004",
                    "name": "tipRefinement",
                    "label": "鼻尖精细度",
                    "type": "slider",
                    "min": 1,
                    "max": 5,
                    "step": 0.5,
                    "default_value": 3
                }
            ]
        }
    ]
    
    for type_data in project_types:
        existing = db.query(ProjectType).filter(
            ProjectType.name == type_data["name"]
        ).first()
        
        if not existing:
            project_type = ProjectType(**type_data)
            db.add(project_type)
            print(f"创建项目类型: {type_data['label']}")
    
    db.commit()


def init_sample_plans(db: Session):
    """初始化示例方案数据"""
    # 查找已有的项目模板
    double_eyelid = db.query(ProjectTemplate).filter(
        ProjectTemplate.name == "全切双眼皮"
    ).first()
    nose_surgery = db.query(ProjectTemplate).filter(
        ProjectTemplate.name == "鼻部整形"
    ).first()
    
    if not double_eyelid or not nose_surgery:
        print("警告: 需要先创建项目模板才能创建示例方案")
        return
    
    # 创建示例方案
    sample_plan = {
        "customer_id": "101",  # 假设的客户ID
        "customer_name": "李小姐",
        "consultant_id": "2",  # 假设的顾问ID
        "consultant_name": "李顾问",
        "customer_profile": {
            "age": 28,
            "gender": "female",
            "concerns": ["眼睛单眼皮", "鼻子不够挺"],
            "budget": 20000,
            "expected_results": "希望变得更加精致自然"
        },
        "projects": [
            {
                "id": double_eyelid.id,
                "name": double_eyelid.name,
                "description": double_eyelid.description,
                "cost": double_eyelid.base_cost,
                "duration": double_eyelid.duration,
                "recovery_time": double_eyelid.recovery_time,
                "expected_results": double_eyelid.expected_results,
                "risks": double_eyelid.risks
            },
            {
                "id": nose_surgery.id,
                "name": nose_surgery.name,
                "description": nose_surgery.description,
                "cost": nose_surgery.base_cost,
                "duration": nose_surgery.duration,
                "recovery_time": nose_surgery.recovery_time,
                "expected_results": nose_surgery.expected_results,
                "risks": nose_surgery.risks
            }
        ],
        "total_cost": double_eyelid.base_cost + nose_surgery.base_cost,
        "estimated_timeframe": "2周",
        "status": PlanStatusEnum.SHARED,
        "notes": "客户对方案表示满意，计划下周确认"
    }
    
    existing_plan = db.query(PersonalizedPlan).filter(
        PersonalizedPlan.customer_id == "101",
        PersonalizedPlan.customer_name == "李小姐"
    ).first()
    
    if not existing_plan:
        plan = PersonalizedPlan(**sample_plan)
        db.add(plan)
        db.commit()
        print(f"创建示例方案: {sample_plan['customer_name']}")


def main():
    """主函数"""
    print("开始初始化顾问相关数据...")
    
    # 获取数据库会话
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # 初始化数据
        init_project_templates(db)
        init_project_types(db)
        # 暂时跳过示例方案创建，因为需要真实的顾问和客户ID
        # init_sample_plans(db)
        
        print("数据初始化完成！")
        
    except Exception as e:
        print(f"数据初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main() 