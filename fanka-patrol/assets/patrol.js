(() => {
  'use strict';
  const form = document.querySelector('.filters');
  const search = document.querySelector('#search');
  const platform = document.querySelector('#platform');
  const kind = document.querySelector('#kind');
  const sentiment = document.querySelector('#sentiment');
  const date = document.querySelector('#date');
  const priority = document.querySelector('#priority');
  const records = [...document.querySelectorAll('.record')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#empty');
  function filter() {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const record of records) {
      const data = record.dataset;
      const matches = (!platform.value || data.platform === platform.value)
        && (!sentiment.value || data.sentiment === sentiment.value)
        && (!date.value || data.date === date.value)
        && (!kind.value || data.kind === kind.value)
        && (!priority.checked || data.priority === 'true')
        && terms.every(term => data.search.toLocaleLowerCase().includes(term));
      record.hidden = !matches;
      if (matches) visible++;
    }
    for (const group of document.querySelectorAll('.date-group')) {
      group.hidden = !Array.from(group.querySelectorAll('.record')).some(record => !record.hidden);
    }
    count.textContent = `显示 ${visible} / ${records.length} 条记录`;
    empty.hidden = visible !== 0;
  }
  function reset() {
    search.value = '';
    platform.value = '';
    kind.value = '';
    priority.checked = false;
    date.value = '';
    sentiment.value = '';
    filter();
  }
  form.hidden = false;
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', filter);
  form.addEventListener('change', filter);
  form.addEventListener('reset', event => { event.preventDefault(); reset(); });
  document.querySelector('#empty-reset').addEventListener('click', () => { reset(); search.focus(); });
  for (const link of document.querySelectorAll('[data-reveal]')) {
    link.addEventListener('click', () => {
      reset();
      const target = document.getElementById(link.dataset.reveal);
      target.querySelector('details').open = true;
    });
  }
  filter();
})();
