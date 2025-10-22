// Store uploaded files
let uploadedFiles = [];
let activeListId = null;
let currentSchedules = [];

// Load schedule lists
async function loadScheduleLists() {
    try {
        const response = await fetch('/schedule_lists');
        const lists = await response.json();
        
        const tabsContainer = document.getElementById('scheduleListTabs');
        if (!tabsContainer) return;
        
        tabsContainer.innerHTML = '';
        
        lists.forEach(list => {
            const tab = document.createElement('div');
            tab.className = `tab ${list.is_active ? 'active' : ''}`;
            tab.onclick = () => activateList(list.id);
            
            if (list.is_active) {
                activeListId = list.id;
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
            loadScheduleLists();
            loadSchedules();
        }
    } catch (error) {
        console.error('Error activating list:', error);
        showMessageModal('Error', 'Failed to activate list');
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
    const select = document.getElementById('selectedFile');
    select.innerHTML = '';
    
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
    const selectedFile = document.getElementById('selectedFile').value;
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
        }
        audioPlayer.src = `/audio/${selectedFile}`;
        audioPlayer.play()
            .then(() => {
                playButton.innerHTML = '<i class="fas fa-stop"></i>';
                playButton.title = 'Stop';
            })
            .catch((error) => {
                showMessageModal('Error', 'Failed to play audio file');
                console.error('Error playing audio:', error);
            });
    }
}

// Add new schedule
async function addSchedule() {
    const filename = document.getElementById('selectedFile').value;
    const time = document.getElementById('scheduleTime').value;
    const dayCheckboxes = document.querySelectorAll('.days-checkboxes input[type="checkbox"]');
    
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
    try {
        const response = await fetch('/get_schedules');
        const schedules = await response.json();
        currentSchedules = schedules;
        
        const schedulesList = document.getElementById('schedulesList');
        schedulesList.innerHTML = '';
        schedules.forEach(schedule => {
            const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            const dayNames = schedule.days.map(d => appTranslations.days_list[dayKeys[d]]);
            const nextRun = schedule.next_run
                ? new Date(schedule.next_run).toLocaleString(currentLang === 'hu' ? 'hu-HU' : 'en-US')
                : appTranslations.current_schedules.not_scheduled || 'Not scheduled';
            
            const muteButtonTitle = schedule.is_muted 
                ? (appTranslations.current_schedules.unmute || 'Unmute')
                : (appTranslations.current_schedules.mute || 'Mute');
            const muteButtonIcon = schedule.is_muted ? 'fa-volume-up' : 'fa-volume-mute';
            const muteButtonClass = schedule.is_muted ? 'unmute' : 'mute';
            const rowClass = schedule.is_muted ? 'muted' : '';
            
            const row = document.createElement('tr');
            row.className = rowClass;
            row.innerHTML = `
                <td>${schedule.filename}</td>
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
            method: 'GET'
        });
        const data = await response.json();
        if (data.success) {
            window.location.reload();
        }
    } catch (error) {
        console.error('Error changing language:', error);
    }
}

// Modal event listeners
window.addEventListener('DOMContentLoaded', () => {
    document.getElementById('confirmDeleteBtn').onclick = confirmDelete;
    document.getElementById('cancelDeleteBtn').onclick = hideDeleteModal;
    document.getElementById('closeMessageModalBtn').onclick = hideMessageModal;
    const confirmEditBtn = document.getElementById('confirmEditBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    if (confirmEditBtn) confirmEditBtn.onclick = confirmEdit;
    if (cancelEditBtn) cancelEditBtn.onclick = hideEditModal;
    startRealtimeClock();
    loadScheduleLists();
    loadSchedules();
});

// Load schedules when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadScheduleLists();
    loadSchedules();
});

// Realtime clock updater
function startRealtimeClock() {
    const el = document.getElementById('realtimeClock');
    if (!el) return;
    const update = () => {
        try {
            const now = new Date();
            const locale = (typeof currentLang === 'string' && currentLang === 'hu') ? 'hu-HU' : 'en-US';
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