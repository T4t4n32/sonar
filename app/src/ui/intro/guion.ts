/** Guion del tutorial: todos los textos y duraciones en un solo sitio (editar aquí, no en las escenas).
 *  `caps[].at` = fracción (0..1) de la escena en la que aparece ese subtítulo. */
import type { FxEvent } from '../../state/feedback'

export type Act = 1 | 2
export type IntroMode = 'ambos' | 'acto1' | 'acto2'
export interface Cap { at: number; text: string }
export interface Sfx { at: number; ev: FxEvent }
export interface SceneDef { id: string; act: Act; dur: number; title: string; caps: Cap[]; sfx?: Sfx[] }

export const ACTOS: Record<Act, string> = { 1: 'ACTO 1 · DINÁMICA', 2: 'ACTO 2 · INTERFAZ' }

export const ESCENAS: SceneDef[] = [
  // ---------- ACTO 1 · dinámica del juego (~51 s) ----------
  { id: 'flota', act: 1, dur: 8000, title: 'La flota', caps: [
    { at: 0, text: 'Cada equipo tiene su flota en un tablero de 20×20.' },
    { at: 0.5, text: 'Tres embarcaciones de 2 casillas y dos submarinos de 4, en horizontal o vertical.' },
  ] },
  { id: 'bluetooth', act: 1, dur: 6000, title: 'Bluetooth', caps: [
    { at: 0, text: 'Cada equipo tiene SU tablero físico con SU flota.' },
    { at: 0.45, text: 'El rival maneja TU tablero por Bluetooth: celular ↔ módulo «SONAR-A».' },
  ], sfx: [{ at: 0.3, ev: 'ok' }] },
  { id: 'test', act: 1, dur: 6000, title: 'El TEST', caps: [
    { at: 0, text: 'Primero, el TEST de 5 posiciones: el láser visita cinco puntos del tablero.' },
    { at: 0.72, text: 'Cinco ✓ y el enlace queda listo.' },
  ], sfx: [{ at: 0.2, ev: 'ok' }, { at: 0.36, ev: 'ok' }, { at: 0.52, ev: 'ok' }, { at: 0.68, ev: 'ok' }, { at: 0.82, ev: 'ok' }] },
  { id: 'coordenada', act: 1, dur: 6000, title: 'La coordenada', caps: [
    { at: 0, text: 'El atacante (el profesor) escribe una coordenada.' },
    { at: 0.18, text: 'Primero X…' },
    { at: 0.5, text: '…y luego Y.' },
    { at: 0.82, text: 'Así: «10, 15».' },
  ] },
  { id: 'laser', act: 1, dur: 5000, title: 'El láser', caps: [
    { at: 0, text: 'El láser aparece en esa coordenada del tablero real.' },
  ], sfx: [{ at: 0.25, ev: 'disparo' }] },
  { id: 'ledio', act: 1, dur: 4500, title: '¡Le dio!', caps: [
    { at: 0, text: 'Los estudiantes miran su tablero físico y dicen: «¡Le dio!»' },
    { at: 0.55, text: '¡Explosión!' },
  ], sfx: [{ at: 0.55, ev: 'acierto' }] },
  { id: 'noledio', act: 1, dur: 4500, title: 'No le dio', caps: [
    { at: 0, text: 'O dicen: «No le dio». Cae una gota de agua.' },
  ], sfx: [{ at: 0.55, ev: 'agua' }] },
  { id: 'ubicar', act: 1, dur: 6000, title: 'Ubicar el barco', caps: [
    { at: 0, text: 'Si le dio, se ubica el barco: arrastra el dedo sobre sus casillas.' },
    { at: 0.6, text: 'De (10,15) a (10,12): LISTO y vuelve a apuntar.' },
  ] },
  { id: 'victoria', act: 1, dur: 5000, title: 'Victoria', caps: [
    { at: 0, text: 'Gana quien hunde toda la flota rival: 14 casillas.' },
    { at: 0.6, text: '¡Victoria!' },
  ], sfx: [{ at: 0.6, ev: 'victoria' }] },

  // ---------- ACTO 2 · recorrido de la interfaz (~43 s) ----------
  { id: 'enlace', act: 2, dur: 6000, title: 'Enlace', caps: [
    { at: 0, text: 'Enlace: elige el módulo SONAR-A.' },
    { at: 0.45, text: 'Toca CONECTAR: el punto se pone verde.' },
  ], sfx: [{ at: 0.62, ev: 'ok' }] },
  { id: 'enlace-test', act: 2, dur: 6000, title: 'TEST de 5 posiciones', caps: [
    { at: 0, text: 'Pulsa TEST: el láser recorre cinco posiciones.' },
    { at: 0.82, text: 'Cinco ✓ y aparece APROBADO.' },
  ] },
  { id: 'batalla', act: 2, dur: 7000, title: 'Batalla', caps: [
    { at: 0, text: 'Batalla: el radar 20×20 del tablero rival.' },
    { at: 0.3, text: 'Escribe x, y con el teclado.' },
    { at: 0.58, text: 'DISPARAR envía la coordenada…' },
    { at: 0.8, text: '…y STOP siempre está a mano.' },
  ] },
  { id: 'veredicto', act: 2, dur: 6000, title: 'La pausa', caps: [
    { at: 0, text: 'El disparo se pausa justo antes del impacto.' },
    { at: 0.2, text: 'Los estudiantes pulsan SÍ LE DIO…' },
    { at: 0.55, text: '…o NO LE DIO.' },
  ] },
  { id: 'ubicar-ui', act: 2, dur: 6000, title: 'Ubica el barco', caps: [
    { at: 0, text: 'SÍ LE DIO: ubica el barco arrastrando el dedo.' },
    { at: 0.7, text: 'LISTO lo registra y vuelves a apuntar.' },
  ] },
  { id: 'flota-ui', act: 2, dur: 6000, title: 'Mi flota', caps: [
    { at: 0, text: 'Mi flota: coloca tus barcos en el tablero.' },
    { at: 0.45, text: 'La lista de coordenadas te dice dónde armar el tablero físico.' },
  ] },
  { id: 'partida', act: 2, dur: 6500, title: 'Partida', caps: [
    { at: 0, text: 'Partida: estadísticas de la batalla.' },
    { at: 0.35, text: 'La bitácora guarda cada disparo con su hora.' },
    { at: 0.7, text: 'Aquí también puedes volver a «Ver tutorial».' },
  ] },
]

export function escenasDe(mode: IntroMode): SceneDef[] {
  return mode === 'ambos' ? ESCENAS : ESCENAS.filter(s => s.act === (mode === 'acto1' ? 1 : 2))
}
export const MODOS: { id: IntroMode; label: string }[] = [
  { id: 'ambos', label: 'Todo' }, { id: 'acto1', label: 'Acto 1' }, { id: 'acto2', label: 'Acto 2' },
]
export const TXT = {
  saltar: 'Saltar', atras: 'Atrás', siguiente: 'Siguiente', pausa: 'Pausa', seguir: 'Continuar',
  empezar: 'Empezar', listo: 'Listo', pausado: 'PAUSA',
}
