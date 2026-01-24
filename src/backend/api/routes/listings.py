"""Listings API routes."""
from fastapi import APIRouter, HTTPException, Query

from ..data import get_all_listings, get_listing_by_id

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("")
async def list_listings(
    include_sold: bool = Query(True, description="Include sold listings"),
    sold_only: bool = Query(False, description="Show only sold listings")
):
    """Get all listings, sorted by created_at descending."""
    return get_all_listings(include_sold=include_sold, sold_only=sold_only)


@router.get("/{listing_id}")
async def get_listing(listing_id: str):
    """Get a single listing by ID."""
    listing = get_listing_by_id(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
