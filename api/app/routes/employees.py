import csv
from io import BytesIO, StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import require_admin
from ..models import Employee
from ..schemas import EmployeeImportResult, EmployeeIn, EmployeeOut

router = APIRouter(prefix="/employees", tags=["employees"], dependencies=[Depends(require_admin)])

@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create(data: EmployeeIn, db: Session = Depends(get_db)):
    if db.get(Employee, data.id): raise HTTPException(409, "Employee id already exists; use restore explicitly if inactive.")
    item = Employee(**data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item
@router.get("", response_model=list[EmployeeOut])
def list_items(include_inactive: bool = False, db: Session = Depends(get_db)):
    q = select(Employee).order_by(Employee.name)
    if not include_inactive: q = q.where(Employee.isActive.is_(True))
    return db.scalars(q).all()
@router.get("/{employee_id}", response_model=EmployeeOut)
def get_one(employee_id: str, db: Session = Depends(get_db)):
    item = db.get(Employee, employee_id)
    if not item: raise HTTPException(404, "Employee not found")
    return item
@router.put("/{employee_id}", response_model=EmployeeOut)
def update(employee_id: str, data: EmployeeIn, db: Session = Depends(get_db)):
    item = db.get(Employee, employee_id)
    if not item: raise HTTPException(404, "Employee not found")
    if not item.isActive: raise HTTPException(409, "Inactive employee must be restored explicitly")
    if data.id != employee_id: raise HTTPException(422, "Employee id cannot be changed")
    for k, v in data.model_dump(exclude={"id"}).items(): setattr(item, k, v)
    db.commit(); db.refresh(item); return item
@router.post("/{employee_id}/deactivate", response_model=EmployeeOut)
def deactivate(employee_id: str, db: Session = Depends(get_db)):
    item = db.get(Employee, employee_id)
    if not item: raise HTTPException(404, "Employee not found")
    item.isActive = False; db.commit(); db.refresh(item); return item
@router.post("/{employee_id}/restore", response_model=EmployeeOut)
def restore(employee_id: str, db: Session = Depends(get_db)):
    item = db.get(Employee, employee_id)
    if not item: raise HTTPException(404, "Employee not found")
    item.isActive = True; db.commit(); db.refresh(item); return item


@router.post("/import", response_model=EmployeeImportResult)
async def import_employees(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Create employees from a CSV or XLSX file without modifying existing records."""
    filename = (file.filename or "").lower()
    if not filename.endswith((".csv", ".xlsx")):
        raise HTTPException(422, "Upload a CSV or XLSX employee file.")
    raw = await file.read()
    try:
        if filename.endswith(".csv"):
            rows = list(csv.DictReader(StringIO(raw.decode("utf-8-sig"))))
        else:
            from openpyxl import load_workbook
            sheet = load_workbook(BytesIO(raw), read_only=True, data_only=True).active
            values = list(sheet.values)
            headers = [str(x).strip() if x is not None else "" for x in values[0]]
            rows = [dict(zip(headers, row)) for row in values[1:] if any(x is not None for x in row)]
    except Exception as exc:
        raise HTTPException(422, "Could not read the uploaded employee file.") from exc

    required = {"id", "name", "email", "department"}
    optional = {"attendanceStatus", "checkInTime", "avatarSeed"}
    headers = set(rows[0]) if rows else set()
    if not rows or not required.issubset(headers):
        raise HTTPException(422, "File must include: id, name, email, department.")
    created = skipped = 0
    errors: list[str] = []
    for number, row in enumerate(rows, start=2):
        # Do not normalize values here: an employee ID is an opaque uploaded
        # string, so values such as TR123 and leading zeroes must survive intact.
        payload = {
            key: "" if row.get(key) is None else str(row.get(key))
            for key in required
        }
        payload.update({
            key: (None if key not in headers or row.get(key) is None else str(row[key]))
            for key in optional
        })
        if not payload["id"]:
            errors.append(f"Row {number}: Employee ID is required."); continue
        if db.get(Employee, payload["id"]):
            skipped += 1; continue
        try:
            # Isolate a bad row so it cannot roll back successfully imported
            # rows that precede it in the same file.
            with db.begin_nested():
                db.add(Employee(**EmployeeIn(**payload).model_dump()))
                db.flush()
            created += 1
        except Exception as exc:
            errors.append(f"Row {number}: {exc}")
    db.commit()
    return EmployeeImportResult(created=created, skipped=skipped, errors=errors)
