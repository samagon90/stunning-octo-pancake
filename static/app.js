// App State
const state = {
  posts: [],
  selectedPosts: new Map(), // id -> post object
  currentPage: 1,
  currentQuery: 'Милена Лисицына',
  currentSource: 'adult_meta',
  isLoading: false,
  hasMore: true,
  previewIndex: -1,
  mode: 'search',
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
const searchBtn = document.getElementById('searchBtn');
const galleryGrid = document.getElementById('galleryGrid');
const loadingGrid = document.getElementById('loadingGrid');
const emptyState = document.getElementById('emptyState');
const infiniteScrollContainer = document.getElementById('infiniteScrollContainer');
const loadingMoreSpinner = document.getElementById('loadingMoreSpinner');
const loadMoreBtn = document.getElementById('loadMoreBtn');
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

// Mode Switcher Elements
const modeSearchBtn = document.getElementById('modeSearchBtn');
const modeBrowserBtn = document.getElementById('modeBrowserBtn');
const searchBoxContainer = document.getElementById('searchBoxContainer');
const urlGrabberContainer = document.getElementById('urlGrabberContainer');
const urlGrabberInput = document.getElementById('urlGrabberInput');
const grabUrlBtn = document.getElementById('grabUrlBtn');
const presetsBar = document.getElementById('presetsBar');

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

// Initial Setup
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  await fetchSettings();
  setupEventListeners();
  setupInfiniteScroll();
  
  if (searchInput) searchInput.value = 'Милена Лисицына';
  performSearch(true);
});

// Infinite Scroll Window Listener
function setupInfiniteScroll() {
  window.addEventListener('scroll', () => {
    if (state.isLoading || !state.hasMore || state.posts.length === 0) return;
    
    const scrollPosition = window.innerHeight + window.scrollY;
    const threshold = document.body.offsetHeight - 400;
    
    if (scrollPosition >= threshold) {
      loadNextPage();
    }
  });

  if (loadMoreBtn) {
    loadMoreBtn.addEventListener('click', () => {
      loadNextPage();
    });
  }
}

function loadNextPage() {
  if (state.isLoading || !state.hasMore) return;
  state.currentPage += 1;
  performSearch(false);
}

// Mode Switching
function switchMode(mode) {
  state.mode = mode;
  if (mode === 'search') {
    modeSearchBtn.classList.add('bg-brand-500', 'text-white');
    modeSearchBtn.classList.remove('text-slate-400');
    modeBrowserBtn.classList.remove('bg-brand-500', 'text-white');
    modeBrowserBtn.classList.add('text-slate-400');

    searchBoxContainer.classList.remove('hidden');
    urlGrabberContainer.classList.add('hidden');
    presetsBar.classList.remove('hidden');
  } else {
    modeBrowserBtn.classList.add('bg-brand-500', 'text-white');
    modeBrowserBtn.classList.remove('text-slate-400');
    modeSearchBtn.classList.remove('bg-brand-500', 'text-white');
    modeSearchBtn.classList.add('text-slate-400');

    searchBoxContainer.classList.add('hidden');
    urlGrabberContainer.classList.remove('hidden');
    presetsBar.classList.add('hidden');
  }
}

// External Search Openers
window.openExternalSearch = function(engine) {
  const q = encodeURIComponent(searchInput ? searchInput.value.trim() || 'Милена Лисицына' : 'Милена Лисицына');
  let targetUrl = '';
  if (engine === 'yandex') targetUrl = `https://yandex.ru/images/search?text=${q}`;
  else if (engine === 'bing') targetUrl = `https://www.bing.com/images/search?q=${q}&adlt=off`;
  else if (engine === 'erome') targetUrl = `https://www.erome.com/search?q=${q}`;
  else if (engine === 'coomer') targetUrl = `https://coomer.su/posts?q=${q}`;

  urlGrabberInput.value = targetUrl;
  window.open(targetUrl, '_blank');
  showToast('Страница открыта в браузере. Скопируйте ссылку и нажмите «Захватить»!', 'info');
};

// URL Grabber Action
async function handleUrlGrab() {
  const url = urlGrabberInput.value.trim();
  if (!url) {
    showToast('Пожалуйста, вставьте ссылку на страницу с картинками!', 'warning');
    return;
  }

  showLoading(true);
  statusBanner.classList.add('hidden');

  try {
    showToast('Захват всех изображений со страницы...', 'info');
    const res = await fetch(`/api/extract-url?url=${encodeURIComponent(url)}`);
    if (!res.ok) throw new Error(`Ошибка захвата: ${res.status}`);

    const data = await res.json();
    state.posts = data.posts || [];

    if (state.posts.length === 0) {
      showToast('На указанной странице не найдено прямых картинок.', 'warning');
      statusBannerText.innerText = 'На странице не найдено подходящих изображений. Попробуйте скопировать ссылку на конкретный альбом или поисковую выдачу.';
      statusBanner.classList.remove('hidden');
    } else {
      showToast(`Успешно захвачено ${state.posts.length} картинок со страницы!`, 'success');
    }

    renderGallery();
  } catch (e) {
    showToast('Ошибка: ' + e.message, 'error');
  } finally {
    showLoading(false);
  }
}

