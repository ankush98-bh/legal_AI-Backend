from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base
from .group_model import Group  # Needed for relationship reference

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100))
    username = Column(String(100), unique=True, nullable=False)
    mail_id = Column(String(255), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    role = Column(String(100), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"), nullable=True)
    is_staff = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("Group", back_populates="users")