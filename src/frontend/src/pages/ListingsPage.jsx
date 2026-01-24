import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import Header from '../components/Header'
import FilterToggle from '../components/FilterToggle'
import ListingCard from '../components/ListingCard'
import MapView from '../components/MapView'
import { fetchListings, fetchUserState, toggleFavorite, toggleRemoved, restoreListing } from '../api/listings'

export default function ListingsPage() {
  const [listings, setListings] = useState([])
  const [userState, setUserState] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('active') // 'all', 'active', 'sold'
  const [viewFilter, setViewFilter] = useState('main') // 'main', 'favorites', 'removed'
  const [activeListingId, setActiveListingId] = useState(null)
  const listingRefs = useRef({})

  useEffect(() => {
    loadListings()
  }, [filter, viewFilter])

  useEffect(() => {
    loadUserState()
  }, [])

  const loadListings = async () => {
    setLoading(true)
    setError(null)
    try {
      // For favorites/removed views, always fetch all listings
      // For main view, apply the sold/active filter
      const params = viewFilter === 'main'
        ? {
            includeSold: filter !== 'active',
            soldOnly: filter === 'sold'
          }
        : {
            includeSold: true,
            soldOnly: false
          }
      const data = await fetchListings(params)
      setListings(data)
      // Set first listing as active initially
      if (data.length > 0) {
        setActiveListingId(data[0].id)
      }
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  const loadUserState = async () => {
    try {
      const state = await fetchUserState()
      setUserState(state)
    } catch (err) {
      console.error('Failed to load user state:', err)
    }
  }

  // Filter listings based on viewFilter
  const filteredListings = useMemo(() => {
    return listings.filter(listing => {
      const state = userState[listing.id] || {}
      if (viewFilter === 'favorites') {
        return state.favorite === true
      }
      if (viewFilter === 'removed') {
        return state.removed === true
      }
      // 'main' view: show non-removed listings
      return state.removed !== true
    })
  }, [listings, userState, viewFilter])

  // Handlers for favorite/remove/restore
  const handleToggleFavorite = useCallback(async (listingId) => {
    try {
      const newState = await toggleFavorite(listingId)
      setUserState(prev => ({
        ...prev,
        [listingId]: newState
      }))
    } catch (err) {
      console.error('Failed to toggle favorite:', err)
    }
  }, [])

  const handleToggleRemoved = useCallback(async (listingId) => {
    try {
      const newState = await toggleRemoved(listingId)
      setUserState(prev => ({
        ...prev,
        [listingId]: newState
      }))
    } catch (err) {
      console.error('Failed to toggle removed:', err)
    }
  }, [])

  const handleRestore = useCallback(async (listingId) => {
    try {
      const newState = await restoreListing(listingId)
      setUserState(prev => ({
        ...prev,
        [listingId]: newState
      }))
    } catch (err) {
      console.error('Failed to restore listing:', err)
    }
  }, [])

  // Intersection Observer to track visible listings
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        // Find the most visible entry
        const visibleEntries = entries.filter(entry => entry.isIntersecting)
        if (visibleEntries.length > 0) {
          // Get the one with highest intersection ratio
          const mostVisible = visibleEntries.reduce((prev, current) =>
            current.intersectionRatio > prev.intersectionRatio ? current : prev
          )
          setActiveListingId(mostVisible.target.dataset.listingId)
        }
      },
      {
        root: null,
        rootMargin: '-20% 0px -60% 0px', // Trigger when listing is in upper-middle of viewport
        threshold: [0, 0.25, 0.5, 0.75, 1]
      }
    )

    // Observe all listing elements
    Object.values(listingRefs.current).forEach(ref => {
      if (ref) observer.observe(ref)
    })

    return () => observer.disconnect()
  }, [filteredListings])

  // Scroll to listing when clicking on map marker
  const scrollToListing = useCallback((listingId) => {
    const element = listingRefs.current[listingId]
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      setActiveListingId(listingId)
    }
  }, [])

  // Handle hover on listing card
  const handleListingHover = useCallback((listingId) => {
    setActiveListingId(listingId)
  }, [])

  return (
    <div className="h-screen flex flex-col">
      <Header listingCount={filteredListings.length} />

      {/* Controls bar */}
      <div className="bg-white border-b px-4 py-3">
        <FilterToggle
          filter={filter}
          onFilterChange={setFilter}
          viewFilter={viewFilter}
          onViewFilterChange={setViewFilter}
        />
      </div>

      {/* Main content - split view */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left side - Scrollable listings */}
        <div className="w-1/2 overflow-y-auto bg-gray-50 p-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading listings...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12 bg-white rounded-lg">
              <p className="text-red-500 text-lg">{error}</p>
              <button
                onClick={loadListings}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Retry
              </button>
            </div>
          ) : filteredListings.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg">
              <p className="text-gray-500 text-lg">
                {viewFilter === 'favorites' ? 'No favorite listings yet' :
                 viewFilter === 'removed' ? 'No removed listings' :
                 'No listings found'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredListings.map((listing) => {
                const state = userState[listing.id] || {}
                return (
                  <div
                    key={listing.id}
                    ref={(el) => (listingRefs.current[listing.id] = el)}
                    data-listing-id={listing.id}
                    onMouseEnter={() => handleListingHover(listing.id)}
                    className={`transition-all duration-200 rounded-lg ${
                      activeListingId === listing.id
                        ? 'ring-2 ring-blue-500 ring-offset-2'
                        : ''
                    }`}
                  >
                    <ListingCard
                      listing={listing}
                      isFavorite={state.favorite === true}
                      isRemoved={state.removed === true}
                      onToggleFavorite={handleToggleFavorite}
                      onToggleRemoved={handleToggleRemoved}
                      onRestore={handleRestore}
                      viewFilter={viewFilter}
                    />
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Right side - Fixed map */}
        <div className="w-1/2 relative">
          {!loading && filteredListings.length > 0 && (
            <MapView
              listings={filteredListings}
              activeListingId={activeListingId}
              onMarkerClick={scrollToListing}
            />
          )}
        </div>
      </div>
    </div>
  )
}
