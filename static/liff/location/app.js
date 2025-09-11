// LIFF Location Setting App
// AUTO_UPDATE_VERSION: 20250911-1445 (AI can update this timestamp when making changes - Converted comments to English with // format)
class LocationApp {
    constructor() {
        this.adminData = {};
        this.isInitialized = false;
        this.isLoadingAdminData = false;
        this.retryCount = 0;
        this.maxRetries = 2;

        // Move event binding forward: bind events regardless of login status
        this.setupEventListeners();
        this.init();
    }

    async init() {
        try {
            // Check if LIFF SDK is loaded
            if (typeof liff === 'undefined') {
                throw new Error('LIFF SDK not loaded');
            }

            // Initialize LIFF with real LIFF ID
            const liffId = '2007938807-GQzRrDoy';
            await liff.init({ liffId: liffId });

            // Use new separated login check and data loading
            await this.ensureAuth();
            await this.ensureData();
            this.populateCounties();

            // Start auto-resume mechanism (might be needed after overlay login)
            setTimeout(() => {
                if (!this.hasAdminData()) {
                    console.log('Data still empty after init, starting polling...');
                    this.tryResumeFlowWithPolling();
                }
            }, 500);

        } catch (error) {
            console.error('LIFF initialization failed:', error);

            // Provide more specific error messages based on error type
            let errorMessage = '初始化失敗，請重新整理頁面';
            if (error.message && error.message.includes('LIFF SDK not loaded')) {
                errorMessage = 'LIFF SDK 載入失敗，請檢查網路連線或重新整理頁面';
            } else if (error.message && error.message.includes('permission')) {
                errorMessage = '權限設定有誤，請聯繫客服';
            } else if (error.message && error.message.includes('network')) {
                errorMessage = '網路連線異常，請檢查網路後重試';
            }

            this.showMessage(errorMessage, 'error');
        }
    }

    // Unified error handling function
    // @param {Error} error - Error object
    // @param {string} defaultMessage - Default error message
    // @param {boolean} shouldRedirectLogin - Whether to redirect to login
    handleError(error, defaultMessage = '操作失敗，請重試', shouldRedirectLogin = false) {
        console.error('Error occurred:', error);

        if (shouldRedirectLogin) {
            this.showMessage('登入狀態已過期，請重新登入', 'error');
            setTimeout(() => {
                this.redirectToLogin();
            }, 2000);
            return;
        }

        const message = error.message || defaultMessage;
        this.showMessage(message, 'error');
    }

    // Check and get access token safely
    // @returns {string} accessToken
    // @throws {Error} When unable to get token
    getAccessTokenSafely() {
        try {
            const accessToken = liff.getAccessToken();
            if (!accessToken) {
                throw new Error('No Access Token available');
            }
            return accessToken;
        } catch (error) {
            throw new Error('登入狀態過期');
        }
    }

    // Redirect to login page using current page as return target
    redirectToLogin() {
        liff.login({ redirectUri: window.location.href });
    }

    // Helper function to create option elements
    // @param {string} value - option value
    // @param {string} text - option display text
    // @param {boolean} disabled - whether to disable
    // @param {string} className - CSS class name
    // @returns {HTMLOptionElement}
    createOption(value, text, disabled = false, className = '') {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = text;
        option.disabled = disabled;
        if (className) {
            option.className = className;
        }
        return option;
    }

    // Check if admin data exists
    hasAdminData() {
        return Object.keys(this.adminData).length > 0;
    }

    async ensureAuth() {
        if (!liff.isLoggedIn()) {
            // Force use redirectUri to ensure complete refresh
            this.redirectToLogin();
            return;
        }

        // Check if tokens are available
        try {
            const accessToken = liff.getAccessToken();
            if (!accessToken) {
                this.redirectToLogin();
                return;
            }
        } catch (error) {
            this.redirectToLogin();
            return;
        }
    }

    async ensureData() {
        // Idempotent design: return quickly if data already exists
        if (this.hasAdminData()) {
            return;
        }

        try {
            await this.loadAdminData();
        } catch (error) {
            // Re-throw exception for upper-level callers to handle UI prompts
            throw new Error('無法載入行政區資料: ' + error.message);
        }
    }

    async ensureDataLoaded() {
        // Prevent duplicate loading
        if (this.isLoadingAdminData) {
            return;
        }

        // Check if data is loaded, reload if not
        if (!this.hasAdminData()) {
            console.log('Admin data missing, reloading...');

            try {
                this.isLoadingAdminData = true;
                this.showCountyPlaceholder('(載入中...)');

                // Ensure login status first
                await this.ensureAuth();
                await this.ensureData();
                this.populateCounties();

                this.retryCount = 0; // Reset retry count
            } catch (error) {
                console.error('Failed to reload data:', error);
                this.retryCount++;

                if (this.retryCount >= this.maxRetries) {
                    this.showCountyPlaceholder('(請關閉後重新開啟或稍後再試)', false);
                } else {
                    this.showCountyPlaceholder('(載入失敗，點擊重試)', true);
                }
            } finally {
                this.isLoadingAdminData = false;
            }
        }
    }

