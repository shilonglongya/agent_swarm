/**
 * Scroll Effects Module
 * Agent Swarm - Scroll Effects Controller
 */

import { $, $$, throttle, prefersReducedMotion, getScrollProgress } from './utils.js';

// ========================================
// Scroll Progress
// ========================================

/**
 * Scroll Progress Bar
 */
export class ScrollProgress {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            position: 'top',
            height: '3px',
            background: 'linear-gradient(90deg, #007AFF, #5856D6)',
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        this.element.style.position = 'fixed';
        this.element.style.top = this.options.position === 'top' ? '0' : 'auto';
        this.element.style.bottom = this.options.position === 'bottom' ? '0' : 'auto';
        this.element.style.left = '0';
        this.element.style.width = '0%';
        this.element.style.height = this.options.height;
        this.element.style.background = this.options.background;
        this.element.style.zIndex = '9999';
        this.element.style.transition = 'width 0.1s ease';
        
        window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
        window.addEventListener('resize', this.onScroll.bind(this), { passive: true });
    }
    
    onScroll() {
        const progress = getScrollProgress() * 100;
        this.element.style.width = `${progress}%`;
    }
    
    destroy() {
        window.removeEventListener('scroll', this.onScroll);
        window.removeEventListener('resize', this.onScroll);
    }
}

// ========================================
// Back to Top
// ========================================

/**
 * Back to Top Button
 */
export class BackToTop {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            showAfter: 300,
            scrollToTop: true,
            scrollSpeed: 800,
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        this.element.style.opacity = '0';
        this.element.style.visibility = 'hidden';
        this.element.style.transition = 'all 0.3s ease';
        
        this.element.addEventListener('click', () => {
            if (this.options.scrollToTop) {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            }
        });
        
        window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
    }
    
    onScroll() {
        const scrolled = window.scrollY;
        
        if (scrolled > this.options.showAfter) {
            this.element.style.opacity = '1';
            this.element.style.visibility = 'visible';
        } else {
            this.element.style.opacity = '0';
            this.element.style.visibility = 'hidden';
        }
    }
    
    destroy() {
        window.removeEventListener('scroll', this.onScroll);
    }
}

// ========================================
// Sticky Header
// ========================================

/**
 * Sticky Header
 */
export class StickyHeader {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            hideOnScrollDown: true,
            hideThreshold: 100,
            ...options
        };
        
        this.lastScroll = 0;
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
    }
    
    onScroll() {
        const currentScroll = window.scrollY;
        
        if (currentScroll <= 0) {
            this.element.classList.remove('hidden');
            this.element.classList.add('visible');
            return;
        }
        
        if (this.options.hideOnScrollDown) {
            if (currentScroll > this.lastScroll && currentScroll > this.options.hideThreshold) {
                // Scroll down
                this.element.classList.add('hidden');
                this.element.classList.remove('visible');
            } else {
                // Scroll up
                this.element.classList.remove('hidden');
                this.element.classList.add('visible');
            }
        }
        
        // Add scrolled class
        if (currentScroll > 50) {
            this.element.classList.add('scrolled');
        } else {
            this.element.classList.remove('scrolled');
        }
        
        this.lastScroll = currentScroll;
    }
    
    destroy() {
        window.removeEventListener('scroll', this.onScroll);
    }
}

// ========================================
// Parallax
// ========================================

/**
 * Parallax Background
 */
export class Parallax {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            speed: 0.5,
            direction: 'vertical',
            reverse: false,
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.element || prefersReducedMotion()) return;
        
        this.updatePosition = throttle(this.updatePosition.bind(this), 16);
        
        window.addEventListener('scroll', this.updatePosition, { passive: true });
        window.addEventListener('resize', this.updatePosition, { passive: true });
        
        this.updatePosition();
    }
    
    updatePosition() {
        const scrolled = window.scrollY;
        const speed = this.options.reverse 
            ? -this.options.speed 
            : this.options.speed;
        
        if (this.options.direction === 'vertical') {
            this.element.style.transform = `translateY(${scrolled * speed}px)`;
        } else {
            this.element.style.transform = `translateX(${scrolled * speed}px)`;
        }
    }
    
    destroy() {
        window.removeEventListener('scroll', this.updatePosition);
        window.removeEventListener('resize', this.updatePosition);
    }
}

// ========================================
// Scroll Reveal
// ========================================

/**
 * Scroll Reveal Animation
 */
export class ScrollReveal {
    constructor(elements, options = {}) {
        this.elements = typeof elements === 'string' 
            ? $$(elements) 
            : elements;
        
        this.options = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px',
            once: true,
            animation: 'fadeUp',
            delay: 0,
            stagger: 100,
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.elements.length) return;
        
        this.observer = new IntersectionObserver(
            this.handleIntersection.bind(this),
            {
                threshold: this.options.threshold,
                rootMargin: this.options.rootMargin
            }
        );
        
        this.elements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transition = 'none';
            
            // Store original transition
            el.dataset.originalTransition = el.style.transition;
            
