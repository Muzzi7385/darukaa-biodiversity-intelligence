import MetricGroup from './MetricGroup.jsx'

export default function EnvironmentalState({ environment }) {
  if (!environment) return null

  const { climate = {}, soil = {}, land_use = {}, biodiversity = {}, human_impact = {} } =
    environment

  const groups = [
    {
      title: 'Climate',
      metrics: [
        { label: 'Rainfall', value: climate.rainfall },
        { label: 'Temperature', value: climate.temperature }
      ]
    },
    {
      title: 'Soil',
      metrics: [
        { label: 'Soil moisture', value: soil.moisture },
        { label: 'Organic carbon', value: soil.organic_carbon },
        { label: 'pH', value: soil.ph }
      ]
    },
    {
      title: 'Land use',
      metrics: [
        { label: 'Land use', value: land_use.land_use_type },
        { label: 'Crop', value: land_use.crop },
        { label: 'System', value: land_use.system }
      ]
    },
    {
      title: 'Biodiversity',
      metrics: [
        { label: 'Species richness', value: biodiversity.species_richness },
        { label: 'Habitat diversity', value: biodiversity.habitat_diversity }
      ]
    },
    {
      title: 'Human impact',
      metrics: [
        { label: 'Pollution', value: human_impact.pollution },
        { label: 'Deforestation', value: human_impact.deforestation }
      ]
    }
  ]

  return (
    <section className="panel" aria-labelledby="env-state-heading">
      <div className="panel__head">
        <h2 id="env-state-heading" className="panel__heading">
          Environmental state
        </h2>
        {environment.region && (
          <span className="panel__region">{environment.region.replace(/_/g, ' ')}</span>
        )}
      </div>
      <div className="metric-grid">
        {groups.map((group) => (
          <MetricGroup key={group.title} title={group.title} metrics={group.metrics} />
        ))}
      </div>
    </section>
  )
}
