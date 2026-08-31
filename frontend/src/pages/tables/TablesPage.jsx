import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, UtensilsCrossed, RefreshCw } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { tablesAPI, ordersAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, EmptyState, PageHeader, FormField } from '../../components/ui/index.jsx'
import { useAuth } from '../../context/AuthContext'

const TABLE_STATUS = ['LIVRE', 'OCUPADA', 'CONTA', 'RESERVADA', 'LIMPEZA']

function TableCard({ table, onStatusChange, onSelect, onOpenComanda, onCloseBill }) {
  const colors = {
    LIVRE: 'border-green-800/50 bg-green-950/20',
    OCUPADA: 'border-brand-red/50 bg-brand-red/10',
    CONTA: 'border-purple-700/60 bg-purple-950/30',
    RESERVADA: 'border-blue-800/50 bg-blue-950/20',
    LIMPEZA: 'border-yellow-800/50 bg-yellow-950/20',
  }

  return (
    <div className={`card border-2 ${colors[table.status]} p-4 transition-all duration-200 hover:scale-[1.02]`}>
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="font-display text-xl font-bold text-brand-white">Mesa {table.number}</h3>
          <p className="text-brand-muted text-xs">{table.seats} lugares</p>
        </div>
        <StatusBadge status={table.status} label={table.status_display} />
      </div>
      {table.observation && (
        <p className="text-brand-muted text-xs mb-3 line-clamp-2">{table.observation}</p>
      )}
      {table.status === 'CONTA' && (
        <p className="text-purple-300 text-xs mb-2">Conta fechada — aguardando o caixa.</p>
      )}
      <div className="flex flex-col gap-2 mt-auto">
        {table.status === 'LIVRE' && (
          <button className="btn-primary text-xs py-1.5 px-3" onClick={() => onSelect(table)}>
            Abrir Comanda
          </button>
        )}

        {table.active_order_id && (
          <button className="btn-primary text-xs py-1.5 px-3" onClick={() => onOpenComanda(table.active_order_id)}>
            {table.status === 'CONTA' ? 'Ver conta' : 'Ver / Lançar itens'}
          </button>
        )}

        {table.status === 'OCUPADA' && table.active_order_id && (
          <button className="btn-gold text-xs py-1.5 px-3" onClick={() => onCloseBill(table.active_order_id)}>
            Fechar Conta
          </button>
        )}
        {table.status === 'OCUPADA' && !table.active_order_id && (
          <button className="btn-ghost text-xs py-1.5 px-3" onClick={() => onStatusChange(table, 'LIMPEZA')}>
            Liberar → Limpeza
          </button>
        )}
        {table.status === 'LIMPEZA' && (
          <button className="btn-gold text-xs py-1.5 px-3" onClick={() => onStatusChange(table, 'LIVRE')}>
            Marcar como Livre
          </button>
        )}
        {table.status === 'RESERVADA' && !table.active_order_id && (
          <button className="btn-primary text-xs py-1.5 px-3" onClick={() => onSelect(table)}>
            Abrir Comanda (check-in)
          </button>
        )}
      </div>
    </div>
  )
}

