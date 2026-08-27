import { useState, useEffect, useCallback } from 'react'
import { Plus, Ticket, RefreshCw, Volume2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { queueAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, PageHeader, FormField } from '../../components/ui/index.jsx'

export default function QueuePage() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('AGUARDANDO')
  const [showCreate, setShowCreate] = useState(false)
  const [display, setDisplay] = useState(null)
  const { register, handleSubmit, reset } = useForm()

  const load = useCallback(() => {
    const params = filter !== 'ALL' ? { status: filter } : {}
    Promise.all([
      queueAPI.list(params),
      queueAPI.publicDisplay(),
    ])
      .then(([listRes, displayRes]) => {
        setTickets(listRes.data.results || listRes.data)
        setDisplay(displayRes.data)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [filter])

  useEffect(() => { load() }, [load])

  const handleCreate = async (data) => {
    try {
      const r = await queueAPI.create(data)
      toast.success(`Senha ${r.data.code} gerada!`)
      reset(); setShowCreate(false); load()
    } catch { toast.error('Erro ao gerar senha') }
  }

  const handleCallNext = async () => {
    try {
      const r = await queueAPI.callNext()
      toast.success(`Chamando senha ${r.data.code}!`)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Nenhuma senha na fila')
    }
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Fila de Espera"
        subtitle="Gerenciamento de senhas"
        actions={
          <>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
            <button onClick={handleCallNext} className="btn-gold flex items-center gap-2">
              <Volume2 size={16} /> Chamar Próxima
            </button>
            <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
              <Plus size={16} /> Gerar Senha
            </button>
          </>
        }
      />

      {/* Display board */}
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

      {/* Filter */}
      <div className="flex gap-2 flex-wrap">
        {['ALL', 'AGUARDANDO', 'CHAMADO', 'FINALIZADO', 'CANCELADO'].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              filter === s ? 'bg-brand-gold text-brand-black' : 'bg-brand-dark text-brand-muted border border-brand-border hover:text-brand-white'
            }`}
          >
            {s === 'ALL' ? 'Todas' : s}
          </button>
        ))}
      </div>

      {/* Ticket List */}
      {loading ? <LoadingSpinner size="lg" className="h-48" /> : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-brand-border">
                <th className="table-header text-left p-4">Código</th>
                <th className="table-header text-left p-4">Cliente</th>
                <th className="table-header text-center p-4">Pessoas</th>
                <th className="table-header text-center p-4">Status</th>
                <th className="table-header text-left p-4">Gerado em</th>
                <th className="table-header text-left p-4">Chamado em</th>
                <th className="table-header p-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {tickets.map(t => (
                <tr key={t.id} className="hover:bg-brand-dark/50 transition-colors">
                  <td className="p-4 font-mono font-bold text-brand-gold">{t.code}</td>
                  <td className="p-4 text-brand-white">{t.customer_name || '—'}</td>
                  <td className="p-4 text-center text-brand-muted">{t.people_count}</td>
                  <td className="p-4 text-center"><StatusBadge status={t.status} label={t.status_display} /></td>
                  <td className="p-4 text-brand-muted text-sm">
                    {new Date(t.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="p-4 text-brand-muted text-sm">
                    {t.called_at ? new Date(t.called_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '—'}
                  </td>
                  <td className="p-4">
                    {t.status === 'AGUARDANDO' && (
                      <button onClick={async () => { await queueAPI.cancel(t.id); load() }}
                        className="text-xs text-red-500 hover:text-red-400 transition-colors">Cancelar</button>
                    )}
                    {t.status === 'CHAMADO' && (
                      <button onClick={async () => { await queueAPI.finalize(t.id); load() }}
                        className="text-xs text-green-400 hover:text-green-300 transition-colors">Finalizar</button>
                    )}
                  </td>
                </tr>
              ))}
              {tickets.length === 0 && (
                <tr><td colSpan={7} className="p-8 text-center text-brand-muted">Nenhuma senha encontrada.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Gerar Nova Senha">
        <form onSubmit={handleSubmit(handleCreate)} className="space-y-4">
          <FormField label="Nome do Cliente">
            <input {...register('customer_name')} className="input" placeholder="Opcional" />
          </FormField>
          <FormField label="Número de Pessoas">
            <input {...register('people_count', { min: 1 })} type="number" className="input" defaultValue={1} />
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setShowCreate(false)}>Cancelar</button>
            <button type="submit" className="btn-gold">Gerar Senha</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
