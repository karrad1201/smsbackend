from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, BigInteger, Numeric, SmallInteger, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.infrastructure.database.base import Base
from sqlalchemy.dialects.postgresql import INET, JSONB

import os
if os.environ["TESTING"] == "1":
    class JSONB(JSON):
        pass

    class INET(String):
        pass


class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255), nullable=False, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    email = Column(String(255), index=True)
    balance = Column(Float, nullable=False, default=0.0)
    language = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))
    discount_rate = Column(Float, nullable=False, default=0.0)
    api_key = Column(String(255), index=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    password_hash = Column(String(255), nullable=False)

    orders = relationship("OrderORM", back_populates="user")
    payments = relationship("PaymentORM", back_populates="user")

class OrderORM(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    number = Column(String(255))
    activ_id = Column(String(255))
    code = Column(String(255))
    service = Column(String(255))
    price = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    country_code = Column(String(10))
    provider_cost_price = Column(Float)
    status_id = Column(SmallInteger, ForeignKey("status_types.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), index=True)
    client_ip = Column(INET)

    # Relationships
    provider = relationship("ProviderORM", back_populates="orders")
    user = relationship("UserORM", back_populates="orders")
    status = relationship("StatusTypeORM", back_populates="orders")

class StatusTypeORM(Base):
    __tablename__ = "status_types"

    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    code = Column(String(30), nullable=False, unique=True)
    name_en = Column(String(50), nullable=False)
    name_ru = Column(String(50))
    description = Column(Text)
    is_final = Column(Boolean, default=False)
    is_error = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())

    orders = relationship("OrderORM", back_populates="status")

class PaymentORM(Base):
    __tablename__ = "payment_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float)
    cash_register = Column(String(255))
    invoice_id = Column(String(255), unique=True)
    status = Column(String(50))
    transaction_hash = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))

    user = relationship("UserORM", back_populates="payments")

class ServiceReferenceORM(Base):
    __tablename__ = "service_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    icon = Column(String(10))
    is_popular = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))
    sort_order = Column(Integer, default=0)

class CountryReferenceORM(Base):
    __tablename__ = "country_reference"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_en = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    iso_code = Column(String(3))
    region = Column(String(100))
    is_popular = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True))
    sort_order = Column(Integer, default=0)


class ProviderRoutesORM(Base):
    __tablename__ = "provider_routes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    provider_id = Column(Integer,ForeignKey("providers.id"), nullable=False)
    country_code = Column(String(10), nullable=False)
    service_code = Column(String(50), nullable=False)
    provider_country_code = Column(String(50), nullable=False)
    provider_service_code = Column(String(100), nullable=False)
    external_product_id = Column(String(100))
    cost_price = Column(Numeric(10, 4), nullable=False, default=0.0)
    client_price = Column(Numeric(10, 4), nullable=False, default=0.0)
    vip_client_price = Column(Numeric(10, 4), nullable=False, default=0.0)
    min_margin_percent = Column(Numeric(5, 2), default=20.0)
    available_count = Column(Integer, nullable=False, default=0)
    max_daily_limit = Column(Integer)
    booking_duration_hours = Column(Integer, default=24)
    priority = Column(SmallInteger, default=100)
    rating_score = Column(Float(24), default=50.0)
    success_rate = Column(Float(24), default=0.0)
    avg_response_time_ms = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    last_success_at = Column(DateTime(timezone=True))
    last_failure_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    last_price_update = Column(DateTime(timezone=True), server_default=func.now())
    provider_specific_data = Column(JSONB, default=dict)
    notes = Column(Text)
    provider = relationship("ProviderORM", back_populates="routes")

class ProviderORM(Base):
    """ORM для существующей таблицы providers"""
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    adapter_class = Column(String(100), nullable=False)
    config = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    display_name = Column(String(255))
    api_url = Column(String(500))
    api_key = Column(String(500))
    priority = Column(Integer, default=100)
    max_requests_per_second = Column(Integer, default=10)
    timeout_seconds = Column(Integer, default=20)
    adapter_type = Column(String(50), default='smslive')
    mapping_type = Column(String(50), default='smsactivate_type')
    max_requests_per_minute = Column(Integer, default=250)

    routes = relationship("ProviderRoutesORM", back_populates="provider")
    balance_snapshots = relationship("ProviderBalanceSnapshotORM", back_populates="provider")
    route_stats = relationship("ProviderRouteStatsORM", back_populates="provider")
    orders = relationship("OrderORM", back_populates="provider")


class ProviderBalanceSnapshotORM(Base):
    __tablename__ = "provider_balance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_datetime = Column(DateTime(timezone=True), server_default=func.now())
    balance = Column(Float, nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"))

    provider = relationship("ProviderORM", back_populates="balance_snapshots")


class ProviderRouteStatsORM(Base):
    __tablename__ = "provider_route_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(Integer,ForeignKey("providers.id"), nullable=False)
    country_code = Column(String(10), nullable=False)
    service_code = Column(String(50), nullable=False)
    rating_score = Column(Float(53), nullable=False, default=50.0)
    success_rate = Column(Float(53), nullable=False, default=0.0)
    consecutive_failures = Column(Integer, nullable=False, default=0)
    disabled_until = Column(DateTime(timezone=True))
    attempts_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    consecutive_no_numbers = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    successful_activations = Column(Integer, default=0)
    failed_activations = Column(Integer, default=0)
    hanging_activations = Column(Integer, default=0)
    manual_rating = Column(Integer)
    disabled_reason = Column(String(255))
    last_success_at = Column(DateTime(timezone=True))
    last_failure_at = Column(DateTime(timezone=True))
    last_no_numbers_at = Column(DateTime(timezone=True))
    last_stats_reset = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    provider = relationship("ProviderORM", back_populates="route_stats")


class SystemConfigORM(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    category = Column(String(50), default='general')
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

__all__ = [
    "UserORM",
    "OrderORM",
    "StatusTypeORM",
    "PaymentORM",
    "ServiceReferenceORM",
    "CountryReferenceORM",
    "ProviderRoutesORM",
    "ProviderORM",
    "ProviderBalanceSnapshotORM",
    "ProviderRouteStatsORM",
    "SystemConfigORM"
]