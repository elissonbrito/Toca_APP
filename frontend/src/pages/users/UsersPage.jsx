import { useState, useEffect, useCallback } from 'react'
import { Plus, Users, RefreshCw, Edit2, UserX } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { toast } from 'react-toastify'
import { usersAPI } from '../../services/api'
import { Modal, StatusBadge, LoadingSpinner, PageHeader, FormField, EmptyState } from '../../components/ui/index.jsx'
import { useAuth } from '../../context/AuthContext'

const ROLES = ['ADM_MAXIMO','GERENTE','GARCOM','COZINHA','PARRILLA','CAIXA','RECEPCAO']
const ROLE_LABELS = {
  ADM_MAXIMO: 'Administrador', GERENTE: 'Gerente', GARCOM: 'Garçom',
  COZINHA: 'Cozinha', PARRILLA: 'Parrilla', CAIXA: 'Caixa', RECEPCAO: 'Recepção'
}

export default function UsersPage() {
  const { isAdmin } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editing, setEditing] = useState(null)
  const { register, handleSubmit, reset, formState: { errors } } = useForm()
  const { register: regE, handleSubmit: handleE, reset: resetE, setValue } = useForm()

  const load = useCallback(() => {
    usersAPI.list()
      .then(r => setUsers(r.data.results || r.data))
      .catch(() => toast.error('Erro ao carregar usuários'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async (data) => {
    try {
      await usersAPI.create(data)
      toast.success('Usuário criado!'); reset(); setShowCreate(false); load()
    } catch (e) {
      const err = e.response?.data
      toast.error(err?.email?.[0] || err?.password?.[0] || 'Erro ao criar usuário')
    }
  }

  const handleUpdate = async (data) => {
    try {
      await usersAPI.update(editing.id, data)
      toast.success('Usuário atualizado!'); resetE(); setEditing(null); load()
    } catch { toast.error('Erro ao atualizar usuário') }
  }

  const handleDeactivate = async (user) => {
    if (!confirm(`Desativar ${user.name}?`)) return
    try {
      await usersAPI.delete(user.id)
      toast.success('Usuário desativado.'); load()
    } catch { toast.error('Erro') }
  }

  const openEdit = (user) => {
    setEditing(user)
    setValue('name', user.name); setValue('email', user.email)
    setValue('role', user.role); setValue('is_active', user.is_active)
  }

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Usuários"
        subtitle={`${users.length} funcionário(s) cadastrado(s)`}
        actions={
          <>
            <button onClick={load} className="btn-ghost p-2"><RefreshCw size={16} /></button>
            {isAdmin && (
              <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
                <Plus size={16} /> Novo Usuário
              </button>
            )}
          </>
        }
      />

      {loading ? <LoadingSpinner size="lg" className="h-64" /> : users.length === 0 ? (
        <EmptyState icon={Users} title="Nenhum usuário" description="Cadastre o primeiro usuário." />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-brand-border">
                <th className="table-header text-left p-4">Nome</th>
                <th className="table-header text-left p-4">Email</th>
                <th className="table-header text-center p-4">Perfil</th>
                <th className="table-header text-center p-4">Status</th>
                <th className="table-header text-left p-4">Desde</th>
                {isAdmin && <th className="table-header p-4"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-border">
              {users.map(u => (
                <tr key={u.id} className={`hover:bg-brand-dark/50 transition-colors ${!u.is_active ? 'opacity-50' : ''}`}>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-gold-muted flex items-center justify-center text-xs font-bold text-brand-gold">
                        {u.name.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-brand-white font-medium">{u.name}</span>
                    </div>
                  </td>
                  <td className="p-4 text-brand-muted text-sm">{u.email}</td>
                  <td className="p-4 text-center">
                    <StatusBadge status={u.role} label={ROLE_LABELS[u.role]} />
                  </td>
                  <td className="p-4 text-center">
                    <span className={`badge ${u.is_active ? 'bg-green-900/30 text-green-400 border-green-800' : 'bg-red-900/30 text-red-400 border-red-800'} border`}>
                      {u.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="p-4 text-brand-muted text-sm">
                    {new Date(u.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  {isAdmin && (
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button onClick={() => openEdit(u)} className="text-brand-muted hover:text-brand-gold transition-colors"><Edit2 size={15} /></button>
                        {u.is_active && (
                          <button onClick={() => handleDeactivate(u)} className="text-brand-muted hover:text-red-500 transition-colors"><UserX size={15} /></button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Novo Usuário">
        <form onSubmit={handleSubmit(handleCreate)} className="space-y-4">
          <FormField label="Nome" error={errors.name?.message}>
            <input {...register('name', { required: 'Obrigatório' })} className="input" placeholder="Nome completo" />
          </FormField>
          <FormField label="Email" error={errors.email?.message}>
            <input {...register('email', { required: 'Obrigatório', pattern: { value: /\S+@\S+\.\S+/, message: 'Email inválido' } })} type="email" className="input" />
          </FormField>
          <FormField label="Perfil">
            <select {...register('role')} className="input">
              {ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
            </select>
          </FormField>
          <FormField label="Senha" error={errors.password?.message}>
            <input {...register('password', { required: 'Obrigatório', minLength: { value: 6, message: 'Mínimo 6 caracteres' } })} type="password" className="input" />
          </FormField>
          <FormField label="Confirmar Senha" error={errors.password_confirm?.message}>
            <input {...register('password_confirm', { required: 'Obrigatório' })} type="password" className="input" />
          </FormField>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setShowCreate(false)}>Cancelar</button>
            <button type="submit" className="btn-primary">Criar</button>
          </div>
        </form>
      </Modal>

      {/* Edit User Modal */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title={`Editar — ${editing?.name}`}>
        <form onSubmit={handleE(handleUpdate)} className="space-y-4">
          <FormField label="Nome">
            <input {...regE('name', { required: true })} className="input" />
          </FormField>
          <FormField label="Email">
            <input {...regE('email', { required: true })} type="email" className="input" />
          </FormField>
          <FormField label="Perfil">
            <select {...regE('role')} className="input">
              {ROLES.map(r => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
            </select>
          </FormField>
          <label className="flex items-center gap-2 text-sm text-brand-muted cursor-pointer">
            <input {...regE('is_active')} type="checkbox" className="accent-brand-gold" />
            Ativo
          </label>
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" className="btn-ghost" onClick={() => setEditing(null)}>Cancelar</button>
            <button type="submit" className="btn-primary">Salvar</button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
