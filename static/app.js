// App State
const state = {
  posts: [],
  selectedPosts: new Map(), // id -> post object
  currentPage: 1,
  currentQuery: '',
  currentSource: 'web',
  currentRating: 'all',
  currentAspect: 'all',
  currentSort: 'recent',
  previewIndex: -1,
  settings: {
    download_dir: './downloads',
    naming_pattern: '{source}_{id}_{tags}',
    threads: 4,
    limit: 40,
    create_subfolders: true,
    skip_existing: true,
    save_metadata: true
  },
  downloadPollingInterval: null
};

// DOM Elements
const searchInput = document.getElementById('searchInput');
const sourceSelect = document.getElementById('sourceSelect');
const ratingSelect = document.getElementById('ratingSelect');
const aspectSelect = document.getElementById('aspectSelect');
const sortSelect = document.getElementById('sortSelect');
const searchBtn = document.getElementById('searchBtn');
const galleryGrid = document.getElementById('galleryGrid');
const loadingGrid = document.getElementById('loadingGrid');
const emptyState = document.getElementById('emptyState');
const paginationBar = document.getElementById('paginationBar');
const currentPageNum = document.getElementById('currentPageNum');
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');
const selectedCountBadge = document.getElementById('selectedCountBadge');
const dlCountSpan = document.getElementById('dlCountSpan');
const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
const downloadZipBtn = document.getElementById('downloadZipBtn');
const selectAllBtn = document.getElementById('selectAllBtn');
const deselectAllBtn = document.getElementById('deselectAllBtn');
const invertSelectBtn = document.getElementById('invertSelectBtn');
const selectHighResBtn = document.getElementById('selectHighResBtn');
const autocompleteList = document.getElementById('autocompleteList');
const statusBanner = document.getElementById('statusBanner');
const statusBannerText = document.getElementById('statusBannerText');

// Progress Elements
const downloadProgressCard = document.getElementById('downloadProgressCard');
const dlProgressBar = document.getElementById('dlProgressBar');
const dlProgressStats = document.getElementById('dlProgressStats');
const dlSpeedText = document.getElementById('dlSpeedText');
const dlCurrentFile = document.getElementById('dlCurrentFile');
const cancelDlBtn = document.getElementById('cancelDlBtn');

// Modal Elements
const previewModal = document.getElementById('previewModal');
const closeModalBtn = document.getElementById('closeModalBtn');
const modalImage = document.getElementById('modalImage');
const modalPrevBtn = document.getElementById('modalPrevBtn');
const modalNextBtn = document.getElementById('modalNextBtn');
const modalSourceBadge = document.getElementById('modalSourceBadge');
const modalRatingBadge = document.getElementById('modalRatingBadge');
const modalPostTitle = document.getElementById('modalPostTitle');
const modalDimensions = document.getElementById('modalDimensions');
const modalScore = document.getElementById('modalScore');
const modalFormat = document.getElementById('modalFormat');
const modalTagsContainer = document.getElementById('modalTagsContainer');
const modalSelectToggleBtn = document.getElementById('modalSelectToggleBtn');
const modalSelectToggleText = document.getElementById('modalSelectToggleText');
const modalDownloadDirectBtn = document.getElementById('modalDownloadDirectBtn');
const modalSourceLink = document.getElementById('modalSourceLink');

// Help Modal Elements
const openHelpBtn = document.getElementById('openHelpBtn');
const helpModal = document.getElementById('helpModal');
const closeHelpModalBtn = document.getElementById('closeHelpModalBtn');
const closeHelpBtn2 = document.getElementById('closeHelpBtn2');

// Settings Elements
const openSettingsBtn = document.getElementById('openSettingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsModalBtn = document.getElementById('closeSettingsModalBtn');
const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');
const settingDownloadDir = document.getElementById('settingDownloadDir');
const settingNamingPattern = document.getElementById('settingNamingPattern');
const settingThreads = document.getElementById('settingThreads');
const settingLimit = document.getElementById('settingLimit');
const settingSubfolders = document.getElementById('settingSubfolders');
const settingSkipExisting = document.getElementById('settingSkipExisting');
const settingSaveMeta = document.getElementById('settingSaveMeta');

// Initial Setup
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  await fetchSettings();
  setupEventListeners();
  
  // Default demo search to populate on start
  performSearch();
});

