from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .security import get_current_user

router = APIRouter(prefix="/items", tags=["Items (protected)"])


def _get_owned_item(item_id: int, user: models.User, db: Session) -> models.Item:
    item = db.get(models.Item, item_id)
    if item is None or item.owner_id != user.id:
        # 404 for both cases so we don't leak which IDs exist
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
    return item


@router.post("/", response_model=schemas.ItemOut, status_code=201)
def create_item(
    payload: schemas.ItemCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    item = models.Item(**payload.model_dump(), owner_id=user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=list[schemas.ItemOut])
def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    stmt = (
        select(models.Item)
        .where(models.Item.owner_id == user.id)
        .order_by(models.Item.id)
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


@router.get("/{item_id}", response_model=schemas.ItemOut)
def read_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return _get_owned_item(item_id, user, db)


@router.put("/{item_id}", response_model=schemas.ItemOut)
def update_item(
    item_id: int,
    payload: schemas.ItemUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    item = _get_owned_item(item_id, user, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    item = _get_owned_item(item_id, user, db)
    db.delete(item)
    db.commit()
