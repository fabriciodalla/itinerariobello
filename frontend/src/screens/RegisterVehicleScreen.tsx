import { useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, CarFront, Loader2 } from 'lucide-react'
import { ApiError, api } from '../services/api'
import type { TipoDisponibilidadeVeiculo, TipoVeiculo, User } from '../types/domain'

interface RegisterVehicleScreenProps {
  token: string
  users: User[]
  onMessage: (message: string) => void
  onBack: () => void
  onCreated: () => void
}

interface FormState {
  usuarioResponsavelId: string
  placa: string
  modelo: string
  marca: string
  tipoVeiculo: TipoVeiculo
  tipoDisponibilidade: TipoDisponibilidadeVeiculo
  unidade: string
  categoria: string
  principal: boolean
}

const emptyForm: FormState = {
  usuarioResponsavelId: '',
  placa: '',
  modelo: '',
  marca: '',
  tipoVeiculo: 'proprio',
  tipoDisponibilidade: 'fixo',
  unidade: '',
  categoria: '',
  // esta tela normalmente adiciona um segundo (ou terceiro) carro a um
  // motorista que ja pode ter um principal; fica desmarcado por padrao para
  // nao substituir o principal atual sem intencao explicita do admin
  principal: false,
}

function describeError(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message : fallback
}

export function RegisterVehicleScreen({ token, users, onMessage, onBack, onCreated }: RegisterVehicleScreenProps) {
  const [form, setForm] = useState<FormState>(emptyForm)
  const [apoliceArquivo, setApoliceArquivo] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)

  const usuariosAtivos = users.filter((u) => u.ativo)

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()

    const required = [form.usuarioResponsavelId, form.placa, form.modelo, form.marca]
    if (required.some((value) => !value.trim())) {
      onMessage('Preencha os campos obrigatorios.')
      return
    }
    if (form.tipoDisponibilidade === 'fixo' && !form.usuarioResponsavelId) {
      onMessage('Veiculo fixo exige um motorista responsavel.')
      return
    }

    setSaving(true)
    try {
      const veiculo = await api.createVehicle(token, {
        placa: form.placa.trim().toUpperCase(),
        modelo: form.modelo.trim(),
        marca: form.marca.trim(),
        tipo: form.tipoVeiculo,
        tipo_disponibilidade: form.tipoDisponibilidade,
        usuario_responsavel_id: form.usuarioResponsavelId,
        unidade: form.unidade.trim() || null,
        categoria: form.categoria.trim() || null,
        ativo: true,
        principal: form.principal,
      })

      if (apoliceArquivo) {
        try {
          await api.uploadVehicleApolice(token, veiculo.id, apoliceArquivo)
        } catch (error) {
          onMessage(`Veiculo cadastrado, mas falha ao enviar apolice: ${describeError(error, 'erro desconhecido')}`)
        }
      }

      onMessage(`Veiculo ${veiculo.placa} cadastrado e vinculado com sucesso.`)
      setForm(emptyForm)
      setApoliceArquivo(null)
      onCreated()
    } catch (error) {
      onMessage(describeError(error, 'Nao foi possivel cadastrar o veiculo.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="panel panel-edge-bottom">
      <div className="section-title">
        <CarFront />
        <div>
          <h2>Cadastrar somente veiculo</h2>
          <p>Vincule um veiculo novo a um motorista ja existente</p>
        </div>
      </div>

      <form className="signup-form" onSubmit={(event) => void handleSubmit(event)}>
        <div className="form-section-title">Motorista responsavel</div>
        <label>
          <span>Motorista</span>
          <select
            value={form.usuarioResponsavelId}
            onChange={(e) => update('usuarioResponsavelId', e.target.value)}
          >
            <option value="">Selecione o motorista</option>
            {usuariosAtivos.map((u) => (
              <option key={u.id} value={u.id}>{u.nome}</option>
            ))}
          </select>
        </label>

        <div className="form-section-title">Veiculo</div>
        <div className="signup-grid">
          <label>
            <span>Placa</span>
            <input
              value={form.placa}
              maxLength={10}
              onChange={(e) => update('placa', e.target.value.toUpperCase())}
            />
          </label>
          <label>
            <span>Modelo</span>
            <input value={form.modelo} onChange={(e) => update('modelo', e.target.value)} />
          </label>
        </div>
        <div className="signup-grid">
          <label>
            <span>Marca</span>
            <input value={form.marca} onChange={(e) => update('marca', e.target.value)} />
          </label>
          <label>
            <span>Tipo do veiculo</span>
            <select
              value={form.tipoVeiculo}
              onChange={(e) => {
                const tipoVeiculo = e.target.value as TipoVeiculo
                // veiculo proprio costuma ser de uso exclusivo do motorista (fixo);
                // alugado/empresa costumam ser compartilhados entre motoristas
                // (alocado) — mesma regra que o backend aplica quando a
                // disponibilidade nao e informada explicitamente
                setForm((current) => ({
                  ...current,
                  tipoVeiculo,
                  tipoDisponibilidade: tipoVeiculo === 'proprio' ? 'fixo' : 'alocado',
                }))
              }}
            >
              <option value="proprio">Proprio</option>
              <option value="alugado">Alugado</option>
              <option value="empresa">Empresa</option>
            </select>
          </label>
        </div>
        <div className="signup-grid">
          <label>
            <span>Disponibilidade</span>
            <select
              value={form.tipoDisponibilidade}
              onChange={(e) => update('tipoDisponibilidade', e.target.value as TipoDisponibilidadeVeiculo)}
            >
              <option value="fixo">Fixo (uso exclusivo do motorista)</option>
              <option value="alocado">Alocado (compartilhado)</option>
            </select>
          </label>
          <label>
            <span>Unidade (opcional)</span>
            <input value={form.unidade} onChange={(e) => update('unidade', e.target.value)} />
          </label>
        </div>
        <label>
          <span>Categoria (opcional)</span>
          <input value={form.categoria} onChange={(e) => update('categoria', e.target.value)} />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.principal}
            onChange={(e) => update('principal', e.target.checked)}
          />
          <span>Definir como veiculo principal (aparece primeiro para o motorista; substitui o principal atual, se houver)</span>
        </label>

        <div className="form-section-title">Documentos (opcional)</div>
        <label>
          <span>Apolice de seguro do veiculo (opcional)</span>
          <input
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            onChange={(e) => setApoliceArquivo(e.target.files?.[0] ?? null)}
          />
        </label>

        <button className="primary-button full" type="submit" disabled={saving}>
          {saving ? <Loader2 className="spin" /> : <CarFront />}
          <span>Cadastrar veiculo</span>
        </button>
        <button className="secondary-button full" type="button" onClick={onBack} disabled={saving}>
          <ArrowLeft />
          <span>Voltar para solicitacoes</span>
        </button>
      </form>
    </section>
  )
}
