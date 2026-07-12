from __future__ import annotations

import json
from typing import Any

import click

from ..config import BlenderRemoteConfig
from ..constants import DEFAULT_PORT
from ..transport import connect_and_send_command


def _parameter(value: str) -> tuple[str, Any]:
    if "=" not in value:
        raise click.BadParameter("parameters must use key=value")
    key, raw = value.split("=", 1)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = raw
    return key, parsed


@click.command()
@click.argument("operation", default="scene_summary")
@click.option(
    "--param", "parameters", multiple=True, help="Query parameter as key=value"
)
@click.option("--offset", type=int, default=0, show_default=True)
@click.option("--limit", type=int, default=50, show_default=True)
@click.option("--max-bytes", type=int, default=32 * 1024, show_default=True)
@click.option(
    "--result-id", help="Cached result identifier returned by an earlier query"
)
@click.option("--port", type=int, help="Override the configured Blender TCP port")
def query(
    operation: str,
    parameters: tuple[str, ...],
    offset: int,
    limit: int,
    max_bytes: int,
    result_id: str | None,
    port: int | None,
) -> None:
    """Run a bounded, token-efficient query against live Blender."""
    params: dict[str, Any] = {
        "op": operation,
        "offset": offset,
        "limit": limit,
        "max_bytes": max_bytes,
    }
    if result_id:
        params["result_id"] = result_id
    for value in parameters:
        key, parsed = _parameter(value)
        params[key] = parsed

    config = BlenderRemoteConfig()
    tcp_port = port or config.get("mcp_service.default_port") or DEFAULT_PORT
    response = connect_and_send_command("compact_query", params, port=tcp_port)
    if response.get("status") != "success":
        raise click.ClickException(response.get("message", "Compact query failed"))
    click.echo(
        json.dumps(
            response.get("result", {}), ensure_ascii=False, separators=(",", ":")
        )
    )
