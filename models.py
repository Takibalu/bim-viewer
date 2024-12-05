from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class FileModel(Base):
    __tablename__ = "bim-app-store"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ifc_filename: Mapped[str]
    img_filename: Mapped[str]
    upload_time: Mapped[datetime] = mapped_column(default=datetime.now())