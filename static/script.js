// Store uploaded files - declared in base.html template
// let uploadedFiles = []; // Removed - declared in template
let activeListId = null;
let currentSchedules = [];

// Load schedule lists
async function loadScheduleLists() {
    console.log('Loading schedule lists...');
    try {
        const response = await fetch('/schedule_lists');
        console.log('Schedule lists response status:', response.status);
        
        const lists = await response.json();
        console.log('Schedule lists data:', lists);
        
        const tabsContainer = document.getElementById('scheduleListTabs');
        if (!tabsContainer) {
            console.log('scheduleListTabs element not found');
            return;
        }
        
        tabsContainer.innerHTML = '';
        
        // First, remove active class from all existing tabs to prevent conflicts
        const existingTabs = document.querySelectorAll('.schedule-list-tabs .tab');
        existingTabs.forEach(tab => tab.classList.remove('active'));
        
        lists.forEach(list => {
            const tab = document.createElement('div');
            // Start with basic tab class
            tab.className = 'tab';
            tab.onclick = () => activateList(list.id);
            
            if (list.is_active) {
                activeListId = list.id;
                // Add active class to the server-determined active list
                tab.classList.add('active');
                console.log('Marked schedule list tab as active:', list.name);
            }
            
            tab.innerHTML = `
                <span class="tab-name" id="tab-name-${list.id}">${list.name}</span>
                <input type="text" class="tab-name-edit" id="tab-edit-${list.id}" value="${list.name}" style="display:none;" />
                <button class="tab-action" onclick="event.stopPropagation(); startRenameList(${list.id})" title="${appTranslations.schedule_lists?.rename || 'Rename'}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="tab-action" onclick="event.stopPropagation(); deleteList(${list.id})" title="${appTranslations.schedule_lists?.delete_list || 'Delete'}">
                    <i class="fas fa-times"></i>
                </button>
            `;
            tabsContainer.appendChild(tab);
        });
        
        // Add new list button
        const newTabBtn = document.createElement('div');
        newTabBtn.className = 'tab new-tab';
        newTabBtn.onclick = createNewList;
        newTabBtn.innerHTML = `<i class="fas fa-plus"></i> ${appTranslations.schedule_lists?.new_list || 'New List'}`;
        tabsContainer.appendChild(newTabBtn);
        
        console.log('Schedule lists loaded, activeListId:', activeListId);
        
    } catch (error) {
        console.error('Error loading schedule lists:', error);
    }
}

async function createNewList() {
    const name = prompt(appTranslations.schedule_lists?.name_prompt || 'Enter list name:', '');
    if (!name) return;
    
    try {
        const response = await fetch('/schedule_lists', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();
        if (data.success) {
            loadScheduleLists();
        }
    } catch (error) {
        console.error('Error creating list:', error);
        showMessageModal('Error', 'Failed to create list');
    }
}

async function activateList(listId) {
    try {
        const response = await fetch(`/schedule_lists/${listId}/activate`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            activeListId = listId;
            // Ensure only one schedule list tab is active
            ensureOnlyOneScheduleListTabActive(listId);
            loadScheduleLists();
            loadSchedules();
        }
    } catch (error) {
        console.error('Error activating list:', error);
        showMessageModal('Error', 'Failed to activate list');
    }
}

// Ensure only one schedule list tab is active at a time
function ensureOnlyOneScheduleListTabActive(activeId = null) {
    const allTabs = document.querySelectorAll('.schedule-list-tabs .tab:not(.new-tab)');
    
    // Remove active class from all tabs first
    allTabs.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // If activeId is provided, find and activate that specific tab
    if (activeId) {
        const activeTab = Array.from(allTabs).find(tab => {
            const onclickAttr = tab.getAttribute('onclick');
            return onclickAttr && onclickAttr.includes(`activateList(${activeId})`);
        });
        
        if (activeTab) {
            activeTab.classList.add('active');
        }
    } else if (activeListId) {
        // If no activeId provided but we have a global activeListId, use that
        const activeTab = Array.from(allTabs).find(tab => {
            const onclickAttr = tab.getAttribute('onclick');
            return onclickAttr && onclickAttr.includes(`activateList(${activeListId})`);
        });
        
        if (activeTab) {
            activeTab.classList.add('active');
        }
    }
}

function startRenameList(listId) {
    const nameSpan = document.getElementById(`tab-name-${listId}`);
    const editInput = document.getElementById(`tab-edit-${listId}`);
    
    if (!nameSpan || !editInput) return;
    
    // Show input, hide span
    nameSpan.style.display = 'none';
    editInput.style.display = 'inline-block';
    editInput.focus();
    editInput.select();
    
    // Handle save on Enter or blur
    const saveRename = async () => {
        const newName = editInput.value.trim();
        if (!newName) {
            loadScheduleLists(); // Reset if empty
            return;
        }
        
        try {
            const response = await fetch(`/schedule_lists/${listId}/rename`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName })
            });
            const data = await response.json();
            if (data.success) {
                loadScheduleLists();
            }
        } catch (error) {
            console.error('Error renaming list:', error);
            showMessageModal('Error', 'Failed to rename list');
        }
    };
    
    editInput.onkeydown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveRename();
        } else if (e.key === 'Escape') {
            loadScheduleLists(); // Cancel
        }
    };
    
    editInput.onblur = saveRename;
}

