"""Seed data for development and demos."""

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.models import AdminUser, City, Commodity, CommodityCategory, User, UserRole


def seed_data() -> None:
    db: Session = SessionLocal()
    try:
        existing_cities = db.query(City).count()
        if existing_cities == 0:
            cities = [
                City(name="Lahore", province="Punjab"),
                City(name="Karachi", province="Sindh"),
                City(name="Islamabad", province="Islamabad Capital Territory"),
                City(name="Multan", province="Punjab"),
                City(name="Bahawalpur", province="Punjab"),
            ]
            db.add_all(cities)

        existing_commodities = db.query(Commodity).count()
        if existing_commodities == 0:
            commodities = [
                Commodity(name="Wheat", category=CommodityCategory.grains, unit="kg"),
                Commodity(name="Rice", category=CommodityCategory.grains, unit="kg"),
                Commodity(name="Sugar", category=CommodityCategory.others, unit="kg"),
                Commodity(name="Tomato", category=CommodityCategory.vegetables, unit="kg"),
                Commodity(name="Onion", category=CommodityCategory.vegetables, unit="kg"),
                Commodity(name="Potato", category=CommodityCategory.vegetables, unit="kg"),
                Commodity(name="Chicken", category=CommodityCategory.meat, unit="kg"),
                Commodity(name="Milk", category=CommodityCategory.dairy, unit="liter"),
            ]
            db.add_all(commodities)

        existing_admin = db.query(AdminUser).filter(AdminUser.email == "admin@pricewatch.pk").first()
        if existing_admin is None:
            admin_user = AdminUser(
                email="admin@pricewatch.pk",
                hashed_password=hash_password("Admin@123456"),
                full_name="Administrator",
                role="super_admin",
                is_active=True,
            )
            db.add(admin_user)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
