/**
 * Utility Functions
 * Agent Swarm - Utils Module
 */

// ========================================
// DOM Utilities
// ========================================

/**
 * Query selector wrapper
 */
export function $(selector, context = document) {
    return context.querySelector(selector);
}

/**
 * Query selector all wrapper
 */
export function $$(selector, context = document) {
    return [...context.querySelectorAll(selector)];
}

/**
 * Create element with attributes
 */
export function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    
    Object.entries(attrs).forEach(([key, value]) => {
        if (key === 'class') {
            el.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(el.style, value);
        } else if (key.startsWith('data')) {
            el.setAttribute(key, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            el.addEventListener(key.slice(2).toLowerCase(), value);
        } else {
            el.setAttribute(key, value);
        }
    });
    
    children.forEach(child => {
        if (typeof child === 'string') {
            el.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            el.appendChild(child);
        }
    });
    
    return el;
}

/**
 * Check if element is in viewport
 */
export function isInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top < window.innerHeight &&
        rect.bottom > 0 &&
        rect.left < window.innerWidth &&
        rect.right > 0
    );
}

/**
 * Get element's scroll offset
 */
export function getScrollOffset(el) {
    const rect = el.getBoundingClientRect();
    return {
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX
    };
}

// ========================================
// Event Utilities
// ========================================

/**
 * Throttle function
 */
export function throttle(func, limit = 100) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Debounce function
 */
export function debounce(func, delay = 300) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Once - execute function only once
 */
export function once(func) {
    let called = false;
    let result;
    return function(...args) {
        if (!called) {
            called = true;
            result = func.apply(this, args);
        }
        return result;
    };
}

// ========================================
// Class Utilities
// ========================================

/**
 * Add class with animation
 */
export function addClass(el, className) {
    if (el) el.classList.add(className);
}

/**
 * Remove class with animation
 */
export function removeClass(el, className) {
    if (el) el.classList.remove(className);
}

/**
 * Toggle class
 */
export function toggleClass(el, className, force) {
    if (el) el.classList.toggle(className, force);
}

/**
 * Has class
 */
export function hasClass(el, className) {
    return el ? el.classList.contains(className) : false;
}

// ========================================
// Storage Utilities
// ========================================

/**
 * Local storage wrapper
 */
export const storage = {
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('Storage get error:', e);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.warn('Storage set error:', e);
            return false;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.warn('Storage remove error:', e);
            return false;
        }
    },
    
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (e) {
            console.warn('Storage clear error:', e);
            return false;
        }
    }
};

// ========================================
// Animation Utilities
// ========================================

/**
 * Animate CSS
 */
export function animate(el, properties, duration = 300) {
    return new Promise(resolve => {
        if (!el) {
            resolve();
            return;
        }
        
        const start = {};
        const computed = getComputedStyle(el);
        
        Object.keys(properties).forEach(prop => {
            start[prop] = parseFloat(computed[prop]) || 0;
        });
        
        const startTime = performance.now();
        
        function step(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            
            Object.keys(properties).forEach(prop => {
                const value = start[prop] + (properties[prop] - start[prop]) * eased;
                el.style[prop] = typeof properties[prop] === 'number' 
                    ? value + 'px' 
                    : properties[prop];
            });
            
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                resolve();
            }
        }
        
        requestAnimationFrame(step);
    });
}

/**
 * Fade in element
 */
export function fadeIn(el, duration = 300) {
    if (!el) return Promise.resolve();
    el.style.opacity = '0';
    el.style.display = '';
    
    return new Promise(resolve => {
        requestAnimationFrame(() => {
            el.style.transition = `opacity ${duration}ms ease`;
            el.style.opacity = '1';
            
            setTimeout(() => {
                el.style.transition = '';
                resolve();
            }, duration);
        });
    });
}

/**
 * Fade out element
 */
export function fadeOut(el, duration = 300) {
    if (!el) return Promise.resolve();
    
    return new Promise(resolve => {
        el.style.transition = `opacity ${duration}ms ease`;
        el.style.opacity = '0';
        
        setTimeout(() => {
            el.style.display = 'none';
            el.style.transition = '';
            resolve();
        }, duration);
    });
}

/**
 * Slide element
 */
export function slideUp(el, duration = 300) {
    if (!el) return Promise.resolve();
    
    const height = el.offsetHeight;
    el.style.height = height + 'px';
    el.style.overflow = 'hidden';
    el.style.transition = `height ${duration}ms ease`;
    
    return new Promise(resolve => {
        requestAnimationFrame(() => {
            el.style.height = '0';
            
            setTimeout(() => {
                el.style.display = 'none';
                el.style.height = '';
                el.style.overflow = '';
                el.style.transition = '';
                resolve();
            }, duration);
        });
    });
}

export function slideDown(el, duration = 300) {
    if (!el) return Promise.resolve();
    
    el.style.display = '';
    const height = el.offsetHeight;
    el.style.height = '0';
    el.style.overflow = 'hidden';
    el.style.transition = `height ${duration}ms ease`;
    
    return new Promise(resolve => {
        requestAnimationFrame(() => {
            el.style.height = height + 'px';
            
            setTimeout(() => {
                el.style.height = '';
                el.style.overflow = '';
                el.style.transition = '';
                resolve();
            }, duration);
        });
    });
}

// ========================================
// Format Utilities
// ========================================

/**
 * Format date
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

/**
 * Format file size
 */
export function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format number with commas
 */
export function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format time duration
 */
export function formatDuration(seconds) {
    if (seconds < 60) {
        return `${seconds.toFixed(1)}秒`;
    } else if (seconds < 3600) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}分${secs}秒`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hours}小时${mins}分`;
    }
}

// ========================================
// Validation Utilities
// ========================================

/**
 * Validate email
 */
export function isEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate URL
 */
export function isUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

/**
 * Validate API key format
 */
export function isValidApiKey(key) {
    return key && key.trim().length >= 10;
}

// ========================================
// Copy to Clipboard
// ========================================

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text) {
    try {
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(text);
            return true;
        }
        
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
    } catch (e) {
        console.error('Copy failed:', e);
        return false;
    }
}

// ========================================
// Device Detection
// ========================================

/**
 * Check if mobile device
 */
export function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Check if touch device
 */
export function isTouch() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

/**
 * Check reduced motion preference
 */
export function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// ========================================
// Scroll Utilities
// ========================================

/**
 * Smooth scroll to element
 */
export function scrollTo(target, offset = 0) {
    const el = typeof target === 'string' 
        ? document.querySelector(target) 
        : target;
    
    if (!el) return;
    
    const top = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({
        top,
        behavior: 'smooth'
    });
}

/**
 * Get scroll progress
 */
export function getScrollProgress() {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    return docHeight > 0 ? window.scrollY / docHeight : 0;
}

// ========================================
// Deep Clone
// ========================================

/**
 * Deep clone object
 */
export function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

// ========================================
// Random Utilities
// ========================================

/**
 * Generate random ID
 */
export function generateId(prefix = 'id') {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Random integer between min and max
 */
export function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Pick random item from array
 */
export function randomPick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}
