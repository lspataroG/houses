"""Image serving routes."""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/images", tags=["images"])

SCRAPED_DATA_PATH = Path("data/scraped")


@router.get("/{date}/{folder}/{filename}")
async def serve_image(date: str, folder: str, filename: str):
    """Serve listing images from the scraped data folder."""
    image_path = SCRAPED_DATA_PATH / date / folder / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Ensure we're not serving files outside the scraped folder (path traversal protection)
    try:
        image_path.resolve().relative_to(SCRAPED_DATA_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        image_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000"}  # Cache for 1 year
    )