// Presets
window.applyPreset = function(tags) {
  searchInput.value = tags;
  state.currentPage = 1;
  performSearch();
};

// Settings Management
async function fetchSettings() {
  try {
    const res = await fetch('/api/settings');
    if (res.ok) {
      state.settings = await res.json();
      settingDownloadDir.value = state.settings.download_dir || './downloads';
      settingNamingPattern.value = state.settings.naming_pattern || '{source}_{id}_{tags}';
      settingThreads.value = state.settings.threads || 4;
      settingLimit.value = state.settings.limit || 40;
      settingSubfolders.checked = state.settings.create_subfolders !== false;
      settingSkipExisting.checked = state.settings.skip_existing !== false;
      settingSaveMeta.checked = state.settings.save_metadata !== false;
    }
  } catch (e) {
    console.warn('Could not load settings:', e);
  }
}

async function saveSettings() {
  const updated = {
    download_dir: settingDownloadDir.value.trim() || './downloads',
    naming_pattern: settingNamingPattern.value,
    threads: parseInt(settingThreads.value) || 4,
    limit: parseInt(settingLimit.value) || 40,
    create_subfolders: settingSubfolders.checked,
    skip_existing: settingSkipExisting.checked,
    save_metadata: settingSaveMeta.checked
  };

  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    });
    if (res.ok) {
      state.settings = updated;
      settingsModal.classList.add('hidden');
      showToast('Настройки успешно сохранены!', 'success');
    }
  } catch (e) {
    showToast('Ошибка сохранения настроек: ' + e.message, 'error');
  }
}

// Event Listeners
function setupEventListeners() {
  searchBtn.addEventListener('click', () => {
    state.currentPage = 1;
    performSearch();
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      autocompleteList.classList.add('hidden');
      state.currentPage = 1;
      performSearch();
    }
  });

  // Autocomplete on input
  let debounceTimeout;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(handleAutocomplete, 250);
  });

  document.addEventListener('click', (e) => {
    if (!autocompleteList.contains(e.target) && e.target !== searchInput) {
      autocompleteList.classList.add('hidden');
    }
  });

  sourceSelect.addEventListener('change', () => {
    state.currentPage = 1;
    performSearch();
  });

  ratingSelect.addEventListener('change', () => {
    state.currentPage = 1;
    performSearch();
  });

  aspectSelect.addEventListener('change', () => {
    performSearch();
  });

  sortSelect.addEventListener('change', () => {
    performSearch();
  });

  // Quick tag chips
  document.querySelectorAll('.tag-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const tag = btn.innerText.replace('+', '').trim();
      const current = searchInput.value.trim();
      if (!current.split(/\s+/).includes(tag)) {
        searchInput.value = current ? `${current} ${tag}` : tag;
      }
      state.currentPage = 1;
      performSearch();
    });
  });

  // Pagination
  prevPageBtn.addEventListener('click', () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      performSearch();
    }
  });

  nextPageBtn.addEventListener('click', () => {
    state.currentPage++;
    performSearch();
  });

  // Selection actions
  selectAllBtn.addEventListener('click', selectAll);
  deselectAllBtn.addEventListener('click', deselectAll);
  invertSelectBtn.addEventListener('click', invertSelection);
  selectHighResBtn.addEventListener('click', selectHighRes);

  // Download actions
  downloadSelectedBtn.addEventListener('click', startLocalDownload);
  downloadZipBtn.addEventListener('click', downloadAsZip);
  cancelDlBtn.addEventListener('click', cancelDownload);

  // Modal
  closeModalBtn.addEventListener('click', closeModal);
  modalPrevBtn.addEventListener('click', () => navigateModal(-1));
  modalNextBtn.addEventListener('click', () => navigateModal(1));
  modalSelectToggleBtn.addEventListener('click', toggleModalPostSelection);

  // Help modal
  if (openHelpBtn) openHelpBtn.addEventListener('click', () => helpModal.classList.remove('hidden'));
  if (closeHelpModalBtn) closeHelpModalBtn.addEventListener('click', () => helpModal.classList.add('hidden'));
  if (closeHelpBtn2) closeHelpBtn2.addEventListener('click', () => helpModal.classList.add('hidden'));

  // Keyboard navigation for modal
  document.addEventListener('keydown', (e) => {
    if (!previewModal.classList.contains('hidden')) {
      if (e.key === 'Escape') closeModal();
      else if (e.key === 'ArrowLeft') navigateModal(-1);
      else if (e.key === 'ArrowRight') navigateModal(1);
    }
  });

  // Settings modal
  openSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  closeSettingsModalBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  cancelSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  saveSettingsBtn.addEventListener('click', saveSettings);
}

