// API client for listings and user state

// User state management
export async function fetchUserState() {
  const response = await fetch('/api/user-state')
  if (!response.ok) {
    throw new Error('Failed to fetch user state')
  }
  return response.json()
}

export async function toggleFavorite(listingId) {
  const response = await fetch(`/api/user-state/${listingId}/favorite`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('Failed to toggle favorite')
  }
  return response.json()
}

export async function toggleRemoved(listingId) {
  const response = await fetch(`/api/user-state/${listingId}/remove`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('Failed to toggle removed')
  }
  return response.json()
}

export async function restoreListing(listingId) {
  const response = await fetch(`/api/user-state/${listingId}/restore`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error('Failed to restore listing')
  }
  return response.json()
}

// Listings
export async function fetchListings({ includeSold = true, soldOnly = false } = {}) {
  const params = new URLSearchParams({
    include_sold: includeSold,
    sold_only: soldOnly
  })
  const response = await fetch(`/api/listings?${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch listings')
  }
  return response.json()
}

export async function fetchListing(id) {
  const response = await fetch(`/api/listings/${id}`)
  if (!response.ok) {
    throw new Error('Failed to fetch listing')
  }
  return response.json()
}

// Build image URLs from listing folder_path and image_count
export function getImageUrls(listing) {
  if (!listing.folder_path || !listing.image_count) {
    return []
  }
  const base = listing.folder_path.replace('data/scraped/', '')
  return Array.from({ length: listing.image_count }, (_, i) =>
    `/images/${base}/image_${String(i).padStart(3, '0')}.jpg`
  )
}

// Get floor plan image URLs from floor_plan_indices
export function getFloorPlanUrls(listing) {
  if (!listing.folder_path || !listing.image_count) {
    return []
  }

  // Use actual floor_plan_indices if available
  const indices = listing.floor_plan_indices
  if (!indices || !Array.isArray(indices) || indices.length === 0) {
    return []
  }

  const base = listing.folder_path.replace('data/scraped/', '')

  // Filter indices that are within the downloaded image range
  const validIndices = indices.filter(i => i < listing.image_count)

  return validIndices.map(i =>
    `/images/${base}/image_${String(i).padStart(3, '0')}.jpg`
  )
}
