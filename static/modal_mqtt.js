
async function checkMQTTStatus() {
    try {
        const response = await fetch('/api/mqtt/status');
        const data = await response.json();
        const statusDiv = document.getElementById('mqtt-status');
        statusDiv.textContent = 'MQTT Status: ' + (data.connected ? 'Connected' : 'Disconnected');
        statusDiv.style.color = data.connected ? 'green' : 'red';
        
        if (data.connected) {
        enableMQTTSpanButtons();
        }
    } catch {
        const s = document.getElementById('mqtt-status');
        s.textContent = 'MQTT Status: Error';
        s.style.color = 'gray';
    }
}

function enableMQTTSpanButtons() {
    const topics = [
      { id: 'mqtt-status-topic', sample: '{"active": "1", "enabled": 1, "open": 0}' },
      { id: 'mqtt-enable-topic', sample: '{"enable": false}' },
      { id: 'mqtt-override-topic', sample: '{"override": true}' }
    ];

    topics.forEach(({ id, sample }) => {
      const span = document.getElementById(id);
      const topic = span.textContent.trim();
      if (topic && topic !== '-') {
        span.classList.add('text-btn');
        span.style.cursor = 'pointer';
        span.onclick = () => openMQTTModal(topic, sample);
      }
    });
  }

  function openMQTTModal(topic, samplePayload) {
    document.getElementById('mqtt-topic-display').textContent = topic;
    document.getElementById('mqtt-payload').value = samplePayload;
    document.getElementById('mqtt-msg-response').textContent = '';
    document.getElementById('mqtt-modal').style.display = 'flex';
  }

  function closeMQTTModal() {
    document.getElementById('mqtt-modal').style.display = 'none';
  }

  async function sendMQTTMessage() {
    const topic = document.getElementById('mqtt-topic-display').textContent;
    const payload = document.getElementById('mqtt-payload').value;

    try {
      const res = await fetch('/api/mqtt/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, payload })
      });

      if (res.ok) {
        document.getElementById('mqtt-msg-response').textContent = 'Απεστάλη!';
      } else {
        document.getElementById('mqtt-msg-response').textContent = 'Σφάλμα αποστολής.';
      }
    } catch {
      document.getElementById('mqtt-msg-response').textContent = 'Σφάλμα σύνδεσης.';
    }
  }