// Autocomplete handler
async function handleAutocomplete() {
  const query = searchInput.value.trim();
  if (!query) {
    autocompleteList.classList.add('hidden');
    return;
  }
  try {
    const res = await fetch(`/api/tags/suggest?q=${encodeURIComponent(query)}`);
    if (res.ok) {
      const data = await res.json();
      const suggestions = data.suggestions || [];
      if (suggestions.length === 0) {
        autocompleteList.classList.add('hidden');
        return;
      }
      autocompleteList.innerHTML = suggestions.map(tag => `
        <div class="px-3 py-2 text-xs text-slate-200 hover:bg-brand-500/20 hover:text-brand-400 cursor-pointer flex items-center justify-between transition-all" onclick="applySuggestion('${tag}')">
          <span class="font-mono">${tag}</span>
          <span class="text-[10px] text-slate-500">тег</span>
        </div>
      `).join('');
      autocompleteList.classList.remove('hidden');
    }
  } catch (e) {
    autocompleteList.classList.add('hidden');
  }
}

window.applySuggestion = function(tag) {
  const tokens = searchInput.value.trim().split(/\s+/);
  tokens[tokens.length - 1] = tag;
  searchInput.value = tokens.join(' ') + ' ';
  autocompleteList.classList.add('hidden');
  searchInput.focus();
};

// Search Execution
async function performSearch() {
  const query = searchInput.value.trim();
  const source = sourceSelect.value;
  const rating = ratingSelect.value;
  const aspect = aspectSelect.value;
  const sort = sortSelect.value;

  state.currentQuery = query;
  state.currentSource = source;
  state.currentRating = rating;
  state.currentAspect = aspect;
  state.currentSort = sort;

  showLoading(true);
  statusBanner.classList.add('hidden');

  try {
    const params = new URLSearchParams({
      query: query,
      source: source,
      page: state.currentPage,
      limit: state.settings.limit || 40,
      rating: rating,
      aspect_ratio: aspect,
      sort: sort
    });

    const res = await fetch(`/api/search?${params.toString()}`);
    if (!res.ok) {
      throw new Error(`Ошибка сервера: ${res.status}`);
    }

    const data = await res.json();
    state.posts = data.posts || [];

    if (data.errors && data.errors.length > 0) {
      statusBannerText.innerText = data.errors.join(' | ');
      statusBanner.classList.remove('hidden');
    }

    renderGallery();
  } catch (err) {
    console.error('Search error:', err);
    showToast('Ошибка поиска: ' + err.message, 'error');
    galleryGrid.innerHTML = '';
    emptyState.classList.remove('hidden');
  } finally {
    showLoading(false);
  }
}

function showLoading(isLoading) {
  if (isLoading) {
    emptyState.classList.add('hidden');
    galleryGrid.classList.add('hidden');
    paginationBar.classList.add('hidden');
    loadingGrid.classList.remove('hidden');
    
    // Render 10 skeleton cards
    loadingGrid.innerHTML = Array(10).fill(0).map(() => `
      <div class="bg-dark-800 rounded-2xl p-3 border border-slate-800 animate-pulse">
        <div class="w-full h-56 bg-dark-900 rounded-xl mb-3"></div>
        <div class="h-3 bg-slate-700 rounded w-3/4 mb-2"></div>
        <div class="h-2.5 bg-slate-800 rounded w-1/2"></div>
      </div>
    `).join('');
  } else {
    loadingGrid.classList.add('hidden');
    galleryGrid.classList.remove('hidden');
  }
}

