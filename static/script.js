// Store uploaded files
let uploadedFiles = [];

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

function showDeleteModal(id) {
    pendingDeleteId = id;
    document.getElementById('deleteModal').style.display = 'flex';
}

function hideDeleteModal() {
    pendingDeleteId = null;
    document.getElementById('deleteModal').style.display = 'none';
}

async function confirmDelete() {
    if (!pendingDeleteId) return;
    try {
        const response = await fetch(`/delete_schedule/${pendingDeleteId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (data.success) {
            loadSchedules();
        } else {
            alert('Error deleting schedule');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error deleting schedule');
    }
    hideDeleteModal();
}

// Load current schedules
async function loadSchedules() {
    try {
        const response = await fetch('/get_schedules');
        const schedules = await response.json();
        
        const schedulesList = document.getElementById('schedulesList');
        schedulesList.innerHTML = '';
        schedules.forEach(schedule => {
            const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            const dayNames = schedule.days.map(d => appTranslations.days_list[dayKeys[d]]);
            const nextRun = schedule.next_run
                ? new Date(schedule.next_run).toLocaleString(currentLang === 'hu' ? 'hu-HU' : 'en-US')
                : appTranslations.current_schedules.not_scheduled || 'Not scheduled';
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${schedule.filename}</td>
                <td>${schedule.time}</td>
                <td>${dayNames.join(', ')}</td>
                <td>${nextRun}</td>
                <td>
                    <button class="action-btn delete" title="Delete" onclick="showDeleteModal(${schedule.id})">
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
    loadSchedules();
});

// Load schedules when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadSchedules();
});