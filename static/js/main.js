const apiKey = 'bdash-X_KzUaBBMlM8d5a5xbAav4Z6bYqS3rnBN94ugjtkhsI';
let currentData = {};

function loadMenuContent() {
    const serverId = new URLSearchParams(window.location.search).get('server');
    if (!serverId) {
        document.getElementById('menu-bar').style.display = 'none';
        return;
    }

    const menuData = JSON.parse(document.getElementById('menu-data').textContent);
    const menuBar = document.getElementById('menu-bar');
    menuBar.innerHTML = '';

    menuData.menu_items.forEach(item => {
        const a = document.createElement('a');
        a.href = '#';
        a.textContent = item.name;
        a.className = 'menu-item';
        a.dataset.loadEndpoint = item.endpoints.load.replace('{guild_id}', serverId);
        a.dataset.saveEndpoint = item.endpoints.save.replace('{guild_id}', serverId);

        a.addEventListener('click', event => {
            event.preventDefault();
            loadApiData(a.dataset.loadEndpoint);
            document.getElementById('server-details').style.display = 'none';
            localStorage.setItem('currentSaveEndpoint', a.dataset.saveEndpoint);
            localStorage.setItem('currentLoadEndpoint', a.dataset.loadEndpoint);
            document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('selected'));
            a.classList.add('selected');
        });

        menuBar.appendChild(a);
    });

    menuBar.style.display = 'flex';
}

function replaceValue(data, targetValue, replacementValue) {
    if (data === targetValue) {
        return replacementValue;
    }
    if (Array.isArray(data)) {
        return data.map(item => replaceValue(item, targetValue, replacementValue));
    }
    if (typeof data === 'object' && data !== null) {
        return Object.fromEntries(
            Object.entries(data).map(([key, value]) => [key, replaceValue(value, targetValue, replacementValue)])
        );
    }
    return data;
}