// Presets
window.applyPreset = function(tags) {
  if (searchInput) searchInput.value = tags;
  state.currentPage = 1;
  performSearch(true);
};

// Settings Management
async function fetchSettings() {
  try {
    const res = await fetch('/api/settings');
    if (res.ok) {
      state.settings = await res.json();
      if (settingDownloadDir) settingDownloadDir.value = state.settings.download_dir || './downloads';
    }
  } catch (e) {
    console.warn('Could not load settings:', e);
  }
}

async function saveSettings() {
  const updated = {
    download_dir: settingDownloadDir ? settingDownloadDir.value.trim() || './downloads' : './downloads',
    naming_pattern: '{source}_{id}_{tags}',
    threads: 4,
    limit: 40,
    create_subfolders: true,
    skip_existing: true,
    save_metadata: true
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
  if (modeSearchBtn) modeSearchBtn.addEventListener('click', () => switchMode('search'));
  if (modeBrowserBtn) modeBrowserBtn.addEventListener('click', () => switchMode('browser'));
  if (grabUrlBtn) grabUrlBtn.addEventListener('click', handleUrlGrab);
  if (urlGrabberInput) {
    urlGrabberInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleUrlGrab();
    });
  }

  if (searchBtn) {
    searchBtn.addEventListener('click', () => {
      performSearch(true);
    });
  }

  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        if (autocompleteList) autocompleteList.classList.add('hidden');
        performSearch(true);
      }
    });
  }

  if (sourceSelect) {
    sourceSelect.addEventListener('change', () => {
      performSearch(true);
    });
  }

  // Selection actions
  if (selectAllBtn) selectAllBtn.addEventListener('click', selectAll);
  if (deselectAllBtn) deselectAllBtn.addEventListener('click', deselectAll);
  if (invertSelectBtn) invertSelectBtn.addEventListener('click', invertSelection);
  if (selectHighResBtn) selectHighResBtn.addEventListener('click', selectHighRes);

  // Download actions
  if (downloadSelectedBtn) downloadSelectedBtn.addEventListener('click', startLocalDownload);
  if (downloadZipBtn) downloadZipBtn.addEventListener('click', downloadAsZip);
  if (cancelDlBtn) cancelDlBtn.addEventListener('click', cancelDownload);

  // Modal
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
  if (modalPrevBtn) modalPrevBtn.addEventListener('click', () => navigateModal(-1));
  if (modalNextBtn) modalNextBtn.addEventListener('click', () => navigateModal(1));
  if (modalSelectToggleBtn) modalSelectToggleBtn.addEventListener('click', toggleModalPostSelection);

  // Help modal
  if (openHelpBtn) openHelpBtn.addEventListener('click', () => helpModal.classList.remove('hidden'));
  if (closeHelpModalBtn) closeHelpModalBtn.addEventListener('click', () => helpModal.classList.add('hidden'));
  if (closeHelpBtn2) closeHelpBtn2.addEventListener('click', () => helpModal.classList.add('hidden'));

  // Keyboard navigation for modal
  document.addEventListener('keydown', (e) => {
    if (previewModal && !previewModal.classList.contains('hidden')) {
      if (e.key === 'Escape') closeModal();
      else if (e.key === 'ArrowLeft') navigateModal(-1);
      else if (e.key === 'ArrowRight') navigateModal(1);
    }
  });

  // Settings modal
  if (openSettingsBtn) openSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  if (closeSettingsModalBtn) closeSettingsModalBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  if (cancelSettingsBtn) cancelSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));
  if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', saveSettings);
}

// Search Execution
async function performSearch(reset = true) {
  if (state.isLoading) return;

  if (reset) {
    state.currentPage = 1;
    state.posts = [];
    state.hasMore = true;
    showLoading(true);
  } else {
    if (loadingMoreSpinner) loadingMoreSpinner.classList.remove('hidden');
    if (loadMoreBtn) loadMoreBtn.classList.add('hidden');
  }

  state.isLoading = true;
  const query = searchInput ? searchInput.value.trim() : 'Милена Лисицына';
  const source = sourceSelect ? sourceSelect.value : 'adult_meta';

  state.currentQuery = query;
  state.currentSource = source;
  statusBanner.classList.add('hidden');

  try {
    const params = new URLSearchParams({
      query: query,
      source: source,
      page: state.currentPage,
      limit: 40
    });

    const res = await fetch(`/api/search?${params.toString()}`);
    if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);

    const data = await res.json();
    const newItems = data.posts || [];

    if (newItems.length === 0) {
      state.hasMore = false;
    } else {
      const seenIds = new Set(state.posts.map(p => p.id));
      for (const item of newItems) {
        if (!seenIds.has(item.id)) {
          seenIds.add(item.id);
          state.posts.push(item);
        }
      }
    }

    if (data.errors && data.errors.length > 0 && state.posts.length === 0) {
      statusBannerText.innerText = data.errors.join(' | ');
      statusBanner.classList.remove('hidden');
    }

    renderGallery();
  } catch (err) {
    console.error('Search error:', err);
    showToast('Ошибка поиска: ' + err.message, 'error');
  } finally {
    state.isLoading = false;
    showLoading(false);
    if (loadingMoreSpinner) loadingMoreSpinner.classList.add('hidden');
    if (loadMoreBtn && state.hasMore && state.posts.length > 0) {
      loadMoreBtn.classList.remove('hidden');
    }
  }
}

