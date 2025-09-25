from src.core.domain.entity.provider import Provider
from src.infrastructure.database.schemas import ProviderORM

class ProviderMapper:
    @staticmethod
    def orm_to_entity(orm: ProviderORM) -> Provider:
        return Provider(
            id=orm.id,
            name=orm.name,
            adapter_class=orm.adapter_class,
            config=orm.config,
            is_active=orm.is_active,
            display_name=orm.display_name,
            api_url=orm.api_url,
            priority=orm.priority,
            max_requests_per_second=orm.max_requests_per_second,
            timeout_seconds=orm.timeout_seconds,
            adapter_type=orm.adapter_type,
            mapping_type=orm.mapping_type,
            max_requests_per_minute=orm.max_requests_per_minute,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )