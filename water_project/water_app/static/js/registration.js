// registration.js - Superwater Registration Module

(function() {
    'use strict';

    // ============================================
    // DOM References
    // ============================================
    const DOM = {
        passwordInput: document.getElementById('password'),
        confirmInput: document.getElementById('confirmPassword'),
        strengthLevel: document.getElementById('strengthLevel'),
        strengthText: document.getElementById('strengthText'),
        passwordMatch: document.getElementById('passwordMatch'),
        registrationForm: document.getElementById('registrationForm'),
        registerBtn: document.getElementById('registerBtn'),
        termsCheckbox: document.getElementById('terms'),
        termsError: document.getElementById('termsError'),
    };

    // ============================================
    // Password Toggle
    // ============================================
    window.togglePassword = function(fieldId) {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        const icon = field.parentElement.querySelector('.password-toggle i');
        if (field.type === 'password') {
            field.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            field.type = 'password';
            icon.className = 'fas fa-eye';
        }
    };

    // ============================================
    // Password Strength Checker
    // ============================================
    function checkPasswordStrength(password) {
        let strength = 0;
        const requirements = {
            length: document.getElementById('reqLength'),
            upper: document.getElementById('reqUpper'),
            lower: document.getElementById('reqLower'),
            number: document.getElementById('reqNumber'),
            special: document.getElementById('reqSpecial')
        };

        // Check each requirement
        const checks = [
            { pattern: password.length >= 8, id: 'length' },
            { pattern: /[A-Z]/.test(password), id: 'upper' },
            { pattern: /[a-z]/.test(password), id: 'lower' },
            { pattern: /[0-9]/.test(password), id: 'number' },
            { pattern: /[^A-Za-z0-9]/.test(password), id: 'special' }
        ];

        checks.forEach(check => {
            const req = requirements[check.id];
            if (req) {
                if (check.pattern) {
                    strength++;
                    req.querySelector('i').className = 'fas fa-check-circle';
                } else {
                    req.querySelector('i').className = 'fas fa-circle';
                }
            }
        });

        // Update strength bar
        const percentage = (strength / 5) * 100;
        DOM.strengthLevel.style.width = percentage + '%';

        const colors = ['#dc3545', '#dc3545', '#ffc107', '#28a745', '#28a745'];
        const texts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        const color = colors[strength - 1] || '#dc3545';
        const text = texts[strength - 1] || 'Very Weak';

        DOM.strengthLevel.style.background = color;
        DOM.strengthText.textContent = text;
        DOM.strengthText.style.color = color;
    }

    // ============================================
    // Password Match Checker
    // ============================================
    function checkPasswordMatch() {
        const password = DOM.passwordInput ? DOM.passwordInput.value : '';
        const confirm = DOM.confirmInput ? DOM.confirmInput.value : '';

        if (confirm.length === 0) {
            DOM.passwordMatch.textContent = '';
            DOM.passwordMatch.className = 'password-match';
            return;
        }

        if (password === confirm) {
            DOM.passwordMatch.textContent = '✅ Passwords match';
            DOM.passwordMatch.className = 'password-match match';
        } else {
            DOM.passwordMatch.textContent = '❌ Passwords do not match';
            DOM.passwordMatch.className = 'password-match no-match';
        }
    }

    // ============================================
    // Role Selection
    // ============================================
    function initRoleSelection() {
        document.querySelectorAll('.role-option').forEach(option => {
            option.addEventListener('click', function() {
                const radio = this.querySelector('input[type="radio"]');
                if (radio) radio.checked = true;
                
                document.querySelectorAll('.role-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                this.classList.add('selected');
            });
        });
    }

    // ============================================
    // Field Validations
    // ============================================
    const fieldValidations = {
        firstName: {
            validate: (val) => val.trim().length >= 2,
            error: 'First name must be at least 2 characters'
        },
        lastName: {
            validate: (val) => val.trim().length >= 2,
            error: 'Last name must be at least 2 characters'
        },
        email: {
            validate: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
            error: 'Please enter a valid email address'
        },
        phone: {
            validate: (val) => /^[0-9+\-\s()]{10,15}$/.test(val.trim()),
            error: 'Please enter a valid phone number (10-15 digits)'
        },
        address: {
            validate: (val) => val.trim().length >= 5,
            error: 'Address must be at least 5 characters'
        },
        district: {
            validate: (val) => val.trim().length >= 2,
            error: 'Please enter a valid district name'
        }
    };

    // ============================================
    // Validate Single Field
    // ============================================
    function validateField(fieldId) {
        const input = document.getElementById(fieldId);
        const errorEl = document.getElementById(fieldId + 'Error');
        if (!input || !errorEl) return true;

        const validation = fieldValidations[fieldId];
        if (!validation) return true;

        const value = input.value;
        if (!validation.validate(value)) {
            errorEl.textContent = validation.error;
            errorEl.style.display = 'block';
            input.classList.add('invalid');
            input.classList.remove('valid');
            return false;
        } else {
            errorEl.textContent = '';
            errorEl.style.display = 'none';
            input.classList.remove('invalid');
            input.classList.add('valid');
            return true;
        }
    }

    // ============================================
    // Initialize Validation Listeners
    // ============================================
    function initValidationListeners() {
        Object.keys(fieldValidations).forEach(fieldId => {
            const input = document.getElementById(fieldId);
            if (input) {
                input.addEventListener('blur', function() {
                    validateField(fieldId);
                });
                input.addEventListener('input', function() {
                    const errorEl = document.getElementById(fieldId + 'Error');
                    if (errorEl) {
                        errorEl.textContent = '';
                        errorEl.style.display = 'none';
                    }
                    input.classList.remove('invalid');
                });
            }
        });
    }

    // ============================================
    // Toast Notification
    // ============================================
    function showToast(message, type = 'info') {
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) existingToast.remove();
        
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer;">
                <i class="fas fa-times"></i>
            </button>
        `;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            z-index: 10000;
            min-width: 280px;
            max-width: 450px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            animation: slideUp 0.3s ease;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
            font-family: system-ui, -apple-system, sans-serif;
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 5000);
    }

    // ============================================
    // Form Submission
    // ============================================
    function initFormSubmission() {
        if (!DOM.registrationForm) return;

        DOM.registrationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            let isValid = true;
            
            // Validate all required fields
            Object.keys(fieldValidations).forEach(fieldId => {
                if (!validateField(fieldId)) {
                    isValid = false;
                }
            });
            
            // Validate password
            const password = DOM.passwordInput ? DOM.passwordInput.value : '';
            const confirm = DOM.confirmInput ? DOM.confirmInput.value : '';
            
            if (password !== confirm) {
                showToast('Passwords do not match!', 'error');
                isValid = false;
            }
            
            if (password.length < 8) {
                showToast('Password must be at least 8 characters long!', 'error');
                isValid = false;
            }
            
            if (!DOM.termsCheckbox || !DOM.termsCheckbox.checked) {
                if (DOM.termsError) {
                    DOM.termsError.textContent = 'Please agree to the Terms of Service';
                    DOM.termsError.style.display = 'block';
                }
                isValid = false;
            }
            
            if (!isValid) {
                const firstError = document.querySelector('.field-error[style*="display: block"]');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }
            
            // Show loading
            if (DOM.registerBtn) {
                DOM.registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
                DOM.registerBtn.disabled = true;
            }
            
            // Submit the form
            this.submit();
        });
    }

    // ============================================
    // Password Input Listeners
    // ============================================
    function initPasswordListeners() {
        if (DOM.passwordInput) {
            DOM.passwordInput.addEventListener('input', function() {
                checkPasswordStrength(this.value);
                checkPasswordMatch();
            });
        }

        if (DOM.confirmInput) {
            DOM.confirmInput.addEventListener('input', function() {
                checkPasswordMatch();
            });
        }
    }

    // ============================================
    // Initialize Everything
    // ============================================
    function init() {
        initRoleSelection();
        initValidationListeners();
        initPasswordListeners();
        initFormSubmission();
        
        console.log('Registration module initialized successfully');
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();