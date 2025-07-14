
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
  const topicSamples = {
    status: '{}',
    enable: '1',
    override: '0',
    report_status: ''
  };

  document.querySelectorAll('.mqtt-topic').forEach(span => {
    const topic = span.textContent.trim();
    const type = span.dataset.topicType;
    if (!topic || topic === '-') return;

    span.classList.add('text-btn');
    span.style.cursor = 'pointer';

    span.onclick = async () => {
      if (type === 'status') {
        const card = span.closest('.device-card');
        const title = card?.querySelector('.device-title')?.textContent?.trim();
        const device = allDevices.find(d => d.name === title);

        if (device?.id) {
          try {
            const res = await fetch(`/api/devices/status/${device.id}`);
            const json = await res.json();
            const text = JSON.stringify(json, null, 2);
            openMQTTModal(topic, text);
          } catch (err) {
            console.error('Failed to fetch device status:', err);
            openMQTTModal(topic, '{}');
          }
        } else {
          console.warn('Device not found for status topic');
          openMQTTModal(topic, '{}');
        }
      } else {
        openMQTTModal(topic, topicSamples[type] || '');
      }
    };
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