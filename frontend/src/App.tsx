import { Routes, Route } from 'react-router-dom'

import Landing from './pages/Landing'
import Analyze from './pages/Analyze'

function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<Analyze />} />
      </Routes>
    </div>
  )
}

export default App