function deleteList(listId) {
    showDeleteListModal(listId);
}

// Upload audio file
async function uploadFile() {
    const fileInput = document.getElementById('audioFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessageModal(appTranslations && appTranslations.modals && appTranslations.modals.info && appTranslations.modals.info.title ? appTranslations.modals.info.title : 'Info', 'Please select a file first');
        return;
    }

    const formData = new FormData();
    formData.append('audio', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessageModal(appTranslations && appTranslations.modals && appTranslations.modals.info && appTranslations.modals.info.title ? appTranslations.modals.info.title : 'Info', 'File uploaded successfully!');
            // Reload the page to refresh the file list after a short delay so the user can see the modal
            setTimeout(() => window.location.reload(), 800);
        } else {
            showMessageModal('Error', 'Error uploading file: ' + data.error);
        }
    } catch (error) {
        showMessageModal('Error', 'Error uploading file: ' + error);
    }
}

// Update file select dropdown
function updateFileSelect() {
    const select = document.getElementById('fileSelect');
    if (!select) return;
    
    // Keep the default option
    select.innerHTML = '<option value="">Select File</option>';
    
    uploadedFiles.forEach(filename => {
        const option = document.createElement('option');
        option.value = filename;
        option.textContent = filename;
        select.appendChild(option);
    });
}

// Show custom modal for success/error when adding a schedule instead of alert.
function showMessageModal(title, message) {
    document.getElementById('messageModalTitle').textContent = title;
    document.getElementById('messageModalText').textContent = message;
    document.getElementById('messageModal').style.display = 'flex';
}
function hideMessageModal() {
    document.getElementById('messageModal').style.display = 'none';
}

// Audio preview functionality
let audioPlayer = null;

function playSelectedFile() {
    const selectedFile = document.getElementById('fileSelect').value;
    const playButton = document.querySelector('.file-select-group .action-btn');
    
    if (!selectedFile) {
        showMessageModal('Error', 'Please select an audio file first');
        return;
    }

    if (audioPlayer && !audioPlayer.paused) {
        // If audio is playing, stop it
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        playButton.innerHTML = '<i class="fas fa-play"></i>';
        playButton.title = 'Play';
    } else {
        // If no audio is playing, start playing
        if (!audioPlayer) {
            audioPlayer = new Audio();
            audioPlayer.onended = () => {
                playButton.innerHTML = '<i class="fas fa-play"></i>';
                playButton.title = 'Play';
            };
            audioPlayer.onerror = (error) => {
                console.error('Audio error:', error);
                showMessageModal('Error', 'Failed to load audio file');
                playButton.innerHTML = '<i class="fas fa-play"></i>';
                playButton.title = 'Play';
            };
        }
        
        const audioUrl = `/audio/${selectedFile}`;
        console.log('Attempting to play audio:', audioUrl);
        audioPlayer.src = audioUrl;
        audioPlayer.play()
            .then(() => {
                console.log('Audio playback started successfully');
                playButton.innerHTML = '<i class="fas fa-stop"></i>';
                playButton.title = 'Stop';
            })
            .catch((error) => {
                console.error('Error playing audio:', error);
                showMessageModal('Error', `Failed to play audio file: ${error.message}`);
                playButton.innerHTML = '<i class="fas fa-play"></i>';
                playButton.title = 'Play';
            });
    }
}

