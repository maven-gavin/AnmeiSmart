#!/usr/bin/env python
from app.db.models.customer import CustomerProfile
from app.db.base import SessionLocal

def main():
    db = SessionLocal()
    try:
        profiles = db.query(CustomerProfile).all()
        print(f'找到 {len(profiles)} 个客户档案')
        for p in profiles:
            print(f'- ID: {p.id}, 客户ID: {p.customer_id}')
    finally:
        db.close()

if __name__ == "__main__":
    main() 