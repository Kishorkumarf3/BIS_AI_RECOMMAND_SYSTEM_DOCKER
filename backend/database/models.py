"""
SQLAlchemy schemas for the BIS Standards Catalog, QCO Alerts,
and the 754-Product Option 2 Simplified Procedure list.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Table,
    func,
)
from sqlalchemy.orm import relationship
from database import Base


# Association table for many-to-many: Standard <-> Normative Reference
standard_references = Table(
    "standard_references",
    Base.metadata,
    Column("standard_id", Integer, ForeignKey("standards.id"), primary_key=True),
    Column("reference_id", Integer, ForeignKey("standards.id"), primary_key=True),
)


class Standard(Base):
    """Core catalog of Indian Standards (IS) codes."""
    __tablename__ = "standards"

    id = Column(Integer, primary_key=True, index=True)
    is_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "IS 1239 Part 1"
    title = Column(Text, nullable=False)
    category = Column(String(100), index=True)          # e.g. "Steel & Steel Products"
    subcategory = Column(String(200))
    scope = Column(Text)                                  # plain-English scope summary
    status = Column(String(30), default="Active")         # Active | Withdrawn | Under Revision
    revision_year = Column(Integer)
    superseded_by = Column(String(50), nullable=True)     # IS code that replaced this one
    date_published = Column(DateTime, nullable=True)
    date_amended = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship to normative references (self-referential M2M)
    normative_refs = relationship(
        "Standard",
        secondary=standard_references,
        primaryjoin=(standard_references.c.standard_id == id),
        secondaryjoin=(standard_references.c.reference_id == id),
        backref="referenced_by",
    )

    # One-to-one flags
    qco_alert = relationship("QCOAlert", uselist=False, back_populates="standard")
    simplified_procedure = relationship("SimplifiedProcedure754", uselist=False, back_populates="standard")


class QCOAlert(Base):
    """Mandatory Quality Control Orders and Compulsory Registration Scheme flags."""
    __tablename__ = "qco_alerts"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=False, index=True)
    qco_notification = Column(String(200))        # e.g. "QCO Order dated 2023-03-14"
    is_mandatory = Column(Boolean, default=False)
    crs_applicable = Column(Boolean, default=False)   # Compulsory Registration Scheme
    crs_registration_no = Column(String(100), nullable=True)
    penalty_non_compliance = Column(Text, nullable=True)
    effective_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    standard = relationship("Standard", back_populates="qco_alert")


class SimplifiedProcedure754(Base):
    """
    754-Product Option 2 Simplified Procedure list.
    Standards on this list are eligible for 30-day fast-track BIS licensing.
    """
    __tablename__ = "simplified_procedure_754"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id"), nullable=False, index=True)
    product_name = Column(String(300), nullable=False)
    option2_eligible = Column(Boolean, default=True)
    fast_track_days = Column(Integer, default=30)
    listed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    standard = relationship("Standard", back_populates="simplified_procedure")
