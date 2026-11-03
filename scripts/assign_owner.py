"""Assign documents uploaded before per-user isolation to one user.

Legacy chunks have no owner_id, so after the upgrade nobody can retrieve, list or delete
them. This gives them an owner. It never deletes anything: chunks get an owner_id added
and their files are moved (not copied over) into that user's upload folder.

Usage (from the repo root):
    python -m scripts.assign_owner <user_id>            # dry run: shows what would change
    python -m scripts.assign_owner <user_id> --apply    # performs the migration
Back up data/chroma and uploads/ first.
"""

from __future__ import annotations

import argparse
from collections import Counter

from src.utils.config import settings
from src.vectordb.vector_store import VectorStoreService


def assign_unowned(store: VectorStoreService, owner_id: str, apply: bool = False) -> Counter:
    """Return {document_name: chunk_count} for unowned chunks; assign them when apply=True."""
    collection = store._collection
    found = collection.get(include=["metadatas"])
    ids, metadatas = [], []
    for chunk_id, metadata in zip(found["ids"], found["metadatas"] or [], strict=True):
        if not metadata.get("owner_id"):
            ids.append(chunk_id)
            metadatas.append({**metadata, "owner_id": owner_id})

    summary = Counter(f"{m['document_id']} ({m.get('document_name')})" for m in metadatas)
    if apply and ids:
        collection.update(ids=ids, metadatas=metadatas)
        user_dir = settings.upload_dir / owner_id
        user_dir.mkdir(exist_ok=True)
        for document_id in {m["document_id"] for m in metadatas}:
            for path in settings.upload_dir.glob(f"{document_id}_*"):
                target = user_dir / path.name
                if path.is_file() and not target.exists():
                    path.rename(target)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("user_id")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.user_id not in settings.auth_tokens.values():
        parser.error(f"{args.user_id!r} is not a user in AUTH_TOKENS.")

    summary = assign_unowned(VectorStoreService(), args.user_id, apply=args.apply)
    for document, chunks in summary.items():
        print(f"{document}: {chunks} chunks")
    verb = "Assigned" if args.apply else "Would assign (dry run, add --apply)"
    print(f"{verb} {len(summary)} documents to {args.user_id!r}.")


if __name__ == "__main__":
    main()