    showCountyPlaceholder(text, clickable = false) {
        const countySelect = document.getElementById('county');

        // Remove previous placeholder
        const existingPlaceholder = countySelect.querySelector('.placeholder-option');
        if (existingPlaceholder) {
            existingPlaceholder.remove();
        }

        // Add new placeholder
        const placeholderOption = this.createOption('', text, !clickable, 'placeholder-option');

        if (clickable) {
            placeholderOption.style.cursor = 'pointer';
            // Note: option element click events are unreliable in some browsers
            // This is just styling, actual retry logic is handled in county change event
        }

        // Insert as first option
        countySelect.insertBefore(placeholderOption, countySelect.firstChild);
        countySelect.value = '';
    }

    async forceRecover() {
        if (this.isLoadingAdminData) {
            return; // Prevent duplicate execution
        }

        try {
            this.isLoadingAdminData = true;
            this.showCountyPlaceholder('(重新載入中...)');

            await this.ensureAuth();
            await this.ensureData();
            this.populateCounties();

            this.retryCount = 0;
        } catch (error) {
            console.error('Force recover failed:', error);
            this.retryCount++;

            if (this.retryCount >= this.maxRetries) {
                this.showCountyPlaceholder('(請關閉後重新開啟或稍後再試)', false);
            } else {
                this.showCountyPlaceholder('(載入失敗，點擊重試)', true);
            }
        } finally {
            this.isLoadingAdminData = false;
        }
    }

    async tryResumeFlowWithPolling(maxMs = 5000, stepMs = 300) {
        const startTime = Date.now();

        console.log('Starting overlay resume polling...');
        this.showCountyPlaceholder('(載入中...)');

        while (Date.now() - startTime < maxMs) {
            try {
                if (liff.isLoggedIn() && liff.getAccessToken()) {
                    console.log('Login state recovered, loading data...');
                    await this.ensureData();
                    this.populateCounties();
                    console.log('Overlay resume successful');
                    return true;
                }
            } catch (error) {
                // Ignore errors, continue polling or timeout handling
                console.log('Polling step failed, continuing...', error);
            }

            await new Promise(resolve => setTimeout(resolve, stepMs));
        }

        console.log('Overlay resume timeout');
        this.showCountyPlaceholder('(載入逾時，點擊重試)', true);
        return false;
    }

