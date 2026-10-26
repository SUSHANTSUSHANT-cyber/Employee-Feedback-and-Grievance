from datetime import datetime, timedelta, timezone
import time

import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import require_admin
from ..models import AdminUser, DeletedGrievance, GrievanceStatusHistory, InteractionLog
from ..schemas import (
    GrievanceStatusHistoryOut,
    InteractionLogIn,
    InteractionLogOut,
    InteractionLogStatusUpdate,
    InteractionLogSyncWrapper,
)


router = APIRouter(
    prefix="/interaction-logs",
    tags=["interaction logs"]
)


def apply(item: InteractionLog, data: InteractionLogIn, *, from_sync: bool = False):
    values = data.model_dump(
        exclude_unset=True,
        exclude={"id"}
    )

    for key, value in values.items():
        # The admin console owns a workflow status once it has moved beyond the
        # Android default.  A routine device retry must not reset it.
        if from_sync and key == "status" and value == "Pending Review" and item.status != value:
            continue
        setattr(item, key, value)


@router.post(
    "",
    response_model=InteractionLogOut,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: InteractionLogIn,
    db: Session = Depends(get_db)
):
    values = data.model_dump(exclude={"id"})

    if not values.get("timestamp"):
        values["timestamp"] = int(time.time() * 1000)

    if values.get("complaintNumber"):
        is_deleted = db.scalar(
            select(DeletedGrievance.complaintNumber).where(
                DeletedGrievance.complaintNumber == values["complaintNumber"]
            )
        )
        if is_deleted is not None:
            raise HTTPException(409, "Complaint number was deleted and cannot be reused")
        duplicate = db.scalar(select(InteractionLog.id).where(InteractionLog.complaintNumber == values["complaintNumber"]))
        if duplicate is not None:
            raise HTTPException(409, "Complaint number already exists")
    item = InteractionLog(**values)

    db.add(item)
    db.flush()

    # Record initial registration event
    history = GrievanceStatusHistory(
        grievance_id=item.id,
        previous_status=None,
        new_status=item.status or "Pending Review",
        changed_by="system",
        remarks="Initial registration",
    )
    db.add(history)
    db.commit()
    db.refresh(item)

    return item


@router.post(
    "/bulk",
    response_model=list[InteractionLogOut]
)
@router.post(
    "/upsert",
    response_model=list[InteractionLogOut]
)
def bulk_upsert(
    items: list[InteractionLogIn] | InteractionLogSyncWrapper,
    db: Session = Depends(get_db)
):
    if isinstance(items, InteractionLogSyncWrapper):
        items = items.objects

    result = []

    try:
        # Pre-fetch tombstones for incoming complaint numbers to prevent resurrected grievances
        complaint_numbers = [d.complaintNumber for d in items if d.complaintNumber]
        deleted_set = (
            set(
                db.scalars(
                    select(DeletedGrievance.complaintNumber).where(
                        DeletedGrievance.complaintNumber.in_(complaint_numbers)
                    )
                ).all()
            )
            if complaint_numbers
            else set()
        )

        for data in items:

            # A Room row ID is local to an Android installation and cannot be
            # trusted as the primary identity of a central record.  A non-empty
            # complaint number is the database's existing stable business key.
            complaint_number = data.complaintNumber

            # Stale client sync must NEVER restore an intentionally deleted grievance.
            if complaint_number and complaint_number in deleted_set:
                continue

            item = (
                db.scalar(
                    select(InteractionLog).where(
                        InteractionLog.complaintNumber == complaint_number
                    )
                )
                if complaint_number
                else None
            )

            # Rows without a complaint number have no business key. Retain the
            # legacy server-ID fallback so a snapshot downloaded from this server
            # can be uploaded again without creating a new row.
            if item is None and not complaint_number and data.id and data.id != 0:
                item = db.get(InteractionLog, data.id)

            if item:
                old_status = item.status
                apply(item, data, from_sync=True)
                if item.status != old_status:
                    history = GrievanceStatusHistory(
                        grievance_id=item.id,
                        previous_status=old_status,
                        new_status=item.status,
                        changed_by="device_sync",
                        remarks="Status updated via synchronization",
                    )
                    db.add(history)

            else:
                values = data.model_dump(exclude={"id"})

                if not values.get("timestamp"):
                    values["timestamp"] = int(
                        time.time() * 1000
                    )

                item = InteractionLog(**values)
                # The pre-read above provides updates; the savepoint also makes
                # concurrent duplicate sync requests idempotent under the partial
                # unique index.  In that race, use the just-created canonical row.
                try:
                    with db.begin_nested():
                        db.add(item)
                        db.flush()
                        history = GrievanceStatusHistory(
                            grievance_id=item.id,
                            previous_status=None,
                            new_status=item.status or "Pending Review",
                            changed_by="device_sync",
                            remarks="Initial registration via synchronization",
                        )
                        db.add(history)
                except IntegrityError:
                    if not complaint_number:
                        raise
                    item = db.scalar(
                        select(InteractionLog).where(
                            InteractionLog.complaintNumber == complaint_number
                        )
                    )
                    if item is None:
                        raise
                    old_status = item.status
                    apply(item, data, from_sync=True)
                    if item.status != old_status:
                        history = GrievanceStatusHistory(
                            grievance_id=item.id,
                            previous_status=old_status,
                            new_status=item.status,
                            changed_by="device_sync",
                            remarks="Status updated via synchronization",
                        )
                        db.add(history)

            result.append(item)

        db.commit()

        for item in result:
            db.refresh(item)

        return result

    except Exception:
        db.rollback()
        raise


