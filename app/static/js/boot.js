/* Start-up: draw the menu and open the catalogue. Loaded last. */
document.getElementById('brand').addEventListener('click', (e) => { e.preventDefault(); show('catalogue'); });
renderNav();
show('catalogue');