export default function TablesPage() {
  const { isManager } = useAuth()
  const navigate = useNavigate()
  const [tables, setTables] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [showCreate, setShowCreate] = useState(false)
  const [showOrder, setShowOrder] = useState(null)
  const { register, handleSubmit, reset, formState: { errors } } = useForm()
  const { register: regOrder, handleSubmit: handleOrder, reset: resetOrder, formState: { errors: errOrder } } = useForm()

  const load = useCallback(() => {
    setLoading(true)
    tablesAPI.list()
      .then(r => setTables(r.data.results || r.data))
      .catch(() => toast.error('Erro ao carregar mesas'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleStatusChange = async (table, newStatus) => {
    try {
      await tablesAPI.update(table.id, { status: newStatus })
      toast.success(`Mesa ${table.number} → ${newStatus}`)
      load()
    } catch { toast.error('Erro ao atualizar status') }
  }

  const handleCloseBill = async (orderId) => {
    if (!confirm('Fechar a conta desta mesa? Ela vai para o caixa.')) return
    try {
      await ordersAPI.closeBill(orderId)
      toast.success('Conta fechada — enviada para o caixa.')
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || e.response?.data?.[0] || 'Erro ao fechar a conta.')
    }
  }

  const handleCreateTable = async (data) => {
    try {
      await tablesAPI.create(data)
      toast.success('Mesa criada!')
      reset(); setShowCreate(false); load()
    } catch (e) {
      toast.error(e.response?.data?.number?.[0] || 'Erro ao criar mesa')
    }
  }

  const handleOpenOrder = async (data) => {
    try {
      const order = await ordersAPI.create({ table: showOrder.id, ...data })
      toast.success(`Comanda #${order.data.id} aberta!`)
      resetOrder(); setShowOrder(null)
      navigate(`/orders/${order.data.id}`)
    } catch { toast.error('Erro ao abrir comanda') }
  }

  const filtered = filter === 'ALL' ? tables : tables.filter(t => t.status === filter)

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Mesas"
        subtitle={`${tables.length} mesas cadastradas`}
        actions={
          <>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
            {isManager && (
              <button className="btn-primary flex items-center gap-2" onClick={() => setShowCreate(true)}>
                <Plus size={16} /> Nova Mesa
              </button>
            )}
          </>
        }
      />

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {['ALL', ...TABLE_STATUS].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              filter === s
                ? 'bg-brand-gold text-brand-black'
                : 'bg-brand-dark text-brand-muted border border-brand-border hover:text-brand-white'
            }`}
          >
            {s === 'ALL' ? 'Todas' : s} {s !== 'ALL' && `(${tables.filter(t => t.status === s).length})`}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="h-64" />
      ) : filtered.length === 0 ? (
        <EmptyState icon={UtensilsCrossed} title="Nenhuma mesa encontrada" description="Ajuste o filtro ou cadastre novas mesas." />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {filtered.map(t => (
            <TableCard
              key={t.id}
              table={t}
              onStatusChange={handleStatusChange}
              onSelect={setShowOrder}
              onOpenComanda={(oid) => navigate(`/orders/${oid}`)}
              onCloseBill={handleCloseBill}
            />
          ))}
        </div>
      )}

      {/* Create Table Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Nova Mesa">
        <form onSubmit={handleSubmit(handleCreateTable)} className="space-y-4">
          <FormField label="Número da Mesa" error={errors.number?.message}>
            <input {...register('number', { required: 'Obrigatório', min: { value: 1, message: 'Mínimo 1' } })}
              type="number" className="input" placeholder="Ex: 15" />
          </FormField>
          <FormField label="Lugares" error={errors.seats?.message}>
            <input {...register('seats', { required: 'Obrigatório', min: { value: 1, message: 'Mínimo 1' } })}
              type="number" className="input" placeholder="Ex: 4" defaultValue={4} />
          </FormField>
          <FormField label="Observação">
            <textarea {...register('observation')} className="input resize-none" rows={2} placeholder="Opcional..." />
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setShowCreate(false)}>Cancelar</button>
            <button type="submit" className="btn-primary">Criar Mesa</button>
          </div>
        </form>
      </Modal>

      {/* Open Order Modal */}
      <Modal open={!!showOrder} onClose={() => setShowOrder(null)} title={`Abrir Comanda — Mesa ${showOrder?.number}`}>
        <form onSubmit={handleOrder(handleOpenOrder)} className="space-y-4">
          <FormField label="Nome do Cliente" error={errOrder.customer_name?.message}>
            <input {...regOrder('customer_name')} className="input" placeholder="Opcional" />
          </FormField>
          <FormField label="Número de Pessoas" error={errOrder.people_count?.message}>
            <input {...regOrder('people_count', { min: 1 })} type="number" className="input" defaultValue={1} />
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setShowOrder(null)}>Cancelar</button>
            <button type="submit" className="btn-primary">Abrir Comanda</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
