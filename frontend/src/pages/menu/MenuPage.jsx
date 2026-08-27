import { useCallback, useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import {
  BookOpen, Plus, RefreshCw, Edit2, Trash2, Search,
  CheckCircle2, AlertTriangle, XCircle, ShieldCheck,
} from 'lucide-react'
import { menuAPI } from '../../services/api'
import { Modal, LoadingSpinner, PageHeader, FormField, EmptyState } from '../../components/ui/index.jsx'
import { useAuth } from '../../context/AuthContext'

const SECTORS = [
  { value: 'COZINHA', label: 'Cozinha' },
  { value: 'PARRILLA', label: 'Parrilla' },
  { value: 'BAR', label: 'Bar' },
]

function FiscalPill({ status }) {
  if (!status) return null
  if (status.errors?.length) {
    return <span className="badge border bg-red-900/40 text-red-400 border-red-800 inline-flex items-center gap-1">
      <XCircle size={12} /> {status.errors.length} pendência(s)
    </span>
  }
  if (status.warnings?.length) {
    return <span className="badge border bg-yellow-900/40 text-yellow-400 border-yellow-800 inline-flex items-center gap-1">
      <AlertTriangle size={12} /> {status.warnings.length} alerta(s)
    </span>
  }
  return <span className="badge border bg-green-900/40 text-green-400 border-green-800 inline-flex items-center gap-1">
    <CheckCircle2 size={12} /> Conforme
  </span>
}

const BLANK = {
  category: '', name: '', description: '', sector: 'COZINHA', price: '', preparation_minutes: '',
  is_active: true, sku: '', barcode_gtin: '', unit_commercial: 'UN', unit_taxable: 'UN',
  origem: '0', ncm: '', cest: '', cfop: '5102', csosn: '102', icms_aliquota: '',
  pis_cst: '49', pis_aliquota: '0', cofins_cst: '49', cofins_aliquota: '0', fisco_info: '',
}

export default function MenuPage() {
  const { isManager } = useAuth()
  const [items, setItems] = useState([])
  const [categories, setCategories] = useState([])
  const [choices, setChoices] = useState(null)
  const [ncmSug, setNcmSug] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ category: '', sector: '', search: '' })
  const [editing, setEditing] = useState(null) // item | 'new' | null
  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm({ defaultValues: BLANK })

  const csosn = watch('csosn')
  const needsCest = choices?.csosn_com_st?.includes(csosn)
  const needsIcms = choices?.csosn_com_icms_proprio?.includes(csosn)

  const load = useCallback(() => {
    setLoading(true)
    const p = {}
    if (filters.category) p.category = filters.category
    if (filters.sector) p.sector = filters.sector
    if (filters.search) p.search = filters.search
    Promise.all([
      menuAPI.listItems({ ...p, page_size: 200 }),
      menuAPI.listCategories({ page_size: 100 }),
    ]).then(([it, cat]) => {
      setItems(it.data.results || it.data)
      setCategories(cat.data.results || cat.data)
    }).catch(() => toast.error('Erro ao carregar o cardápio'))
      .finally(() => setLoading(false))
  }, [filters])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    menuAPI.fiscalChoices().then(r => setChoices(r.data)).catch(() => {})
    menuAPI.ncmSuggestions().then(r => setNcmSug(r.data)).catch(() => {})
  }, [])

  const openNew = () => { reset(BLANK); setEditing('new') }
  const openEdit = (it) => {
    reset({ ...BLANK, ...it, category: it.category, icms_aliquota: it.icms_aliquota ?? '' })
    setEditing(it)
  }

  const onSubmit = async (data) => {
    const payload = {
      ...data,
      preparation_minutes: data.preparation_minutes || null,
      icms_aliquota: data.icms_aliquota === '' ? null : data.icms_aliquota,
    }
    try {
      if (editing === 'new') {
        const r = await menuAPI.createItem(payload)
        toast.success(`"${r.data.name}" cadastrado.`)
      } else {
        const r = await menuAPI.updateItem(editing.id, payload)
        toast.success(`"${r.data.name}" atualizado.`)
      }
      setEditing(null); load()
    } catch (e) {
      const err = e.response?.data || {}
      const firstKey = Object.keys(err)[0]
      toast.error(err[firstKey]?.[0] || err[firstKey] || 'Erro ao salvar o item.')
    }
  }

  const remove = async (it) => {
    if (!confirm(`Remover "${it.name}" do cardápio?`)) return
    try { await menuAPI.deleteItem(it.id); toast.success('Item removido.'); load() }
    catch { toast.error('Não foi possível remover (item já usado em pedidos?).') }
  }

  const summary = useMemo(() => {
    const s = { ok: 0, warn: 0, err: 0 }
    for (const it of items) {
      const f = it.fiscal_status
      if (f?.errors?.length) s.err++
      else if (f?.warnings?.length) s.warn++
      else s.ok++
    }
    return s
  }, [items])

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Cardápio"
        subtitle={`${items.length} item(ns) — ${summary.ok} conformes · ${summary.warn} com alerta · ${summary.err} com pendência fiscal`}
        actions={
          <>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
            {isManager && (
              <button onClick={openNew} className="btn-primary flex items-center gap-2">
                <Plus size={16} /> Novo Item
              </button>
            )}
          </>
        }
      />

      {/* Filtros */}
      <div className="card p-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[180px]">
          <label className="label">Buscar</label>
          <div className="relative">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-brand-muted" />
            <input className="input pl-9" placeholder="nome, SKU, NCM, GTIN"
              value={filters.search} onChange={e => setFilters(f => ({ ...f, search: e.target.value }))} />
          </div>
        </div>
        <div className="min-w-[160px]">
          <label className="label">Categoria</label>
          <select className="input" value={filters.category}
            onChange={e => setFilters(f => ({ ...f, category: e.target.value }))}>
            <option value="">Todas</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="min-w-[140px]">
          <label className="label">Setor</label>
          <select className="input" value={filters.sector}
            onChange={e => setFilters(f => ({ ...f, sector: e.target.value }))}>
            <option value="">Todos</option>
            {SECTORS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
      </div>

      {loading ? <LoadingSpinner size="lg" className="h-64" /> : items.length === 0 ? (
        <EmptyState icon={BookOpen} title="Cardápio vazio"
          description="Cadastre os itens com a classificação fiscal para habilitar a NFC-e." />
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[860px]">
            <thead>
              <tr className="border-b border-brand-border">
                <th className="table-header text-left p-3">Item</th>
                <th className="table-header text-left p-3">Categoria</th>
                <th className="table-header text-center p-3">Setor</th>
                <th className="table-header text-right p-3">Preço</th>
                <th className="table-header text-left p-3">NCM</th>
                <th className="table-header text-center p-3">CSOSN</th>
                <th className="table-header text-left p-3">Fiscal</th>
                {isManager && <th className="table-header p-3"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {items.map(it => (
                <tr key={it.id} className={`hover:bg-brand-dark/50 ${!it.is_active ? 'opacity-50' : ''}`}>
                  <td className="p-3">
                    <div className="text-brand-white font-medium">{it.name}</div>
                    <div className="text-xs text-brand-muted">{it.sku}{it.barcode_gtin ? ` · GTIN ${it.barcode_gtin}` : ''}</div>
                  </td>
                  <td className="p-3 text-brand-muted text-sm">{it.category_name}</td>
                  <td className="p-3 text-center text-sm text-brand-muted">{it.sector_display}</td>
                  <td className="p-3 text-right text-brand-white">R$ {Number(it.price).toFixed(2)}</td>
                  <td className="p-3 text-brand-muted text-sm font-mono">{it.ncm || '—'}</td>
                  <td className="p-3 text-center text-brand-muted text-sm font-mono">{it.csosn}</td>
                  <td className="p-3"><FiscalPill status={it.fiscal_status} /></td>
                  {isManager && (
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <button onClick={() => openEdit(it)} className="text-brand-muted hover:text-brand-gold"><Edit2 size={15} /></button>
                        <button onClick={() => remove(it)} className="text-brand-muted hover:text-red-500"><Trash2 size={15} /></button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={!!editing} onClose={() => setEditing(null)}
        title={editing === 'new' ? 'Novo Item do Cardápio' : `Editar — ${editing?.name || ''}`} size="xl">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-h-[70vh] overflow-y-auto pr-1">

          {/* Operacional */}
          <section className="space-y-3">
            <h3 className="text-brand-gold text-xs font-semibold uppercase tracking-wide">Operacional</h3>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Nome" error={errors.name?.message}>
                <input {...register('name', { required: 'Obrigatório' })} className="input" />
              </FormField>
              <FormField label="Categoria" error={errors.category?.message}>
                <select {...register('category', { required: 'Obrigatório' })} className="input">
                  <option value="">Selecione…</option>
                  {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </FormField>
              <FormField label="Setor de preparo">
                <select {...register('sector')} className="input">
                  {SECTORS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </FormField>
              <FormField label="Preço de venda (R$)" error={errors.price?.message}>
                <input {...register('price', { required: 'Obrigatório' })} type="number" step="0.01" min="0" className="input" />
              </FormField>
              <FormField label="Tempo de preparo (min)">
                <input {...register('preparation_minutes')} type="number" min="0" className="input" />
              </FormField>
              <label className="flex items-center gap-2 text-sm text-brand-muted cursor-pointer mt-6">
                <input {...register('is_active')} type="checkbox" className="accent-brand-gold" /> Ativo no cardápio
              </label>
            </div>
            <FormField label="Descrição">
              <textarea {...register('description')} className="input" rows={2} />
            </FormField>
          </section>

          {/* Comercial */}
          <section className="space-y-3">
            <h3 className="text-brand-gold text-xs font-semibold uppercase tracking-wide">Comercial</h3>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="SKU (código interno)" error={errors.sku?.message}>
                <input {...register('sku', { required: 'Obrigatório' })} className="input font-mono" />
              </FormField>
              <FormField label="GTIN / EAN (código de barras)">
                <input {...register('barcode_gtin')} className="input font-mono" placeholder="deixe vazio p/ SEM GTIN" />
              </FormField>
              <FormField label="Unidade comercial">
                <select {...register('unit_commercial')} className="input">
                  {choices?.unidade?.map(u => <option key={u.value} value={u.value}>{u.value} — {u.label}</option>)}
                </select>
              </FormField>
              <FormField label="Unidade tributável">
                <select {...register('unit_taxable')} className="input">
                  {choices?.unidade?.map(u => <option key={u.value} value={u.value}>{u.value} — {u.label}</option>)}
                </select>
              </FormField>
            </div>
          </section>

          {/* Fiscal */}
          <section className="space-y-3">
            <h3 className="text-brand-gold text-xs font-semibold uppercase tracking-wide flex items-center gap-2">
              <ShieldCheck size={14} /> Fiscal — Simples Nacional (NFC-e)
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Origem da mercadoria">
                <select {...register('origem')} className="input">
                  {choices?.origem?.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </FormField>
              <FormField label="NCM (8 dígitos)" error={errors.ncm?.message}>
                <input {...register('ncm', { required: 'Obrigatório' })} list="ncm-list" className="input font-mono" maxLength={8} />
                <datalist id="ncm-list">
                  {ncmSug.map(n => <option key={n.ncm} value={n.ncm}>{n.descricao}</option>)}
                </datalist>
              </FormField>
              <FormField label={`CEST (7 dígitos)${needsCest ? ' — obrigatório p/ ICMS-ST' : ''}`}>
                <input {...register('cest', {
                  validate: v => (!needsCest || (v && v.replace(/\D/g, '').length === 7)) || 'CEST obrigatório p/ este CSOSN',
                })} className={`input font-mono ${needsCest ? 'border-brand-gold/50' : ''}`} maxLength={7} />
              </FormField>
              <FormField label="CFOP">
                <select {...register('cfop')} className="input">
                  {choices?.cfop?.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </FormField>
              <FormField label="CSOSN">
                <select {...register('csosn')} className="input">
                  {choices?.csosn?.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </FormField>
              {needsIcms && (
                <FormField label="Alíquota ICMS próprio (%)" error={errors.icms_aliquota?.message}>
                  <input {...register('icms_aliquota', { required: 'Obrigatório p/ este CSOSN' })}
                    type="number" step="0.01" min="0" className="input" />
                </FormField>
              )}
              <FormField label="CST PIS">
                <select {...register('pis_cst')} className="input">
                  {choices?.cst_pis_cofins?.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </FormField>
              <FormField label="Alíquota PIS (%)">
                <input {...register('pis_aliquota')} type="number" step="0.01" min="0" className="input" />
              </FormField>
              <FormField label="CST COFINS">
                <select {...register('cofins_cst')} className="input">
                  {choices?.cst_pis_cofins?.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </FormField>
              <FormField label="Alíquota COFINS (%)">
                <input {...register('cofins_aliquota')} type="number" step="0.01" min="0" className="input" />
              </FormField>
            </div>
            <FormField label="Informação adicional ao fisco">
              <input {...register('fisco_info')} className="input" />
            </FormField>
          </section>

          <div className="flex gap-3 justify-end pt-2 border-t border-brand-border">
            <button type="button" className="btn-ghost" onClick={() => setEditing(null)}>Cancelar</button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Salvando…' : 'Salvar'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
