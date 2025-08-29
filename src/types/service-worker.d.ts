interface ExtendableEvent extends Event {
  waitUntil(fn: Promise<any>): void;
}

interface FetchEvent extends Event {
  request: Request;
  respondWith(response: Promise<Response> | Response): void;
}

interface ServiceWorkerGlobalScope extends Window {
  skipWaiting(): void;
  clients: {
    claim(): void;
  };
}

declare var self: ServiceWorkerGlobalScope;
