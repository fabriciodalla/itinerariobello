import { useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowLeft, Loader2, UserPlus } from 'lucide-react'
import { PasswordInput } from '../components/PasswordInput'
import { ApiError, api } from '../services/api'
import type { PerfilUsuario, TipoVeiculo, User } from '../types/domain'
import { CARGO_OPTIONS } from '../utils/cargos'

interface RegisterDriverScreenProps {
  token: string
  users: User[]
  onMessage: (message: string) => void
  onBack: () => void
  onCreated: () => void
}

interface FormState {
  nome: string
  email: string
  senha: string
  cargo: string
  perfil: PerfilUsuario
  superiorId: string
  podeAprovar: boolean
  veiculoPlaca: string
  veiculoModelo: string
  veiculoMarca: string
  tipoVeiculo: TipoVeiculo
}

const emptyForm: FormState = {
  nome: '',
  email: '',
  senha: '',
  cargo: '',
  perfil: 'motorista',
  superiorId: '',
  podeAprovar: false,
  veiculoPlaca: '',
  veiculoModelo: '',
  veiculoMarca: '',
  tipoVeiculo: 'proprio',
}

function describeError(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message : fallback
}

export function RegisterDriverScreen({ token, users, onMessage, onBack, onCreated }: RegisterDriverScreenProps) {
  const [form, setForm] = useState<FormState>(emptyForm)
  const [cnhArquivo, setCnhArquivo] = useState<File | null>(null)
  const [apoliceArquivo, setApoliceArquivo] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()

    const required = [form.nome, form.email, form.senha, form.cargo, form.veiculoPlaca, form.veiculoModelo, form.veiculoMarca]
    if (required.some((value) => !value.trim())) {
      onMessage('Preencha os campos obrigatorios.')
      return
    }
    if (form.senha.length < 8) {
      onMessage('A senha deve ter no minimo 8 caracteres.')
      return
    }

    setSaving(true)
    try {
      const usuario = await api.createUser(token, {
        nome: form.nome.trim(),
        email: form.email.trim(),
        senha: form.senha,
        perfil: form.perfil,
        cargo: form.cargo.trim(),
        superior_id: form.superiorId || null,
        pode_aprovar: form.podeAprovar,
        ativo: true,
      })

      let veiculoId: string | null = null
      try {
        const veiculo = await api.createVehicle(token, {
          placa: form.veiculoPlaca.trim().toUpperCase(),
          modelo: form.veiculoModelo.trim(),
          marca: form.veiculoMarca.trim(),
          tipo: form.tipoVeiculo,
          usuario_responsavel_id: usuario.id,
          ativo: true,
        })
        veiculoId = veiculo.id
      } catch (error) {
        onMessage(
          `Motorista ${usuario.nome} cadastrado, mas nao foi possivel cadastrar o veiculo: ` +
            `${describeError(error, 'erro desconhecido')}. Vincule o veiculo depois pela tela de veiculos.`,
        )
      }

      if (cnhArquivo) {
        try {
          await api.uploadUserCnh(token, usuario.id, cnhArquivo)
        } catch (error) {
          onMessage(`Motorista cadastrado, mas falha ao enviar CNH: ${describeError(error, 'erro desconhecido')}`)
        }
      }

      if (apoliceArquivo && veiculoId) {
        try {
          await api.uploadVehicleApolice(token, veiculoId, apoliceArquivo)
        } catch (error) {
          onMessage(`Motorista cadastrado, mas falha ao enviar apolice: ${describeError(error, 'erro desconhecido')}`)
        }
      }

      onMessage(`Motorista ${usuario.nome} cadastrado com sucesso.`)
      setForm(emptyForm)
      setCnhArquivo(null)
      setApoliceArquivo(null)
      onCreated()
    } catch (error) {
      onMessage(describeError(error, 'Nao foi possivel cadastrar o motorista.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="panel panel-edge-bottom">
      <div className="section-title">
        <UserPlus />
        <div>
          <h2>Cadastrar motorista</h2>
          <p>Cadastro direto, sem esperar solicitacao</p>
        </div>
      </div>

      <form className="signup-form" onSubmit={(event) => void handleSubmit(event)}>
        <div className="form-section-title">Dados de acesso</div>
        <label>
          <span>Nome</span>
          <input value={form.nome} onChange={(e) => update('nome', e.target.value)} />
        </label>
        <label>
          <span>E-mail</span>
          <input type="email" autoComplete="email" value={form.email} onChange={(e) => update('email', e.target.value)} />
        </label>
        <PasswordInput
          label="Senha"
          autoComplete="new-password"
          placeholder="Minimo 8 caracteres"
          value={form.senha}
          onChange={(e) => update('senha', e.target.value)}
        />
        <div className="form-section-title">Hierarquia</div>
        <label>
          <span>Cargo</span>
          <select value={form.cargo} onChange={(e) => update('cargo', e.target.value)}>
            <option value="">Selecione o cargo</option>
            {CARGO_OPTIONS.map((cargo) => (
              <option key={cargo} value={cargo}>{cargo}</option>
            ))}
          </select>
        </label>
        <div className="signup-grid">
          <label>
            <span>Perfil</span>
            <select value={form.perfil} onChange={(e) => update('perfil', e.target.value as PerfilUsuario)}>
              <option value="motorista">Motorista</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label>
            <span>Superior</span>
            <select value={form.superiorId} onChange={(e) => update('superiorId', e.target.value)}>
              <option value="">Sem superior</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.nome}</option>
              ))}
            </select>
          </label>
        </div>
        <label className="checkbox-row">
          <input type="checkbox" checked={form.podeAprovar} onChange={(e) => update('podeAprovar', e.target.checked)} />
          <span>Pode fechar mensalmente</span>
        </label>

        <div className="form-section-title">Veiculo</div>
        <div className="signup-grid">
          <label>
            <span>Placa</span>
            <input
              value={form.veiculoPlaca}
              maxLength={10}
              onChange={(e) => update('veiculoPlaca', e.target.value.toUpperCase())}
            />
          </label>
          <label>
            <span>Modelo</span>
            <input value={form.veiculoModelo} onChange={(e) => update('veiculoModelo', e.target.value)} />
          </label>
        </div>
        <div className="signup-grid">
          <label>
            <span>Marca</span>
            <input value={form.veiculoMarca} onChange={(e) => update('veiculoMarca', e.target.value)} />
          </label>
          <label>
            <span>Tipo do veiculo</span>
            <select value={form.tipoVeiculo} onChange={(e) => update('tipoVeiculo', e.target.value as TipoVeiculo)}>
              <option value="proprio">Proprio</option>
              <option value="alugado">Alugado</option>
              <option value="empresa">Empresa</option>
            </select>
          </label>
        </div>

        <div className="form-section-title">Documentos (opcional)</div>
        <label>
          <span>CNH do motorista (opcional)</span>
          <input
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            onChange={(e) => setCnhArquivo(e.target.files?.[0] ?? null)}
          />
        </label>
        <label>
          <span>Apolice de seguro do veiculo (opcional)</span>
          <input
            type="file"
            accept="application/pdf,image/jpeg,image/png,image/webp"
            onChange={(e) => setApoliceArquivo(e.target.files?.[0] ?? null)}
          />
        </label>

        <button className="primary-button full" type="submit" disabled={saving}>
          {saving ? <Loader2 className="spin" /> : <UserPlus />}
          <span>Cadastrar motorista</span>
        </button>
        <button className="secondary-button full" type="button" onClick={onBack} disabled={saving}>
          <ArrowLeft />
          <span>Voltar para solicitacoes</span>
        </button>
      </form>
    </section>
  )
}
