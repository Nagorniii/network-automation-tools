const allowedInterfaces = ['Tunnel0', 'Tunnel1'];

async function loadData() {
  const response = await fetch('/api/results');
  const data = await response.json(); // тепер масив
  const tbody = document.querySelector('#resultsTable tbody');
  tbody.innerHTML = '';

  for (const item of data) {
    const ip = item.ip;
    const info = item;
    const statusClass = info.status === 'online' ? 'online' : 'offline';

    const interfaceColumns = allowedInterfaces.map(ifaceName => {
      if (info.interfaces) {
        const iface = info.interfaces.find(i => i.interface === ifaceName);
        if (iface) {
          const colorClass = iface.protocol.toLowerCase() === 'down' ? 'down' : '';
          return `<span class="${colorClass}">${iface.interface} (${iface.protocol})</span>`;
        } else {
          return '-';
        }
      }
      return '-';
    });

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${ip}</td>
      <td class="${statusClass}">${info.status}</td>
      <td>${info.hostname || ''}</td>
      <td>${interfaceColumns[0]}</td>
      <td>${interfaceColumns[1]}</td>
      <td>${info.timestamp || ''}</td>
    `;

    tbody.appendChild(row);
  }
}

loadData();
setInterval(loadData, 300000);
