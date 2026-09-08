import { useCallback, useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { BarChart3, RefreshCw, Trophy, UserRound, Trash2 } from 'lucide-react'
import { reportsAPI } from '../../services/api'
import { LoadingSpinner, PageHeader, EmptyState } from '../../components/ui/index.jsx'

const MONTHS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
const money = (v) => `R$ ${Number(v || 0).toFixed(2)}`

export default function ReportsPage() {
  const now = new Date()
  const [year, setYear] = useState(now.getFullYear())
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [loading, setLoading] = useState(true)
  const [waiters, setWaiters] = useState([])
  const [items, setItems] = useState([])
  const [detail, setDetail] = useState(null) // { waiter_name, rows }

  const load = useCallback(() => {
    setLoading(true)
    setDetail(null)
    Promise.all([
      reportsAPI.salesByWaiter({ year, month }),
      reportsAPI.itemRanking({ year, month }),
    ])
      .then(([w, i]) => {
        setWaiters(w.data.rows || [])
        setItems(i.data.rows || [])
      })
      .catch(() => toast.error('Erro ao carregar relatórios'))
      .finally(() => setLoading(false))
  }, [year, month])

  useEffect(() => { load() }, [load])

  const openDetail = async (row) => {
    try {
      const r = await reportsAPI.waiterDetail({ year, month, waiter: row.waiter_id })
      setDetail({ waiter_name: row.waiter_name, rows: r.data.rows || [] })
    } catch { toast.error('Erro ao abrir o detalhe do garçom') }
  }

  const years = [now.getFullYear(), now.getFullYear() - 1, now.getFullYear() - 2]
  const topSeller = waiters[0]

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Relatórios de Vendas"
        subtitle="Produtividade por garçom e ranking de itens — base para metas"
        actions={<button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>}
      />

      <div className="flex gap-3 flex-wrap items-center">
        <select className="input w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
          {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
        </select>
        <select className="input w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {years.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {loading ? (
        <LoadingSpinner size="lg" className="h-64" />
      ) : (
        <>
          {topSeller && (
            <div className="card p-4 border-brand-gold/40 bg-brand-gold/5 flex items-center gap-3">
              <Trophy className="text-brand-gold" size={22} />
              <div>
                <p className="text-brand-muted text-xs">Maior venda do mês</p>
                <p className="text-brand-white font-semibold">
                  {topSeller.waiter_name} — {money(topSeller.revenue)} ({topSeller.sold_qty} itens)
                </p>
              </div>
            </div>
          )}

          {/* Ranking de garçons */}
          <div className="card overflow-hidden">
            <div className="flex items-center gap-2 p-4 border-b border-brand-border">
              <UserRound size={16} className="text-brand-gold" />
              <h2 className="font-display text-base font-semibold text-brand-white">Ranking de Garçons</h2>
            </div>
            {waiters.length === 0 ? (
              <EmptyState icon={BarChart3} title="Sem vendas no período" description="Nenhum item lançado neste mês." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px]">
                  <thead>
                    <tr className="border-b border-brand-border">
                      <th className="table-header text-left p-3">#</th>
                      <th className="table-header text-left p-3">Garçom</th>
                      <th className="table-header text-right p-3">Vendas</th>
                      <th className="table-header text-right p-3">Itens</th>
                      <th className="table-header text-right p-3">Qtd</th>
                      <th className="table-header text-right p-3">Retirados</th>
                      <th className="table-header text-right p-3">R$ retirado</th>
                      <th className="table-header p-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border">
                    {waiters.map((r, idx) => (
                      <tr key={r.waiter_id} className="hover:bg-brand-dark/50">
                        <td className="p-3 text-brand-muted">{idx + 1}</td>
                        <td className="p-3 text-brand-white">{r.waiter_name}</td>
                        <td className="p-3 text-right font-medium text-brand-gold">{money(r.revenue)}</td>
                        <td className="p-3 text-right text-brand-muted">{r.sold_items}</td>
                        <td className="p-3 text-right text-brand-muted">{r.sold_qty}</td>
                        <td className="p-3 text-right">
                          <span className={r.removed_items ? 'text-red-400' : 'text-brand-muted'}>
                            {r.removed_items ? <Trash2 size={12} className="inline mr-1" /> : null}{r.removed_items}
                          </span>
                        </td>
                        <td className="p-3 text-right text-red-400/80">{money(r.removed_value)}</td>
                        <td className="p-3 text-right">
                          <button className="btn-ghost text-xs py-1 px-2" onClick={() => openDetail(r)}>ver itens</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {detail && (
            <div className="card overflow-hidden">
              <div className="flex items-center justify-between p-4 border-b border-brand-border">
                <h2 className="font-display text-base font-semibold text-brand-white">
                  O que {detail.waiter_name} vendeu
                </h2>
                <button className="btn-ghost text-xs py-1 px-2" onClick={() => setDetail(null)}>fechar</button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[420px]">
                  <thead>
                    <tr className="border-b border-brand-border">
                      <th className="table-header text-left p-3">Item</th>
                      <th className="table-header text-right p-3">Qtd</th>
                      <th className="table-header text-right p-3">Receita</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border">
                    {detail.rows.map((r) => (
                      <tr key={r.product_name} className="hover:bg-brand-dark/50">
                        <td className="p-3 text-brand-white">{r.product_name}</td>
                        <td className="p-3 text-right text-brand-muted">{r.qty}</td>
                        <td className="p-3 text-right text-brand-gold">{money(r.revenue)}</td>
                      </tr>
                    ))}
                    {detail.rows.length === 0 && (
                      <tr><td colSpan={3} className="p-4 text-center text-brand-muted">Nada vendido no período.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Ranking de itens */}
          <div className="card overflow-hidden">
            <div className="flex items-center gap-2 p-4 border-b border-brand-border">
              <Trophy size={16} className="text-brand-gold" />
              <h2 className="font-display text-base font-semibold text-brand-white">Ranking de Itens Vendidos</h2>
            </div>
            {items.length === 0 ? (
              <EmptyState icon={BarChart3} title="Sem itens no período" description="Nenhuma venda registrada neste mês." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[480px]">
                  <thead>
                    <tr className="border-b border-brand-border">
                      <th className="table-header text-left p-3">#</th>
                      <th className="table-header text-left p-3">Item</th>
                      <th className="table-header text-right p-3">Qtd</th>
                      <th className="table-header text-right p-3">Comandas</th>
                      <th className="table-header text-right p-3">Receita</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-border">
                    {items.map((r, idx) => (
                      <tr key={r.product_name} className="hover:bg-brand-dark/50">
                        <td className="p-3 text-brand-muted">{idx + 1}</td>
                        <td className="p-3 text-brand-white">{r.product_name}</td>
                        <td className="p-3 text-right text-brand-muted">{r.qty}</td>
                        <td className="p-3 text-right text-brand-muted">{r.orders}</td>
                        <td className="p-3 text-right text-brand-gold">{money(r.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