compat_router = APIRouter(
    prefix="/interaction_logs",
    tags=["interaction logs compat"]
)
compat_router.add_api_route(
    "/bulk",
    bulk_upsert,
    methods=["POST"],
    response_model=list[InteractionLogOut]
)
compat_router.add_api_route(
    "/upsert",
    bulk_upsert,
    methods=["POST"],
    response_model=list[InteractionLogOut]
)



@router.get(
    "",
    response_model=list[InteractionLogOut]
)
def list_items(
    employee_id: str | None = None,
    category_name: str | None = None,
    status_value: str | None = None,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    query = select(InteractionLog).order_by(
        InteractionLog.timestamp.desc()
    )

    if employee_id:
        query = query.where(
            InteractionLog.employeeId == employee_id
        )

    if category_name:
        query = query.where(
            InteractionLog.departmentCategory == category_name
        )

    if status_value:
        query = query.where(
            InteractionLog.status == status_value
        )

    return db.scalars(query).all()


@router.get(
    "/{log_id:int}",
    response_model=InteractionLogOut
)
def get_one(
    log_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    item = db.get(
        InteractionLog,
        log_id
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Interaction log not found"
        )

    return item


@router.put(
    "/{log_id:int}",
    response_model=InteractionLogOut
)
def update_status(
    log_id: int,
    data: InteractionLogStatusUpdate,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(require_admin),
):
    """Safely update the grievance workflow state and record auditable status history."""
    item = db.get(InteractionLog, log_id)

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Interaction log not found"
        )

    old_status = item.status
    new_status = data.status.strip()

    # Record history only if status actually changed
    if old_status != new_status:
        item.status = new_status
        history = GrievanceStatusHistory(
            grievance_id=item.id,
            previous_status=old_status,
            new_status=new_status,
            changed_by=admin.username,
            remarks=data.remarks.strip() if data.remarks and data.remarks.strip() else None,
        )
        db.add(history)
        db.commit()
        db.refresh(item)

    return item


@router.get(
    "/{log_id:int}/history",
    response_model=list[GrievanceStatusHistoryOut]
)
def get_history(
    log_id: int,
    db: Session = Depends(get_db),
    _: AdminUser = Depends(require_admin),
):
    """Retrieve complete chronological status history for a specific grievance."""
    item = db.get(InteractionLog, log_id)
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Interaction log not found"
        )

    history = db.scalars(
        select(GrievanceStatusHistory)
        .where(GrievanceStatusHistory.grievance_id == log_id)
        .order_by(GrievanceStatusHistory.changed_at.asc(), GrievanceStatusHistory.id.asc())
    ).all()

    return history


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db), _: object = Depends(require_admin)):
    logs = db.scalars(select(InteractionLog).order_by(InteractionLog.timestamp.desc())).all()
    output = StringIO()
    fields = ["id", "complaintNumber", "employeeId", "employeeName", "employeeDept", "queryText", "responseText", "aiResponse", "departmentCategory", "categoryName", "routingInfo", "status", "timestamp"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for item in logs:
        writer.writerow({field: getattr(item, field) for field in fields})
    return Response(output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=grievances.csv"})


@router.delete(
    "/{log_id:int}",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    include_in_schema=False
)
def delete_one():
    """Grievance deletion is permanently disabled."""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Grievance deletion has been permanently disabled"
    )


@router.post(
    "/delete-bulk",
    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
    include_in_schema=False
)
def delete_bulk():
    """Grievance bulk deletion is permanently disabled."""
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Grievance deletion has been permanently disabled"
    )


@router.post(
    "/purge-tombstones",
    status_code=status.HTTP_200_OK
)
def purge_tombstones(
    older_than_days: int = 90,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Compaction policy for tombstones older than the retention threshold."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    result = db.execute(
        delete(DeletedGrievance).where(DeletedGrievance.deletedAt < cutoff)
    )
    db.commit()
    return {
        "purged": result.rowcount,
        "retentionDays": older_than_days
    }

