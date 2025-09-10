// LIFF Location Setting App
// AUTO_UPDATE_VERSION: 20250910-2233 (AI can update this timestamp when making changes)
class LocationApp {
    constructor() {
        this.adminData = {};
        this.isInitialized = false;
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
            if (!this.isInitialized) {
                this.setupEventListeners();
                this.isInitialized = true;
            }
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

    async ensureDataLoaded() {
        // 檢查資料是否已載入，如果沒有則重新載入
        if (Object.keys(this.adminData).length === 0) {
            console.log('Admin data missing, reloading...');

            // 顯示載入提示
            this.showMessage('正在載入地區資料...', 'info');

            try {
                await this.loadAdminData();
                this.populateCounties();

                // 短暫顯示成功訊息後隱藏
                this.showMessage('地區資料載入完成', 'success');
                setTimeout(() => {
                    const messageEl = document.getElementById('message');
                    if (messageEl) {
                        messageEl.classList.add('hidden');
                    }
                }, 1000);

            } catch (error) {
                this.showMessage('載入地區資料失敗，請重新整理頁面', 'error');
            }
        }
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
            this.showMessage('載入地區資料失敗', 'error');
        }
    }

    populateCounties() {
        const countySelect = document.getElementById('county');

        // 清空現有選項（除了第一個預設選項）
        countySelect.innerHTML = '<option value="">請選擇縣市</option>';

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

        // County selection events
        countySelect.addEventListener('focus', async () => {
            // 當用戶點擊縣市下拉選單時，確保資料已載入
            await this.ensureDataLoaded();
        });

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
                    this.showMessage('登入狀態已過期，請重新登入', 'error');
                    setTimeout(() => {
                        liff.login();
                    }, 2000);
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
            this.showMessage(`✅ ${locationType === 'home' ? '住家' : '公司'}地點設定成功！\n你可以關閉本視窗或繼續設定其他地點`, 'success');

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
