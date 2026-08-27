import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, ChefHat } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { ordersAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, FormField, ConfirmDialog } from '../../components/ui/index.jsx'

const SECTORS = ['COZINHA', 'PARRILLA', 'BAR']
const STATUS_FLOW = {
  ABERTO: ['PREPARANDO', 'CANCELADO'],
  PREPARANDO: ['PRONTO', 'CANCELADO'],
  PRONTO: ['FINALIZADO'],
}

export default function OrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddItem, setShowAddItem] = useState(false)
  const [confirmCancel, setConfirmCancel] = useState(null)
  const { register, handleSubmit, reset, formState: { errors } } = useForm()

  const load = useCallback(() => {
    ordersAPI.get(id)
      .then(r => setOrder(r.data))
      .catch(() => navigate('/orders'))
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => { load() }, [load])

  const handleAddItem = async (data) => {
    try {
      await ordersAPI.addItem(id, { ...data, unit_price: Number(data.unit_price), quantity: Number(data.quantity) })
      toast.success('Item adicionado!')
      reset(); setShowAddItem(false); load()
    } catch { toast.error('Erro ao adicionar item') }
  }

  const handleRemoveItem = async (itemId) => {
    try {
      await ordersAPI.removeItem(id, itemId)
      toast.success('Item removido'); load()
    } catch { toast.error('Erro ao remover item') }
  }

  const handleStatus = async (status) => {
    try {
      await ordersAPI.updateStatus(id, status)
      toast.success(`Status → ${status}`); load()
    } catch { toast.error('Erro ao atualizar status') }
  }

  if (loading) return <LoadingSpinner size="lg" className="h-64" />
  if (!order) return null

  const canEdit = ['ABERTO'].includes(order.status)
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
      {nextStatuses.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {nextStatuses.map(s => (
            <button
              key={s}
              onClick={() => s === 'CANCELADO' ? setConfirmCancel(s) : handleStatus(s)}
              className={s === 'CANCELADO' ? 'btn-danger' : s === 'FINALIZADO' ? 'btn-gold' : 'btn-primary'}
            >
              → {s}
            </button>
          ))}
          {canEdit && (
            <button className="btn-ghost flex items-center gap-2" onClick={() => setShowAddItem(true)}>
              <Plus size={16} /> Adicionar Item
            </button>
          )}
        </div>
      )}

      {/* Items Table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-brand-border">
          <h2 className="font-display text-base font-semibold text-brand-white">Itens do Pedido</h2>
          <span className="text-brand-muted text-sm">{order.items?.length || 0} itens</span>
        </div>
        {!order.items?.length ? (
          <div className="p-8 text-center">
            <ChefHat size={40} className="text-brand-border mx-auto mb-3" />
            <p className="text-brand-muted">Nenhum item adicionado ainda.</p>
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
                        <button onClick={() => handleRemoveItem(item.id)} className="text-brand-muted hover:text-red-500 transition-colors">
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

      {/* Add Item Modal */}
      <Modal open={showAddItem} onClose={() => setShowAddItem(false)} title="Adicionar Item">
        <form onSubmit={handleSubmit(handleAddItem)} className="space-y-4">
          <FormField label="Produto" error={errors.product_name?.message}>
            <input {...register('product_name', { required: 'Obrigatório' })} className="input" placeholder="Nome do produto" />
          </FormField>
          <div className="grid grid-cols-2 gap-3">
            <FormField label="Quantidade" error={errors.quantity?.message}>
              <input {...register('quantity', { required: true, min: 1 })} type="number" className="input" defaultValue={1} />
            </FormField>
            <FormField label="Preço Unitário" error={errors.unit_price?.message}>
              <input {...register('unit_price', { required: true, min: 0 })} type="number" step="0.01" className="input" placeholder="0.00" />
            </FormField>
          </div>
          <FormField label="Setor">
            <select {...register('sector')} className="input">
              {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </FormField>
          <FormField label="Observações">
            <textarea {...register('observations')} className="input resize-none" rows={2} placeholder="Sem cebola, etc." />
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setShowAddItem(false)}>Cancelar</button>
            <button type="submit" className="btn-primary">Adicionar</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!confirmCancel}
        onClose={() => setConfirmCancel(null)}
        onConfirm={() => { handleStatus('CANCELADO'); setConfirmCancel(null) }}
        title="Cancelar Pedido"
        message="Tem certeza que deseja cancelar este pedido? Esta ação não pode ser desfeita."
        danger
      />
    </div>
  )
}
