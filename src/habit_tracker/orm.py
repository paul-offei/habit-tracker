"""
SQLAlchemy ORM models.

These classes define the database schema. They are strictly infrastructure
concerns and should never leak into the domain or UI layers.
"""


from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from habit_tracker.database import Base


class HabitORM(Base):
    """Database representation of a Habit."""
    __tablename__ = "habits"

    # Teach mypy that 'id' is a string at runtime
    # id: Mapped[str] = mapped_column(primary_key=True)
    # name: Mapped[str]
    # description: Mapped[str]
    # periodicity: Mapped[str]
    # status: Mapped[str]
    # created_at: Mapped[datetime]

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False, default="")
    periodicity = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    # Establish relationship. If a habit is hard-deleted, delete its completions.
    completions = relationship(
        "CompletionORM", 
        back_populates="habit", 
        cascade="all, delete-orphan"
    )


class CompletionORM(Base):
    """Database representation of a Completion event."""
    __tablename__ = "completions"
    # id: Mapped[str] = mapped_column(primary_key=True)
    # habit_id: Mapped[str]
    # completed_at: Mapped[datetime]

    id = Column(String, primary_key=True, index=True)
    habit_id = Column(String, ForeignKey("habits.id"), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=False)

    # Establish inverse relationship
    habit = relationship("HabitORM", back_populates="completions")