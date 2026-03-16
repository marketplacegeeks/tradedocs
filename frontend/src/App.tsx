import { Routes, Route, Navigate } from 'react-router-dom'
import OrganisationListPage from './pages/master-data/OrganisationListPage'
import OrganisationFormPage from './pages/master-data/OrganisationFormPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/master-data/organisations" replace />} />
      <Route path="/master-data/organisations" element={<OrganisationListPage />} />
      <Route path="/master-data/organisations/new" element={<OrganisationFormPage />} />
      <Route path="/master-data/organisations/:id/edit" element={<OrganisationFormPage />} />
    </Routes>
  )
}
