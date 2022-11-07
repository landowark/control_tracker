from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, TIMESTAMP, text, JSON, INTEGER, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class ControlType(Base):
    """
    Base class of a control archetype.

    Args:
        Base (_type_): _description_
    """    
    __tablename__ = '_control_types'
    
    id = Column(INTEGER, primary_key=True) #: primary key   
    name = Column(String(255), unique=True) #: controltype name (e.g. MCS)
    targets = Column(JSON) #: organisms checked for
    instances = relationship("Control", back_populates="controltype") #: control samples created of this type.
    # UniqueConstraint('name', name='uq_controltype_name')


class Control(Base):
    """
    Base class of a control sample.

    Args:
        Base (_type_): _description_
    """    

    __tablename__ = '_control_samples'
    
    id = Column(INTEGER, primary_key=True) #: primary key
    parent_id = Column(INTEGER, ForeignKey("_control_types.id")) #: primary key of control type
    controltype = relationship("ControlType", back_populates="instances") #: reference to parent control type
    name = Column(String(255), unique=True) #: Sample ID
    submitted_date = Column(TIMESTAMP) #: Date submitted to Robotics
    contains = Column(JSON) #: unstructured hashes in contains.tsv for each organism
    matches = Column(JSON) #: unstructured hashes in matches.tsv for each organism
    # UniqueConstraint('name', name='uq_control_name')