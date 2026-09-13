"""
stripe_transactions.py
Stripe Financial Connections Transactions integration
Handles transaction retrieval and processing
"""

import os
import stripe
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


# ── Data Models ──────────────────────────────────────────────────────────────

class TransactionAmount(BaseModel):
    """Transaction amount details"""
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(..., description="Currency code (e.g., 'usd')")
    
    def to_decimal(self) -> float:
        """Convert cents to decimal"""
        return self.amount / 100


class TransactionStatus(str):
    """Transaction status enum"""
    PENDING = "pending"
    POSTED = "posted"
    FAILED = "failed"


class TransactionNormalized(BaseModel):
    """Normalized Stripe transaction"""
    transaction_id: str = Field(..., alias="id")
    account_id: str
    amount: TransactionAmount
    status: TransactionStatus
    description: str
    posted_at: Optional[datetime] = None
    created_at: datetime
    merchant_name: Optional[str] = None
    merchant_category_code: Optional[str] = None
    reference: Optional[str] = None
    
    class Config:
        populate_by_name = True


# ── Transaction Handlers ─────────────────────────────────────────────────────

def get_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Retrieve a single transaction from Stripe.
    
    Args:
        transaction_id: The Stripe transaction ID
        
    Returns:
        Transaction details dictionary
    """
    try:
        transaction = stripe.financial_connections.Transaction.retrieve(transaction_id)
        return {
            "success": True,
            "transaction": normalize_transaction(transaction)
        }
    except stripe.error.StripeError as e:
        return {
            "success": False,
            "error": str(e),
            "transaction_id": transaction_id
        }


def list_transactions(
    account_id: str,
    limit: int = 10,
    starting_after: Optional[str] = None
) -> Dict[str, Any]:
    """
    List transactions for a Financial Connections Account.
    
    Args:
        account_id: The Financial Connections Account ID
        limit: Number of transactions to retrieve (max 100)
        starting_after: Pagination cursor
        
    Returns:
        List of transactions with pagination info
    """
    try:
        params = {
            "account": account_id,
            "limit": min(limit, 100)
        }
        
        if starting_after:
            params["starting_after"] = starting_after
        
        transactions = stripe.financial_connections.Transaction.list(**params)
        
        normalized = [normalize_transaction(t) for t in transactions.data]
        
        return {
            "success": True,
            "count": len(normalized),
            "transactions": normalized,
            "has_more": transactions.has_more,
            "pagination": {
                "limit": limit,
                "starting_after": starting_after
            }
        }
    except stripe.error.StripeError as e:
        return {
            "success": False,
            "error": str(e),
            "account_id": account_id,
            "transactions": []
        }


def normalize_transaction(transaction: Any) -> Dict[str, Any]:
    """
    Normalize a Stripe transaction object.
    
    Args:
        transaction: Raw Stripe transaction object
        
    Returns:
        Normalized transaction dictionary
    """
    return {
        "transaction_id": transaction.id,
        "account_id": transaction.account,
        "amount": {
            "amount": transaction.amount,
            "currency": transaction.currency.upper() if transaction.currency else "USD"
        },
        "status": transaction.status,
        "description": transaction.description or "",
        "posted_at": datetime.fromtimestamp(transaction.posted_at) if transaction.posted_at else None,
        "created_at": datetime.fromtimestamp(transaction.created),
        "merchant_name": transaction.merchant_name,
        "merchant_category_code": transaction.merchant_category_code,
        "reference": transaction.reference
    }


# ── Webhook Event Handlers ───────────────────────────────────────────────────

def handle_transaction_created(event: Dict[str, Any]) -> bool:
    """Handle financial_connections.transaction.created event"""
    transaction = event.get("data", {}).get("object", {})
    print(f"[Transaction Created] {transaction.get('id')} - {transaction.get('amount')} {transaction.get('currency')}")
    return True


def handle_transaction_updated(event: Dict[str, Any]) -> bool:
    """Handle financial_connections.transaction.updated event"""
    transaction = event.get("data", {}).get("object", {})
    print(f"[Transaction Updated] {transaction.get('id')} - Status: {transaction.get('status')}")
    return True


def handle_transaction_deleted(event: Dict[str, Any]) -> bool:
    """Handle financial_connections.transaction.deleted event"""
    transaction = event.get("data", {}).get("object", {})
    print(f"[Transaction Deleted] {transaction.get('id')}")
    return True


def process_transaction_webhook(event: Dict[str, Any]) -> bool:
    """
    Process transaction-related webhook events.
    
    Args:
        event: Stripe webhook event
        
    Returns:
        True if successfully processed
    """
    event_type = event.get("type", "")
    
    handlers = {
        "financial_connections.transaction.created": handle_transaction_created,
        "financial_connections.transaction.updated": handle_transaction_updated,
        "financial_connections.transaction.deleted": handle_transaction_deleted,
    }
    
    handler = handlers.get(event_type)
    if handler:
        return handler(event)
    
    return False


# ── Export Functions ─────────────────────────────────────────────────────────

__all__ = [
    "get_transaction",
    "list_transactions",
    "normalize_transaction",
    "process_transaction_webhook",
    "TransactionNormalized",
]
