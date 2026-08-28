import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, ChefHat, Search, BookOpen } from 'lucide-react'
import { toast } from 'react-toastify'
import { ordersAPI, menuAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, ConfirmDialog } from '../../components/ui/index.jsx'

const STATUS_FLOW = {
  ABERTO: ['PREPARANDO', 'CANCELADO'],
  PREPARANDO: ['PRONTO', 'CANCELADO'],
  PRONTO: ['FINALIZADO'],
}
const CLOSED = ['FINALIZADO', 'CANCELADO']

export default function OrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showMenu, setShowMenu] = useState(false)
  const [confirmCancel, setConfirmCancel] = useState(null)

  // cardápio
  const [menuItems, setMenuItems] = useState([])
  const [menuSearch, setMenuSearch] = useState('')
  const [qty, setQty] = useState({})       // { [menuItemId]: number }
  const [adding, setAdding] = useState(null) // menuItemId em processamento

  const load = useCallback(() => {
    ordersAPI.get(id)
      .then(r => setOrder(r.data))
      .catch(() => navigate('/orders'))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    menuAPI.listItems({ is_active: true, page_size: 500, ordering: 'name' })
      .then(r => setMenuItems(r.data.results || r.data))
      .catch(() => {})
  }, [])

  const addFromMenu = async (menuItem) => {
    setAdding(menuItem.id)
    try {
      await ordersAPI.addItem(id, {
        menu_item: menuItem.id,
        quantity: Number(qty[menuItem.id]) || 1,
      })
      toast.success(`+ ${menuItem.name}`)
      setQty(q => ({ ...q, [menuItem.id]: 1 }))
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao lançar o item.')
    } finally {
      setAdding(null)
    }
  }

  const removeItem = async (itemId) => {
    try { await ordersAPI.removeItem(id, itemId); toast.success('Item removido'); load() }
    catch { toast.error('Erro ao remover item') }
  }

  const changeStatus = async (status) => {
    try { await ordersAPI.updateStatus(id, status); toast.success(`Status → ${status}`); load() }
    catch { toast.error('Erro ao atualizar status') }
  }

  const grouped = useMemo(() => {
    const q = menuSearch.trim().toLowerCase()
    const list = q
      ? menuItems.filter(i =>
          i.name.toLowerCase().includes(q) || (i.sku || '').toLowerCase().includes(q))
      : menuItems
    const by = {}
    for (const it of list) (by[it.category_name || 'Outros'] ||= []).push(it)
    return Object.entries(by).sort((a, b) => a[0].localeCompare(b[0]))
  }, [menuItems, menuSearch])

  if (loading) return <LoadingSpinner size="lg" className="h-64" />
  if (!order) return null

  const canEdit = !CLOSED.includes(order.status)
  const nextStatuses = STATUS_FLOW[order.status] || []

  return (
    <div className="animate-fade-in space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/orders')} className="text-brand-muted hover:text-brand-white transition-colors">
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="font-display text-2xl font-bold text-brand-white">
            Comanda #{order.id} — Mesa {order.table?.number}
          </h1>
          <div className="flex items-center gap-3 mt-1">
            <StatusBadge status={order.status} label={order.status_display} />
            {order.customer_name && <span className="text-brand-muted text-sm">Cliente: {order.customer_name}</span>}
            <span className="text-brand-muted text-sm">{order.people_count} pessoa(s)</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-brand-muted text-xs">Total</div>
          <div className="font-display text-2xl font-bold text-brand-gold">R$ {Number(order.total_amount).toFixed(2)}</div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        {nextStatuses.map(s => (
          <button
            key={s}
            onClick={() => s === 'CANCELADO' ? setConfirmCancel(s) : changeStatus(s)}
            className={s === 'CANCELADO' ? 'btn-danger' : s === 'FINALIZADO' ? 'btn-gold' : 'btn-primary'}
          >
            → {s}
          </button>
        ))}
        {canEdit && (
          <button className="btn-primary flex items-center gap-2" onClick={() => setShowMenu(true)}>
            <BookOpen size={16} /> Lançar do Cardápio
          </button>
        )}
      </div>

      {/* Items */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-brand-border">
          <h2 className="font-display text-base font-semibold text-brand-white">Itens da Comanda</h2>
          <span className="text-brand-muted text-sm">{order.items?.length || 0} itens</span>
        </div>
        {!order.items?.length ? (
          <div className="p-8 text-center">
            <ChefHat size={40} className="text-brand-border mx-auto mb-3" />
            <p className="text-brand-muted">Nenhum item lançado ainda.</p>
            {canEdit && (
              <button className="btn-ghost mt-4 inline-flex items-center gap-2" onClick={() => setShowMenu(true)}>
                <Plus size={15} /> Lançar do cardápio
              </button>
            )}
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-brand-border">
                <th className="table-header text-left p-4">Produto</th>
                <th className="table-header text-center p-4">Qtd</th>
                <th className="table-header text-center p-4">Setor</th>
                <th className="table-header text-right p-4">Unit.</th>
                <th className="table-header text-right p-4">Total</th>
                <th className="table-header text-center p-4">Status</th>
                {canEdit && <th className="table-header p-4"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {order.items.map(item => (
                <tr key={item.id} className={`transition-colors ${item.status === 'CANCELADO' ? 'opacity-40' : 'hover:bg-brand-dark/50'}`}>
                  <td className="p-4 text-brand-white">{item.product_name}</td>
                  <td className="p-4 text-center text-brand-muted">{item.quantity}</td>
                  <td className="p-4 text-center">
                    <span className="text-xs text-brand-muted border border-brand-border px-2 py-0.5 rounded">{item.sector}</span>
                  </td>
                  <td className="p-4 text-right text-brand-muted">R$ {Number(item.unit_price).toFixed(2)}</td>
                  <td className="p-4 text-right font-medium text-brand-white">R$ {Number(item.total_price).toFixed(2)}</td>
                  <td className="p-4 text-center"><StatusBadge status={item.status} label={item.status_display} /></td>
                  {canEdit && (
                    <td className="p-4">
                      {item.status !== 'CANCELADO' && (
                        <button onClick={() => removeItem(item.id)} className="text-brand-muted hover:text-red-500 transition-colors">
                          <Trash2 size={15} />
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Menu picker */}
      <Modal open={showMenu} onClose={() => setShowMenu(false)} title="Cardápio" size="lg">
        <div className="space-y-4">
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted" />
            <input
              className="input pl-9"
              placeholder="Buscar item…"
              value={menuSearch}
              onChange={e => setMenuSearch(e.target.value)}
              autoFocus
            />
          </div>

          <div className="max-h-[55vh] overflow-y-auto pr-1 space-y-4">
            {grouped.length === 0 && (
              <p className="text-brand-muted text-sm text-center py-6">Nenhum item encontrado.</p>
            )}
            {grouped.map(([cat, items]) => (
              <div key={cat}>
                <h4 className="text-brand-gold text-xs font-semibold uppercase tracking-wide mb-2">{cat}</h4>
                <div className="space-y-1">
                  {items.map(it => (
                    <div key={it.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-brand-dark/60">
                      <div className="flex-1 min-w-0">
                        <div className="text-brand-white text-sm truncate">{it.name}</div>
                        <div className="text-brand-muted text-xs">R$ {Number(it.price).toFixed(2)} · {it.sector_display}</div>
                      </div>
                      <input
                        type="number" min="1"
                        className="input w-16 text-center py-1"
                        value={qty[it.id] ?? 1}
                        onChange={e => setQty(q => ({ ...q, [it.id]: e.target.value }))}
                      />
                      <button
                        className="btn-primary py-1.5 px-3 text-sm flex items-center gap-1 disabled:opacity-50"
                        disabled={adding === it.id}
                        onClick={() => addFromMenu(it)}
                      >
                        <Plus size={14} /> Lançar
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-2 border-t border-brand-border">
            <button className="btn-ghost" onClick={() => setShowMenu(false)}>Fechar</button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        open={!!confirmCancel}
        onClose={() => setConfirmCancel(null)}
        onConfirm={() => { changeStatus('CANCELADO'); setConfirmCancel(null) }}
        title="Cancelar Comanda"
        message="Tem certeza que deseja cancelar esta comanda? Esta ação não pode ser desfeita."
        danger
      />
    </div>
  )
}
