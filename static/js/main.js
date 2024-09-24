async function saveModuleData(saveApiEndpoint) {
    const moduleData = document.getElementById('module-data');
    const updatedData = {};
    moduleData.querySelectorAll('input, select').forEach(element => {
        const key = element.id;
        if (element.type === 'checkbox') {
            updatedData[key] = element.checked ? 1 : 0;
        } else if (element.tagName.toLowerCase() === 'select') {
            const activeDropKey = `${key.replace('-drop', '')}-activedrop`;
            updatedData[activeDropKey] = { [element.value]: element.options[element.selectedIndex].text };
        } else {
            updatedData[key] = element.value;
        }
    });
    const allModuleData = JSON.parse(moduleData.getAttribute('data-full-json') || '{}');
    for (const [key, value] of Object.entries(allModuleData)) {
        if (!updatedData.hasOwnProperty(key)) {
            updatedData[key] = value;
        }
    }

    try {
        const response = await fetch('/api/module-save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                apiEndpoint: saveApiEndpoint,
                guildId: guildId,
                data: updatedData
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        showNotification('notify-success', 'Changes saved successfully');
        console.log(updatedData)
    } catch (error) {
        console.error('Error:', error);
        showNotification('notify-error', `Failed to save changes: ${error.message}`);
    }
}

function filterModules() {
    const searchBar = document.querySelector('.search-bar');
    const query = searchBar.value.toLowerCase();
    const modules = document.querySelectorAll('.module');

    modules.forEach(module => {
        const title = module.querySelector('.module-title').textContent.toLowerCase();
        if (title.includes(query)) {
            module.style.display = '';
        } else {
            module.style.display = 'none';
        }
    });
}
document.querySelector('.search-bar').addEventListener('input', filterModules);

function handleGuildClick(name, id, ownerUsername, memberCount, url) {
    showServer(name);
    guildid(id);
    owner(ownerUsername);
    members(memberCount);
    const serverIconDiv = document.querySelector('.server-icon');
    serverIconDiv.style.backgroundImage = url;
}

let guildId = '';
let Ownerusername = '';
let Servermembercount = '';
var test = 'teststartvar';

function owner(username) {
    Ownerusername = username
    document.getElementById('serverownername').textContent = "Owner: " + Ownerusername
}

function members(count) {
    Servermembercount = count
}

function guildid(id) {
    guildId = id
    test = id
}

const modules = [
    { title: "Anti Raid", description: "Protect your server by automatically blocking users and bots if it resembles a raid.", enabled: true, apiEndpoint: "settings/load/anti_raid", saveApiEndpoint: "anti_raid" },
    { title: "Minigame guessing", description: "The mini-game where you have to guess a number alone or as a team.", enabled: true, apiEndpoint: "settings/load/mgg", saveApiEndpoint: "mgg" },
    { title: "Counting game", description: "The mini-game in which you have to count as far as possible as a team without making a mistake.", enabled: true, apiEndpoint: "settings/load/mgc", saveApiEndpoint: "mgc" },
    { title: "Global chat", description: "Chat with users from many different communities.", enabled: true, apiEndpoint: "settings/load/gc", saveApiEndpoint: "gc" },
    { title: "Welcome system", description: "Automatically welcome new users to your server.", enabled: true, apiEndpoint: "settings/load/welc", saveApiEndpoint: "welc" },
    { title: "Verify system", description: "Secure your server with the Verify System to keep bot / automated accounts away.", enabled: true, apiEndpoint: "settings/load/verify", saveApiEndpoint: "verify" },
    { title: "Suggestion system", description: "Let the community vote on user suggestions quickly and easily.", enabled: true, apiEndpoint: "settings/load/sugg", saveApiEndpoint: "sugg" },
    { title: "Ticket system", description: "Manage your communitys support requests easier than ever before.", enabled: true, apiEndpoint: "settings/load/ticket", saveApiEndpoint: "ticket" },
    { title: "Log system", description: "Document all the things on your server that cannot be found in the audit log.", enabled: true, apiEndpoint: "settings/load/log", saveApiEndpoint: "log" },
    { title: "Security system", description: "Protect your channels with our smart chat filter and automatically remove inappropriate content.", enabled: true, apiEndpoint: "settings/load/sec", saveApiEndpoint: "sec" },
    { title: "Auto Role", description: "Let users automatically add roles as soon as they join your server.", enabled: true, apiEndpoint: "settings/load/auto_roles", saveApiEndpoint: "auto_roles" },
];

const container = document.getElementById('modules-container');
const startPage = document.getElementById('start-page');
const serverContent = document.getElementById('server-content');
const modulePage = document.getElementById('module-page');
const serverNameElement = document.getElementById('server-name');
const modulePageTitle = document.getElementById('module-page-title');
const modulePageDescription = document.getElementById('module-page-description');

let currentServer = '';
function showStartPage() {
    startPage.classList.remove('hidden');
    serverContent.classList.add('hidden');
    modulePage.classList.add('hidden');
}

function showServer(serverName) {
    currentServer = serverName;
    startPage.classList.add('hidden');
    serverContent.classList.remove('hidden');
    modulePage.classList.add('hidden');
    serverNameElement.textContent = serverName;

    container.innerHTML = '';

    modules.forEach(module => {
        const moduleElement = document.createElement('div');
        moduleElement.className = 'module';
        moduleElement.innerHTML = `
    <div class="module-header">
        <h3 class="module-title">${module.title}</h3>
        <div class="status-indicator ${module.enabled ? 'status-enabled' : 'status-disabled'}"></div>
    </div>
    <p class="module-description">${module.description}</p>
    <button class="manage-button" onclick="showModulePage('${module.title}', '${module.description}', '${module.apiEndpoint}', '${module.saveApiEndpoint}')">Manage</button>
`;
        container.appendChild(moduleElement);
    });
}

async function showModulePage(title, description, apiEndpoint, saveApiEndpoint) {
    startPage.classList.add('hidden');
    serverContent.classList.add('hidden');
    modulePage.classList.remove('hidden');
    modulePageTitle.textContent = title;
    modulePageDescription.textContent = description;

    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');
    const moduleData = document.getElementById('module-data');

    loader.classList.remove('hidden');
    errorMessage.classList.add('hidden');
    moduleData.innerHTML = '';

    try {
        const response = await fetch(`/api/module-data?apiEndpoint=${encodeURIComponent(apiEndpoint)}&guildId=${encodeURIComponent(guildId)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(data);

        let htmlContent = '<div class="json-card">';
        for (const [key, value] of Object.entries(data)) {
            if (!key.endsWith('-activedrop') && !key.endsWith('-label')) {
                htmlContent += renderField(key, value, data);
            }
        }
        htmlContent += '</div>';
        moduleData.innerHTML = htmlContent;

        moduleData.setAttribute('data-full-json', JSON.stringify(data));
        for (const [key, value] of Object.entries(data)) {
            if (key.endsWith('-drop')) {
                const activeDropKey = `${key.replace('-drop', '')}-activedrop`;
                if (data[activeDropKey]) {
                    const activeValue = Object.keys(data[activeDropKey])[0];
                    const select = document.querySelector(`select[onchange*="${key}"]`);
                    if (select) {
                        select.value = activeValue;
                    }
                }
            }
        }
        moduleData.innerHTML += `<button onclick="saveModuleData('${saveApiEndpoint}')" class="sbutton">
<div class="svg-wrapper-1">
<div class="svg-wrapper">
<svg
xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 24 24"
width="30"
height="30"
class="icon"
>
<path
  d="M22,15.04C22,17.23 20.24,19 18.07,19H5.93C3.76,19 2,17.23 2,15.04C2,13.07 3.43,11.44 5.31,11.14C5.28,11 5.27,10.86 5.27,10.71C5.27,9.33 6.38,8.2 7.76,8.2C8.37,8.2 8.94,8.43 9.37,8.8C10.14,7.05 11.13,5.44 13.91,5.44C17.28,5.44 18.87,8.06 18.87,10.83C18.87,10.94 18.87,11.06 18.86,11.17C20.65,11.54 22,13.13 22,15.04Z"
></path>
</svg>
</div>
</div>
<span>Save</span>
</button>`;

        const notifyKey = Object.keys(data).find(key => key.startsWith('notify-'));
        if (notifyKey) {
            showNotification(notifyKey, data[notifyKey]);
        }
    } catch (error) {
        console.error('Error:', error);
        errorMessage.textContent = `Failed to load module data: ${error.message}`;
        errorMessage.classList.remove('hidden');
    } finally {
        loader.classList.add('hidden');
    }
}

function renderField(key, value, data) {
    let labelHtml = '';
    const baseKey = key.replace(/-(?:switch|drop|input|image-input|table)$/, '');
    const associatedLabelKey = `${baseKey}-label`;

    if (data[associatedLabelKey]) {
        labelHtml = `<h2 class="render-field-label">${data[associatedLabelKey]}</h2>`;
    }
    if (key.endsWith('-switch')) {
        return `
<div class="render-field-container">
${labelHtml}
<label class="custom-switch" style="display: flex; align-items: center;">
<input type="checkbox" id="${key}" class="custom-switch-input" ${value === 1 ? 'checked' : ''} onchange="handleSwitchChange('${key}', this.checked)">
<span class="slider"></span>
</label>
</div>`;
    } else if (key.endsWith('-drop')) {
        const activeDropKey = `${baseKey}-activedrop`;
        const activeValue = data[activeDropKey] ? Object.keys(data[activeDropKey])[0] : null;
        let options = Object.entries(value).map(([id, label]) => {
            const isSelected = id === activeValue || (label.toLowerCase().includes('please select') && !activeValue);
            return `<option value="${id}" ${isSelected ? 'selected' : ''}>${label}</option>`;
        }).join('');
        return `
<div class="render-field-container">
${labelHtml}
<select id="${key}" class="render-field-select" style="width: 100%; padding: 10px; border: 1px solid #ccc;" onchange="handleDropChange('${key}', this.value)">
  ${options}
</select>
</div>`;
    } else if (key.endsWith('-input')) {
        return `
<div class="render-field-container">
${labelHtml}
<input type="text" id="${key}" class="render-field-input" value="${value}" style="width: 100%; padding: 10px; border: 1px solid #ccc;" onchange="handleInputChange('${key}', this.value)">
</div>`;
    } else if (key.startsWith('image-')) {
        console.log("Image  Found!")
    } else if (key.endsWith('-table')) {
        console.log("No Image Found!")
        if (Array.isArray(value) && value.length > 0) {
            const headers = Object.keys(value[0]);
            let tableHtml = `
<table class="render-field-table" border="1" style="width: 100%; border-collapse: collapse;">
  <thead>
    <tr>${headers.map(header => `<th>${header}</th>`).join('')}</tr>
  </thead>
  <tbody>
    ${value.map(row => `
      <tr>${headers.map(header => `<td>${row[header]}</td>`).join('')}</tr>
    `).join('')}
  </tbody>
</table>
`;
            return `
<div class="render-field-container">
${labelHtml}
${tableHtml}
</div>`;
        } else if (typeof value === 'object' && Object.keys(value).length > 0) {
            let tableHtml = `
<table class="render-field-table" border="1" style="width: 100%; border-collapse: collapse;">
  <thead>
    <tr><th>Key</th><th>Value</th></tr>
  </thead>
  <tbody>
    ${Object.entries(value).map(([k, v]) => `
      <tr><td>${k}</td><td>${v}</td></tr>
    `).join('')}
  </tbody>
</table>
`;
            return `
<div class="render-field-container">
${labelHtml}
${tableHtml}
</div>`;
        } else {
            return '';
        }
    } else {
        return `
<div class="render-field-container">
${labelHtml}
<p style="margin-bottom: 20px;">${JSON.stringify(value)}</p>
</div>`;
    }
}
function isValidImageUrl(url) {
    return url.match(/\.(jpeg|jpg|gif|png)$/) != null;
}
function handleSwitchChange(key, isChecked) {
    console.log(`Switch ${key} changed to ${isChecked}`);
}
function handleDropChange(key, selectedValue) {
    console.log(`Dropdown ${key} changed to ${selectedValue}`);
}
function handleInputChange(key, value) {
    console.log(`Input ${key} changed to ${value}`);
}
function handleImageInputChange(key, value) {
    console.log(`Image input ${key} changed to ${value}`);
    const previewElement = document.getElementById(`${key}-preview`);
    previewElement.src = isValidImageUrl(value) ? value : 'https://placehold.co/400x200?text=Image Not valid';
}
function isValidImageUrl(url) {
    return url.match(/\.(jpeg|jpg|gif|png)$/) != null;
}

function showNotification(type, message) {
    const notificationElement = document.getElementById('notification');
    notificationElement.className = type;
    notificationElement.textContent = message;
    notificationElement.classList.add('show');
    setTimeout(() => {
        notificationElement.classList.remove('show');
    }, 5000);
}