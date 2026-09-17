import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, RefreshCw, Volume2, UtensilsCrossed, ExternalLink, BookOpen, Pencil, Star } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { queueAPI, tablesAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, PageHeader, FormField } from '../../components/ui/index.jsx'
import { useAuth } from '../../context/AuthContext'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'

// Filtro operacional da tela (reduzido): status "SENTADO"/"FINALIZADO" ficam
// visíveis em Mesas/Pedidos, aqui só o que importa pra atender a fila.
const FILTERS = [
  { value: 'ALL', label: 'Todos' },
  { value: 'PRIORITY', label: 'Prioridade' },
  { value: 'AGUARDANDO', label: 'Aguardando' },
  { value: 'NORMAL', label: 'Fila Normal' },
  { value: 'CHAMADO', label: 'Chamado' },
  { value: 'CANCELADO', label: 'Cancelado' },
]
// Filtros que traduzem direto pro parâmetro ?status= da API; PRIORITY/NORMAL/ALL
// não são status — controlam quais das duas filas aparecem na tela.
const STATUS_FILTERS = new Set(['AGUARDANDO', 'CHAMADO', 'CANCELADO'])

// Lei 10.048/2000 (+ Lei 13.466/2017, que deu atendimento imediato a 80+).
// Ajuste os rótulos se a lei municipal do estabelecimento pedir outra redação.
const PRIORITY_OPTIONS = [
  { value: 'NENHUMA', label: 'Sem prioridade' },
  { value: 'IDOSO_80', label: 'Idoso(a) 80+ — atendimento imediato' },
  { value: 'PCD', label: 'Pessoa com deficiência' },
  { value: 'IDOSO_60', label: 'Idoso(a) 60–79 anos' },
  { value: 'GESTANTE', label: 'Gestante' },
  { value: 'LACTANTE', label: 'Lactante' },
  { value: 'COLO', label: 'Pessoa com criança de colo' },
  { value: 'OBESIDADE', label: 'Pessoa com obesidade' },
]

