// WebSocket Event Listener for Real-Time Dashboard Updates

let socket = null;
let eventHandlers = [];

export function initWebSocket(onStatusChange) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/events`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("WebSocket connected to real-time event stream");
    if (onStatusChange) onStatusChange(true);
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      console.log("Real-Time Event Received:", msg);
      eventHandlers.forEach(handler => handler(msg.event, msg.data));
    } catch (e) {
      console.error("Error parsing WebSocket message:", e);
    }
  };

  socket.onclose = () => {
    console.warn("WebSocket disconnected. Reconnecting in 3s...");
    if (onStatusChange) onStatusChange(false);
    setTimeout(() => initWebSocket(onStatusChange), 3000);
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
    if (onStatusChange) onStatusChange(false);
  };
}

export function subscribeToEvents(handler) {
  eventHandlers.push(handler);
}
