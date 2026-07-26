from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ironforgedcore.database import Base
from ironforgedcore.models.decorators import UTCDateTime


class ApiAudit(Base):
    __tablename__ = "api_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )
    request_id: Mapped[str] = mapped_column(
        String(length=36), nullable=False, index=True
    )
    consumer_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_consumers.id"), nullable=True, index=True
    )
    consumer_name: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    consumer_perms: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    required_perm: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    method: Mapped[str] = mapped_column(String(length=8), nullable=False)
    path: Mapped[str] = mapped_column(String(length=512), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    client_ip: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    error: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    query_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    route_template: Mapped[str | None] = mapped_column(
        String(length=256), nullable=True
    )
    response_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_hit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    api_version: Mapped[str | None] = mapped_column(String(length=32), nullable=True)

    def __repr__(self) -> str:
        return (
            f"ApiAudit(id={self.id}, method={self.method!r}, "
            f"path={self.path!r}, status_code={self.status_code})"
        )
