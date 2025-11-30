from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..core.database import Base


class MatchLog(Base):
    __tablename__ = "match_logs"

    id = Column(Integer, primary_key=True, index=True)

    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)

    score = Column(Integer, nullable=False)
    strategy = Column(String, nullable=False)  # "naive" or "openai"
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    org = relationship("Organization", backref="match_logs")
    job = relationship("Job", backref="match_logs")
    candidate = relationship("Candidate", backref="match_logs")
