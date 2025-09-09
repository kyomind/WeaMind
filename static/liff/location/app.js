// LIFF Location Setting App
// AUTO_UPDATE_VERSION: 20250909-2334 (AI can update this timestamp when making changes)
class LocationApp {
    constructor() {
        this.adminData = {};
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

            if (!liff.isLoggedIn()) {
                liff.login();
                return;
            }

            // Check if tokens are available
            try {
                const accessToken = liff.getAccessToken();

                if (!accessToken) {
                    liff.login();
                    return;
                }
            } catch (error) {
                liff.login();
                return;
            }

            // 載入並初始化頁面
            await this.loadAdminData();
            this.setupEventListeners();
            this.populateCounties();
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

    async loadAdminData() {
        try {
            const response = await fetch('https://api.kyomind.tw/static/data/tw_admin_divisions.json');
            if (!response.ok) {
                throw new Error('Failed to load admin data');
            }
            this.adminData = await response.json();
        } catch (error) {
            console.error('Failed to load administrative data:', error);
            this.showMessage('載入地區資料失敗', 'error');
        }
    }

    populateCounties() {
        const countySelect = document.getElementById('county');
        const counties = Object.keys(this.adminData).sort((a, b) => a.localeCompare(b));

        counties.forEach(county => {
            const option = document.createElement('option');
            option.value = county;
            option.textContent = county;
            countySelect.appendChild(option);
        });
    }

    setupEventListeners() {
        const countySelect = document.getElementById('county');
        const districtSelect = document.getElementById('district');
        const form = document.getElementById('locationForm');
        const cancelBtn = document.getElementById('cancelBtn');

        // County selection change
        countySelect.addEventListener('change', () => {
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

        // Cancel button
        cancelBtn.addEventListener('click', () => {
            this.closeApp();
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
                const option = document.createElement('option');
                option.value = district;
                option.textContent = district;
                districtSelect.appendChild(option);
            });
        } else {
            // Disable district select
            districtSelect.disabled = true;
        }
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

            // Get Access Token (recommended for server API calls)
            let accessToken;
            try {
                accessToken = liff.getAccessToken();
                if (!accessToken) {
                    throw new Error('No Access Token available');
                }
            } catch (error) {
                // Token might be expired, try to refresh by re-login
                this.showMessage('登入狀態過期，請重新登入...', 'info');
                liff.login();
                return;
            }            // Prepare payload
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
                    try {
                        const errorData = await response.json();
                        this.showMessage(`登入狀態已過期：${errorData.detail}`, 'error');
                    } catch (e) {
                        this.showMessage('登入狀態已過期，請重新登入', 'error');
                    }
                    setTimeout(() => {
                        liff.login();
                    }, 2000);
                    return;
                }

                const errorData = await response.json();
                throw new Error(errorData.detail || '設定失敗');
            }

            const result = await response.json();

            // Show success message
            this.showMessage(`${locationType === 'home' ? '住家' : '公司'}地點設定成功！`, 'success');

            // Close LIFF after delay
            setTimeout(() => {
                this.closeApp();
            }, 2000);

        } catch (error) {
            this.showMessage(error.message || '設定失敗，請重試', 'error');
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

        // Auto hide after 5 seconds for error messages, 3 seconds for others
        const hideDelay = type === 'error' ? 5000 : 3000;
        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, hideDelay);
    }

    closeApp() {
        liff.closeWindow();
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
