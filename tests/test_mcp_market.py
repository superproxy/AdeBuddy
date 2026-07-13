"""mcp_market 去重与安装 hint 单元测试（不依赖外网）。"""
import pathlib
import sys

SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from lib.mcp_market import (
    _dedupe,
    _dedupe_key,
    _local_name,
    _norm_url,
    _registry_install_hint,
    _result,
)


def test_norm_url_strips_git_suffix():
    assert _norm_url("https://github.com/a/b.git") == "github.com/a/b"
    assert _norm_url("git@github.com:a/b.git") == "github.com/a/b"


def test_dedupe_prefers_first_by_repo():
    a = _result(source="registry", id="io.x/a", name="a", repo_url="https://github.com/o/r")
    b = _result(source="glama", id="o/r", name="r", repo_url="https://github.com/o/r.git")
    out = _dedupe([a, b])
    assert len(out) == 1
    assert out[0]["source"] == "registry"
    assert _dedupe_key(a) == _dedupe_key(b)


def test_dedupe_by_package_name():
    a = _result(source="registry", id="x", name="x", package_name="@scope/pkg")
    b = _result(source="pulsemcp", id="y", name="y", package_name="@scope/pkg")
    assert len(_dedupe([a, b])) == 1


def test_local_name():
    assert _local_name("io.github.foo/bar-baz") == "bar-baz"
    assert _local_name("@owner/my mcp") == "my-mcp"


def test_registry_install_hint_from_remote():
    hint = _registry_install_hint({
        "remotes": [{"type": "streamable-http", "url": "https://example.com/mcp"}],
    })
    assert hint == {"type": "streamableHttp", "url": "https://example.com/mcp"}


def test_registry_install_hint_from_npm_package():
    hint = _registry_install_hint({
        "packages": [{
            "identifier": "@modelcontextprotocol/server-filesystem",
            "runtimeHint": "npx",
            "runtimeArguments": [{"value": "-y", "type": "positional"}],
            "transport": {"type": "stdio"},
            "environmentVariables": [{"name": "API_KEY", "isRequired": True}],
        }],
    })
    assert hint["command"] == "npx"
    assert "-y" in hint["args"]
    assert "@modelcontextprotocol/server-filesystem" in hint["args"]
    assert hint["env"]["API_KEY"] == "${API_KEY}"


def test_modelscope_owner_name():
    from lib.mcp_market import _modelscope_owner_name
    assert _modelscope_owner_name("@modelcontextprotocol/github") == (
        "modelcontextprotocol",
        "github",
    )
    assert _modelscope_owner_name("YTGX123/search") == ("YTGX123", "search")


def test_modelscope_parses_mcp_server_list(monkeypatch):
    from lib import mcp_market as mm

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "success": True,
                "data": {
                    "mcp_server_list": [
                        {
                            "id": "@modelcontextprotocol/github",
                            "name": "GitHub",
                            "description": "GitHub MCP",
                            "categories": ["version-control"],
                        }
                    ],
                    "total_count": 1,
                },
            }

    monkeypatch.setattr(mm.requests, "put", lambda *a, **k: FakeResp())
    items = mm.ModelScopeClient().search("github", limit=5)
    assert len(items) == 1
    assert items[0]["source"] == "modelscope"
    assert items[0]["owner"] == "modelcontextprotocol"
    assert items[0]["name"] == "GitHub"
