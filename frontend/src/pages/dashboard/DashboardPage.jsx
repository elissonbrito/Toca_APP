import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { TrendingUp, ShoppingBag, UtensilsCrossed, Ticket, DollarSign, Users, Flame } from 'lucide-react'
import { dashboardAPI } from '../../services/api'
import { StatCard, LoadingSpinner, PageHeader } from '../../components/ui/index.jsx'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-brand-card border border-brand-border rounded-lg p-3 text-sm">
      <p className="text-brand-muted mb-1">{label}</p>
      <p className="text-brand-gold font-bold">R$ {Number(payload[0].value).toFixed(2)}</p>
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    dashboardAPI.stats()
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner size="lg" className="h-64" />

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle={`Visão geral operacional — ${new Date().toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}`}
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={DollarSign}
          label="Faturamento Hoje"
          value={`R$ ${Number(data?.today?.revenue || 0).toFixed(2)}`}
          sub={`${data?.today?.orders || 0} pedidos`}
          accent
        />
        <StatCard
          icon={TrendingUp}
          label="Faturamento Mensal"
          value={`R$ ${Number(data?.monthly_revenue || 0).toFixed(2)}`}
        />
        <StatCard
          icon={UtensilsCrossed}
          label="Mesas Ocupadas"
          value={`${data?.tables?.occupied || 0}/${data?.tables?.total || 0}`}
          sub={`${data?.tables?.occupation_rate || 0}% de ocupação`}
        />
        <StatCard
          icon={Ticket}
          label="Na Fila"
          value={data?.queue?.waiting || 0}
          sub="aguardando atendimento"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <div className="card p-5 lg:col-span-2">
          <h2 className="font-display text-base font-semibold text-brand-white mb-4">
            Faturamento — Últimos 7 dias
          </h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data?.daily_revenue || []} barSize={32}>
              <XAxis dataKey="date" tick={{ fill: '#9A8A7A', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#9A8A7A', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={v => `R$${v}`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(201,168,76,0.06)' }} />
              <Bar dataKey="revenue" radius={[4, 4, 0, 0]}>
                {(data?.daily_revenue || []).map((_, i) => (
                  <Cell key={i} fill={i === 6 ? '#C9A84C' : '#8B1A1A'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top Products */}
        <div className="card p-5">
          <h2 className="font-display text-base font-semibold text-brand-white mb-4">
            Produtos Mais Vendidos
          </h2>
          <div className="space-y-3">
            {(data?.top_products || []).slice(0, 6).map((p, i) => (
              <div key={p.product_name} className="flex items-center gap-3">
                <span className="text-xs font-mono text-brand-muted w-4">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-brand-white truncate">{p.product_name}</p>
                  <div className="flex gap-2 items-center mt-0.5">
                    <div className="h-1 rounded-full bg-brand-border flex-1">
                      <div
                        className="h-full rounded-full bg-brand-gold"
                        style={{ width: `${Math.min(100, (p.total_qty / (data.top_products[0]?.total_qty || 1)) * 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-brand-muted flex-shrink-0">{p.total_qty}x</span>
                  </div>
                </div>
              </div>
            ))}
            {!(data?.top_products?.length) && (
              <p className="text-brand-muted text-sm text-center py-4">Nenhum dado disponível</p>
            )}
          </div>
        </div>
      </div>

      {/* Active Orders by Status */}
      <div className="card p-5">
        <h2 className="font-display text-base font-semibold text-brand-white mb-4">Pedidos de Hoje por Status</h2>
        <div className="flex flex-wrap gap-3">
          {(data?.orders_by_status || []).map(s => (
            <div key={s.status} className="flex items-center gap-2 bg-brand-dark px-4 py-2 rounded-lg border border-brand-border">
              <span className="text-brand-muted text-sm">{s.status}</span>
              <span className="text-brand-white font-bold text-lg">{s.count}</span>
            </div>
          ))}
          {!data?.orders_by_status?.length && (
            <p className="text-brand-muted text-sm">Nenhum pedido hoje ainda.</p>
          )}
        </div>
      </div>
    </div>
  )
}
