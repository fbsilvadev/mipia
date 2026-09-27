"""Orders MCP server: a read-only demo that lets an AI assistant query a SQLite orders database.

Run:  python server.py            (stdio, for Claude Desktop / Claude Code / Cursor)
Test: python test_server.py
"""
import sqlite3
from datetime import date
from pathlib import Path

from mcp.server.mcpserver import MCPServer

DB_PATH = Path(__file__).with_name("orders.db")

mcp = MCPServer(
    "orders-mcp",
    instructions=(
        "Read-only access to the sample orders database. "
        "Use search_orders to find orders, get_order for one order with its items, "
        "and sales_summary for revenue by month or status."
    ),
)


def _connect() -> sqlite3.Connection:
    # Read-only connection: the assistant can never change data.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def search_orders(
    customer: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search orders. Dates use YYYY-MM-DD. Status is one of: paid, shipped, cancelled, refunded."""
    limit = max(1, min(limit, 100))
    for value in (date_from, date_to):
        if value:
            date.fromisoformat(value)  # rejects malformed dates before they reach SQL
    sql = "SELECT id, customer, status, order_date, total FROM orders WHERE 1=1"
    args: list = []
    if customer:
        sql += " AND customer LIKE ?"
        args.append(f"%{customer}%")
    if status:
        sql += " AND status = ?"
        args.append(status.lower())
    if date_from:
        sql += " AND order_date >= ?"
        args.append(date_from)
    if date_to:
        sql += " AND order_date <= ?"
        args.append(date_to)
    sql += " ORDER BY order_date DESC, id DESC LIMIT ?"
    args.append(limit)
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql, args)]


@mcp.tool()
def get_order(order_id: int) -> dict:
    """Return one order with its line items."""
    with _connect() as conn:
        order = conn.execute(
            "SELECT id, customer, status, order_date, total FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()
        if order is None:
            raise ValueError(f"Order {order_id} not found")
        items = conn.execute(
            "SELECT sku, name, quantity, unit_price FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
    return {**dict(order), "items": [dict(i) for i in items]}


@mcp.tool()
def sales_summary(group_by: str = "month") -> list[dict]:
    """Revenue and order count grouped by 'month' or 'status'. Cancelled and refunded orders are excluded from revenue."""
    if group_by not in ("month", "status"):
        raise ValueError("group_by must be 'month' or 'status'")
    key = "substr(order_date, 1, 7)" if group_by == "month" else "status"
    sql = f"""
        SELECT {key} AS {group_by}, COUNT(*) AS orders,
               ROUND(SUM(CASE WHEN status IN ('paid','shipped') THEN total ELSE 0 END), 2) AS revenue
        FROM orders GROUP BY {key} ORDER BY {key}
    """
    with _connect() as conn:
        return [dict(r) for r in conn.execute(sql)]


if __name__ == "__main__":
    mcp.run()
