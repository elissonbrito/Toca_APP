import { useCallback, useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { Printer, Plus, Trash2, Save, RefreshCw, ScanLine, FileText } from 'lucide-react'
import { printingAPI } from '../../services/api'
import { Modal, PageHeader, FormField, LoadingSpinner, EmptyState } from '../../components/ui/index.jsx'
import { listQzPrinters, printJob } from '../../services/qz'

const SECTORS = [
  { value: 'BAR', label: 'Bar / Bebidas' },
  { value: 'PARRILLA', label: 'Parrilla' },
  { value: 'COZINHA', label: 'Cozinha' },
  { value: 'CAIXA', label: 'Caixa / Recibo' },
]
const BLANK_PRINTER = { name: '', sector: 'BAR', qz_printer_name: '', is_active: true, copies: 1 }

export default function PrinterSettingsPage() {
  const [loading, setLoading] = useState(true)
  const [printers, setPrinters] = useState([])
  const [settings, setSettings] = useState(null)
  const [editing, setEditing] = useState(null) // printer | 'new' | null
  const [form, setForm] = useState(BLANK_PRINTER)
  const [detected, setDetected] = useState([])
  const [savingSettings, setSavingSettings] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    Promise.all([printingAPI.listPrinters(), printingAPI.getSettings()])
      .then(([p, s]) => {
        setPrinters(p.data.results || p.data)
        setSettings(s.data)
      })
      .catch(() => toast.error('Erro ao carregar configuração de impressão'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const detectPrinters = async () => {
    try {
      const found = await listQzPrinters()
      setDetected(found)
      if (!found.length) toast.info('Nenhuma impressora detectada pelo QZ Tray')
    } catch {
      toast.error('QZ Tray não está conectado nesta máquina')
    }
  }

  const openNew = () => { setForm(BLANK_PRINTER); setEditing('new') }
  const openEdit = (p) => { setForm({ ...p }); setEditing(p) }

  const savePrinter = async () => {
    if (!form.name || !form.qz_printer_name) {
      toast.error('Informe o nome e a impressora do QZ Tray')
      return
    }
    try {
      if (editing === 'new') await printingAPI.createPrinter(form)
      else await printingAPI.updatePrinter(editing.id, form)
      toast.success('Impressora salva')
      setEditing(null); load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao salvar impressora')
    }
  }

  const removePrinter = async (p) => {
    if (!confirm(`Remover a impressora "${p.name}"?`)) return
    try { await printingAPI.deletePrinter(p.id); toast.success('Removida'); load() }
    catch { toast.error('Erro ao remover') }
  }

  const saveSettings = async () => {
    setSavingSettings(true)
    try {
      const r = await printingAPI.saveSettings(settings)
      setSettings(r.data)
      toast.success('Configuração salva')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao salvar configuração')
    } finally {
      setSavingSettings(false)
    }
  }

  const testPrint = async (p) => {
    try {
      const body = [
        settings.header_title || 'Toca do Espanhol',
        '-'.repeat(settings.paper_width || 48),
        'TESTE DE IMPRESSAO',
        `Impressora: ${p.name}`,
        `Setor: ${p.sector}`,
        new Date().toLocaleString('pt-BR'),
        '-'.repeat(settings.paper_width || 48),
        settings.footer_text || '',
      ].join('\n')
      await printJob(p.qz_printer_name, body, settings, { copies: 1 })
      toast.success('Teste enviado')
    } catch (e) {
      toast.error('Falha no teste: ' + String(e?.message || e).slice(0, 120))
    }
  }

  const setS = (k, v) => setSettings((s) => ({ ...s, [k]: v }))

  if (loading || !settings) return <LoadingSpinner size="lg" className="h-64" />

  return (
    <div className="animate-fade-in space-y-6 max-w-4xl">
      <PageHeader
        title="Impressoras"
        subtitle="Cadastro de impressoras térmicas e configuração geral de impressão"
        actions={
          <>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
            <button onClick={openNew} className="btn-primary flex items-center gap-2"><Plus size={16} /> Nova</button>
          </>
        }
      />

      {/* Impressoras */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b border-brand-border flex items-center gap-2">
          <Printer size={16} className="text-brand-gold" />
          <h2 className="font-display text-base font-semibold text-brand-white">Impressoras cadastradas</h2>
        </div>
        {printers.length === 0 ? (
          <EmptyState icon={Printer} title="Nenhuma impressora" description="Cadastre a impressora do bar e da parrilla." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px]">
              <thead>
                <tr className="border-b border-brand-border">
                  <th className="table-header text-left p-3">Nome</th>
                  <th className="table-header text-left p-3">Setor</th>
                  <th className="table-header text-left p-3">QZ Tray</th>
                  <th className="table-header text-center p-3">Vias</th>
                  <th className="table-header text-center p-3">Ativa</th>
                  <th className="table-header p-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border">
                {printers.map((p) => (
                  <tr key={p.id} className="hover:bg-brand-dark/50">
                    <td className="p-3 text-brand-white">{p.name}</td>
                    <td className="p-3 text-brand-muted">{p.sector_display}</td>
                    <td className="p-3 text-brand-muted font-mono text-xs">{p.qz_printer_name}</td>
                    <td className="p-3 text-center text-brand-muted">{p.copies}</td>
                    <td className="p-3 text-center">{p.is_active ? '✔' : '—'}</td>
                    <td className="p-3 text-right whitespace-nowrap">
                      <button className="btn-ghost text-xs py-1 px-2" onClick={() => testPrint(p)}>testar</button>
                      <button className="btn-ghost text-xs py-1 px-2" onClick={() => openEdit(p)}>editar</button>
                      <button className="text-brand-muted hover:text-red-500 ml-1" onClick={() => removePrinter(p)}>
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Configuração geral */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2">
          <FileText size={16} className="text-brand-gold" />
          <h2 className="font-display text-base font-semibold text-brand-white">Configuração geral de impressão</h2>
        </div>
        <div className="grid sm:grid-cols-2 gap-4">
          <FormField label="Título do cabeçalho">
            <input className="input" value={settings.header_title || ''} onChange={(e) => setS('header_title', e.target.value)} />
          </FormField>
          <FormField label="Rodapé">
            <input className="input" value={settings.footer_text || ''} onChange={(e) => setS('footer_text', e.target.value)} />
          </FormField>
          <FormField label="Marca d'água">
            <input className="input" value={settings.watermark_text || ''} onChange={(e) => setS('watermark_text', e.target.value)} />
          </FormField>
          <FormField label="Logo (data URL base64, opcional)">
            <input className="input" placeholder="data:image/png;base64,..." value={settings.header_image || ''} onChange={(e) => setS('header_image', e.target.value)} />
          </FormField>
          <FormField label="Fonte">
            <select className="input" value={settings.font_family} onChange={(e) => setS('font_family', e.target.value)}>
              <option value="A">Padrão (A)</option>
              <option value="B">Condensada (B)</option>
            </select>
          </FormField>
          <FormField label="Tamanho (1 a 4)">
            <input type="number" min="1" max="4" className="input" value={settings.font_size} onChange={(e) => setS('font_size', Number(e.target.value))} />
          </FormField>
          <FormField label="Alinhamento">
            <select className="input" value={settings.align} onChange={(e) => setS('align', e.target.value)}>
              <option value="left">Esquerda</option>
              <option value="center">Centro</option>
              <option value="right">Direita</option>
            </select>
          </FormField>
          <FormField label="Largura do papel (colunas)">
            <input type="number" min="24" max="96" className="input" value={settings.paper_width} onChange={(e) => setS('paper_width', Number(e.target.value))} />
          </FormField>
          <FormField label="Margem esquerda (colunas)">
            <input type="number" min="0" max="20" className="input" value={settings.margin_left} onChange={(e) => setS('margin_left', Number(e.target.value))} />
          </FormField>
          <FormField label="Linhas em branco no topo">
            <input type="number" min="0" max="10" className="input" value={settings.margin_top} onChange={(e) => setS('margin_top', Number(e.target.value))} />
          </FormField>
          <FormField label="Linhas em branco no fim">
            <input type="number" min="0" max="10" className="input" value={settings.margin_bottom} onChange={(e) => setS('margin_bottom', Number(e.target.value))} />
          </FormField>
        </div>
        <div className="flex flex-wrap gap-4 pt-1">
          <label className="flex items-center gap-2 text-sm text-brand-white">
            <input type="checkbox" checked={!!settings.bold} onChange={(e) => setS('bold', e.target.checked)} /> Negrito
          </label>
          <label className="flex items-center gap-2 text-sm text-brand-white">
            <input type="checkbox" checked={!!settings.cut_paper} onChange={(e) => setS('cut_paper', e.target.checked)} /> Cortar papel ao final
          </label>
        </div>
        <div className="flex justify-end">
          <button className="btn-primary flex items-center gap-2" onClick={saveSettings} disabled={savingSettings}>
            <Save size={16} /> {savingSettings ? 'Salvando…' : 'Salvar configuração'}
          </button>
        </div>
      </div>

      {/* Modal impressora */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title={editing === 'new' ? 'Nova impressora' : 'Editar impressora'}>
        <div className="space-y-4">
          <FormField label="Nome">
            <input className="input" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Ex: Impressora do Bar" />
          </FormField>
          <FormField label="Setor">
            <select className="input" value={form.sector} onChange={(e) => setForm((f) => ({ ...f, sector: e.target.value }))}>
              {SECTORS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </FormField>
          <FormField label="Impressora no QZ Tray">
            <div className="flex gap-2">
              <input className="input flex-1" value={form.qz_printer_name} onChange={(e) => setForm((f) => ({ ...f, qz_printer_name: e.target.value }))} placeholder="Nome exato no sistema" />
              <button type="button" className="btn-ghost px-3 flex items-center gap-1" onClick={detectPrinters}>
                <ScanLine size={14} /> detectar
              </button>
            </div>
            {detected.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {detected.map((d) => (
                  <button key={d} type="button" onClick={() => setForm((f) => ({ ...f, qz_printer_name: d }))}
                    className="text-xs px-2 py-1 rounded border border-brand-border text-brand-muted hover:text-brand-white">
                    {d}
                  </button>
                ))}
              </div>
            )}
          </FormField>
          <div className="flex gap-4">
            <FormField label="Vias">
              <input type="number" min="1" max="5" className="input w-24" value={form.copies} onChange={(e) => setForm((f) => ({ ...f, copies: Number(e.target.value) }))} />
            </FormField>
            <label className="flex items-center gap-2 text-sm text-brand-white mt-7">
              <input type="checkbox" checked={!!form.is_active} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))} /> Ativa
            </label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button className="btn-ghost" onClick={() => setEditing(null)}>Cancelar</button>
            <button className="btn-primary" onClick={savePrinter}>Salvar</button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