// Add new schedule
async function addSchedule() {
    const filename = document.getElementById('fileSelect').value;
    const time = document.getElementById('timeInput').value;
    const dayCheckboxes = document.querySelectorAll('#schedulesTab input[type="checkbox"][name="days"]');
    
    if (!filename) {
        showMessageModal('Error', 'Please upload and select an audio file');
        return;
    }
    
    if (!time) {
        showMessageModal('Error', 'Please select a time');
        return;
    }
    
    const selectedDays = [];
    dayCheckboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedDays.push(parseInt(checkbox.value));
        }
    });
    
    if (selectedDays.length === 0) {
        showMessageModal('Error', 'Please select at least one day');
        return;
    }

    try {
        const response = await fetch('/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: filename,
                schedule: [{
                    days: selectedDays,
                    time: time
                }]
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessageModal('Success', 'Schedule added successfully!');
            loadSchedules();
            // Clear the form
            document.getElementById('fileSelect').value = '';
            document.getElementById('timeInput').value = '';
            dayCheckboxes.forEach(checkbox => checkbox.checked = false);
        } else {
            showMessageModal('Error', 'Error adding schedule: ' + data.error);
        }
    } catch (error) {
        showMessageModal('Error', 'Error adding schedule: ' + error);
    }
}

// Delete confirmation modal
let pendingDeleteId = null;
let pendingDeleteType = null; // 'schedule' or 'list'

function showDeleteModal(id) {
    pendingDeleteId = id;
    pendingDeleteType = 'schedule';
    document.getElementById('deleteModal').style.display = 'flex';
}

function showDeleteListModal(id) {
    pendingDeleteId = id;
    pendingDeleteType = 'list';
    document.getElementById('deleteModal').style.display = 'flex';
}

function hideDeleteModal() {
    pendingDeleteId = null;
    pendingDeleteType = null;
    document.getElementById('deleteModal').style.display = 'none';
}