// Gallery Rendering
function renderGallery() {
  if (!state.posts || state.posts.length === 0) {
    galleryGrid.innerHTML = '';
    emptyState.classList.remove('hidden');
    paginationBar.classList.add('hidden');
    return;
  }

  emptyState.classList.add('hidden');
  paginationBar.classList.remove('hidden');
  currentPageNum.innerText = state.currentPage;
  prevPageBtn.disabled = state.currentPage <= 1;

  galleryGrid.innerHTML = state.posts.map((post, idx) => {
    const isSelected = state.selectedPosts.has(post.id);
    const ratingUpper = (post.rating || 'NSFW').toUpperCase();
    const ratingColor = ratingUpper.includes('EXP') ? 'rose' : ratingUpper.includes('QUEST') ? 'amber' : 'emerald';
    
    const previewUrl = post.preview_url ? `/api/proxy-image?url=${encodeURIComponent(post.preview_url)}` : post.file_url;
    const resText = post.width && post.height ? `${post.width}×${post.height}` : (post.file_ext || 'IMG').toUpperCase();
    const score = post.score || 0;

    return `
      <div 
        id="card-${post.id}" 
        class="image-card relative group bg-dark-800 border ${isSelected ? 'border-brand-500 selected' : 'border-slate-800'} rounded-2xl p-2.5 flex flex-col justify-between transition-all cursor-pointer"
        onclick="handleCardClick(event, ${idx})"
      >
        <!-- Card Top Bar: Checkbox & Rating -->
        <div class="flex items-center justify-between mb-2 z-10">
          <label class="flex items-center cursor-pointer" onclick="event.stopPropagation()">
            <input 
              type="checkbox" 
              class="w-4 h-4 rounded bg-dark-900 border-slate-700 text-brand-500 focus:ring-brand-500 cursor-pointer" 
              ${isSelected ? 'checked' : ''}
              onchange="toggleSelectPost('${post.id}', this.checked)"
            />
          </label>

          <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-${ratingColor}-500/20 text-${ratingColor}-400 border border-${ratingColor}-500/30">
            ${ratingUpper.slice(0, 4)}
          </span>
        </div>

        <!-- Thumbnail Image Container -->
        <div class="relative w-full h-56 bg-dark-950 rounded-xl overflow-hidden mb-2 flex items-center justify-center">
          <img 
            src="${previewUrl}" 
            alt="Thumbnail" 
            loading="lazy" 
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onerror="this.onerror=null; this.src='/api/proxy-image?url=fallback';"
          />

          <!-- Quick Preview Overlay Button on Hover -->
          <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <button 
              onclick="event.stopPropagation(); openPreviewModal(${idx});" 
              class="p-2.5 rounded-full bg-dark-900/90 text-white hover:bg-brand-500 hover:scale-110 transition-all shadow-xl"
              title="Открыть предпросмотр"
            >
              <i data-lucide="maximize-2" class="w-4 h-4"></i>
            </button>
          </div>
        </div>

        <!-- Card Footer: Resolution, Score & Source -->
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span class="font-mono text-slate-300 font-medium">${resText}</span>
          <span class="text-amber-400 font-semibold flex items-center gap-0.5">★ ${score}</span>
        </div>
      </div>
    `;
  }).join('');

  if (window.lucide) {
    lucide.createIcons();
  }

  updateSelectionUI();
}

// Selection Logic
window.handleCardClick = function(event, idx) {
  const post = state.posts[idx];
  if (!post) return;
  const isSelected = state.selectedPosts.has(post.id);
  toggleSelectPost(post.id, !isSelected);
};

