from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.services.auth_service import auth_service, get_current_user
from app.services.billing_service import billing_service
from app.services.oss_service import oss_service
from app.services.rag_service import rag_service


router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not auth_service.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def user_payload(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user["id"],
        "email": user["email"],
        "created_at": user["created_at"],
        "is_admin": auth_service.is_admin(user),
    }


def load_user_or_404(user_id: str) -> Dict[str, Any]:
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", summary="Get current admin status")
async def get_admin_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"is_admin": auth_service.is_admin(current_user)}


@router.get("/users", summary="List users with data summaries")
async def list_admin_users(current_user: Dict[str, Any] = Depends(require_admin)):
    users = auth_service.list_users()
    summaries = []
    for user in users:
        notes = rag_service.get_all_notes(limit=0, user_id=user["id"])
        billing = billing_service.get_account_snapshot(user["id"])
        account = billing.get("account") or {}
        summaries.append(
            {
                **user_payload(user),
                "note_count": len(notes),
                "balance": account.get("balance"),
                "total_purchased": account.get("total_purchased"),
                "total_spent": account.get("total_spent"),
            }
        )
    return {"users": summaries}


@router.get("/users/{user_id}", summary="Get one user's stored data")
async def get_admin_user(user_id: str, current_user: Dict[str, Any] = Depends(require_admin)):
    user = load_user_or_404(user_id)
    notes = rag_service.get_all_notes(limit=0, user_id=user_id)
    billing = billing_service.get_account_snapshot(user_id)
    return {
        "user": user_payload(user),
        "notes": notes,
        "billing": billing,
    }


@router.get("/users/{user_id}/export", summary="Export one user's stored data")
async def export_admin_user(user_id: str, current_user: Dict[str, Any] = Depends(require_admin)):
    user = load_user_or_404(user_id)
    notes = rag_service.get_all_notes(limit=0, user_id=user_id)
    billing = billing_service.get_account_snapshot(user_id)
    return {
        "export_version": 1,
        "user": user_payload(user),
        "notes": notes,
        "billing": billing,
    }


@router.patch("/users/{user_id}/credits", summary="Set one user's credit balance")
async def update_admin_user_credits(
    user_id: str,
    balance: int = Body(..., embed=True),
    reason: str = Body("管理员调整额度", embed=True),
    current_user: Dict[str, Any] = Depends(require_admin),
):
    load_user_or_404(user_id)
    reason_text = reason.strip() if reason else "管理员调整额度"
    return billing_service.set_balance(user_id, balance, reason_text)


@router.delete("/users/{user_id}", summary="Delete one user and their stored data")
async def delete_admin_user(user_id: str, current_user: Dict[str, Any] = Depends(require_admin)):
    user = load_user_or_404(user_id)
    if user["id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="Admins cannot delete their own account")

    deleted = {
        "notes": rag_service.delete_user_notes(user_id),
        "files": oss_service.delete_user_files(user_id),
        "billing": billing_service.delete_user_data(user_id),
        "user": 1 if auth_service.delete_user(user_id) else 0,
    }
    return {"status": "deleted", "deleted": deleted}
