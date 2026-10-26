from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


def normalize_multi_email(value: str | None) -> str:
    if not value:
        return ""
    raw_parts = [part.strip() for part in str(value).split(",")]
    parts = [part for part in raw_parts if part]
    if not parts:
        return ""
    seen_lower = set()
    validated = []
    for addr in parts:
        if not EMAIL_REGEX.match(addr):
            raise ValueError(f"Invalid email address: '{addr}'")
        lower = addr.lower()
        if lower not in seen_lower:
            seen_lower.add(lower)
            validated.append(addr)
    return ",".join(validated)


class ORMModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# EMPLOYEES
# ============================================================

class EmployeeIn(BaseModel):
    id: str
    name: str
    email: str
    department: str
    attendanceStatus: str | None = None
    checkInTime: str | None = None
    avatarSeed: str | None = None


class EmployeeOut(EmployeeIn, ORMModel):
    isActive: bool = True


class EmployeeImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[str] = Field(default_factory=list)


# ============================================================
# CUSTOM CATEGORIES
# ============================================================

class CategoryIn(BaseModel):
    name: str
    iconName: str
    colorHex: str
    displayOrder: int = 0
    email: str = ""
    nameHi: str = ""
    nameJa: str = ""
    employeeCodeRequired: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def validate_category_email(cls, value: str | None) -> str:
        return normalize_multi_email(value)


class CategoryOut(CategoryIn, ORMModel):
    isActive: bool = True


# ============================================================
# CUSTOM PRESETS
# ============================================================

class PresetIn(BaseModel):
    categoryName: str
    textEn: str
    textHi: str
    textJa: str = ""
    displayOrder: int = 0


class PresetOut(PresetIn, ORMModel):
    id: int
    isActive: bool = True


# ============================================================
# INTERACTION LOGS
#
# Contains the actual Android Room fields PLUS the existing
# server-side fields so existing functionality is not removed.
# ============================================================

class InteractionLogIn(BaseModel):
    id: int = 0

    complaintNumber: str = ""

    # Android Room fields
    employeeId: str = ""
    employeeName: str = ""
    employeeDept: str = ""

    queryText: str = ""
    responseText: str = ""

    departmentCategory: str = ""

    timestamp: int

    status: str = "Pending Review"

    # Existing server fields retained
    aiResponse: str = ""
    categoryName: str = ""
    routingInfo: str = ""
    isSynced: bool = False

    @field_validator("complaintNumber")
    @classmethod
    def complaint_number_is_not_whitespace(cls, value: str) -> str:
        return value.strip()


class InteractionLogOut(
    InteractionLogIn,
    ORMModel
):
    pass


class InteractionLogSyncWrapper(BaseModel):
    """Compatible with Android Moshi sync wrapper { "objects": [...] }."""
    objects: list[InteractionLogIn] = Field(default_factory=list)


class InteractionLogStatusUpdate(BaseModel):
    """The web console may update only the operational status of a log with optional remarks."""

    status: str
    remarks: str | None = None

    @field_validator("status")
    @classmethod
    def status_is_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Status must not be blank")
        return value


class GrievanceStatusHistoryOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    id: int
    grievance_id: int
    previous_status: str | None = None
    new_status: str
    changed_by: str | None = None
    changed_at: datetime
    remarks: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class AuthUserOut(BaseModel):
    username: str


# ============================================================
# ADMIN CONFIG
# ============================================================

class AdminConfigIn(BaseModel):
    adminPasscode: str = ""
    centralSyncUrl: str = ""

    commonEmail: str = ""
    hrEmail: str = ""
    itEmail: str = ""
    facilitiesEmail: str = ""
    financeEmail: str = ""
    generalEmail: str = ""

    smtpHost: str = ""
    smtpPort: str = ""

    senderEmail: str = ""
    senderPassword: str = ""
    themeColor: str = "#173D72"
    logoName: str = "aisin"

    @field_validator(
        "commonEmail",
        "hrEmail",
        "itEmail",
        "facilitiesEmail",
        "financeEmail",
        "generalEmail",
        mode="before"
    )
    @classmethod
    def validate_config_emails(cls, value: str | None) -> str:
        return normalize_multi_email(value)


class AdminConfigOut(
    AdminConfigIn,
    ORMModel
):
    id: int


# ============================================================
# FULL SYNC SNAPSHOT
# ============================================================

class SyncSnapshot(BaseModel):
    employees: list[EmployeeOut] = Field(
        default_factory=list
    )

    custom_categories: list[CategoryOut] = Field(
        default_factory=list
    )

    custom_presets: list[PresetOut] = Field(
        default_factory=list
    )

    # IMPORTANT:
    # Android expects admin_config as an array/list.
    # There is normally only one config record, but it is
    # returned as a list to match the Android Moshi sync model.
    admin_config: list[AdminConfigOut] = Field(
        default_factory=list
    )

    interaction_logs: list[InteractionLogOut] = Field(
        default_factory=list
    )

    deleted_complaint_numbers: list[str] = Field(
        default_factory=list
    )

