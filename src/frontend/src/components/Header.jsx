import { Link } from 'react-router-dom'
import { Home } from 'lucide-react'

export default function Header({ listingCount }) {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="text-2xl font-bold text-gray-900 hover:text-gray-700 flex items-center gap-2">
            <Home className="w-7 h-7" />
            HouseHunter
          </Link>
          {listingCount !== undefined && (
            <div className="text-sm text-gray-600">
              <span className="font-semibold text-gray-900">{listingCount}</span> listings
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