window.toggleSelectPost = function(postId, isChecked) {
  const post = state.posts.find(p => p.id === postId) || state.selectedPosts.get(postId);
  if (!post) return;

  if (isChecked) {
    state.selectedPosts.set(postId, post);
  } else {
    state.selectedPosts.delete(postId);
  }

  // Update card UI
  const card = document.getElementById(`card-${postId}`);
  if (card) {
    const chk = card.querySelector('input[type="checkbox"]');
    if (chk) chk.checked = isChecked;
    if (isChecked) {
      card.classList.add('border-brand-500', 'selected');
      card.classList.remove('border-slate-800');
    } else {
      card.classList.remove('border-brand-500', 'selected');
      card.classList.add('border-slate-800');
    }
  }

  updateSelectionUI();
};

function updateSelectionUI() {
  const count = state.selectedPosts.size;
  selectedCountBadge.innerText = `Выбрано: ${count} картинок`;
  dlCountSpan.innerText = count;

  if (count > 0) {
    downloadSelectedBtn.disabled = false;
    downloadZipBtn.disabled = false;
  } else {
    downloadSelectedBtn.disabled = true;
    downloadZipBtn.disabled = true;
  }
}

function selectAll() {
  state.posts.forEach(post => {
    state.selectedPosts.set(post.id, post);
  });
  renderGallery();
}

function deselectAll() {
  state.selectedPosts.clear();
  renderGallery();
}

function invertSelection() {
  state.posts.forEach(post => {
    if (state.selectedPosts.has(post.id)) {
      state.selectedPosts.delete(post.id);
    } else {
      state.selectedPosts.set(post.id, post);
    }
  });
  renderGallery();
}

function selectHighRes() {
  state.posts.forEach(post => {
    if ((post.width >= 1920 || post.height >= 1080)) {
      state.selectedPosts.set(post.id, post);
    } else {
      state.selectedPosts.delete(post.id);
    }
  });
  renderGallery();
}

// Lightbox Preview Modal
window.openPreviewModal = function(idx) {
  state.previewIndex = idx;
  const post = state.posts[idx];
  if (!post) return;

  const fullUrl = post.file_url ? `/api/proxy-image?url=${encodeURIComponent(post.file_url)}` : post.sample_url;
  
  modalImage.src = fullUrl;
  modalPostTitle.innerText = `Post #${post.id}`;
  modalSourceBadge.innerText = post.source.toUpperCase();
  modalRatingBadge.innerText = (post.rating || 'NSFW').toUpperCase();
  modalDimensions.innerText = post.width && post.height ? `${post.width} x ${post.height}` : 'Неизвестно';
  modalScore.innerText = `★ ${post.score || 0}`;
  modalFormat.innerText = (post.file_ext || 'JPG').toUpperCase();
  
  modalDownloadDirectBtn.href = post.file_url || post.sample_url;
  modalSourceLink.href = post.source_page_url || post.file_url;

  // Render tags
  modalTagsContainer.innerHTML = (post.tags || []).map(tag => `
    <span class="tag-chip text-[11px]" onclick="searchByTag('${tag}')">${tag}</span>
  `).join('');

  updateModalSelectButton();
  previewModal.classList.remove('hidden');

  if (window.lucide) {
    lucide.createIcons();
  }
};

function closeModal() {
  previewModal.classList.add('hidden');
  modalImage.src = '';
}

function navigateModal(direction) {
  const newIndex = state.previewIndex + direction;
  if (newIndex >= 0 && newIndex < state.posts.length) {
    openPreviewModal(newIndex);
  }
}

function updateModalSelectButton() {
  const post = state.posts[state.previewIndex];
  if (!post) return;
  const isSelected = state.selectedPosts.has(post.id);
  if (isSelected) {
    modalSelectToggleText.innerText = '✓ Выбрано (Нажмите чтобы снять)';
    modalSelectToggleBtn.classList.add('bg-brand-500/20', 'text-brand-400', 'border-brand-500');
  } else {
    modalSelectToggleText.innerText = 'Выбрать для скачивания';
    modalSelectToggleBtn.classList.remove('bg-brand-500/20', 'text-brand-400', 'border-brand-500');
  }
}

function toggleModalPostSelection() {
  const post = state.posts[state.previewIndex];
  if (!post) return;
  const isSelected = state.selectedPosts.has(post.id);
  toggleSelectPost(post.id, !isSelected);
  updateModalSelectButton();
}

window.searchByTag = function(tag) {
  closeModal();
  searchInput.value = tag;
  state.currentPage = 1;
  performSearch();
};

