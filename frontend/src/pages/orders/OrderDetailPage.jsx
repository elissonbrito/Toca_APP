import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, ChefHat, Search, BookOpen, Receipt, Undo2, ArrowLeftRight, Move } from 'lucide-react'
import { toast } from 'react-toastify'
import { ordersAPI, menuAPI, tablesAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, ConfirmDialog } from '../../components/ui/index.jsx'
import { useAuth } from '../../context/AuthContext'

const NO_ITEMS = ['FINALIZADO', 'CANCELADO', 'FECHAMENTO']
const CAN_CLOSE_FROM = ['ABERTO', 'PREPARANDO', 'PRONTO']
const CLOSED = ['FINALIZADO', 'CANCELADO']

export default function OrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { hasRole } = useAuth()
  const isCaixa = hasRole('CAIXA', 'ADM_MAXIMO', 'GERENTE')
  const isCaixaAdmin = hasRole('CAIXA', 'ADM_MAXIMO')
  const canCloseBill = hasRole('GARCOM', 'RECEPCAO', 'CAIXA', 'ADM_MAXIMO', 'GERENTE')
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showMenu, setShowMenu] = useState(false)
  const [confirmCancel, setConfirmCancel] = useState(null)

  // troca de mesa / transferência de itens (caixa/adm)
  const [showTransferTable, setShowTransferTable] = useState(false)
  const [showTransferItems, setShowTransferItems] = useState(false)
  const [freeTables, setFreeTables] = useState([])
  const [openOrders, setOpenOrders] = useState([])
  const [transferTarget, setTransferTarget] = useState('')
  const [pickedItems, setPickedItems] = useState({})

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
    catch (e) { toast.error(e.response?.status === 403 ? 'Só o caixa pode excluir itens lançados.' : 'Erro ao remover item') }
  }

  const changeStatus = async (status) => {
    try { await ordersAPI.updateStatus(id, status); toast.success(`Status → ${status}`); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Erro ao atualizar status') }
  }

  const closeBill = async () => {
    if (!confirm('Fechar a conta? Ela vai para o caixa.')) return
    try { await ordersAPI.closeBill(id); toast.success('Conta fechada — enviada para o caixa.'); load() }
    catch (e) { toast.error(e.response?.data?.detail || e.response?.data?.[0] || 'Erro ao fechar a conta.') }
  }

  const reopenBill = async () => {
    try { await ordersAPI.reopenBill(id); toast.success('Conta reaberta.'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Erro ao reabrir a conta.') }
  }

  const openTransferTable = async () => {
    try {
      const r = await tablesAPI.list()
      const list = (r.data.results || r.data).filter(t => t.status === 'LIVRE')
      setFreeTables(list)
      setShowTransferTable(true)
    } catch { toast.error('Erro ao carregar mesas livres') }
  }

  const doTransferTable = async (tableId) => {
    try {
      await ordersAPI.transferTable(id, tableId)
      toast.success('Mesa trocada.')
      setShowTransferTable(false); load()
    } catch (e) { toast.error(e.response?.data?.table || e.response?.data?.detail || 'Erro ao trocar de mesa.') }
  }

  const openTransferItems = async () => {
    try {
      const r = await ordersAPI.list({ page_size: 200 })
      const list = (r.data.results || r.data).filter(
        o => o.id !== Number(id) && !CLOSED.includes(o.status) && o.status !== 'FECHAMENTO'
      )
      setOpenOrders(list)
      setTransferTarget('')
      setPickedItems({})
      setShowTransferItems(true)
    } catch { toast.error('Erro ao carregar comandas') }
  }

  const doTransferItems = async () => {
    const items = Object.entries(pickedItems).filter(([, v]) => v).map(([k]) => Number(k))
    if (!transferTarget) { toast.error('Escolha a comanda de destino.'); return }
    if (!items.length) { toast.error('Selecione ao menos um item.'); return }
    try {
      await ordersAPI.transferItems(id, Number(transferTarget), items)
      toast.success('Itens transferidos.')
      setShowTransferItems(false); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao transferir itens.') }
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

  const canAddItems = !NO_ITEMS.includes(order.status)
  const canRemoveItem = isCaixa && !['FINALIZADO', 'CANCELADO'].includes(order.status)

  // "Voltar": comanda de mesa -> tela de Mesas; comanda de senha -> Fila; senão Pedidos.
  const goBack = () => navigate(order.table ? '/tables' : order.queue_ticket_code ? '/queue' : '/orders')

  return (
    <div className="animate-fade-in space-y-6 max-w-3xl">
      <div className="flex items-center gap-4">
        <button onClick={goBack} className="text-brand-muted hover:text-brand-white transition-colors">
          <ArrowLeft size={20} />
        </button>
        <div className="flex-1">
          <h1 className="font-display text-2xl font-bold text-brand-white">
            Comanda #{order.id} — {order.table
              ? `Mesa ${order.table.number}`
              : order.queue_ticket_code
                ? `Senha ${order.queue_ticket_code} (aguardando mesa)`
                : 'sem mesa'}
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

      {/* Conta fechada -> aviso */}
      {order.status === 'FECHAMENTO' && (
        <div className="card p-4 border-purple-700/50 bg-purple-950/20 flex items-center justify-between flex-wrap gap-3">
          <p className="text-purple-200 text-sm flex items-center gap-2">
            <Receipt size={16} /> Conta fechada — aguardando pagamento no caixa.
          </p>
          {isCaixa && (
            <button className="btn-ghost text-sm flex items-center gap-2" onClick={reopenBill}>
              <Undo2 size={15} /> Reabrir conta
            </button>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 flex-wrap">
        {canAddItems && (
          <button className="btn-primary flex items-center gap-2" onClick={() => setShowMenu(true)}>
            <BookOpen size={16} /> Lançar do Cardápio
          </button>
        )}
        {canCloseBill && CAN_CLOSE_FROM.includes(order.status) && order.table && (
          <button className="btn-gold flex items-center gap-2" onClick={closeBill}>
            <Receipt size={16} /> Fechar Conta
          </button>
        )}
        {isCaixaAdmin && !CLOSED.includes(order.status) && (
          <>
            <button className="btn-ghost flex items-center gap-2" onClick={openTransferTable}>
              <ArrowLeftRight size={16} /> Trocar mesa
            </button>
            <button className="btn-ghost flex items-center gap-2" onClick={openTransferItems}>
              <Move size={16} /> Transferir itens
            </button>
          </>
        )}
        {isCaixa && !['FINALIZADO', 'CANCELADO'].includes(order.status) && (
          <button className="btn-danger" onClick={() => setConfirmCancel(true)}>
            Cancelar conta
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
            {canAddItems && (
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
                {canRemoveItem && <th className="table-header p-4"></th>}
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
                  {canRemoveItem && (
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

      {/* Trocar mesa */}
      <Modal open={showTransferTable} onClose={() => setShowTransferTable(false)} title="Trocar a mesa do cliente">
        <div className="space-y-3">
          <p className="text-brand-muted text-sm">
            A comanda inteira passa para a mesa escolhida. A mesa atual vai para limpeza.
          </p>
          {freeTables.length === 0 ? (
            <p className="text-brand-muted text-sm">Nenhuma mesa livre no momento.</p>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2 max-h-[50vh] overflow-y-auto">
              {freeTables.map(t => (
                <button key={t.id} className="btn-ghost py-2" onClick={() => doTransferTable(t.id)}>
                  Mesa {t.number}
                </button>
              ))}
            </div>
          )}
          <div className="flex justify-end pt-2 border-t border-brand-border">
            <button className="btn-ghost" onClick={() => setShowTransferTable(false)}>Fechar</button>
          </div>
        </div>
      </Modal>

      {/* Transferir itens */}
      <Modal open={showTransferItems} onClose={() => setShowTransferItems(false)} title="Transferir itens para outra comanda" size="lg">
        <div className="space-y-4">
          <div>
            <label className="text-brand-muted text-xs">Comanda de destino</label>
            <select className="input mt-1" value={transferTarget} onChange={e => setTransferTarget(e.target.value)}>
              <option value="">Selecione…</option>
              {openOrders.map(o => (
                <option key={o.id} value={o.id}>
                  #{o.id} — {o.table ? `Mesa ${o.table.number}` : o.queue_ticket_code ? `Senha ${o.queue_ticket_code}` : 'sem mesa'}
                </option>
              ))}
            </select>
          </div>
          <div className="max-h-[45vh] overflow-y-auto divide-y divide-brand-border border border-brand-border rounded-lg">
            {(order.items || []).filter(it => it.status !== 'CANCELADO').map(it => (
              <label key={it.id} className="flex items-center gap-3 p-3 hover:bg-brand-dark/50 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!pickedItems[it.id]}
                  onChange={e => setPickedItems(p => ({ ...p, [it.id]: e.target.checked }))}
                />
                <span className="flex-1 text-brand-white text-sm">{it.quantity}x {it.product_name}</span>
                <span className="text-brand-muted text-xs">R$ {Number(it.total_price).toFixed(2)}</span>
              </label>
            ))}
          </div>
          <div className="flex justify-end gap-3 pt-2 border-t border-brand-border">
            <button className="btn-ghost" onClick={() => setShowTransferItems(false)}>Cancelar</button>
            <button className="btn-primary" onClick={doTransferItems}>Transferir</button>
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
