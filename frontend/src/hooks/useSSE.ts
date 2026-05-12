import { useEffect, useState, useRef, useCallback } from 'react';

interface UseSSEOptions<T = any> {
  onMessage?: (data: T) => void;
  onError?: (error: string) => void;
  onConnect?: () => void;
}

export function useSSE<T = any>(url: string, options: UseSSEOptions<T> = {}) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) eventSourceRef.current.close();
    const es = new EventSource(url);
    eventSourceRef.current = es;
    es.onopen = () => {
      setConnected(true);
      setIsReconnecting(false);
      setError(null);
      options.onConnect?.();
    };
    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        setData(parsed);
        options.onMessage?.(parsed);
      } catch (e) {
        console.warn('SSE parse error', e);
      }
    };
    es.onerror = () => {
      setConnected(false);
      setIsReconnecting(true);
      setError('Connection lost');
      options.onError?.('Connection lost');
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => eventSourceRef.current?.close();
  }, [connect]);

  const reconnect = useCallback(() => {
    connect();
  }, [connect]);

  return { data, error, connected, isReconnecting, reconnect };
}