// Batch Downloading
async function startLocalDownload() {
  const posts = Array.from(state.selectedPosts.values());
  if (posts.length === 0) {
    showToast('Пожалуйста, выберите хотя бы одно изображение!', 'warning');
    return;
  }

  const payload = {
    posts: posts,
    destination_dir: state.settings.download_dir,
    naming_pattern: state.settings.naming_pattern,
    create_subfolders: state.settings.create_subfolders,
    subfolder_name: state.currentQuery || 'nsfw_images',
    skip_existing: state.settings.skip_existing,
    save_metadata: state.settings.save_metadata,
    threads: state.settings.threads
  };

  try {
    const res = await fetch('/api/download/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast(`Начато скачивание ${posts.length} файлов в ${payload.destination_dir}`, 'success');
      startDownloadPolling();
    } else {
      const err = await res.json();
      showToast(err.error || 'Ошибка запуска скачивания', 'error');
    }
  } catch (e) {
    showToast('Ошибка: ' + e.message, 'error');
  }
}

function startDownloadPolling() {
  downloadProgressCard.classList.remove('hidden');
  if (state.downloadPollingInterval) clearInterval(state.downloadPollingInterval);

  state.downloadPollingInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/download/status');
      if (res.ok) {
        const stats = await res.json();
        const total = stats.total || 1;
        const done = (stats.completed || 0) + (stats.skipped || 0) + (stats.failed || 0);
        const percent = stats.progress_percent || 0;

        dlProgressBar.style.width = `${percent}%`;
        dlProgressStats.innerText = `${done} / ${total} файлов (${stats.completed} скачано, ${stats.skipped} пропущено)`;
        dlSpeedText.innerText = `${stats.speed_kbps || 0} KB/s`;
        dlCurrentFile.innerText = stats.current_file ? `Текущий: ${stats.current_file}` : '';

        if (stats.status === 'completed' || stats.status === 'idle' || stats.status === 'cancelled') {
          clearInterval(state.downloadPollingInterval);
          state.downloadPollingInterval = null;
          
          if (stats.status === 'completed') {
            showToast(`Загрузка завершена! Успешно скачано: ${stats.completed} файлов.`, 'success');
          } else if (stats.status === 'cancelled') {
            showToast('Загрузка была отменена пользователем.', 'info');
          }

          setTimeout(() => {
            downloadProgressCard.classList.add('hidden');
          }, 4000);
        }
      }
    } catch (e) {
      console.warn('Polling error:', e);
    }
  }, 500);
}

async function cancelDownload() {
  try {
    await fetch('/api/download/cancel', { method: 'POST' });
    showToast('Отправлен запрос на отмену загрузки...', 'info');
  } catch (e) {
    console.error(e);
  }
}

async function downloadAsZip() {
  const posts = Array.from(state.selectedPosts.values());
  if (posts.length === 0) return;

  showToast(`Формирование ZIP архива (${posts.length} файлов)...`, 'info');

  try {
    const res = await fetch('/api/download/zip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        posts: posts,
        naming_pattern: state.settings.naming_pattern
      })
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `nsfw_images_${new Date().toISOString().slice(0,10)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      showToast('ZIP архив успешно скачан!', 'success');
    } else {
      showToast('Ошибка создания архива', 'error');
    }
  } catch (e) {
    showToast('Ошибка скачивания архива: ' + e.message, 'error');
  }
}

// Toast notification helper
function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  
  const colors = {
    success: 'bg-emerald-600 text-white border-emerald-500',
    error: 'bg-rose-600 text-white border-rose-500',
    warning: 'bg-amber-600 text-white border-amber-500',
    info: 'bg-dark-800 text-slate-100 border-slate-700'
  };

  toast.className = `pointer-events-auto px-4 py-3 rounded-xl border shadow-2xl text-xs font-medium flex items-center gap-2 transform transition-all duration-300 translate-y-2 opacity-0 ${colors[type] || colors.info}`;
  toast.innerHTML = `<span>${message}</span>`;
  
  toastContainer.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  }, 10);

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-y-2');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
