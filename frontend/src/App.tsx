import { ScrollToTop } from '@/components/ScrollToTop'
import { Home } from '@/pages/Home'
import { Route, Routes } from 'react-router-dom'

function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </>
  )
}

export { App }
