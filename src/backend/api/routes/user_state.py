"""User state management routes."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/user-state", tags=["user-state"])

STATE_FILE = Path("data/user_state.json")


def load_state() -> dict:
    """Load user state from JSON file."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_state(state: dict) -> None:
    """Save user state to JSON file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


class ListingState(BaseModel):
    favorite: bool = False
    removed: bool = False


@router.get("")
async def get_all_state():
    """Get all user state."""
    return load_state()


@router.get("/{listing_id}")
async def get_listing_state(listing_id: str):
    """Get state for a single listing."""
    state = load_state()
    return state.get(listing_id, {"favorite": False, "removed": False})


@router.put("/{listing_id}")
async def update_listing_state(listing_id: str, listing_state: ListingState):
    """Update state for a single listing."""
    state = load_state()

    # If both are false, remove the entry to keep file clean
    if not listing_state.favorite and not listing_state.removed:
        if listing_id in state:
            del state[listing_id]
    else:
        state[listing_id] = {
            "favorite": listing_state.favorite,
            "removed": listing_state.removed
        }

    save_state(state)
    return state.get(listing_id, {"favorite": False, "removed": False})


@router.post("/{listing_id}/favorite")
async def toggle_favorite(listing_id: str):
    """Toggle favorite status for a listing."""
    state = load_state()
    current = state.get(listing_id, {"favorite": False, "removed": False})
    current["favorite"] = not current.get("favorite", False)

    # If both are false, remove the entry
    if not current["favorite"] and not current.get("removed", False):
        if listing_id in state:
            del state[listing_id]
    else:
        state[listing_id] = current

    save_state(state)
    return state.get(listing_id, {"favorite": False, "removed": False})


@router.post("/{listing_id}/remove")
async def toggle_removed(listing_id: str):
    """Toggle removed status for a listing."""
    state = load_state()
    current = state.get(listing_id, {"favorite": False, "removed": False})
    current["removed"] = not current.get("removed", False)

    # If both are false, remove the entry
    if not current.get("favorite", False) and not current["removed"]:
        if listing_id in state:
            del state[listing_id]
    else:
        state[listing_id] = current

    save_state(state)
    return state.get(listing_id, {"favorite": False, "removed": False})


@router.post("/{listing_id}/restore")
async def restore_listing(listing_id: str):
    """Restore a removed listing (unfavorite and unremove)."""
    state = load_state()
    if listing_id in state:
        del state[listing_id]
    save_state(state)
    return {"favorite": False, "removed": False}
