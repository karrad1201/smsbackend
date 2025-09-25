from src.core.domain.entity.status_type import StatusType
from src.infrastructure.database.schemas import StatusTypeORM

class StatusTypeMapper:
    @staticmethod
    def orm_to_entity(orm: StatusTypeORM) -> StatusType:
        return StatusType(
            id=orm.id,
            code=orm.code,
            name_en=orm.name_en,
            name_ru=orm.name_ru,
            description=orm.description,
            is_final=orm.is_final,
            is_error=orm.is_error
        )