function showLoading(isLoading) {
  if (isLoading) {
    emptyState.classList.add('hidden');
    galleryGrid.classList.add('hidden');
    if (infiniteScrollContainer) infiniteScrollContainer.classList.add('hidden');
    loadingGrid.classList.remove('hidden');
    
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
    if (infiniteScrollContainer && state.posts.length > 0) {
      infiniteScrollContainer.classList.remove('hidden');
    }
  }
}

// Gallery Rendering
function renderGallery() {
  if (!state.posts || state.posts.length === 0) {
    galleryGrid.innerHTML = '';
    emptyState.classList.remove('hidden');
    if (infiniteScrollContainer) infiniteScrollContainer.classList.add('hidden');
    return;
  }

  emptyState.classList.add('hidden');
  if (infiniteScrollContainer) infiniteScrollContainer.classList.remove('hidden');

  galleryGrid.innerHTML = state.posts.map((post, idx) => {
    const isSelected = state.selectedPosts.has(post.id);
    const previewUrl = post.preview_url ? `/api/proxy-image?url=${encodeURIComponent(post.preview_url)}` : post.file_url;
    const resText = post.width && post.height ? `${post.width}×${post.height}` : (post.file_ext || 'IMG').toUpperCase();
    const sourceText = (post.source || 'WEB').toUpperCase();

    return `
      <div 
        id="card-${post.id}" 
        class="image-card relative group bg-dark-800 border ${isSelected ? 'border-brand-500 selected' : 'border-slate-800'} rounded-2xl p-2.5 flex flex-col justify-between transition-all cursor-pointer"
        onclick="handleCardClick(event, ${idx})"
      >
        <!-- Card Top Bar -->
        <div class="flex items-center justify-between mb-2 z-10">
          <label class="flex items-center cursor-pointer" onclick="event.stopPropagation()">
            <input 
              type="checkbox" 
              class="w-4 h-4 rounded bg-dark-900 border-slate-700 text-brand-500 focus:ring-brand-500 cursor-pointer" 
              ${isSelected ? 'checked' : ''}
              onchange="toggleSelectPost('${post.id}', this.checked)"
            />
          </label>

          <span class="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider bg-rose-500/20 text-rose-400 border border-rose-500/30">
            ${sourceText.slice(0, 10)}
          </span>
        </div>

        <!-- Thumbnail Container -->
        <div class="relative w-full h-56 bg-dark-950 rounded-xl overflow-hidden mb-2 flex items-center justify-center">
          <img 
            src="${previewUrl}" 
            alt="Thumbnail" 
            loading="lazy" 
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onerror="this.onerror=null; this.style.opacity='0.4';"
          />

          <!-- Quick Zoom Overlay -->
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

        <!-- Card Footer -->
        <div class="flex items-center justify-between text-[11px] text-slate-400 px-1">
          <span class="font-mono text-slate-300 font-medium">${resText}</span>
          <span class="text-amber-400 font-semibold flex items-center gap-0.5">★ ${post.score || 950}</span>
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
  modalPostTitle.innerText = `Photo #${post.id}`;
  modalSourceBadge.innerText = post.source.toUpperCase();
  modalRatingBadge.innerText = (post.rating || 'NSFW').toUpperCase();
  modalDimensions.innerText = post.width && post.height ? `${post.width} x ${post.height}` : '1920x1080';
  modalScore.innerText = `★ ${post.score || 950}`;
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
  if (searchInput) searchInput.value = tag;
  performSearch(true);
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
    destination_dir: state.settings.download_dir || './downloads',
    naming_pattern: '{source}_{id}_{tags}',
    create_subfolders: true,
    subfolder_name: state.currentQuery || 'models',
    skip_existing: true,
    save_metadata: true,
    threads: 4
  };

  try {
    const res = await fetch('/api/download/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast(`Начато скачивание ${posts.length} файлов в папку ${payload.destination_dir}`, 'success');
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
        dlProgressStats.innerText = `${done} / ${total} файлов (${stats.completed} скачано)`;
        dlSpeedText.innerText = `${stats.speed_kbps || 0} KB/s`;
        dlCurrentFile.innerText = stats.current_file ? `Текущий: ${stats.current_file}` : '';

        if (stats.status === 'completed' || stats.status === 'idle' || stats.status === 'cancelled') {
          clearInterval(state.downloadPollingInterval);
          state.downloadPollingInterval = null;
          
          if (stats.status === 'completed') {
            showToast(`Загрузка завершена! Успешно скачано: ${stats.completed} файлов.`, 'success');
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
        naming_pattern: '{source}_{id}_{tags}'
      })
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `photos_collection_${new Date().toISOString().slice(0,10)}.zip`;
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

// Toast helper
function showToast(message, type = 'info') {
  const toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) return;
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
