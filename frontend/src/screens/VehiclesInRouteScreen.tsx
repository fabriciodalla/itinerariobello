import { CarFront, Clock3, Route, UserRound } from 'lucide-react'
import { StatusPill } from '../components/StatusPill'
import type { VehicleInRoute } from '../types/domain'

interface VehiclesInRouteScreenProps {
  vehiclesInRoute: VehicleInRoute[]
}

const dateTimeFormatter = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
})

export function VehiclesInRouteScreen({ vehiclesInRoute }: VehiclesInRouteScreenProps) {
  return (
    <div className="screen-stack">
      <section className="panel">
        <div className="section-title">
          <Route />
          <div>
            <h2>Veiculos em rota</h2>
            <p>Rotas em andamento agora</p>
          </div>
        </div>

        <div className="closure-summary">
          <div>
            <span>Em rota</span>
            <strong>{vehiclesInRoute.length}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        {!vehiclesInRoute.length ? <div className="empty-state">Nenhum veiculo em rota agora.</div> : null}

        <div className="item-list">
          {vehiclesInRoute.map((item) => (
            <article className="list-card route-card" key={item.viagem_id}>
              <div className="list-card-main">
                <div>
                  <strong>
                    {item.placa} | {item.modelo}
                  </strong>
                  <span>
                    <UserRound />
                    {item.motorista_nome}
                  </span>
                </div>
                <StatusPill status="em_rota" />
              </div>

              <div className="metric-row">
                <span>
                  <CarFront />
                  Veiculo em rota
                </span>
                <span>
                  <Clock3 />
                  Inicio {dateTimeFormatter.format(new Date(item.partida_em))}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