            this.observer.observe(el);
        });
    }
    
    handleIntersection(entries) {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const delay = this.options.delay + (index * this.options.stagger);
                
                setTimeout(() => {
                    this.animateElement(el);
                }, delay);
                
                if (this.options.once) {
                    this.observer.unobserve(el);
                }
            }
        });
    }
    
    animateElement(el) {
        if (prefersReducedMotion()) {
            el.style.opacity = '1';
            el.style.transform = 'none';
            return;
        }
        
        const animations = {
            fadeUp: {
                opacity: [0, 1],
                transform: ['translateY(30px)', 'translateY(0)']
            },
            fadeDown: {
                opacity: [0, 1],
                transform: ['translateY(-30px)', 'translateY(0)']
            },
            fadeIn: {
                opacity: [0, 1],
                transform: ['scale(0.95)', 'scale(1)']
            },
            slideInLeft: {
                opacity: [0, 1],
                transform: ['translateX(-50px)', 'translateX(0)']
            },
            slideInRight: {
                opacity: [0, 1],
                transform: ['translateX(50px)', 'translateX(0)']
            }
        };
        
        const anim = animations[this.options.animation] || animations.fadeUp;
        
        el.style.transition = `opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1), transform 0.6s cubic-bezier(0.16, 1, 0.3, 1)`;
        el.style.opacity = '1';
        el.style.transform = anim.transform[1];
    }
    
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// ========================================
// Scroll Snap
// ========================================

/**
 * Scroll Snap Container
 */
export class ScrollSnap {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            direction: 'vertical',
            snapType: 'proximity',
            snapAlign: 'start',
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        this.element.style.scrollSnapType = `${this.options.direction} ${this.options.snapType}`;
        
        const sections = this.element.children;
        [...sections].forEach(section => {
            section.style.scrollSnapAlign = this.options.snapAlign;
            section.style.scrollSnapStop = 'always';
        });
    }
}

// ========================================
// Smooth Scroll Anchor
// ========================================

/**
 * Smooth Scroll for Anchor Links
 */
export class SmoothScrollAnchor {
    constructor(links, options = {}) {
        this.links = typeof links === 'string' ? $$(links) : links;
        
        this.options = {
            offset: 0,
            duration: 800,
            easing: 'easeInOutCubic',
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.links.length) return;
        
        this.links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                const targetId = link.getAttribute('href');
                const target = document.querySelector(targetId);
                
                if (target) {
                    this.scrollTo(target);
                }
            });
        });
    }
    
    scrollTo(target) {
        const targetTop = target.getBoundingClientRect().top + window.scrollY - this.options.offset;
        
        window.scrollTo({
            top: targetTop,
            behavior: 'smooth'
        });
    }
}

// ========================================
// Lazy Load (Scroll-based)
// ========================================

/**
 * Lazy Load Images on Scroll
 */
export class LazyLoadScroll {
    constructor(elements, options = {}) {
        this.elements = typeof elements === 'string' 
            ? $$(elements) 
            : elements;
        
        this.options = {
            threshold: 0,
            rootMargin: '50px',
            placeholder: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.elements.length) return;
        
        this.observer = new IntersectionObserver(
            this.loadImage.bind(this),
            {
                threshold: this.options.threshold,
                rootMargin: this.options.rootMargin
            }
        );
        
        this.elements.forEach(el => {
            const src = el.getAttribute('data-src');
            const srcset = el.getAttribute('data-srcset');
            
            if (src) {
                el.setAttribute('src', this.options.placeholder);
                el.dataset.originalSrc = src;
            }
            
            if (srcset) {
                el.dataset.originalSrcset = srcset;
            }
            
            this.observer.observe(el);
        });
    }
    
    loadImage(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                
                if (el.dataset.originalSrc) {
                    el.setAttribute('src', el.dataset.originalSrc);
                }
                
                if (el.dataset.originalSrcset) {
                    el.setAttribute('srcset', el.dataset.originalSrcset);
                }
                
                el.classList.add('loaded');
                this.observer.unobserve(el);
            }
        });
    }
    
    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// ========================================
// Active Link on Scroll
// ========================================

/**
 * Active Link Highlighter
 */
export class ActiveLink {
    constructor(links, sections, options = {}) {
        this.links = typeof links === 'string' ? $$(links) : links;
        this.sections = typeof sections === 'string' ? $$(sections) : sections;
        
        this.options = {
            offset: 100,
            activeClass: 'active',
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.links.length || !this.sections.length) return;
        
        window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
        this.onScroll();
    }
    
    onScroll() {
        const scrollPos = window.scrollY + this.options.offset;
        
        this.sections.forEach(section => {
            const top = section.offsetTop;
            const height = section.offsetHeight;
            const id = section.getAttribute('id');
            
            if (scrollPos >= top && scrollPos < top + height) {
                this.links.forEach(link => {
                    link.classList.remove(this.options.activeClass);
                    
                    if (link.getAttribute('href') === `#${id}`) {
                        link.classList.add(this.options.activeClass);
                    }
                });
            }
        });
    }
    
    destroy() {
        window.removeEventListener('scroll', this.onScroll);
    }
}

// Export all
export default {
    ScrollProgress,
    BackToTop,
    StickyHeader,
    Parallax,
    ScrollReveal,
    ScrollSnap,
    SmoothScrollAnchor,
    LazyLoadScroll,
    ActiveLink
};
