function addDevice() {
    const name = prompt("Device name:");
    fetch('/api/devices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            pins: { status: 17, enabled: 27, override: 22 }
        })
    }).then(() => location.reload());
}

window.onload = function () {
    fetch('/api/devices')
        .then(res => res.json())
        .then(devices => {
            const list = document.getElementById('deviceList');
            list.innerHTML = '';
            devices.forEach(d => {
                const li = document.createElement('li');
                li.textContent = d.name;
                list.appendChild(li);
            });
        });
}