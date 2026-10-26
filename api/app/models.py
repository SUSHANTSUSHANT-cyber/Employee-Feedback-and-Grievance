from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    department: Mapped[str] = mapped_column(Text)
    # These values are not available in every import source.  Keep them nullable
    # so an import containing only the core employee fields is valid.
    attendanceStatus: Mapped[str | None] = mapped_column(Text, nullable=True)
    checkInTime: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatarSeed: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Server-side functionality
    isActive: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


class Category(Base):
    __tablename__ = "custom_categories"

    name: Mapped[str] = mapped_column(
        Text,
        primary_key=True
    )

    iconName: Mapped[str] = mapped_column(Text)
    colorHex: Mapped[str] = mapped_column(Text)

    displayOrder: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    email: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    nameHi: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    nameJa: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    # Server-side soft delete / sync functionality
    isActive: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # Android Room v13+ category-level employee verification requirement
    employeeCodeRequired: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


class Preset(Base):
    __tablename__ = "custom_presets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    categoryName: Mapped[str] = mapped_column(
        Text,
        ForeignKey(
            "custom_categories.name",
            ondelete="RESTRICT"
        )
    )

    textEn: Mapped[str] = mapped_column(Text)
    textHi: Mapped[str] = mapped_column(Text)

    textJa: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    displayOrder: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # Server-side soft delete / sync functionality
    isActive: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


class InteractionLog(Base):
    __tablename__ = "interaction_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    complaintNumber: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    # Actual Android Room fields
    employeeId: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    employeeName: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    employeeDept: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    queryText: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    responseText: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    departmentCategory: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    timestamp: Mapped[int] = mapped_column(
        BigInteger
    )

    status: Mapped[str] = mapped_column(
        Text,
        default="Pending Review"
    )

    # Existing server functionality — retained
    aiResponse: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    categoryName: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    routingInfo: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    isSynced: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


class DeletedGrievance(Base):
    __tablename__ = "deleted_grievances"

    complaintNumber: Mapped[str] = mapped_column(
        Text,
        primary_key=True
    )

    deletedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class AdminConfig(Base):
    __tablename__ = "admin_config"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        default=1
    )

    adminPasscode: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    centralSyncUrl: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    commonEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    hrEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    itEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    facilitiesEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    financeEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    generalEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    smtpHost: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    smtpPort: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    senderEmail: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    senderPassword: Mapped[str] = mapped_column(
        Text,
        default=""
    )
    themeColor: Mapped[str] = mapped_column(Text, default="#173D72")
    logoName: Mapped[str] = mapped_column(Text, default="aisin")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    username: Mapped[str] = mapped_column(Text, unique=True)
    passwordHash: Mapped[str] = mapped_column(Text)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    tokenHash: Mapped[str] = mapped_column(Text, primary_key=True)
    adminId: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"))
    expiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GrievanceStatusHistory(Base):
    __tablename__ = "grievance_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interaction_logs.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_status: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
