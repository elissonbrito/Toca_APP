import qz from 'qz-tray'

// QZ Tray roda como app local na máquina do restaurante e expõe um websocket
// em localhost. Sem assinatura digital, o QZ mostra um diálogo de confirmação
// na primeira impressão — comportamento esperado para instalação simples.

let connecting = null

export function qzActive() {
  try {
    return qz.websocket.isActive()
  } catch {
    return false
  }
}

export async function ensureQz() {
  if (qzActive()) return qz
  if (!connecting) {
    connecting = qz.websocket
      .connect({ retries: 2, delay: 1 })
      .catch((err) => {
        connecting = null
        throw err
      })
  }
  await connecting
  return qz
}

export async function disconnectQz() {
  if (qzActive()) await qz.websocket.disconnect()
  connecting = null
}

export async function listQzPrinters() {
  await ensureQz()
  const found = await qz.printers.find()
  return Array.isArray(found) ? found : [found]
}

const ESC = '\x1B'
const GS = '\x1D'
const ALIGN = { left: '\x00', center: '\x01', right: '\x02' }

// Converte a configuração geral + o corpo (texto puro vindo do backend) em um
// buffer ESC/POS.
export function buildEscPos(body, s = {}) {
  const size = Math.max(1, Math.min(4, Number(s.font_size) || 1)) - 1
  let out = ESC + '@' // init
  out += ESC + '!' + String.fromCharCode(s.font_family === 'B' ? 0x01 : 0x00)
  out += GS + '!' + String.fromCharCode((size << 4) | size)
  out += ESC + 'E' + String.fromCharCode(s.bold ? 1 : 0)
  out += ESC + 'a' + (ALIGN[s.align] || ALIGN.left)

  const marginTop = Number(s.margin_top) || 0
  const marginBottom = s.margin_bottom == null ? 3 : Number(s.margin_bottom)
  const marginLeft = Number(s.margin_left) || 0
  const pad = ' '.repeat(marginLeft)

  out += '\n'.repeat(marginTop)
  if (s.watermark_text) out += pad + s.watermark_text + '\n'
  out += String(body)
    .split('\n')
    .map((line) => pad + line)
    .join('\n')
  out += '\n'.repeat(marginBottom)
  if (s.cut_paper) out += GS + 'V' + '\x41' + '\x03'
  return out
}

export async function printJob(qzPrinterName, body, settings = {}, { copies = 1 } = {}) {
  await ensureQz()
  const config = qz.configs.create(qzPrinterName, { copies: Math.max(1, copies) })
  const data = []
  if (settings.header_image) {
    data.push({
      type: 'raw',
      format: 'image',
      data: settings.header_image,
      options: { language: 'ESCPOS', dotDensity: 'double' },
    })
  }
  data.push({ type: 'raw', format: 'plain', data: buildEscPos(body, settings) })
  return qz.print(config, data)
}

export default qz
