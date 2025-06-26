  function getToastIcon(type) {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'info':
      default: return 'ℹ️';
    }
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.classList.add('toast', type);

    const icon = document.createElement('span');
    icon.classList.add('icon');
    icon.textContent = getToastIcon(type);

    const msg = document.createElement('span');
    msg.classList.add('message');
    msg.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.classList.add('close-btn');
    closeBtn.innerHTML = '&times;';
    closeBtn.onclick = () => container.removeChild(toast);

    toast.appendChild(icon);
    toast.appendChild(msg);
    toast.appendChild(closeBtn);

    container.appendChild(toast);

    setTimeout(() => {
      if (container.contains(toast)) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => {
          if (container.contains(toast)) container.removeChild(toast);
        }, 300);
      }
    }, 4000);
  }

  // Χρήση παραδείγματος:
  // showToast("Η συσκευή προστέθηκε!", "success");
  // showToast("Κάτι πήγε στραβά.", "error");
