// LIFF Location Setting App
class LocationApp {
    constructor() {
        this.adminData = {};
        this.init();
    }

    async init() {
        try {
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
                const idToken = liff.getIDToken();

                console.log('Initial token check:', {
                    hasAccessToken: !!accessToken,
                    hasIdToken: !!idToken,
                    accessTokenLength: accessToken ? accessToken.length : 0
                });

                if (!accessToken) {
                    console.log('No Access Token available, redirecting to login');
                    liff.login();
                    return;
                }
            } catch (error) {
                console.log('Token error, redirecting to login:', error);
                liff.login();
                return;
            }            // 載入並初始化頁面
            await this.loadAdminData();
            this.setupEventListeners();
            this.populateCounties();
        } catch (error) {
            console.error('LIFF initialization failed:', error);
            this.showMessage('初始化失敗，請重新整理頁面', 'error');
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
        const counties = Object.keys(this.adminData).sort();

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
            const districts = this.adminData[selectedCounty].sort();
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

                // Log token info for debugging (first 20 chars only for security)
                console.log('Access Token obtained:', accessToken.substring(0, 20) + '...');

            } catch (error) {
                // Token might be expired, try to refresh by re-login
                console.log('Access Token issue, attempting re-login:', error);
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
                // Log error details for debugging
                console.error('API request failed:', {
                    status: response.status,
                    statusText: response.statusText,
                    url: response.url
                });

                // Handle token expiration specifically
                if (response.status === 401) {
                    try {
                        const errorData = await response.json();
                        console.error('401 Error details:', errorData);
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

            // Send confirmation message to LINE chat
            await this.sendConfirmationMessage(locationType, county, district);

            // Close LIFF after delay
            setTimeout(() => {
                this.closeApp();
            }, 2000);

        } catch (error) {
            console.error('Submit failed:', error);
            this.showMessage(error.message || '設定失敗，請重試', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async sendConfirmationMessage(locationType, county, district) {
        const locationTypeText = locationType === 'home' ? '住家' : '公司';
        const message = `✅ ${locationTypeText}地點設定完成\n📍 ${county}${district}`;

        await liff.sendMessages([{
            type: 'text',
            text: message
        }]);
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

        // Auto hide after 3 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                messageEl.classList.add('hidden');
            }, 3000);
        }
    }

    closeApp() {
        liff.closeWindow();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LocationApp();
});
