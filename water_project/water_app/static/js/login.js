// login.js - Superwater Login Module

(function() {
    'use strict';

    // ============================================
    // DOM References
    // ============================================
    const DOM = {
        emailInput: document.getElementById('email'),
        passwordInput: document.getElementById('password'),
        loginForm: document.getElementById('loginForm'),
        loginBtn: document.getElementById('loginBtn'),
        rememberMe: document.getElementById('rememberMe'),
        emailError: document.getElementById('emailError'),
        passwordError: document.getElementById('passwordError'),
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
    // Field Validations
    // ============================================
    const validations = {
        email: {
            validate: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
            error: 'Please enter a valid email address'
        },
        password: {
            validate: (val) => val.length >= 1,
            error: 'Please enter your password'
        }
    };

    // ============================================
    // Validate Single Field
    // ============================================
    function validateField(fieldId) {
        const input = document.getElementById(fieldId);
        const errorEl = document.getElementById(fieldId + 'Error');
        if (!input || !errorEl) return true;

        const validation = validations[fieldId];
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
        Object.keys(validations).forEach(fieldId => {
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
                // Press Enter to submit
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        if (DOM.loginForm) {
                            DOM.loginForm.dispatchEvent(new Event('submit'));
                        }
                    }
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
    // Remember Me functionality
    // ============================================
    function initRememberMe() {
        // Check if there's a saved email
        const savedEmail = localStorage.getItem('loginEmail');
        if (savedEmail && DOM.emailInput) {
            DOM.emailInput.value = savedEmail;
            if (DOM.rememberMe) {
                DOM.rememberMe.checked = true;
            }
        }

        // Save email when form is submitted
        if (DOM.rememberMe) {
            DOM.rememberMe.addEventListener('change', function() {
                if (!this.checked) {
                    localStorage.removeItem('loginEmail');
                }
            });
        }
    }

    // ============================================
    // Form Submission
    // ============================================
    function initFormSubmission() {
        if (!DOM.loginForm) return;

        DOM.loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            let isValid = true;
            
            // Validate all fields
            Object.keys(validations).forEach(fieldId => {
                if (!validateField(fieldId)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                const firstError = document.querySelector('.field-error[style*="display: block"]');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }
            
            // Save email if remember me is checked
            if (DOM.rememberMe && DOM.rememberMe.checked && DOM.emailInput) {
                localStorage.setItem('loginEmail', DOM.emailInput.value);
            } else {
                localStorage.removeItem('loginEmail');
            }
            
            // Show loading
            if (DOM.loginBtn) {
                DOM.loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
                DOM.loginBtn.disabled = true;
            }
            
            // Submit the form
            this.submit();
        });
    }

    // ============================================
    // Demo Credentials Auto-fill
    // ============================================
    function initDemoCredentials() {
        // Add click event to demo credentials to auto-fill
        const demoValues = document.querySelectorAll('.demo-value');
        if (demoValues.length >= 2) {
            const demoEmail = demoValues[0].textContent.trim();
            const demoPassword = demoValues[1].textContent.trim();
            
            // Auto-fill on page load (optional - comment out if not wanted)
            // if (DOM.emailInput && !DOM.emailInput.value) {
            //     DOM.emailInput.value = demoEmail;
            // }
            // if (DOM.passwordInput && !DOM.passwordInput.value) {
            //     DOM.passwordInput.value = demoPassword;
            // }
            
            // Allow clicking on demo credentials to fill
            const demoContainer = document.querySelector('.demo-credentials');
            if (demoContainer) {
                demoContainer.style.cursor = 'pointer';
                demoContainer.addEventListener('click', function() {
                    if (DOM.emailInput) {
                        DOM.emailInput.value = demoEmail;
                        DOM.emailInput.classList.add('valid');
                        DOM.emailInput.classList.remove('invalid');
                        if (DOM.emailError) {
                            DOM.emailError.style.display = 'none';
                        }
                    }
                    if (DOM.passwordInput) {
                        DOM.passwordInput.value = demoPassword;
                        DOM.passwordInput.classList.add('valid');
                        DOM.passwordInput.classList.remove('invalid');
                        if (DOM.passwordError) {
                            DOM.passwordError.style.display = 'none';
                        }
                    }
                    showToast('Demo credentials filled! Click Sign In to continue.', 'success');
                });
            }
        }
    }

    // ============================================
    // Password Manager Detection
    // ============================================
    function detectPasswordManager() {
        // Listen for password manager auto-fill
        if (DOM.passwordInput) {
            DOM.passwordInput.addEventListener('animationstart', function(e) {
                if (e.animationName === 'onAutoFillStart') {
                    // Password manager filled the field
                    if (DOM.emailInput && DOM.emailInput.value) {
                        // Trigger validation
                        validateField('email');
                        validateField('password');
                    }
                }
            });
        }
    }

    // ============================================
    // Initialize Everything
    // ============================================
    function init() {
        // Add animation for password manager detection
        const style = document.createElement('style');
        style.textContent = `
            @keyframes onAutoFillStart {
                from { opacity: 1; }
                to { opacity: 1; }
            }
            input:-webkit-autofill {
                animation-name: onAutoFillStart;
            }
        `;
        document.head.appendChild(style);
        
        initValidationListeners();
        initRememberMe();
        initFormSubmission();
        initDemoCredentials();
        detectPasswordManager();
        
        console.log('Login module initialized successfully');
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();