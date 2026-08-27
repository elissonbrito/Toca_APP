import { useState, useEffect, useCallback } from 'react'
import { ScrollText, RefreshCw } from 'lucide-react'
import { auditAPI } from '../../services/api'
import { LoadingSpinner, PageHeader, EmptyState } from '../../components/ui/index.jsx'

const ACTION_COLORS = {
  LOGIN: 'text-green-400', LOGOUT: 'text-gray-400',
  CREATE: 'text-blue-400', UPDATE: 'text-yellow-400',
  DELETE: 'text-red-400',
}

export default function AuditPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    auditAPI.list({ search, page_size: 50 })
      .then(r => setLogs(r.data.results || r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [search])

  useEffect(() => { const t = setTimeout(load, 300); return () => clearTimeout(t) }, [load])

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Auditoria"
        subtitle="Registro de todas as ações do sistema"
        actions={<button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>}
      />

      <div>
        <input
          type="text"
          placeholder="Buscar por detalhes, entidade..."
          className="input max-w-md"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {loading ? <LoadingSpinner size="lg" className="h-64" /> : logs.length === 0 ? (
        <EmptyState icon={ScrollText} title="Nenhum log encontrado" description="Os logs de auditoria aparecerão aqui." />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-brand-border">
                <th className="table-header text-left p-4">Hora</th>
                <th className="table-header text-left p-4">Usuário</th>
                <th className="table-header text-center p-4">Ação</th>
                <th className="table-header text-left p-4">Entidade</th>
                <th className="table-header text-left p-4">Detalhes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {logs.map(log => (
                <tr key={log.id} className="hover:bg-brand-dark/50 transition-colors">
                  <td className="p-4 text-brand-muted text-xs font-mono whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="p-4 text-brand-white text-sm">{log.user_name || '—'}</td>
                  <td className="p-4 text-center">
                    <span className={`text-xs font-bold font-mono ${ACTION_COLORS[log.action] || 'text-brand-muted'}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="p-4 text-brand-muted text-sm">
                    {log.entity} {log.entity_id ? `#${log.entity_id}` : ''}
                  </td>
                  <td className="p-4 text-brand-muted text-sm max-w-xs truncate">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
