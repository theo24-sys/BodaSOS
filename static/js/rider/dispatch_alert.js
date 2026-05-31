export function connectDispatchSocket(riderId) {
  const socket = new WebSocket(`${window.location.origin.replace("http", "ws")}/ws/rider/${riderId}/`);
  let countdownTimer = null;
  let secondsLeft = 45;

  const overlay = document.createElement("div");
  overlay.id = "dispatch-overlay";
  overlay.className = "fixed inset-0 z-50 hidden items-center justify-center bg-black/80 text-white";
  overlay.innerHTML = `
    <div class="w-full max-w-md rounded-3xl bg-[#111827] p-6 text-center shadow-2xl">
      <h2 class="text-2xl font-black">New Dispatch</h2>
      <p id="dispatch-summary" class="mt-3 text-sm text-gray-300"></p>
      <div id="dispatch-countdown" class="mt-4 text-5xl font-black text-[#FF6B00]">45</div>
      <div class="mt-6 flex gap-3">
        <button id="dispatch-accept" class="flex-1 rounded-2xl bg-green-500 px-4 py-3 font-bold">Accept</button>
        <button id="dispatch-decline" class="flex-1 rounded-2xl bg-red-500 px-4 py-3 font-bold">Decline</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const playAlarm = () => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    oscillator.type = "sawtooth";
    oscillator.frequency.value = 880;
    oscillator.connect(audioContext.destination);
    oscillator.start();
    setTimeout(() => oscillator.stop(), 800);
  };

  const showDispatch = (payload) => {
    playAlarm();
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    document.getElementById("dispatch-summary").textContent = `${payload.emergency_type} at ${payload.address || "unknown location"}`;
    secondsLeft = 45;
    document.getElementById("dispatch-countdown").textContent = String(secondsLeft);
    if (countdownTimer) clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      secondsLeft -= 1;
      document.getElementById("dispatch-countdown").textContent = String(Math.max(secondsLeft, 0));
      if (secondsLeft <= 0) {
        clearInterval(countdownTimer);
        socket.send(JSON.stringify({ action: "decline", job_id: payload.job_id }));
        overlay.classList.add("hidden");
      }
    }, 1000);
    window.currentDispatchJobId = payload.job_id;
  };

  socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "dispatch") {
      showDispatch(payload);
    }
  });

  document.addEventListener("click", (event) => {
    if (event.target && event.target.id === "dispatch-accept") {
      socket.send(JSON.stringify({ action: "accept", job_id: window.currentDispatchJobId }));
      overlay.classList.add("hidden");
    }
    if (event.target && event.target.id === "dispatch-decline") {
      socket.send(JSON.stringify({ action: "decline", job_id: window.currentDispatchJobId }));
      overlay.classList.add("hidden");
    }
  });

  return socket;
}