async function confirmDelete() {
    if (!pendingDeleteId || !pendingDeleteType) return;
    
    try {
        let response;
        if (pendingDeleteType === 'schedule') {
            response = await fetch(`/delete_schedule/${pendingDeleteId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (data.success) {
                loadSchedules();
                // Also reload playlist schedules if we're on the playlists tab
                const playlistsTab = document.getElementById('playlistsTab');
                if (playlistsTab && playlistsTab.classList.contains('active')) {
                    loadPlaylistSchedules();
                }
            } else {
                showMessageModal('Error', 'Error deleting schedule');
            }
        } else if (pendingDeleteType === 'list') {
            response = await fetch(`/schedule_lists/${pendingDeleteId}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            if (data.success) {
                loadScheduleLists();
                loadSchedules();
                // Also reload playlist schedules
                loadPlaylistSchedules();
            } else if (data.error) {
                showMessageModal('Error', data.error);
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showMessageModal('Error', 'Error deleting item');
    }
    hideDeleteModal();
}

// Toggle mute/unmute
async function toggleMute(id) {
    try {
        const response = await fetch(`/toggle_mute/${id}`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            loadSchedules();
            // Also refresh playlist schedules if we're on the playlists tab
            const playlistsTab = document.getElementById('playlistsTab');
            if (playlistsTab && playlistsTab.classList.contains('active')) {
                loadPlaylistSchedules();
            }
        } else {
            showMessageModal('Error', 'Error toggling mute status');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessageModal('Error', 'Error toggling mute status');
    }
}

// Load current schedules
async function loadSchedules() {
    console.log('Loading schedules...');
    try {
        const response = await fetch('/get_schedules');
        console.log('Schedules response status:', response.status);
        
        const schedules = await response.json();
        console.log('Schedules data:', schedules);
        
        currentSchedules = schedules;
        
        const schedulesList = document.getElementById('schedulesList');
        if (!schedulesList) {
            console.log('schedulesList element not found');
            // Not on a page with schedules table (e.g., login/settings)
            return;
        }
        
        console.log('Populating schedules table with', schedules.length, 'items');
        schedulesList.innerHTML = '';
        schedules.forEach(schedule => {
            const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            const dayNames = schedule.days.map(d => appTranslations.days_list[dayKeys[d]]);
            const locale = mapLangToLocale(currentLang);
            const nextRun = schedule.next_run
                ? new Date(schedule.next_run).toLocaleString(locale)
                : appTranslations.current_schedules.not_scheduled || 'Not scheduled';
            
            // Display filename for single files, folder name for playlists
            const displayName = schedule.schedule_type === 'playlist' 
                ? (schedule.folder_path ? schedule.folder_path.split('/').pop() + ' (Playlist)' : 'Playlist')
                : schedule.filename;
            
            const muteButtonTitle = schedule.is_muted 
                ? (appTranslations.current_schedules.unmute || 'Unmute')
                : (appTranslations.current_schedules.mute || 'Mute');
            const muteButtonIcon = schedule.is_muted ? 'fa-volume-up' : 'fa-volume-mute';
            const muteButtonClass = schedule.is_muted ? 'unmute' : 'mute';
            const rowClass = schedule.is_muted ? 'muted' : '';
            
            const row = document.createElement('tr');
            row.className = rowClass;
            row.innerHTML = `
                <td>${displayName}</td>
                <td>${schedule.time}</td>
                <td>${dayNames.join(', ')}</td>
                <td>${nextRun}</td>
                <td>
                    <button class="action-btn" title="${appTranslations.current_schedules?.edit || 'Edit'}" onclick="openEditModal(${schedule.id})">
                        <i class="fas fa-pen"></i>
                    </button>
                    <button class="action-btn ${muteButtonClass}" title="${muteButtonTitle}" onclick="toggleMute(${schedule.id})">
                        <i class="fas ${muteButtonIcon}"></i>
                    </button>
                    <button class="action-btn delete" title="${appTranslations.current_schedules.delete || 'Delete'}" onclick="showDeleteModal(${schedule.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            schedulesList.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading schedules:', error);
    }
}

// Edit schedule modal logic
function openEditModal(id) {
    const schedule = currentSchedules.find(s => s.id === id);
    if (!schedule) return;

    // Set hidden id
    document.getElementById('editScheduleId').value = id;

    // Set time
    const timeInput = document.getElementById('editScheduleTime');
    timeInput.value = schedule.time;

    // Set days
    const dayCheckboxes = document.querySelectorAll('#editDaysCheckboxes input[type="checkbox"]');
    dayCheckboxes.forEach(cb => cb.checked = false);
    schedule.days.forEach(d => {
        const cb = document.querySelector(`#editDaysCheckboxes input[type="checkbox"][value="${d}"]`);
        if (cb) cb.checked = true;
    });

    // Show modal
    document.getElementById('editModal').style.display = 'flex';
}

function hideEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

async function confirmEdit() {
    const id = parseInt(document.getElementById('editScheduleId').value, 10);
    const time = document.getElementById('editScheduleTime').value;
    const dayCheckboxes = document.querySelectorAll('#editDaysCheckboxes input[type="checkbox"]');
    const days = [];
    dayCheckboxes.forEach(cb => { if (cb.checked) days.push(parseInt(cb.value)); });

    if (!time || days.length === 0) {
        showMessageModal('Error', 'Please select time and at least one day');
        return;
    }

    try {
        const resp = await fetch(`/update_schedule/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ time, days })
        });
        const data = await resp.json();
        if (data.success) {
            hideEditModal();
            loadSchedules();
        } else {
            showMessageModal('Error', data.error || 'Failed to update schedule');
        }
    } catch (e) {
        console.error(e);
        showMessageModal('Error', 'Failed to update schedule');
    }
}

// Language menu toggle
function toggleLanguageMenu() {
    const menu = document.getElementById('languageMenu');
    menu.classList.toggle('show');
}

// Handle clicking outside language menu
document.addEventListener('click', function(event) {
    const menu = document.getElementById('languageMenu');
    const langBtn = document.querySelector('.lang-btn');
    if (!menu.contains(event.target) && !langBtn.contains(event.target)) {
        menu.classList.remove('show');
    }
});

// Change language
async function changeLanguage(lang) {
    try {
        const response = await fetch(`/set-language/${lang}`, {
            method: 'GET',
            credentials: 'same-origin'
        });
        const data = await response.json();
        if (data && data.success) {
            // Close menu and reload
            const menu = document.getElementById('languageMenu');
            if (menu) menu.classList.remove('show');
            window.location.reload();
            return false;
        } else {
            showMessageModal('Error', 'Failed to change language');
            return false;
        }
    } catch (error) {
        console.error('Error changing language:', error);
        showMessageModal('Error', 'Failed to change language');
        return false;
    }
}

// Modal event listeners and initialization
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Starting initialization');
    console.log('appTranslations:', appTranslations);
    console.log('uploadedFiles:', uploadedFiles);
    
    try {
        // Initialize tab states - ensure only one main tab is active
        initializeTabStates();
        
        // Initialize modal buttons
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
        const closeMessageModalBtn = document.getElementById('closeMessageModalBtn');
        const confirmEditBtn = document.getElementById('confirmEditBtn');
        const cancelEditBtn = document.getElementById('cancelEditBtn');
        
        if (confirmDeleteBtn) confirmDeleteBtn.onclick = confirmDelete;
        if (cancelDeleteBtn) cancelDeleteBtn.onclick = hideDeleteModal;
        if (closeMessageModalBtn) closeMessageModalBtn.onclick = hideMessageModal;
        if (confirmEditBtn) confirmEditBtn.onclick = confirmEdit;
        if (cancelEditBtn) cancelEditBtn.onclick = hideEditModal;
        
        console.log('Modal buttons initialized');
        
        // Initialize clock
        startRealtimeClock();
        console.log('Clock started');
        
        // Load initial data
        console.log('Loading schedule lists...');
        loadScheduleLists();
        console.log('Loading schedules...');
        loadSchedules();
        
        // Initialize playlist folder selection
        const folderSelect = document.getElementById('folderSelect');
        if (folderSelect) {
            console.log('Playlist folder select found, adding event listener');
            folderSelect.addEventListener('change', function() {
                const selectedPath = this.value;
                const preview = document.getElementById('folderPreview');
                
                if (!selectedPath || !preview) {
                    if (preview) preview.classList.remove('show');
                    return;
                }
                
                const folder = playlistFolders.find(f => f.path === selectedPath);
                if (folder) {
                    const folderPreviewText = appTranslations.playlist?.folder_preview || 'Audio files:';
                    preview.innerHTML = `
                        <div class="folder-info">
                            <strong>${folder.name}</strong> - ${folder.file_count} audio files
                        </div>
                        <div class="folder-files">
                            <strong>${folderPreviewText}</strong>
                            <ul>
                                ${folder.files.map(file => `<li>${file}</li>`).join('')}
                                ${folder.file_count > 5 ? `<li><em>... and ${folder.file_count - 5} more</em></li>` : ''}
                            </ul>
                        </div>
                    `;
                    preview.classList.add('show');
                }
            });
        }
        
        console.log('Initialization completed successfully');
    } catch (error) {
        console.error('Error during initialization:', error);
    }
});

// Initialize tab states to ensure only proper tabs are active
function initializeTabStates() {
    console.log('Initializing tab states...');
    
    // For main tabs, ensure HTML template state is respected
    const schedulesBtn = document.getElementById('schedulesTabBtn');
    const playlistsBtn = document.getElementById('playlistsTabBtn');
    const schedulesTab = document.getElementById('schedulesTab');
    const playlistsTab = document.getElementById('playlistsTab');
    
    // Force reset all main tabs first
    if (schedulesBtn) schedulesBtn.classList.remove('active');
    if (playlistsBtn) playlistsBtn.classList.remove('active');
    if (schedulesTab) schedulesTab.classList.remove('active');
    if (playlistsTab) playlistsTab.classList.remove('active');
    
    // Activate only schedules tab (default)
    if (schedulesBtn) {
        schedulesBtn.classList.add('active');
        console.log('Activated schedules button');
    }
    
    if (schedulesTab) {
        schedulesTab.classList.add('active');
        console.log('Activated schedules tab');
    }
    
    console.log('Main tab states initialized - only schedules should be active');
}

// Realtime clock updater
function startRealtimeClock() {
    const el = document.getElementById('realtimeClock');
    if (!el) return;
    const update = () => {
        try {
            const now = new Date();
            const locale = mapLangToLocale(currentLang);
            const time = now.toLocaleTimeString(locale, { hour12: false });
            el.textContent = time;
            el.title = now.toLocaleString(locale);
        } catch (e) {
            // Fallback
            el.textContent = new Date().toISOString().slice(11, 19);
        }
    };
    update();
    setInterval(update, 1000);
}

// Map app language code to full locale
function mapLangToLocale(lang) {
    switch (lang) {
        case 'hu': return 'hu-HU';
        case 'de': return 'de-DE';
        case 'es': return 'es-ES';
        case 'en':
        default: return 'en-US';
    }
}

// Tab switching functionality
function showTab(tabName) {
    console.log('Switching to tab:', tabName);
    
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        console.log('Removed active from tab content:', tab.id);
    });
    
    // Remove active class from all main tab buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        btn.classList.remove('active');
        console.log('Removed active from button:', btn.id);
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + 'Tab');
    const selectedButton = document.getElementById(tabName + 'TabBtn');
    
    if (selectedTab) {
        selectedTab.classList.add('active');
        console.log('Activated tab:', tabName + 'Tab');
    } else {
        console.log('Tab not found:', tabName + 'Tab');
    }
    
    if (selectedButton) {
        selectedButton.classList.add('active');
        console.log('Activated button:', tabName + 'TabBtn');
    } else {
        console.log('Button not found:', tabName + 'TabBtn');
    }
    
    // Load data for the selected tab
    if (tabName === 'playlists') {
        console.log('Loading playlist data...');
        loadPlaylistFolders();
        loadPlaylistSchedules();
    } else if (tabName === 'schedules') {
        console.log('Loading schedules data...');
        loadSchedules();
    }
}

// Playlist functionality
let playlistFolders = [];

async function loadPlaylistFolders() {
    console.log('Loading playlist folders...');
    try {
        const response = await fetch('/get_playlist_folders');
        console.log('Playlist folders response status:', response.status);
        
        playlistFolders = await response.json();
        console.log('Playlist folders data:', playlistFolders);
        
        const folderSelect = document.getElementById('folderSelect');
        if (!folderSelect) {
            console.log('folderSelect element not found');
            return;
        }
        
        folderSelect.innerHTML = `<option value="">${appTranslations.playlist?.select_folder || 'Select a playlist folder'}</option>`;
        
        if (playlistFolders.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = appTranslations.playlist?.no_folders || 'No playlist folders found';
            option.disabled = true;
            folderSelect.appendChild(option);
        } else {
            playlistFolders.forEach(folder => {
                const option = document.createElement('option');
                option.value = folder.path;
                option.textContent = `${folder.name} (${folder.file_count} files)`;
                folderSelect.appendChild(option);
            });
        }
        
    } catch (error) {
        console.error('Error loading playlist folders:', error);
    }
}

async function addPlaylistSchedule() {
    const folderPath = document.getElementById('folderSelect').value;
    const time = document.getElementById('playlistTimeInput').value;
    const duration = document.getElementById('playlistDuration').value;
    const maxTracks = document.getElementById('maxTracks').value;
    const trackInterval = document.getElementById('trackInterval').value;
    const shuffleMode = document.getElementById('shuffleMode').checked;
    
    if (!folderPath || !time) {
        const errorMsg = appTranslations.playlist?.select_folder_time_error || 'Please select a folder and time';
        showMessageModal('Error', errorMsg);
        return;
    }
    
    // Get selected days
    const dayCheckboxes = document.querySelectorAll('input[name="playlist_days"]:checked');
    const days = Array.from(dayCheckboxes).map(cb => parseInt(cb.value));
    
    if (days.length === 0) {
        const errorMsg = appTranslations.playlist?.select_days_error || 'Please select at least one day';
        showMessageModal('Error', errorMsg);
        return;
    }
    
    try {
        const response = await fetch('/add_playlist_schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                folder_path: folderPath,
                time: time,
                days: days,
                playlist_duration: duration ? parseInt(duration) : null,
                max_tracks: maxTracks ? parseInt(maxTracks) : null,
                track_interval: parseInt(trackInterval),
                shuffle_mode: shuffleMode
            })
        });
        
        const data = await response.json();
        if (data.success) {
            const successMsg = appTranslations.playlist?.add_success || 'Playlist schedule added successfully';
            showMessageModal('Success', successMsg);
            // Reset form
            document.getElementById('folderSelect').value = '';
            document.getElementById('playlistTimeInput').value = '';
            document.getElementById('playlistDuration').value = '';
            document.getElementById('maxTracks').value = '';
            document.getElementById('trackInterval').value = '10';
            document.getElementById('shuffleMode').checked = true;
            document.getElementById('folderPreview').classList.remove('show');
            
            // Clear day selections
            document.querySelectorAll('input[name="playlist_days"]').forEach(cb => cb.checked = false);
            
            // Reload playlist schedules
            loadPlaylistSchedules();
        } else {
            showMessageModal('Error', data.error || 'Failed to add playlist schedule');
        }
    } catch (error) {
        console.error('Error adding playlist schedule:', error);
        showMessageModal('Error', 'Failed to add playlist schedule');
    }
}

async function loadPlaylistSchedules() {
    try {
        const response = await fetch('/get_schedules');
        const schedules = await response.json();
        
        // Filter only playlist schedules
        const playlistSchedules = schedules.filter(s => s.schedule_type === 'playlist');
        
        const tbody = document.getElementById('playlistsList');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        playlistSchedules.forEach(schedule => {
            const row = document.createElement('tr');
            
            const folderName = schedule.folder_path ? schedule.folder_path.split('/').pop() : 'Unknown';
            const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            const daysText = schedule.days.map(d => appTranslations.days_list[dayKeys[d]] || dayKeys[d]).join(', ');
            
            // Create combined configuration text
            const durationText = schedule.playlist_duration ? `${schedule.playlist_duration} min` : (appTranslations.playlist?.unlimited || 'Unlimited');
            const tracksText = schedule.max_tracks ? `${schedule.max_tracks} tracks` : (appTranslations.playlist?.unlimited || 'Unlimited');
            const intervalText = schedule.track_interval ? `${schedule.track_interval}s` : 'No interval';
            const shuffleText = schedule.shuffle_mode ? (appTranslations.playlist?.shuffle_enabled || 'On') : (appTranslations.playlist?.shuffle_disabled || 'Off');
            
            const configurationText = `
                <div class="config-item"><strong>${appTranslations.playlist?.config_duration || 'Duration'}:</strong> ${durationText}</div>
                <div class="config-item"><strong>${appTranslations.playlist?.config_tracks || 'Max tracks'}:</strong> ${tracksText}</div>
                <div class="config-item"><strong>${appTranslations.playlist?.config_interval || 'Interval'}:</strong> ${intervalText}</div>
                <div class="config-item"><strong>${appTranslations.playlist?.config_shuffle || 'Shuffle'}:</strong> ${shuffleText}</div>
            `;
            
            const nextRun = schedule.next_run 
                ? new Date(schedule.next_run).toLocaleString(mapLangToLocale(currentLang))
                : (appTranslations.current_schedules?.not_scheduled || 'Not scheduled');
            
            const muteTitle = schedule.is_muted 
                ? (appTranslations.current_schedules?.unmute || 'Unmute')
                : (appTranslations.current_schedules?.mute || 'Mute');
            const deleteTitle = appTranslations.current_schedules?.delete || 'Delete';
            
            row.innerHTML = `
                <td>${folderName}</td>
                <td>${schedule.time}</td>
                <td>${daysText}</td>
                <td>${configurationText}</td>
                <td>${nextRun}</td>
                <td>
                    <button onclick="toggleMute(${schedule.id})" class="action-btn" title="${muteTitle}">
                        <i class="fas fa-volume-${schedule.is_muted ? 'mute' : 'up'}"></i>
                    </button>
                    <button onclick="showDeleteModal(${schedule.id})" class="action-btn delete" title="${deleteTitle}">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading playlist schedules:', error);
    }
}