function QueueGroup({
  title, icon, tickets, emptyLabel, canSeat, canOrder, navigate,
  openEdit, startTicketOrder, openSeat, load, onCallNext, callNextDisabled,
}) {
  const waitingCount = tickets.filter(t => t.status === 'AGUARDANDO').length
  return (
    <div>
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <h2 className="font-display text-base font-semibold text-brand-white flex items-center gap-2">
          {icon}{title}
          <span className="text-xs text-brand-muted font-normal">({waitingCount} aguardando)</span>
        </h2>
        {onCallNext && (
          <button onClick={onCallNext} disabled={callNextDisabled}
            className="btn-gold text-sm flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
            <Volume2 size={14} /> Chamar Próxima
          </button>
        )}
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[680px]">
          <thead>
            <tr className="border-b border-brand-border">
              <th className="table-header text-left p-4">Código</th>
              <th className="table-header text-left p-4">Cliente</th>
              <th className="table-header text-center p-4">Pessoas</th>
              <th className="table-header text-center p-4">Status</th>
              <th className="table-header text-center p-4">Mesa</th>
              <th className="table-header text-left p-4">Gerado</th>
              <th className="table-header p-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-border">
            {tickets.map(t => (
              <tr key={t.id} className="hover:bg-brand-dark/50 transition-colors">
                <td className="p-4">
                  <div className="font-mono font-bold text-brand-gold">{t.code}</div>
                  {t.is_priority && (
                    <span className="mt-1 inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-amber-900/40 text-amber-300 border border-amber-700">
                      <Star size={9} /> {t.priority_category_display}
                    </span>
                  )}
                </td>
                <td className="p-4 text-brand-white">{t.customer_name || '—'}</td>
                <td className="p-4 text-center text-brand-muted">{t.people_count}</td>
                <td className="p-4 text-center"><StatusBadge status={t.status} label={t.status_display} /></td>
                <td className="p-4 text-center">
                  {t.table_number ? (
                    <span className="text-brand-white font-medium">Mesa {t.table_number}</span>
                  ) : <span className="text-brand-muted">—</span>}
                </td>
                <td className="p-4 text-brand-muted text-sm">
                  {new Date(t.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-3 justify-end flex-wrap">
                    {canSeat && !['FINALIZADO', 'CANCELADO'].includes(t.status) && (
                      <button onClick={() => openEdit(t)} title="Editar nome / qtd. pessoas"
                        className="text-brand-muted hover:text-brand-white">
                        <Pencil size={13} />
                      </button>
                    )}
                    {t.active_order_id && (
                      <button onClick={() => navigate(`/orders/${t.active_order_id}`)}
                        className="text-xs text-brand-gold hover:underline inline-flex items-center gap-1">
                        <ExternalLink size={12} /> comanda
                      </button>
                    )}
                    {canOrder && !t.active_order_id && ['AGUARDANDO', 'CHAMADO'].includes(t.status) && (
                      <button onClick={() => startTicketOrder(t)}
                        className="text-xs text-brand-white bg-brand-border hover:bg-brand-dark px-2 py-1 rounded inline-flex items-center gap-1">
                        <BookOpen size={12} /> Lançar pedido
                      </button>
                    )}
                    {canSeat && ['AGUARDANDO', 'CHAMADO'].includes(t.status) && (
                      <button onClick={() => openSeat(t)}
                        className="text-xs text-brand-white bg-brand-red/80 hover:bg-brand-red px-2 py-1 rounded inline-flex items-center gap-1">
                        <UtensilsCrossed size={12} /> Enviar p/ mesa
                      </button>
                    )}
                    {canSeat && ['AGUARDANDO'].includes(t.status) && (
                      <button onClick={async () => { await queueAPI.cancel(t.id); load() }}
                        className="text-xs text-red-500 hover:text-red-400">Cancelar</button>
                    )}
                    {canSeat && ['CHAMADO', 'SENTADO'].includes(t.status) && (
                      <button onClick={async () => { await queueAPI.finalize(t.id); load() }}
                        className="text-xs text-green-400 hover:text-green-300">Finalizar</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {tickets.length === 0 && (
              <tr><td colSpan={7} className="p-6 text-center text-brand-muted text-sm">{emptyLabel}</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function QueuePage() {
  const navigate = useNavigate()
  const { hasRole } = useAuth()
  const canSeat = hasRole('RECEPCAO', 'ADM_MAXIMO', 'GERENTE')
  const canOrder = hasRole('GARCOM', 'RECEPCAO', 'ADM_MAXIMO', 'GERENTE')

  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('AGUARDANDO')
  const [showCreate, setShowCreate] = useState(false)
  const [display, setDisplay] = useState(null)
  const { register, handleSubmit, reset } = useForm()

  // enviar para mesa
  const [seatTicket, setSeatTicket] = useState(null)
  const [freeTables, setFreeTables] = useState([])
  const [seatTableId, setSeatTableId] = useState('')
  const [seatOpenOrder, setSeatOpenOrder] = useState(true)
  const [seating, setSeating] = useState(false)

  // editar senha (nome / qtd pessoas)
  const [editTicket, setEditTicket] = useState(null)
  const [editName, setEditName] = useState('')
  const [editPeople, setEditPeople] = useState(1)
  const [saving, setSaving] = useState(false)

  const load = useCallback((opts = {}) => {
    const params = STATUS_FILTERS.has(filter) ? { status: filter } : {}
    Promise.all([queueAPI.list(params), queueAPI.publicDisplay()])
      .then(([listRes, displayRes]) => {
        setTickets(listRes.data.results || listRes.data)
        setDisplay(displayRes.data)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [filter])

  useEffect(() => { load() }, [load])
  // Outra recepção gerou/chamou/editou uma senha -> aparece aqui sozinho.
  useAutoRefresh(useCallback(() => load({ silent: true }), [load]), { interval: 5000 })

  // Fila dividida em dois grupos -> a recepção escolhe de qual chamar.
  const priorityTickets = useMemo(() => tickets.filter(t => t.is_priority), [tickets])
  const normalTickets = useMemo(() => tickets.filter(t => !t.is_priority), [tickets])
  const showPriority = filter !== 'NORMAL'
  const showNormal = filter !== 'PRIORITY'
  const priorityHasWaiting = priorityTickets.some(t => t.status === 'AGUARDANDO')
  const normalHasWaiting = normalTickets.some(t => t.status === 'AGUARDANDO')

  const handleCreate = async (data) => {
    try {
      const r = await queueAPI.create(data)
      toast.success(`Senha ${r.data.code} gerada!`)
      reset(); setShowCreate(false); load()
    } catch { toast.error('Erro ao gerar senha') }
  }

  const handleCallNext = async (group) => {
    try {
      const r = await queueAPI.callNext(group)
      toast.success(`Chamando senha ${r.data.code}!`); load()
    } catch (e) {
      toast.error(e.response?.data?.detail || e.response?.data?.group || 'Nenhuma senha na fila')
    }
  }

  const openSeat = async (ticket) => {
    setSeatTicket(ticket)
    setSeatTableId('')
    setSeatOpenOrder(true)
    try {
      const r = await tablesAPI.list({ status: 'LIVRE', page_size: 100 })
      setFreeTables(r.data.results || r.data)
    } catch { setFreeTables([]) }
  }

  const startTicketOrder = async (ticket) => {
    try {
      const r = await queueAPI.openOrder(ticket.id)
      toast.success(`Comanda da senha ${ticket.code} aberta`)
      navigate(`/orders/${r.data.id}`)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao abrir a comanda da senha.')
    }
  }

  const confirmSeat = async () => {
    if (!seatTableId) return toast.error('Escolha uma mesa.')
    setSeating(true)
    try {
      const r = await queueAPI.assignTable(seatTicket.id, {
        table: Number(seatTableId),
        open_order: seatOpenOrder,
      })
      toast.success(`Senha ${seatTicket.code} → Mesa ${r.data.table_number}`)
      const orderId = r.data.order_id
      setSeatTicket(null); load()
      if (orderId) navigate(`/orders/${orderId}`)
    } catch (e) {
      toast.error(e.response?.data?.table || e.response?.data?.detail || 'Erro ao enviar para a mesa.')
    } finally {
      setSeating(false)
    }
  }

  const openEdit = (ticket) => {
    setEditTicket(ticket)
    setEditName(ticket.customer_name || '')
    setEditPeople(ticket.people_count)
  }

  const saveEdit = async () => {
    setSaving(true)
    try {
      await queueAPI.edit(editTicket.id, { customer_name: editName, people_count: editPeople })
      toast.success(`Senha ${editTicket.code} atualizada.`)
      setEditTicket(null); load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao editar a senha.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Fila de Espera"
        subtitle="Senhas, chamada e envio para a mesa"
        actions={
          <>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
            {canSeat && (
              <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
                <Plus size={16} /> Gerar Senha
              </button>
            )}
          </>
        }
      />

      {display && (
        <div className="grid grid-cols-2 gap-4">
          <div className="card p-6 border-brand-gold/30 shadow-gold-lg text-center">
            <p className="text-brand-muted text-sm mb-1">Última Chamada</p>
            {display.last_called ? (
              <>
                <div className="font-display text-5xl font-bold text-brand-gold">{display.last_called.code}</div>
                {display.last_called.customer_name && (
                  <p className="text-brand-white mt-2">{display.last_called.customer_name}</p>
                )}
              </>
            ) : (
              <div className="font-display text-3xl text-brand-muted">—</div>
            )}
          </div>
          <div className="card p-6 text-center">
            <p className="text-brand-muted text-sm mb-1">Aguardando</p>
            <div className="font-display text-5xl font-bold text-brand-white">{display.waiting_count}</div>
            <p className="text-brand-muted text-sm mt-1">na fila</p>
          </div>
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        {FILTERS.map(({ value, label }) => (
          <button key={value} onClick={() => setFilter(value)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              filter === value ? 'bg-brand-gold text-brand-black' : 'bg-brand-dark text-brand-muted border border-brand-border hover:text-brand-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner size="lg" className="h-48" /> : (
        <div className="space-y-8">
          {showPriority && (
            <QueueGroup
              title="Fila Prioritária" icon={<Star size={16} className="text-amber-400" />}
              tickets={priorityTickets} emptyLabel="Nenhuma senha prioritária."
              canSeat={canSeat} canOrder={canOrder} navigate={navigate}
              openEdit={openEdit} startTicketOrder={startTicketOrder} openSeat={openSeat} load={load}
              onCallNext={canSeat ? () => handleCallNext('priority') : null}
              callNextDisabled={!priorityHasWaiting}
            />
          )}
          {showNormal && (
            <QueueGroup
              title="Fila Normal" icon={null}
              tickets={normalTickets} emptyLabel="Nenhuma senha na fila normal."
              canSeat={canSeat} canOrder={canOrder} navigate={navigate}
              openEdit={openEdit} startTicketOrder={startTicketOrder} openSeat={openSeat} load={load}
              onCallNext={canSeat ? () => handleCallNext('normal') : null}
              callNextDisabled={!normalHasWaiting}
            />
          )}
        </div>
      )}

      {/* Gerar senha */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Gerar Nova Senha">
        <form onSubmit={handleSubmit(handleCreate)} className="space-y-4">
          <FormField label="Nome do Cliente">
            <input {...register('customer_name')} className="input" placeholder="Opcional" />
          </FormField>
          <FormField label="Número de Pessoas">
            <input {...register('people_count', { min: 0 })} type="number" min="0" className="input" defaultValue={null} />
          </FormField>
          <FormField label="Prioridade (Lei 10.048/2000)">
            <select {...register('priority_category')} className="input" defaultValue="NENHUMA">
              {PRIORITY_OPTIONS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setShowCreate(false)}>Cancelar</button>
            <button type="submit" className="btn-gold">Gerar Senha</button>
          </div>
        </form>
      </Modal>

      {/* Editar senha */}
      <Modal open={!!editTicket} onClose={() => setEditTicket(null)} title={`Editar senha ${editTicket?.code || ''}`}>
        <div className="space-y-4">
          <FormField label="Nome do Cliente">
            <input className="input" value={editName} onChange={e => setEditName(e.target.value)}
              placeholder="Qualquer nome ou observação" />
          </FormField>
          <FormField label="Número de Pessoas">
            <div className="flex gap-2">
              <input type="number" min="0" className="input flex-1" value={editPeople}
                onChange={e => setEditPeople(Number(e.target.value))} />
              <button type="button" className="btn-ghost text-sm" onClick={() => setEditPeople(0)}>
                Zerar
              </button>
            </div>
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-ghost" onClick={() => setEditTicket(null)}>Cancelar</button>
            <button className="btn-primary disabled:opacity-50" disabled={saving} onClick={saveEdit}>
              {saving ? 'Salvando…' : 'Salvar'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Enviar para mesa */}
      <Modal open={!!seatTicket} onClose={() => setSeatTicket(null)}
        title={`Enviar senha ${seatTicket?.code || ''} para a mesa`}>
        <div className="space-y-4">
          <p className="text-brand-muted text-sm">
            Cliente: <span className="text-brand-white">{seatTicket?.customer_name || 'Anônimo'}</span>
            {' · '}{seatTicket?.people_count} pessoa(s)
          </p>
          {seatTicket?.active_order_id && (
            <p className="text-brand-gold text-xs">
              Esta senha já tem uma comanda aberta — os itens lançados na espera vão para a mesa escolhida.
            </p>
          )}
          <FormField label="Mesa livre">
            <select className="input" value={seatTableId} onChange={e => setSeatTableId(e.target.value)}>
              <option value="">Selecione…</option>
              {freeTables.map(m => (
                <option key={m.id} value={m.id}>Mesa {m.number} — {m.seats} lugares</option>
              ))}
            </select>
            {freeTables.length === 0 && (
              <p className="text-yellow-400 text-xs mt-1">Nenhuma mesa livre no momento.</p>
            )}
          </FormField>
          <label className="flex items-center gap-2 text-sm text-brand-muted cursor-pointer">
            <input type="checkbox" className="accent-brand-gold"
              checked={seatOpenOrder} onChange={e => setSeatOpenOrder(e.target.checked)} />
            Abrir a comanda desta mesa agora
          </label>
          <div className="flex gap-3 justify-end pt-2">
            <button className="btn-ghost" onClick={() => setSeatTicket(null)}>Cancelar</button>
            <button className="btn-primary disabled:opacity-50" disabled={seating || !seatTableId}
              onClick={confirmSeat}>
              {seating ? 'Enviando…' : 'Enviar para a mesa'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
