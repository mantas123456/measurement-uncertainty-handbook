"""MkDocs hook: publish notebooks/ as site pages.

The notebooks live at the repository root, next to docs/, so they can be run and
reviewed on their own. MkDocs only builds files inside docs/, so this hook adds
each notebooks/*.ipynb to the build as notebooks/<name>.ipynb. It runs before
mkdocs-jupyter (higher priority) so that plugin renders them as pages.
"""

from __future__ import annotations

from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import event_priority
from mkdocs.structure.files import File, Files


@event_priority(100)
def on_files(files: Files, config: MkDocsConfig) -> Files:
    root = Path(config.config_file_path).parent
    for notebook in sorted((root / "notebooks").glob("*.ipynb")):
        files.append(
            File(
                f"notebooks/{notebook.name}",
                src_dir=str(root),
                dest_dir=config.site_dir,
                use_directory_urls=config.use_directory_urls,
            )
        )
    return files
