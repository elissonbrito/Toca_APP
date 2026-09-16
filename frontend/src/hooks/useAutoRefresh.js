import { useEffect, useRef } from 'react'

/**
 * Chama `callback` a cada `interval` ms enquanto a aba estiver visível, e de
 * novo assim que ela volta a ficar visível (celular saiu do fundo, troca de
 * aba etc.) — é o "outro dispositivo vê sem precisar atualizar a página".
 *
 * `callback` deve ser uma recarga silenciosa (sem acender spinner de tela
 * cheia), senão a UI pisca a cada tick.
 */
export function useAutoRefresh(callback, { interval = 5000, enabled = true } = {}) {
  const callbackRef = useRef(callback)
  useEffect(() => { callbackRef.current = callback }, [callback])

  useEffect(() => {
    if (!enabled) return undefined

    const tick = () => {
      if (document.visibilityState === 'visible') callbackRef.current()
    }
    const id = setInterval(tick, interval)
    document.addEventListener('visibilitychange', tick)
    return () => {
      clearInterval(id)
      document.removeEventListener('visibilitychange', tick)
    }
  }, [interval, enabled])
}
