import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, ChefHat, Clock } from 'lucide-react'
import { toast } from 'react-toastify'
import { kitchenAPI } from '../../services/api'
import { StatusBadge, LoadingSpinner, EmptyState, PageHeader } from '../../components/ui/index.jsx'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'

const ITEM_STATUSES = ['PENDENTE', 'PREPARANDO', 'PRONTO']
const STATUS_LABELS = { PENDENTE: 'Pendente', PREPARANDO: 'Preparando', PRONTO: 'Pronto' }
const NEXT_STATUS = { PENDENTE: 'PREPARANDO', PREPARANDO: 'PRONTO' }

function ItemCard({ item, onStatusChange }) {
  const age = Math.floor((Date.now() - new Date(item.created_at)) / 60000)
  const urgent = age > 15

  return (
    <div className={`card p-4 border-l-4 transition-all ${
      item.status === 'PENDENTE' ? 'border-l-orange-500' :
      item.status === 'PREPARANDO' ? 'border-l-yellow-500' : 'border-l-green-500'
    } ${urgent ? 'ring-1 ring-red-500/50' : ''}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <p className="font-medium text-brand-white">{item.product_name}</p>
          <p className="text-brand-gold font-display text-lg font-bold">× {item.quantity}</p>
        </div>
        <StatusBadge status={item.status} label={STATUS_LABELS[item.status]} />
      </div>
      {item.observations && (
        <p className="text-xs text-yellow-400 bg-yellow-950/30 border border-yellow-800/50 rounded px-2 py-1 mb-2">
          ⚠ {item.observations}
        </p>
      )}
      <div className="flex items-center justify-between mt-3">
        <div className={`flex items-center gap-1 text-xs ${urgent ? 'text-red-400' : 'text-brand-muted'}`}>
          <Clock size={12} />
          <span>{age}min</span>
        </div>
        {NEXT_STATUS[item.status] && (
          <button
            onClick={() => onStatusChange(item.id, NEXT_STATUS[item.status])}
            className={`text-xs px-3 py-1 rounded-lg font-medium transition-all ${
              item.status === 'PENDENTE'
                ? 'bg-yellow-900/50 text-yellow-400 hover:bg-yellow-900 border border-yellow-800'
                : 'bg-green-900/50 text-green-400 hover:bg-green-900 border border-green-800'
            }`}
          >
            → {STATUS_LABELS[NEXT_STATUS[item.status]]}
          </button>
        )}
      </div>
    </div>
  )
}

export default function KitchenPanelPage({ sector = 'COZINHA' }) {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const load = useCallback(() => {
    kitchenAPI.getOrders(sector)
      .then(r => setItems(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [sector])

  useEffect(() => { load() }, [load])
  useAutoRefresh(load, { interval: 4000, enabled: autoRefresh })

  const handleStatusChange = async (itemId, newStatus) => {
    try {
      await kitchenAPI.updateItemStatus(itemId, newStatus)
      toast.success(`Item → ${STATUS_LABELS[newStatus]}`)
      load()
    } catch { toast.error('Erro ao atualizar') }
  }

  const grouped = ITEM_STATUSES.reduce((acc, s) => {
    acc[s] = items.filter(i => i.status === s)
    return acc
  }, {})

  const icon = sector === 'COZINHA' ? ChefHat : null
  const title = sector === 'COZINHA' ? 'Painel da Cozinha' : 'Painel da Parrilla'

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title={title}
        subtitle={`${items.length} item(s) em preparo`}
        actions={
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-brand-muted cursor-pointer">
              <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)}
                className="accent-brand-gold" />
              Auto-refresh (4s)
            </label>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
          </div>
        }
      />

      {loading ? <LoadingSpinner size="lg" className="h-64" /> : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {ITEM_STATUSES.map(status => (
            <div key={status}>
              <div className="flex items-center gap-2 mb-3">
                <h2 className="font-semibold text-brand-white">{STATUS_LABELS[status]}</h2>
                <span className="bg-brand-border text-brand-muted text-xs px-2 py-0.5 rounded-full">
                  {grouped[status].length}
                </span>
              </div>
              <div className="space-y-3">
                {grouped[status].length === 0 ? (
                  <div className="card p-6 text-center">
                    <p className="text-brand-muted text-sm">Nenhum item</p>
                  </div>
                ) : (
                  grouped[status].map(item => (
                    <ItemCard key={item.id} item={item} onStatusChange={handleStatusChange} />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
