"""
Nucleus models: Organization, Branch, UserOrganization.
Multi-tenancy y multi-branch core.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base
from app.models.enums import BranchType


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False, unique=True)
    industry_type = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    branches = relationship("Branch", back_populates="organization")
    memberships = relationship("UserOrganization", back_populates="organization")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    branch_type = Column(Enum(BranchType), nullable=False, default=BranchType.HQ)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="branches")
    memberships = relationship("UserOrganization", back_populates="branch")


class UserOrganization(Base):
    __tablename__ = "user_organizations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("Usuario", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")
    branch = relationship("Branch", back_populates="memberships")
