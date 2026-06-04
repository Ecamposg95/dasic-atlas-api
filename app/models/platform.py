from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.db import Base


class PlatformConfig(Base):
    __tablename__ = "platform_config"

    clave = Column(String(60), primary_key=True)
    valor = Column(Text, nullable=True)
    actualizado_por_id = Column(Integer, nullable=True)
    actualizado_en = Column(DateTime(timezone=True), server_default=func.now())
