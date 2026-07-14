"""插件市场 API 路由（Flask Blueprint）。

通过 create_marketplace_bp() 创建并注入依赖，挂载到 /api/marketplace/*。

依赖注入的回调函数（来自 config_server.py）：
    resolve_plugin_path(fname) -> Path | None
    load_env_config_file(path) -> dict
    collect_plugin_skill_dirs(cfg) -> list[tuple[str, Path]]
    add_plugin_extras_to_zip(zf, cfg, seen) -> None
    import_plugin_zip(buf, overwrite) -> tuple
"""
import io
import json
import shutil
import zipfile
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

from .storage import load_index, save_index, now_iso


def create_marketplace_bp(
    marketplace_dir: Path,
    resolve_plugin_path,      # callable: fname -> Path | None
    load_env_config_file,     # callable: Path -> dict
    collect_plugin_skill_dirs,  # callable: dict -> list[tuple[str, Path]]
    add_plugin_extras_to_zip,  # callable: ZipFile, dict, set|None -> None
    import_plugin_zip,         # callable: BytesIO, bool -> tuple
    add_dir_to_zip,            # callable: ZipFile, Path, str -> None
):
    """创建市场 Blueprint，注入 config_server 的依赖函数。

    Args:
        marketplace_dir: config/marketplace/ 路径
        其他参数为 config_server.py 中的辅助函数引用
    """
    packages_dir = marketplace_dir / "packages"
    index_file = marketplace_dir / "index.json"

    bp = Blueprint("marketplace", __name__)

    @bp.route("", methods=["GET"])
    def marketplace_list():
        """浏览市场。支持 ?q= 搜索（匹配 name/description/tags）。"""
        q = (request.args.get("q") or "").strip().lower()
        items = load_index(index_file)
        if q:
            filtered = []
            for it in items:
                haystack = " ".join([
                    it.get("name", ""),
                    it.get("description", ""),
                    it.get("author", ""),
                    " ".join(it.get("tags", [])),
                ]).lower()
                if q in haystack:
                    filtered.append(it)
            items = filtered
        return jsonify({"ok": True, "data": items, "total": len(items)})

    @bp.route("/publish", methods=["POST"])
    def marketplace_publish():
        """发布插件到市场。

        Body: {file: "xxx.plugin.yaml", tags: ["dev", "backend"]}
        """
        body = request.get_json(force=True)
        fname = (body.get("file") or "").strip()
        tags = body.get("tags") or []
        if not fname:
            return jsonify({"ok": False, "error": "缺少 file 参数"}), 400
        path = resolve_plugin_path(fname)
        if path is None:
            return jsonify({"ok": False, "error": "插件文件不存在"}), 404

        try:
            cfg = load_env_config_file(path)
            plugin_name = cfg.get("name", path.stem)
            version = cfg.get("version", "1.0.0").strip() or "1.0.0"
            description = cfg.get("description", "").strip()
            author = cfg.get("author", "AdeBuddy").strip() or "AdeBuddy"
            skill_dirs = collect_plugin_skill_dirs(cfg)

            # 生成完整智能体 zip
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(path, arcname=fname)
                for skill_name, skill_dir in skill_dirs:
                    add_dir_to_zip(zf, skill_dir, arc_prefix=f"skills/{skill_name}")
                add_plugin_extras_to_zip(zf, cfg)
            buf.seek(0)

            # 保存到 marketplace/packages/
            safe_name = "".join(c for c in plugin_name if c.isalnum() or c in ("-", "_"))
            pkg_name = f"{safe_name or 'plugin'}-{version}.zip"
            packages_dir.mkdir(parents=True, exist_ok=True)
            pkg_path = packages_dir / pkg_name
            pkg_path.write_bytes(buf.getvalue())
            pkg_size = pkg_path.stat().st_size

            # 更新索引
            items = load_index(index_file)
            item_id = f"{plugin_name}-{version}"
            items = [it for it in items if it.get("id") != item_id]
            entry = {
                "id": item_id,
                "name": plugin_name,
                "version": version,
                "description": description,
                "author": author,
                "file": f"packages/{pkg_name}",
                "size": pkg_size,
                "published_at": now_iso(),
                "tags": tags if isinstance(tags, list) else [],
                "downloads": 0,
            }
            items.append(entry)
            save_index(marketplace_dir, items)

            return jsonify({"ok": True, "data": entry})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @bp.route("/download", methods=["GET"])
    def marketplace_download():
        """下载市场中的插件 zip。Query: id=xxx"""
        item_id = (request.args.get("id") or "").strip()
        if not item_id:
            return jsonify({"ok": False, "error": "缺少 id 参数"}), 400
        items = load_index(index_file)
        entry = next((it for it in items if it.get("id") == item_id), None)
        if not entry:
            return jsonify({"ok": False, "error": "插件不存在"}), 404
        pkg_path = marketplace_dir / entry["file"]
        if not pkg_path.exists():
            return jsonify({"ok": False, "error": "包文件丢失"}), 404
        # 增加下载计数
        entry["downloads"] = entry.get("downloads", 0) + 1
        save_index(marketplace_dir, items)
        buf = io.BytesIO(pkg_path.read_bytes())
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name=Path(entry["file"]).name,
                         mimetype="application/zip")

    @bp.route("/install", methods=["GET"])
    def marketplace_install():
        """从市场安装插件。Query: id=xxx"""
        item_id = (request.args.get("id") or "").strip()
        if not item_id:
            return jsonify({"ok": False, "error": "缺少 id 参数"}), 400
        items = load_index(index_file)
        entry = next((it for it in items if it.get("id") == item_id), None)
        if not entry:
            return jsonify({"ok": False, "error": "插件不存在"}), 404
        pkg_path = marketplace_dir / entry["file"]
        if not pkg_path.exists():
            return jsonify({"ok": False, "error": "包文件丢失"}), 404
        try:
            buf = io.BytesIO(pkg_path.read_bytes())
            return import_plugin_zip(buf, overwrite=True)
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    @bp.route("/remove", methods=["DELETE"])
    def marketplace_remove():
        """从市场移除插件。Query: id=xxx"""
        item_id = (request.args.get("id") or "").strip()
        if not item_id:
            return jsonify({"ok": False, "error": "缺少 id 参数"}), 400
        items = load_index(index_file)
        entry = next((it for it in items if it.get("id") == item_id), None)
        if not entry:
            return jsonify({"ok": False, "error": "插件不存在"}), 404
        # 删除包文件
        pkg_path = marketplace_dir / entry["file"]
        if pkg_path.exists():
            pkg_path.unlink()
        # 从索引移除
        items = [it for it in items if it.get("id") != item_id]
        save_index(marketplace_dir, items)
        return jsonify({"ok": True, "id": item_id})

    return bp
