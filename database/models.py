from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Date, ForeignKey, DateTime


class Base(DeclarativeBase):
    ...


class Admin(Base):
    __tablename__ = "admin"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id_admin: Mapped[str] = mapped_column(String(30), unique= False, nullable=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    surname: Mapped[str] = mapped_column(String(30), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    admin_access: Mapped[bool] = mapped_column(nullable=False)
    main_admin: Mapped[bool] = mapped_column(nullable=False)


class WorkingShift(Base):
    __tablename__ = "working_shift"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id_admin: Mapped[str] = mapped_column(String(30), nullable=False)
    date_time_working_shift: Mapped[Date] = mapped_column(DateTime, nullable=False)
    address: Mapped[str] = mapped_column(String(150), nullable=False)
    description_working_shift: Mapped[str] = mapped_column(Text, nullable=True)
    quantity_workers: Mapped[int] = mapped_column(nullable=False)
    cost_work: Mapped[int] = mapped_column(nullable=False)


# work shift workers
class WorkShiftWorker(Base):
    __tablename__ = "work_shift_worker"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    working_shift_id: Mapped[int] = mapped_column(ForeignKey("working_shift.id", ondelete="CASCADE"), nullable=False)
    tg_id_worker: Mapped[str] = mapped_column(String(30), nullable=False)
    going_on_shift: Mapped[bool] = mapped_column(nullable=False)
    approval_admin: Mapped[bool] = mapped_column(nullable=True)

    working_shift: Mapped["WorkingShift"] = relationship(backref="work_shift_worker")


class Worker(Base):
    __tablename__ = "worker"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id_worker: Mapped[str] = mapped_column(String(30), nullable=False)
    name_worker: Mapped[str] = mapped_column(String(30), nullable=False)
    surname_worker: Mapped[str] = mapped_column(String(30), nullable=False)
    age_worker: Mapped[int] = mapped_column(nullable=False)
    work_experience: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number_worker: Mapped[str] = mapped_column(String(30), nullable=False)
    passport_photo_worker: Mapped[str] = mapped_column(String(150), nullable=False)
    access_worker: Mapped[bool] = mapped_column(nullable=False)

