let currentGpioId = null;

function openPinModal(gpioId, gpioValue, label) {
  currentGpioId = gpioId;
  document.getElementById('gpio-id').innerText = gpioId;
  document.getElementById('modal-title').innerText = `${label} (GPIO ${gpioId})`;
  document.getElementById('pin-modal').style.display = 'flex';
  document.getElementById('set-pin-btn').disabled = false;
  document.getElementById('loader').style.display = 'none';
  document.getElementById('response-msg').innerText = '';

  // Θέτουμε checked το radio button με βάση την currentValue
  const radios = document.getElementsByName('pin-value');
  radios.forEach(radio => {
    radio.checked = (radio.value === String(gpioValue));
  });
}

function closePinModal() {
  document.getElementById('pin-modal').style.display = 'none';
}

function submitPinValue() {
  const value = document.querySelector('input[name="pin-value"]:checked').value;
  const setButton = document.getElementById('set-pin-btn');
  const loader = document.getElementById('loader');
  const msg = document.getElementById('response-msg');

  setButton.disabled = true;
  loader.style.display = 'block';
  msg.innerText = '';

  fetch(`/gpio/${currentGpioId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value: Number(value) })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      msg.innerText = 'Επιτυχής αποστολή!';
      msg.style.color = 'green';
    } else {
      msg.innerText = `Σφάλμα: ${data.error}`;
      msg.style.color = 'red';
    }
  })
  .catch(err => {
    msg.innerText = 'Σφάλμα δικτύου';
    msg.style.color = 'red';
  })
  .finally(() => {
    loader.style.display = 'none';
    setButton.disabled = false;
  });
}
