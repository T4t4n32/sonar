// GENERADO por tools/plantillas_flota.py: no editar a mano. Las mismas 5 disposiciones que las hojas impresas.
import type { PlacedShip } from './types'

export interface PlantillaFlota { n: number; nombre: string; barcos: PlacedShip[] }

const B = (id: string, len: number, x: number, y: number, orient: 'H' | 'V'): PlacedShip =>
  ({ id, kind: id.startsWith('S') ? 'submarino' : 'embarcacion', len, x, y, orient })

export const PLANTILLAS: PlantillaFlota[] = [
  { n: 1, nombre: 'Plantilla 1', barcos: [B('S1', 4, 3, 12, 'V'), B('S2', 4, 11, 4, 'H'), B('E1', 2, 16, 15, 'H'), B('E2', 2, 8, 9, 'V'), B('E3', 2, 5, 3, 'H')] },
  { n: 2, nombre: 'Plantilla 2', barcos: [B('S1', 4, 2, 17, 'H'), B('S2', 4, 17, 5, 'V'), B('E1', 2, 10, 12, 'V'), B('E2', 2, 6, 7, 'H'), B('E3', 2, 13, 18, 'H')] },
  { n: 3, nombre: 'Plantilla 3', barcos: [B('S1', 4, 18, 13, 'V'), B('S2', 4, 4, 9, 'H'), B('E1', 2, 10, 3, 'H'), B('E2', 2, 13, 10, 'V'), B('E3', 2, 2, 3, 'V')] },
  { n: 4, nombre: 'Plantilla 4', barcos: [B('S1', 4, 9, 16, 'H'), B('S2', 4, 3, 4, 'V'), B('E1', 2, 15, 9, 'H'), B('E2', 2, 11, 7, 'V'), B('E3', 2, 17, 2, 'H')] },
  { n: 5, nombre: 'Plantilla 5', barcos: [B('S1', 4, 6, 13, 'V'), B('S2', 4, 13, 13, 'H'), B('E1', 2, 1, 8, 'V'), B('E2', 2, 9, 6, 'H'), B('E3', 2, 19, 5, 'V')] },
]