async function loadApiData(endpoint) {
    try {
        const response = await fetch(endpoint, {
            headers: {
                'Authorization': apiKey
            }
        });
        if (!response.ok) throw new Error('Network response was not ok');
        const dataraw = await response.json();
        const data = replaceValue(dataraw, null, "null");
        console.log('API Response:', data);

        currentData = data;

        const toggleSwitch = document.getElementById('toggle-switch');
        const toggleSwitchInput = toggleSwitch.querySelector('input');
        let showToggle = false;

        Object.keys(data).forEach(key => {
            if (key.includes('-switch')) {
                showToggle = true;
                const isChecked = data[key] === 1;
                toggleSwitchInput.checked = isChecked;
                console.log(`Toggle-Switch gefunden: ${key} = ${data[key]} (${isChecked ? 'Aktiviert' : 'Deaktiviert'})`);
            }
        });

        toggleSwitch.style.display = showToggle ? 'block' : 'none';

        const textOutput = document.getElementById('text-output');
        textOutput.innerHTML = '';

        Object.keys(data).forEach(key => {
            if (key.includes('-input')) {
                console.log(`Verarbeite Input-Key: ${key}`);
                const input = document.createElement('input');
                input.name = key;
                input.type = 'text';
                input.placeholder = data[key] === "null" ? 'Enter text...' : data[key];
                input.value = data[key] === "null" ? '' : data[key];
                input.style.display = 'block';
                input.style.marginBottom = '10px';
                textOutput.appendChild(input);
            }
        });

        Object.keys(data).forEach(key => {
            if (typeof data[key] === 'string' &&
                /\.(png|gif|jpg|jpeg)$/.test(data[key]) ||
                data[key].startsWith('https://placehold.co/')) {

                console.log(`Verarbeite Bilddatei: ${key}`);
                const img = document.createElement('img');
                img.src = data[key];
                img.alt = key;
                img.style.maxWidth = '100%';
                img.style.height = 'auto';
                
                img.onload = () => textOutput.appendChild(img);
                img.onerror = () => {
                    console.error(`Bild konnte nicht geladen werden: ${data[key]}`);
                    img.src = 'https://placehold.co/400x200?text=Bild+Konnte+nicht+geladen+werden';
                    img.alt = 'Bild konnte nicht geladen werden';
                    textOutput.appendChild(img);
                };
            }
        });

        const activeDropsMap = {};

        Object.keys(data).forEach(key => {
            if (key.includes('-activedrop')) {
                console.log(`Verarbeite aktiven Drop-Key: ${key}`);
                const activeDropEntries = data[key];
                Object.entries(activeDropEntries).forEach(([subKey, subValue]) => {
                    activeDropsMap[subKey] = subValue;
                    console.log(`Aktiver Drop gefunden: ${subKey} = ${subValue} (aus ${key})`);
                });
            }
        });

        Object.keys(data).forEach(key => {
            if (key.includes('-drop')) {
                console.log(`Verarbeite Drop-Key: ${key}`);
                const dropdown = document.createElement('select');
                dropdown.name = key;
                const dropEntries = data[key];
                let selectedOptionFound = false;

                Object.entries(dropEntries).forEach(([subKey, subValue]) => {
                    console.log(`Überprüfe Option: ${subKey} = ${subValue}`);
                    const option = document.createElement('option');
                    option.value = subKey;
                    option.textContent = subValue.endsWith('-show') ? subValue.replace('-show', '') : subValue;
                    
                    if (subValue.includes("Please select")) {
                        option.selected = true;
                        selectedOptionFound = true;
                        console.log(`Option "${subValue}" (${subKey}) ist ausgewählt, weil es "Please select" enthält.`);
                    } else if (activeDropsMap.hasOwnProperty(subKey) && !selectedOptionFound) {
                        option.selected = true;
                        selectedOptionFound = true;
                        console.log(`Option "${subValue}" (${subKey}) ist aktiv und wird ausgewählt.`);
                    } else {
                        console.log(`Option "${subValue}" (${subKey}) ist nicht aktiv.`);
                    }
                    dropdown.appendChild(option);
                });

                if (!selectedOptionFound) {
                    console.log(`Keine aktive Option für Drop-Key "${key}" gefunden.`);
                }
                textOutput.appendChild(dropdown);
            }

            if (key.includes('-table')) {
                console.log(`Verarbeite Table-Key: ${key}`);
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.style.marginTop = '20px';
                table.style.marginBottom = '20px';
                const tbody = document.createElement('tbody');

                Object.entries(data[key]).forEach(([id, value]) => {
                    const row = document.createElement('tr');
                    const idCell = document.createElement('td');
                    idCell.textContent = id;
                    idCell.style.border = '1px solid #ddd';
                    idCell.style.padding = '8px';
                    row.appendChild(idCell);
                    
                    const valueCell = document.createElement('td');
                    valueCell.textContent = value;
                    valueCell.style.border = '1px solid #ddd';
                    valueCell.style.padding = '8px';
                    row.appendChild(valueCell);
                    
                    tbody.appendChild(row);
                });

                table.appendChild(tbody);
                textOutput.appendChild(table);
            }

            if (key.includes('-text')) {
                console.log(`Verarbeite Text-Key: ${key}`);
                const p = document.createElement('p');
                p.innerHTML = `${key}: ${formatValue(data[key])}`;
                textOutput.appendChild(p);
            }
        });

        document.getElementById('save-button').style.display = 'block';
    } catch (error) {
        console.error('Error fetching content:', error);
    }
}

function showNotification(msgType, msgContent) {
    const notificationCard = document.getElementById("notification-card");
    const messageText = document.getElementById("message-text");
    const subText = document.getElementById("sub-text");
    const iconContainer = document.getElementById("icon-container");
    const icon = document.getElementById("icon");
    const wave = document.getElementById("wave");

    notificationCard.className = `card ${msgType}`;
    iconContainer.className = `icon-container ${msgType}`;
    icon.className = `icon fas`;

    switch (msgType) {
        case 'notify-info':
            icon.classList.add('fa-info-circle', 'icon-info');
            wave.style.fill = '#007bff';
            break;
        case 'notify-success':
            icon.classList.add('fa-check-circle', 'icon-success');
            wave.style.fill = '#28a745';
            break;
        case 'notify-warn':
            icon.classList.add('fa-exclamation-triangle', 'icon-warn');
            wave.style.fill = '#ffc107';
            break;
        case 'notify-error':
            icon.classList.add('fa-times-circle', 'icon-error');
            wave.style.fill = '#dc3545';
            break;
    }

    messageText.textContent = msgContent;
    subText.textContent = "";
    notificationCard.style.display = 'flex';
}

function closeNotification() {
    const notificationCard = document.getElementById("notification-card");
    notificationCard.style.display = 'none';
}

