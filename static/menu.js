/*const toggle = document.getElementById('menu-toggle');
const menu = document.getElementById('menu');
const overlay = document.getElementById('menu-overlay');

function openMenu() {
menu.classList.add('open');
overlay.classList.add('active');
}

function closeMenu() {
menu.classList.remove('open');
overlay.classList.remove('active');
}

toggle.addEventListener('click', (e) => {
e.stopPropagation();
if (menu.classList.contains('open')) {
    closeMenu();
} else {
    openMenu();
}
});

// Close on outside click or overlay click
document.addEventListener('click', (e) => {
if (
    menu.classList.contains('open') &&
    !menu.contains(e.target) &&
    !toggle.contains(e.target)
) {
    closeMenu();
}
});

overlay.addEventListener('click', closeMenu);

// Close on menu item click
document.querySelectorAll('#menu a').forEach(link => {
link.addEventListener('click', closeMenu);
});
*/

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('menu-toggle');
  const menu = document.getElementById('menu');
  const overlay = document.getElementById('menu-overlay');

  function openMenu() {
    menu.classList.add('open');
    overlay.classList.add('active');
  }

  function closeMenu() {
    menu.classList.remove('open');
    overlay.classList.remove('active');
    toggle.classList.remove('open');  // reset hamburger to 3 bars
  }

  toggle.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.contains('open');
    if (isOpen) {
        closeMenu();
        toggle.classList.remove('open');  // remove X animation
    } else {
        openMenu();
        toggle.classList.add('open');     // add X animation
    }
  });


  overlay.addEventListener('click', closeMenu);

  document.querySelectorAll('#menu a').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  // Optional: close menu on pressing ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('open')) {
      closeMenu();
    }
  });
});
