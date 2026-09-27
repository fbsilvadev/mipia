"""End-to-end test: talks to the server through a real MCP client session."""
import asyncio
import json

from mcp import Client

import server


def payload(result):
    if getattr(result, "structured_content", None):
        return result.structured_content
    return json.loads(result.content[0].text)


async def main():
    async with Client(server.mcp) as client:
        tools = {t.name for t in (await client.list_tools()).tools}
        assert tools == {"search_orders", "get_order", "sales_summary"}, tools

        r = await client.call_tool("search_orders", {"status": "paid", "limit": 3})
        data = payload(r)
        rows = data.get("result", data)
        assert 1 <= len(rows) <= 3 and all(x["status"] == "paid" for x in rows), rows

        first = rows[0]["id"]
        o = payload(await client.call_tool("get_order", {"order_id": first}))
        assert o["id"] == first and o["items"], o

        s = payload(await client.call_tool("sales_summary", {"group_by": "month"}))
        srows = s.get("result", s)
        assert len(srows) >= 6 and all("revenue" in x for x in srows), srows

        bad = await client.call_tool("search_orders", {"date_from": "not-a-date"})
        assert bad.is_error, "malformed date must be rejected"
        missing = await client.call_tool("get_order", {"order_id": 999999})
        assert missing.is_error, "unknown order must be an error"
    print("ok: 3 tools, filters, validation and error handling pass")


asyncio.run(main())
