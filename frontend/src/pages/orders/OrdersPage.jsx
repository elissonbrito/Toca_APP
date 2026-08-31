import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ClipboardList, RefreshCw, Eye } from 'lucide-react'
import { ordersAPI } from '../../services/api'
import { StatusBadge, LoadingSpinner, EmptyState, PageHeader } from '../../components/ui/index.jsx'

const STATUS_OPTS = ['ABERTO', 'PREPARANDO', 'PRONTO', 'FINALIZADO', 'CANCELADO']

export default function OrdersPage() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ABERTO')

  const load = useCallback(() => {
    setLoading(true)
    const params = filter !== 'ALL' ? { status: filter } : {}
    ordersAPI.list(params)
      .then(r => setOrders(r.data.results || r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [filter])

  useEffect(() => { load() }, [load])

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Pedidos"
        subtitle="Gerenciamento de comandas"
        actions={<button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>}
      />

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {['ALL', ...STATUS_OPTS].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              filter === s ? 'bg-brand-gold text-brand-black' : 'bg-brand-dark text-brand-muted border border-brand-border hover:text-brand-white'
            }`}
          >
            {s === 'ALL' ? 'Todos' : s}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner size="lg" className="h-64" /> : orders.length === 0 ? (
        <EmptyState icon={ClipboardList} title="Nenhum pedido encontrado" description="Mude o filtro ou abra uma comanda em Mesas." />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-brand-border">
                <th className="table-header text-left p-4">#</th>
                <th className="table-header text-left p-4">Mesa</th>
                <th className="table-header text-left p-4">Cliente</th>
                <th className="table-header text-left p-4">Itens</th>
                <th className="table-header text-right p-4">Total</th>
                <th className="table-header text-center p-4">Status</th>
                <th className="table-header text-left p-4">Aberto em</th>
                <th className="table-header p-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {orders.map(o => (
                <tr key={o.id} className="hover:bg-brand-dark/50 transition-colors">
                  <td className="p-4 text-brand-muted font-mono text-sm">#{o.id}</td>
                  <td className="p-4 font-medium text-brand-white">
                    {o.table ? `Mesa ${o.table.number}`
                      : o.queue_ticket_code ? `Senha ${o.queue_ticket_code}` : '—'}
                  </td>
                  <td className="p-4 text-brand-muted text-sm">{o.customer_name || '—'}</td>
                  <td className="p-4 text-brand-muted text-sm">{o.items?.length || 0}</td>
                  <td className="p-4 text-right font-medium text-brand-gold">
                    R$ {Number(o.total_amount).toFixed(2)}
                  </td>
                  <td className="p-4 text-center">
                    <StatusBadge status={o.status} label={o.status_display} />
                  </td>
                  <td className="p-4 text-brand-muted text-sm">
                    {new Date(o.created_at).toLocaleString('pt-BR', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })}
                  </td>
                  <td className="p-4">
                    <button onClick={() => navigate(`/orders/${o.id}`)} className="text-brand-muted hover:text-brand-gold transition-colors">
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
