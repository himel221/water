/**
 * ========================================
 * Home Page - JavaScript
 * স্ট্যাটিস্টিক্স কাউন্টার অ্যানিমেশন
 * ========================================
 */

document.addEventListener('DOMContentLoaded', function() {
    // ========================================
    // স্ট্যাটিস্টিক্স কাউন্টার অ্যানিমেশন
    // ========================================
    
    const statNumbers = document.querySelectorAll('.stat-number');
    
    /**
     * কাউন্টার অ্যানিমেট করার ফাংশন
     * @param {HTMLElement} element - যে এলিমেন্টে কাউন্টার দেখাবে
     */
    function animateCounter(element) {
        const target = parseInt(element.getAttribute('data-count'));
        const duration = 2000; // 2 সেকেন্ড
        const step = Math.max(1, Math.floor(target / 60));
        let current = 0;
        
        function updateCounter() {
            current += step;
            if (current >= target) {
                // টার্গেটে পৌঁছালে + চিহ্ন যোগ করুন (যদি 99 এর বেশি হয়)
                element.textContent = target + (target > 99 ? '+' : '');
                return;
            }
            element.textContent = current + (target > 99 ? '+' : '');
            requestAnimationFrame(updateCounter);
        }
        
        updateCounter();
    }
    
    /**
     * Intersection Observer - যখন এলিমেন্ট ভিউপোর্টে আসে তখন অ্যানিমেশন শুরু করে
     */
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                animateCounter(target);
                observer.unobserve(target); // একবার অ্যানিমেট হয়ে গেলে আর দেখা হবে না
            }
        });
    }, { 
        threshold: 0.5 // এলিমেন্টের ৫০% দেখা গেলে ট্রিগার হবে
    });
    
    // সব স্ট্যাট এলিমেন্টে Observer যোগ করুন
    statNumbers.forEach(stat => observer.observe(stat));
    
    // ========================================
    // কনসোল লগ (ডিবাগিং এর জন্য)
    // ========================================
    
    console.log('✅ Home page loaded successfully!');
    console.log(`📊 Found ${statNumbers.length} stat counters to animate`);
});