    async loadAdminData() {
        try {
            const response = await fetch('https://api.kyomind.tw/static/data/tw_admin_divisions.json');
            if (!response.ok) {
                throw new Error('Failed to load admin data');
            }
            const data = await response.json();

            // Basic validation of loaded data
            if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
                throw new Error('Invalid admin data format');
            }

            // Validate data structure
            for (const [county, districts] of Object.entries(data)) {
                if (!Array.isArray(districts) || districts.length === 0) {
                    throw new Error('Invalid admin data structure');
                }
            }

            this.adminData = data;
        } catch (error) {
            console.error('Failed to load administrative data:', error);
            // Throw exception for caller to decide how to handle UI
            throw error;
        }
    }

    populateCounties() {
        const countySelect = document.getElementById('county');

        // Clear existing options (including placeholder)
        countySelect.innerHTML = '<option value="">請選擇縣市</option>';

        const counties = Object.keys(this.adminData).sort((a, b) => a.localeCompare(b));

        counties.forEach(county => {
            const option = this.createOption(county, county);
            countySelect.appendChild(option);
        });
    }

    setupEventListeners() {
        // Prevent duplicate binding
        if (this.isInitialized) {
            return;
        }
        this.isInitialized = true;

        const countySelect = document.getElementById('county');
        const districtSelect = document.getElementById('district');
        const form = document.getElementById('locationForm');
        const cancelBtn = document.getElementById('cancelBtn');

        // County selection events
        countySelect.addEventListener('focus', async () => {
            // Ensure data is loaded when user clicks county dropdown
            await this.ensureDataLoaded();
        });

        countySelect.addEventListener('change', () => {
            // Check if retry option is selected
            if (countySelect.value === '' && countySelect.selectedOptions[0]?.textContent?.includes('重試')) {
                this.forceRecover();
                return;
            }

            this.updateDistricts();
            this.validateForm();
        });

        // District selection change
        districtSelect.addEventListener('change', () => {
            this.validateForm();
        });

        // Location type change
        document.querySelectorAll('input[name="locationType"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.validateForm();
            });
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });

        // Cancel button - reset form instead of closing
        cancelBtn.addEventListener('click', () => {
            this.resetForm();
        });
    }

    updateDistricts() {
        const countySelect = document.getElementById('county');
        const districtSelect = document.getElementById('district');
        const selectedCounty = countySelect.value;

        // Clear previous options
        districtSelect.innerHTML = '<option value="">請選擇行政區</option>';

        if (selectedCounty && this.adminData[selectedCounty]) {
            // Enable district select
            districtSelect.disabled = false;

            // Populate districts
            const districts = this.adminData[selectedCounty].sort((a, b) => a.localeCompare(b));
            districts.forEach(district => {
                const option = this.createOption(district, district);
                districtSelect.appendChild(option);
            });
        } else {
            // Disable district select
            districtSelect.disabled = true;
        }
    }

    resetForm() {
        // Reset location type to home
        document.querySelector('input[name="locationType"][value="home"]').checked = true;

        // Reset county selection
        document.getElementById('county').value = '';

        // Reset and disable district selection
        const districtSelect = document.getElementById('district');
        districtSelect.innerHTML = '<option value="">請先選擇縣市</option>';
        districtSelect.disabled = true;

        // Disable submit button
        document.getElementById('submitBtn').disabled = true;

        // Hide any messages
        document.getElementById('message').classList.add('hidden');
    }

    validateForm() {
        const locationType = document.querySelector('input[name="locationType"]:checked');
        const county = document.getElementById('county').value;
        const district = document.getElementById('district').value;
        const submitBtn = document.getElementById('submitBtn');

        const isValid = locationType && county && district;
        submitBtn.disabled = !isValid;
    }

    async submitForm() {
        try {
            // Show loading
            this.showLoading(true);

            // Get form data
            const locationType = document.querySelector('input[name="locationType"]:checked').value;
            const county = document.getElementById('county').value;
            const district = document.getElementById('district').value;

            // Validate input data against known valid values
            if (!['home', 'work'].includes(locationType)) {
                throw new Error('無效的地點類型');
            }

            if (!this.adminData[county]) {
                throw new Error('無效的縣市選擇');
            }

            if (!this.adminData[county].includes(district)) {
                throw new Error('無效的行政區選擇');
            }

            // Get Access Token (recommended for server API calls)
            let accessToken;
            try {
                accessToken = this.getAccessTokenSafely();
            } catch (error) {
                // Token might be expired, try to refresh by re-login
                this.showMessage('登入狀態過期，請重新登入...', 'info');
                this.redirectToLogin();
                return;
            }

            // Prepare payload
            const payload = {
                location_type: locationType,
                county: county,
                district: district
            };

            // Submit to backend
            const response = await fetch('https://api.kyomind.tw/users/locations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                // Handle token expiration specifically
                if (response.status === 401) {
                    this.handleError(new Error('登入狀態已過期'), '', true);
                    return;
                }

                // Don't expose detailed backend error messages to users
                if (response.status === 400) {
                    throw new Error('資料格式錯誤，請重新填寫');
                } else if (response.status === 500) {
                    throw new Error('伺服器暫時無法服務，請稍後再試');
                } else {
                    throw new Error('設定失敗，請重試');
                }
            }

            const result = await response.json();

            // Show success message
            this.showMessage(`✅ ${locationType === 'home' ? '住家' : '公司'}地點設定成功！\n你可以關閉本視窗，或繼續設定其他地點`, 'success');

        } catch (error) {
            this.handleError(error, '設定失敗，請重試');
        } finally {
            this.showLoading(false);
        }
    }

    showLoading(show) {
        const form = document.getElementById('locationForm');
        const loading = document.getElementById('loading');

        if (show) {
            form.classList.add('hidden');
            loading.classList.remove('hidden');
        } else {
            form.classList.remove('hidden');
            loading.classList.add('hidden');
        }
    }

    showMessage(text, type = 'info') {
        const messageEl = document.getElementById('message');
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
        messageEl.classList.remove('hidden');

        // Auto hide after 5 seconds for success and error messages, 3 seconds for info
        const hideDelay = type === 'success' || type === 'error' ? 5000 : 3000;
        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, hideDelay);
    }
}

// Wait for LIFF SDK to load before initializing app
function waitForLIFF() {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max wait

        const checkLIFF = () => {
            attempts++;
            if (typeof liff !== 'undefined') {
                resolve();
            } else if (attempts >= maxAttempts) {
                reject(new Error('LIFF SDK loading timeout'));
            } else {
                setTimeout(checkLIFF, 100);
            }
        };

        checkLIFF();
    });
}

// Initialize app when DOM and LIFF SDK are ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await waitForLIFF();
        const app = new LocationApp();
    } catch (error) {
        console.error('Failed to load LIFF SDK:', error);
        // Show error message directly
        const messageEl = document.getElementById('message');
        if (messageEl) {
            messageEl.textContent = 'LIFF SDK 載入失敗，請重新整理頁面';
            messageEl.className = 'message error';
            messageEl.classList.remove('hidden');
        }
    }
});