function saveChanges() {
    const updatedData = {};
    const toggleSwitchInput = document.querySelector('#toggle-switch input');
    updatedData.active = toggleSwitchInput.checked ? 1 : 0;

    document.querySelectorAll('select').forEach(dropdown => {
        const selectedOption = dropdown.options[dropdown.selectedIndex];
        const originalKey = dropdown.name;
        if (currentData[originalKey]) {
            updatedData[originalKey] = selectedOption.value;
        }
    });

    document.querySelectorAll('input').forEach(input => {
        const originalKey = input.name;
        let value;
        if (input.type === 'checkbox') {
            value = input.checked ? 1 : 0;
        } else if (input.type === 'radio' && !input.checked) {
            return;
        } else {
            value = input.value;
        }
        if (currentData[originalKey]) {
            updatedData[originalKey] = value;
        }
    });

    const senddata = removeSendFromObject(updatedData);
    const saveEndpoint = localStorage.getItem('currentSaveEndpoint');
    if (!saveEndpoint) {
        console.error('Error: No save endpoint found in localStorage.');
        return;
    }

    console.log(senddata);
    fetch(saveEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': apiKey
        },
        body: JSON.stringify(senddata)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const apiEndpoint = localStorage.getItem("currentLoadEndpoint");
            console.log('Save successful:', data);
            loadApiData(apiEndpoint);
            const entries = Object.entries(data);
            if (entries.length > 0) {
                const [key, value] = entries[0];
                showNotification(key, value);
            }
        })
        .catch(error => {
            console.error('Error saving data:', error);
            showNotification('notify-error', 'Fehler beim Speichern: ' + error.message);
        });
}

function removeSendFromObject(obj) {
    if (typeof obj === 'string') {
        return obj.replace("-send", "");
    }
    if (Array.isArray(obj)) {
        return obj.map(removeSendFromObject);
    }
    if (typeof obj === 'object' && obj !== null) {
        return Object.fromEntries(
            Object.entries(obj).map(([key, value]) => [key, removeSendFromObject(value)])
        );
    }
    return obj;
}

function formatValue(value) {
    if (typeof value === 'object' && value !== null) {
        return Object.entries(value).map(([k, v]) => `${k}: ${v}`).join(', ');
    }
    return value;
}

function loadServerDetails(serverId) {
    history.pushState(null, '', '?server=' + serverId);

    const serverDetails = JSON.parse('{{ guild_details | tojson | safe }}').find(guild => guild.id === serverId);
    if (serverDetails) {
        const detailsHtml = `
            <div class="server-header">
                <img src="${serverDetails.icon_url}" alt="${serverDetails.name}" style="width: 80px; height: 80px; border-radius: 50%; margin-right: 20px;">
                <h2>${serverDetails.name}</h2>
            </div>
            <p>ID: ${serverDetails.id}</p>
            <p>Members: ${serverDetails.member_count}</p>
            <p>Owner: ${serverDetails.owner_username}</p>
            <p>Region: ${serverDetails.region}</p>
            <p>Description: ${serverDetails.description}</p>
            <p>Verification Level: ${serverDetails.verification_level}</p>
        `;
        document.getElementById('server-details').innerHTML = detailsHtml;
        document.getElementById('server-details').style.display = 'block';
        document.getElementById('content-area').innerHTML = `
            <label id="toggle-switch" class="switch" style="display: none;">
                <input type="checkbox" id="toggle-input">
                <span class="slider"></span>
            </label>
            <div id="text-output" class="text-output"></div>
            <button id="save-button" style="display: none;" onclick="saveChanges()">Save</button>
        `;
        loadMenuContent();
    }
}

window.onload = function () {
    const urlParams = new URLSearchParams(window.location.search);
    const serverId = urlParams.get('server');
    if (serverId) {
        loadServerDetails(serverId);
    }
}

function start_updater() {
    const imageInput = document.querySelector('input[name="image-input"]');
    if (imageInput) {
        imageInput.addEventListener('input', function () {
            localStorage.setItem("Image-Link", this.value);
            updateImage();
        });
    }
}

function updateImage() {
    const imgElement = document.querySelector('img[alt="image-input"]');
    const linkraw = localStorage.getItem("Image-Link");
    const linkExtension = linkraw.split('.').pop().split('?')[0];
    const validExtensions = ["png", "gif", "jpg", "jpeg", "webp", "placehold"];
    const isValidLink = validExtensions.includes(linkExtension);
    const link = isValidLink ? linkraw : "https://placehold.co/200x100?text=Sorry but your url does not work";

    if (imgElement) {
        imgElement.src = link;
    }
}
