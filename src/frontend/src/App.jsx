import { Routes, Route } from 'react-router-dom'
import ListingsPage from './pages/ListingsPage'
import ListingDetailPage from './pages/ListingDetailPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<ListingsPage />} />
      <Route path="/listing/:id" element={<ListingDetailPage />} />
    </Routes>
  )
}

export default App
