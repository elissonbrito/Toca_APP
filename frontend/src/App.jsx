import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/layout/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import TablesPage from './pages/tables/TablesPage'
import OrdersPage from './pages/orders/OrdersPage'
import OrderDetailPage from './pages/orders/OrderDetailPage'
import KitchenPage from './pages/kitchen/KitchenPage'
import ParrillaPage from './pages/kitchen/ParrillaPage'
import QueuePage from './pages/queue/QueuePage'
import CashPage from './pages/cash/CashPage'
import MenuPage from './pages/menu/MenuPage'
import FiscalConferencePage from './pages/menu/FiscalConferencePage'
import UsersPage from './pages/users/UsersPage'
import AuditPage from './pages/users/AuditPage'

function PrivateRoute({ children, roles }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return children
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={user?.role === 'ADM_MAXIMO' ? <DashboardPage /> : <Navigate to="/tables" replace />} />
        <Route path="tables" element={<TablesPage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="orders/:id" element={<OrderDetailPage />} />
        <Route path="kitchen" element={<PrivateRoute roles={['COZINHA','ADM_MAXIMO','GERENTE']}><KitchenPage /></PrivateRoute>} />
        <Route path="parrilla" element={<PrivateRoute roles={['PARRILLA','ADM_MAXIMO','GERENTE']}><ParrillaPage /></PrivateRoute>} />
        <Route path="queue" element={<QueuePage />} />
        <Route path="cash" element={<PrivateRoute roles={['CAIXA','ADM_MAXIMO','GERENTE']}><CashPage /></PrivateRoute>} />
        <Route path="menu" element={<MenuPage />} />
        <Route path="fiscal" element={<PrivateRoute roles={['ADM_MAXIMO','GERENTE']}><FiscalConferencePage /></PrivateRoute>} />
        <Route path="users" element={<PrivateRoute roles={['ADM_MAXIMO','GERENTE']}><UsersPage /></PrivateRoute>} />
        <Route path="audit" element={<PrivateRoute roles={['ADM_MAXIMO','GERENTE']}><AuditPage /></PrivateRoute>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ErrorBoundary>
        <AppRoutes />
      </ErrorBoundary>
    </AuthProvider>
  )
}
