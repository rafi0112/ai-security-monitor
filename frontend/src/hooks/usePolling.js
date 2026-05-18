import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Stable polling hook — data persists across re-renders.
 *
 * KEY FIX: Uses a ref to hold the latest fetchFn so the interval
 * never needs to be recreated when deps change, preventing the
 * "scroll wipes content" bug caused by component remounts.
 */
export function usePolling(fetchFn, interval = 5000, deps = []) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  // Always hold the latest fetchFn in a ref — never stale, never causes re-mounts
  const fnRef    = useRef(fetchFn)
  const timerRef = useRef(null)

  // Keep ref current whenever fetchFn or deps change
  useEffect(() => {
    fnRef.current = fetchFn
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchFn, ...deps])

  const run = useCallback(async () => {
    try {
      const result = await fnRef.current()
      setData(result)
      setError(null)
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Fetch failed')
    } finally {
      setLoading(false)
    }
  }, []) // ← empty deps: this function never changes identity = no remounts

  useEffect(() => {
    run()
    timerRef.current = setInterval(run, interval)
    return () => clearInterval(timerRef.current)
  }, [run, interval])

  const refetch = useCallback(() => run(), [run])

  return { data, loading, error, refetch }
}
