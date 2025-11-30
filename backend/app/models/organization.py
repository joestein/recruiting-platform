from sqlalchemy import Column, DateTime, Integer, String, func

from ..core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    plan = Column(String, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
