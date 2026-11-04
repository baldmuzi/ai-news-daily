document.querySelectorAll('.channels a').forEach(async (link) => {
  const channel = link.getAttribute('href').replace(/\/$/, '');
  try {
    const response = await fetch(`${channel}/latest.json`, { cache: 'no-store' });
    if (!response.ok) return;
    const report = await response.json();
    if (report.environment !== 'test' || report.channel !== channel) return;
    link.querySelector('small').textContent = `测试第 ${report.edition} 期 · ${report.date}`;
    link.querySelector('.action').textContent = '查看完整日报';
  } catch {
    // Keep the honest initial status until the first test report exists.
  }
});
