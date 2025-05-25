#!/usr/bin/env python
from app.db.models.user import User
from app.db.models.customer import Customer, CustomerProfile
from app.db.base import SessionLocal

def main():
    db = SessionLocal()
    try:
        # 查找所有顾客角色的用户
        customer_users = db.query(User).filter(User.roles.any(name="customer")).all()
        print(f'找到 {len(customer_users)} 个有顾客角色的用户')
        
        for user in customer_users:
            print(f'用户: {user.username}, ID: {user.id}')
            
            # 检查是否有Customer记录
            customer = db.query(Customer).filter(Customer.user_id == user.id).first()
            if customer:
                print(f'  - 有Customer记录')
                
                # 检查是否有CustomerProfile记录
                profile = db.query(CustomerProfile).filter(CustomerProfile.customer_id == user.id).first()
                if profile:
                    print(f'  - 有CustomerProfile记录，ID: {profile.id}')
                else:
                    print(f'  - 没有CustomerProfile记录')
            else:
                print(f'  - 没有Customer记录')
                
        # 检查可能孤立的CustomerProfile记录
        profiles = db.query(CustomerProfile).all()
        customer_ids = [u.id for u in customer_users]
        
        for profile in profiles:
            if profile.customer_id not in customer_ids:
                print(f'发现孤立的CustomerProfile记录: ID={profile.id}, customer_id={profile.customer_id}')
    finally:
        db.close()

if __name__ == "__main__":
    main() 