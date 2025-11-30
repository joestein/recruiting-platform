from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    full_name = Column(String, nullable=False)
    headline = Column(String, nullable=True)
    location = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    current_title = Column(String, nullable=True)
    current_company = Column(String, nullable=True)

    linkedin_url = Column(String, nullable=True)
    github_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    org = relationship("Organization", backref="candidates")
    user = relationship("User", backref="candidate_profile", uselist=False)
    applications = relationship("Application", back_populates="candidate")
