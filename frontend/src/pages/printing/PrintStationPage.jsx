import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'react-toastify'
import { Printer, Plug, PlugZap, RefreshCw, Play, Pause, RotateCcw, AlertTriangle } from 'lucide-react'
import { printingAPI } from '../../services/api'
import { PageHeader, LoadingSpinner } from '../../components/ui/index.jsx'
import { ensureQz, disconnectQz, qzActive, listQzPrinters, printJob } from '../../services/qz'

const POLL_MS = 4000

export default function PrintStationPage() {
  const [connected, setConnected] = useState(qzActive())
  const [connecting, setConnecting] = useState(false)
  const [auto, setAuto] = useState(true)
  const [settings, setSettings] = useState(null)
  const [qzPrinters, setQzPrinters] = useState([])
  const [pending, setPending] = useState([])
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)
  const busy = useRef(false)

  useEffect(() => {
    printingAPI.getSettings()
      .then((r) => setSettings(r.data))
      .catch(() => setSettings({}))
      .finally(() => setLoading(false))
  }, [])

  const connect = async () => {
    setConnecting(true)
    try {
      await ensureQz()
      setConnected(true)
      setQzPrinters(await listQzPrinters().catch(() => []))
      toast.success('QZ Tray conectado')
    } catch {
      setConnected(false)
      toast.error('Não foi possível conectar ao QZ Tray. Ele está aberto nesta máquina?')
    } finally {
      setConnecting(false)
    }
  }

  const disconnect = async () => {
    await disconnectQz().catch(() => {})
    setConnected(false)
  }

  const runQueue = useCallback(async () => {
    if (busy.current || !auto) return
    if (!qzActive()) { setConnected(false); return }
    busy.current = true
    try {
      const { data } = await printingAPI.pendingJobs()
      setPending(data)
      for (const job of data) {
        const target = job.qz_printer_name
        if (!target) {
          await printingAPI.markError(job.id, 'Impressora sem nome do QZ Tray configurado')
          continue
        }
        try {
          await printJob(target, job.body, settings || {}, { copies: job.copies || 1 })
          await printingAPI.markPrinted(job.id)
          setRecent((r) => [{ ...job, status: 'IMPRESSO' }, ...r].slice(0, 20))
        } catch (err) {
          await printingAPI.markError(job.id, String(err?.message || err).slice(0, 200))
          setRecent((r) => [{ ...job, status: 'ERRO' }, ...r].slice(0, 20))
        }
      }
      if (data.length) {
        const left = await printingAPI.pendingJobs()
        setPending(left.data)
      }
    } catch {
      /* rede — tenta de novo no próximo tick */
    } finally {
      busy.current = false
    }
  }, [auto, settings])

  useEffect(() => {
    const id = setInterval(runQueue, POLL_MS)
    runQueue()
    return () => clearInterval(id)
  }, [runQueue])

  const refreshPending = async () => {
    try { setPending((await printingAPI.pendingJobs()).data) } catch { /* noop */ }
  }

  const reprint = async (id) => {
    try { await printingAPI.reprint(id); toast.info('Reenviado para a fila'); refreshPending() }
    catch { toast.error('Erro ao reenfileirar') }
  }

  if (loading) return <LoadingSpinner size="lg" className="h-64" />

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Estação de Impressão"
        subtitle="Mantenha esta tela aberta num PC com QZ Tray e a impressora térmica instalada"
        actions={<button onClick={refreshPending} className="btn-ghost p-2"><RefreshCw size={16} /></button>}
      />

      <div className="card p-4 flex flex-wrap items-center gap-4">
        <span className={`inline-flex items-center gap-2 text-sm font-medium ${connected ? 'text-green-400' : 'text-red-400'}`}>
          {connected ? <PlugZap size={16} /> : <Plug size={16} />}
          {connected ? 'QZ Tray conectado' : 'QZ Tray desconectado'}
        </span>
        {connected ? (
          <button className="btn-ghost text-sm" onClick={disconnect}>Desconectar</button>
        ) : (
          <button className="btn-primary text-sm" onClick={connect} disabled={connecting}>
            {connecting ? 'Conectando…' : 'Conectar ao QZ Tray'}
          </button>
        )}
        <button
          className={`text-sm flex items-center gap-2 ${auto ? 'btn-gold' : 'btn-ghost'}`}
          onClick={() => setAuto((a) => !a)}
        >
          {auto ? <Pause size={14} /> : <Play size={14} />}
          {auto ? 'Impressão automática ligada' : 'Impressão automática pausada'}
        </button>
        {qzPrinters.length > 0 && (
          <span className="text-brand-muted text-xs">
            Impressoras no PC: {qzPrinters.join(', ')}
          </span>
        )}
      </div>

      {/* Fila pendente */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-brand-border">
          <h2 className="font-display text-base font-semibold text-brand-white flex items-center gap-2">
            <Printer size={16} className="text-brand-gold" /> Fila de impressão (ordem de emissão)
          </h2>
          <span className="text-brand-muted text-sm">{pending.length} na fila</span>
        </div>
        {pending.length === 0 ? (
          <p className="p-8 text-center text-brand-muted">Nada na fila.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px]">
              <thead>
                <tr className="border-b border-brand-border">
                  <th className="table-header text-left p-3">#</th>
                  <th className="table-header text-left p-3">Setor</th>
                  <th className="table-header text-left p-3">Item</th>
                  <th className="table-header text-left p-3">Impressora</th>
                  <th className="table-header text-center p-3">Status</th>
                  <th className="table-header p-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border">
                {pending.map((j) => (
                  <tr key={j.id} className="hover:bg-brand-dark/50">
                    <td className="p-3 text-brand-muted">{j.id}</td>
                    <td className="p-3 text-brand-muted">{j.sector}</td>
                    <td className="p-3 text-brand-white">{j.title}</td>
                    <td className="p-3 text-brand-muted">{j.printer_name || '—'}</td>
                    <td className="p-3 text-center">
                      <span className={`badge border ${j.status === 'ERRO'
                        ? 'bg-red-900/40 text-red-400 border-red-800'
                        : 'bg-yellow-900/40 text-yellow-400 border-yellow-800'}`}>
                        {j.status_display || j.status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button className="btn-ghost text-xs py-1 px-2 inline-flex items-center gap-1" onClick={() => reprint(j.id)}>
                        <RotateCcw size={12} /> reenviar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Últimas impressões */}
      {recent.length > 0 && (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-brand-border">
            <h2 className="font-display text-base font-semibold text-brand-white">Últimas impressões (sessão)</h2>
          </div>
          <ul className="divide-y divide-brand-border">
            {recent.map((j, i) => (
              <li key={`${j.id}-${i}`} className="p-3 flex items-center gap-3 text-sm">
                {j.status === 'ERRO'
                  ? <AlertTriangle size={14} className="text-red-400" />
                  : <Printer size={14} className="text-green-400" />}
                <span className="text-brand-muted">#{j.id}</span>
                <span className="text-brand-white flex-1">{j.title}</span>
                <span className={j.status === 'ERRO' ? 'text-red-400' : 'text-green-400'}>{j.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
