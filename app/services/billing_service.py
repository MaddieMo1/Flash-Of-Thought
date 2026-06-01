import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.core.config import get_settings


class BillingService:
    DEFAULT_CREDITS = 50
    PLANS = [
        {
            "id": "starter",
            "name": "灵感补给包",
            "credits": 100,
            "amount_cents": 1900,
            "currency": "CNY",
            "description": "适合轻量记录和日常整理",
        },
        {
            "id": "pro",
            "name": "深度思考包",
            "credits": 350,
            "amount_cents": 4900,
            "currency": "CNY",
            "description": "适合频繁分析、问答和周报",
        },
        {
            "id": "team",
            "name": "灵感工坊包",
            "credits": 1000,
            "amount_cents": 12900,
            "currency": "CNY",
            "description": "适合高频使用和团队试用",
        },
    ]

    def __init__(self):
        settings = get_settings()
        self.db_path = Path(settings.USERS_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_credits (
                    user_id TEXT PRIMARY KEY,
                    balance INTEGER NOT NULL,
                    total_purchased INTEGER NOT NULL DEFAULT 0,
                    total_spent INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    description TEXT NOT NULL,
                    reference_id TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    plan_name TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    credits INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    paid_at TEXT
                )
                """
            )
            conn.commit()

    def _ensure_account(self, conn: sqlite3.Connection, user_id: str) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM user_credits WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row:
            return row

        now = self._now()
        conn.execute(
            """
            INSERT INTO user_credits (user_id, balance, total_purchased, total_spent, updated_at)
            VALUES (?, ?, 0, 0, ?)
            """,
            (user_id, self.DEFAULT_CREDITS, now),
        )
        self._record_transaction(
            conn,
            user_id=user_id,
            transaction_type="grant",
            amount=self.DEFAULT_CREDITS,
            balance_after=self.DEFAULT_CREDITS,
            description="新用户赠送额度",
            reference_id=None,
        )
        return conn.execute(
            "SELECT * FROM user_credits WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    def _record_transaction(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        transaction_type: str,
        amount: int,
        balance_after: int,
        description: str,
        reference_id: str | None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO credit_transactions
                (id, user_id, type, amount, balance_after, description, reference_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                user_id,
                transaction_type,
                amount,
                balance_after,
                description,
                reference_id,
                self._now(),
            ),
        )

    def list_plans(self) -> List[Dict[str, Any]]:
        return self.PLANS

    def get_account(self, user_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            account = self._ensure_account(conn, user_id)
            transactions = conn.execute(
                """
                SELECT type, amount, balance_after, description, reference_id, created_at
                FROM credit_transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (user_id,),
            ).fetchall()
            conn.commit()

        return {
            "balance": account["balance"],
            "total_purchased": account["total_purchased"],
            "total_spent": account["total_spent"],
            "updated_at": account["updated_at"],
            "recent_transactions": [dict(row) for row in transactions],
        }

    def spend_credits(self, user_id: str, amount: int, description: str) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("amount must be positive")

        with self._connect() as conn:
            account = self._ensure_account(conn, user_id)
            balance = int(account["balance"])
            if balance < amount:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail={
                        "message": "额度不足，请先充值",
                        "required": amount,
                        "balance": balance,
                    },
                )

            new_balance = balance - amount
            conn.execute(
                """
                UPDATE user_credits
                SET balance = ?, total_spent = total_spent + ?, updated_at = ?
                WHERE user_id = ?
                """,
                (new_balance, amount, self._now(), user_id),
            )
            self._record_transaction(
                conn,
                user_id=user_id,
                transaction_type="spend",
                amount=-amount,
                balance_after=new_balance,
                description=description,
                reference_id=None,
            )
            conn.commit()
            return {"balance": new_balance}

    def ensure_credits(self, user_id: str, amount: int) -> Dict[str, Any]:
        with self._connect() as conn:
            account = self._ensure_account(conn, user_id)
            conn.commit()

        balance = int(account["balance"])
        if balance < amount:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "message": "额度不足，请先充值",
                    "required": amount,
                    "balance": balance,
                },
            )
        return {"balance": balance}

    def create_mock_payment(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        plan = next((item for item in self.PLANS if item["id"] == plan_id), None)
        if not plan:
            raise HTTPException(status_code=404, detail="充值套餐不存在")

        order_id = str(uuid.uuid4())
        now = self._now()
        with self._connect() as conn:
            account = self._ensure_account(conn, user_id)
            new_balance = int(account["balance"]) + int(plan["credits"])
            conn.execute(
                """
                INSERT INTO payment_orders
                    (id, user_id, plan_id, plan_name, amount_cents, currency, credits, status, created_at, paid_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    user_id,
                    plan["id"],
                    plan["name"],
                    plan["amount_cents"],
                    plan["currency"],
                    plan["credits"],
                    "paid",
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                UPDATE user_credits
                SET balance = ?, total_purchased = total_purchased + ?, updated_at = ?
                WHERE user_id = ?
                """,
                (new_balance, plan["credits"], now, user_id),
            )
            self._record_transaction(
                conn,
                user_id=user_id,
                transaction_type="purchase",
                amount=plan["credits"],
                balance_after=new_balance,
                description=f"模拟支付：{plan['name']}",
                reference_id=order_id,
            )
            conn.commit()

        return {
            "order_id": order_id,
            "status": "paid",
            "plan": plan,
            "balance": new_balance,
        }


billing_service = BillingService()
