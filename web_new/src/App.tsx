import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HostsPage } from './pages/HostsPage'
import { PlaybooksPage } from './pages/PlaybooksPage'
import { RunsPage } from './pages/RunsPage'
import { DashboardPage } from './pages/DashboardPage'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/hosts" element={<HostsPage />} />
          <Route path="/playbooks" element={<PlaybooksPage />} />
          <Route path="/runs" element={<RunsPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
