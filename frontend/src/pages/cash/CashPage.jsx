import { useState, useEffect, useCallback } from 'react'
import { Banknote, Plus, X, RefreshCw } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { cashAPI, ordersAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, PageHeader, FormField } from '../../components/ui/index.jsx'

const METHODS = ['DINHEIRO', 'PIX', 'DEBITO', 'CREDITO']

export default function CashPage() {
  const [register, setRegister] = useState(null)
  const [loading, setLoading] = useState(true)
  const [payments, setPayments] = useState([])
  const [openOrders, setOpenOrders] = useState([])
  const [showOpen, setShowOpen] = useState(false)
  const [showClose, setShowClose] = useState(false)
  const [showPayment, setShowPayment] = useState(false)
  const { register: reg, handleSubmit, reset, formState: { errors } } = useForm()
  const { register: regP, handleSubmit: handleP, reset: resetP } = useForm()
  const { register: regC, handleSubmit: handleC, reset: resetC } = useForm()

  const load = useCallback(() => {
    setLoading(true)
    Promise.all([
      cashAPI.getCurrent().catch(() => ({ data: null })),
      cashAPI.listPayments({ page_size: 20 }).catch(() => ({ data: { results: [] } })),
      ordersAPI.list({ status: 'PRONTO' }).catch(() => ({ data: { results: [] } })),
    ]).then(([regRes, payRes, ordRes]) => {
      setRegister(regRes.data)
      setPayments(payRes.data.results || payRes.data)
      setOpenOrders(ordRes.data.results || ordRes.data)
    }).finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleOpen = async (data) => {
    try {
      await cashAPI.open({ initial_amount: Number(data.initial_amount) })
      toast.success('Caixa aberto!'); reset(); setShowOpen(false); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao abrir caixa') }
  }

  const handleClose = async (data) => {
    try {
      await cashAPI.close(register.id, { final_amount: Number(data.final_amount), observations: data.observations })
      toast.success('Caixa fechado!'); resetC(); setShowClose(false); load()
    } catch { toast.error('Erro ao fechar caixa') }
  }

  const handlePayment = async (data) => {
    try {
      await cashAPI.createPayment({ order: data.order, amount: Number(data.amount), payment_method: data.payment_method })
      toast.success('Pagamento registrado!'); resetP(); setShowPayment(false); load()
    } catch { toast.error('Erro ao registrar pagamento') }
  }

  if (loading) return <LoadingSpinner size="lg" className="h-64" />

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title="Caixa" subtitle="Controle financeiro" actions={
        <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
      } />

      {/* Register Status */}
      <div className="card p-6">
        {!register ? (
          <div className="text-center py-4">
            <Banknote size={40} className="text-brand-border mx-auto mb-3" />
            <p className="text-brand-muted mb-4">Nenhum caixa aberto no momento.</p>
            <button onClick={() => setShowOpen(true)} className="btn-gold">Abrir Caixa</button>
          </div>
        ) : (
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="font-display text-lg font-bold text-brand-white">Caixa #{register.id}</h2>
                <StatusBadge status={register.status} label={register.status_display} />
              </div>
              <p className="text-brand-muted text-sm">Aberto por {register.opened_by_name} às {new Date(register.opened_at).toLocaleTimeString('pt-BR')}</p>
              <p className="text-brand-muted text-sm">Fundo inicial: <span className="text-brand-gold">R$ {Number(register.initial_amount).toFixed(2)}</span></p>
            </div>
            <div className="flex gap-3">
              <button onClick={() => setShowPayment(true)} className="btn-primary flex items-center gap-2">
                <Plus size={16} /> Registrar Pagamento
              </button>
              <button onClick={() => setShowClose(true)} className="btn-danger">Fechar Caixa</button>
            </div>
          </div>
        )}
      </div>

      {/* Ready Orders */}
      {openOrders.length > 0 && register && (
        <div className="card p-4">
          <h3 className="font-semibold text-brand-white mb-3">Pedidos Prontos para Pagamento ({openOrders.length})</h3>
          <div className="flex flex-wrap gap-2">
            {openOrders.map(o => (
              <button key={o.id} onClick={() => setShowPayment(true)}
                className="bg-green-950/30 border border-green-800/50 text-green-400 text-sm px-3 py-1.5 rounded-lg hover:bg-green-950/60 transition-colors">
                Mesa {o.table?.number} — R$ {Number(o.total_amount).toFixed(2)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Payments */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b border-brand-border">
          <h3 className="font-display text-base font-semibold text-brand-white">Pagamentos Registrados</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-brand-border">
              <th className="table-header text-left p-4">Mesa</th>
              <th className="table-header text-left p-4">Método</th>
              <th className="table-header text-right p-4">Valor</th>
              <th className="table-header text-left p-4">Recebido por</th>
              <th className="table-header text-left p-4">Horário</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-border">
            {payments.map(p => (
              <tr key={p.id} className="hover:bg-brand-dark/50 transition-colors">
                <td className="p-4 text-brand-white">Mesa {p.order_table}</td>
                <td className="p-4">
                  <span className="text-xs bg-brand-border px-2 py-0.5 rounded text-brand-muted">{p.payment_method_display}</span>
                </td>
                <td className="p-4 text-right font-bold text-brand-gold">R$ {Number(p.amount).toFixed(2)}</td>
                <td className="p-4 text-brand-muted text-sm">{p.received_by_name}</td>
                <td className="p-4 text-brand-muted text-sm">{new Date(p.paid_at).toLocaleTimeString('pt-BR')}</td>
              </tr>
            ))}
            {payments.length === 0 && (
              <tr><td colSpan={5} className="p-6 text-center text-brand-muted">Nenhum pagamento registrado.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Open Cash Modal */}
      <Modal open={showOpen} onClose={() => setShowOpen(false)} title="Abrir Caixa">
        <form onSubmit={handleSubmit(handleOpen)} className="space-y-4">
          <FormField label="Fundo de Caixa (R$)" error={errors.initial_amount?.message}>
            <input {...reg('initial_amount', { required: 'Obrigatório', min: 0 })} type="number" step="0.01" className="input" placeholder="0.00" />
          </FormField>
          <div className="flex gap-3 justify-end">
            <button type="button" className="btn-ghost" onClick={() => setShowOpen(false)}>Cancelar</button>
            <button type="submit" className="btn-gold">Abrir Caixa</button>
          </div>
        </form>
      </Modal>

      {/* Close Cash Modal */}
      <Modal open={showClose} onClose={() => setShowClose(false)} title="Fechar Caixa">
        <form onSubmit={handleC(handleClose)} className="space-y-4">
          <FormField label="Valor Final em Caixa (R$)">
            <input {...regC('final_amount', { required: true })} type="number" step="0.01" className="input" placeholder="0.00" />
          </FormField>
          <FormField label="Observações">
            <textarea {...regC('observations')} className="input resize-none" rows={2} />
          </FormField>
          <div className="flex gap-3 justify-end">
            <button type="button" className="btn-ghost" onClick={() => setShowClose(false)}>Cancelar</button>
            <button type="submit" className="btn-danger">Fechar Caixa</button>
          </div>
        </form>
      </Modal>

      {/* Payment Modal */}
      <Modal open={showPayment} onClose={() => setShowPayment(false)} title="Registrar Pagamento">
        <form onSubmit={handleP(handlePayment)} className="space-y-4">
          <FormField label="Pedido (ID)">
            <input {...regP('order', { required: true })} type="number" className="input" placeholder="ID do pedido" />
          </FormField>
          <FormField label="Valor (R$)">
            <input {...regP('amount', { required: true, min: 0.01 })} type="number" step="0.01" className="input" />
          </FormField>
          <FormField label="Método de Pagamento">
            <select {...regP('payment_method', { required: true })} className="input">
              {METHODS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </FormField>
          <div className="flex gap-3 justify-end">
            <button type="button" className="btn-ghost" onClick={() => setShowPayment(false)}>Cancelar</button>
            <button type="submit" className="btn-primary">Registrar</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
