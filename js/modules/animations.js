/**
 * Animations Module
 * Agent Swarm - Animations Controller
 */

import { $, $$, prefersReducedMotion } from './utils.js';

// ========================================
// Animation Controller
// ========================================

class AnimationController {
    constructor() {
        this.animations = new Map();
        this.rafId = null;
        this.startTime = null;
    }
    
    /**
     * Add animation
     */
    add(id, animation) {
        this.animations.set(id, animation);
    }
    
    /**
     * Remove animation
     */
    remove(id) {
        this.animations.delete(id);
    }
    
    /**
     * Start animation loop
     */
    start() {
        if (this.rafId) return;
        
        const loop = (timestamp) => {
            if (!this.startTime) this.startTime = timestamp;
            const elapsed = timestamp - this.startTime;
            
            this.animations.forEach(animation => {
                if (animation.running) {
                    animation.update(elapsed);
                }
            });
            
            this.rafId = requestAnimationFrame(loop);
        };
        
        this.rafId = requestAnimationFrame(loop);
    }
    
    /**
     * Stop animation loop
     */
    stop() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
            this.startTime = null;
        }
    }
}

// Global animation controller
export const animationController = new AnimationController();

// ========================================
// Built-in Animations
// ========================================

/**
 * Fade in animation
 */
export function fadeIn(element, options = {}) {
    const {
        duration = 600,
        delay = 0,
        easing = 'cubic-bezier(0.16, 1, 0.3, 1)'
    } = options;
    
    if (prefersReducedMotion() || !element) {
        element.style.opacity = '1';
        return Promise.resolve();
    }
    
    element.style.transition = `opacity ${duration}ms ${easing} ${delay}ms`;
    element.style.opacity = '0';
    
    return new Promise(resolve => {
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            
            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, duration + delay);
        });
    });
}

/**
 * Fade out animation
 */
export function fadeOut(element, options = {}) {
    const {
        duration = 600,
        delay = 0,
        easing = 'cubic-bezier(0.16, 1, 0.3, 1)'
    } = options;
    
    if (prefersReducedMotion() || !element) {
        element.style.opacity = '0';
        return Promise.resolve();
    }
    
    element.style.transition = `opacity ${duration}ms ${easing} ${delay}ms`;
    element.style.opacity = '0';
    
    return new Promise(resolve => {
        setTimeout(() => {
            element.style.transition = '';
            resolve();
        }, duration + delay);
    });
}

/**
 * Slide in from direction
 */
export function slideIn(element, direction = 'up', options = {}) {
    const {
        duration = 600,
        delay = 0,
        distance = 30,
        easing = 'cubic-bezier(0.16, 1, 0.3, 1)'
    } = options;
    
    if (prefersReducedMotion() || !element) {
        element.style.opacity = '1';
        element.style.transform = '';
        return Promise.resolve();
    }
    
    const transforms = {
        up: `translateY(${distance}px)`,
        down: `translateY(-${distance}px)`,
        left: `translateX(${distance}px)`,
        right: `translateX(-${distance}px)`
    };
    
    element.style.transition = `opacity ${duration}ms ${easing} ${delay}ms, transform ${duration}ms ${easing} ${delay}ms`;
    element.style.opacity = '0';
    element.style.transform = transforms[direction] || transforms.up;
    
    return new Promise(resolve => {
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translate(0, 0)';
            
            setTimeout(() => {
                element.style.transition = '';
                element.style.transform = '';
                resolve();
            }, duration + delay);
        });
    });
}

/**
 * Scale animation
 */
export function scaleIn(element, options = {}) {
    const {
        duration = 600,
        delay = 0,
        from = 0.9,
        easing = 'cubic-bezier(0.34, 1.56, 0.64, 1)'
    } = options;
    
    if (prefersReducedMotion() || !element) {
        element.style.opacity = '1';
        element.style.transform = '';
        return Promise.resolve();
    }
    
    element.style.transition = `opacity ${duration}ms ${easing} ${delay}ms, transform ${duration}ms ${easing} ${delay}ms`;
    element.style.opacity = '0';
    element.style.transform = `scale(${from})`;
    
    return new Promise(resolve => {
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
            
            setTimeout(() => {
                element.style.transition = '';
                element.style.transform = '';
                resolve();
            }, duration + delay);
        });
    });
}

/**
 * Shake animation
 */
export function shake(element, options = {}) {
    const {
        duration = 400,
        distance = 10
    } = options;
    
    if (prefersReducedMotion() || !element) return Promise.resolve();
    
    const original = element.style.transform;
    element.style.transition = 'transform 0.1s ease';
    
    const steps = [
        { transform: `translateX(-${distance}px)` },
        { transform: `translateX(${distance}px)` },
        { transform: `translateX(-${distance}px)` },
        { transform: `translateX(${distance}px)` },
        { transform: original || 'translateX(0)' }
    ];
    
    return new Promise(resolve => {
        let stepIndex = 0;
        
        const step = () => {
            if (stepIndex < steps.length) {
                element.style.transform = steps[stepIndex].transform;
                stepIndex++;
                setTimeout(step, duration / steps.length);
            } else {
                element.style.transition = '';
                element.style.transform = original;
                resolve();
            }
        };
        
        step();
    });
}

/**
 * Pulse animation
 */
export function pulse(element, options = {}) {
    const {
        scale = 1.05,
        duration = 300
    } = options;
    
    if (prefersReducedMotion() || !element) return Promise.resolve();
    
    element.style.transition = `transform ${duration}ms ease`;
    element.style.transform = `scale(${scale})`;
    
    return new Promise(resolve => {
        setTimeout(() => {
            element.style.transform = 'scale(1)';
            
            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, duration);
        }, duration);
    });
}

/**
 * Counter animation (number counting)
 */
export function counter(element, options = {}) {
    const {
        from = 0,
        to = 100,
        duration = 1000,
        easing = 'cubic-bezier(0.16, 1, 0.3, 1)',
        prefix = '',
        suffix = ''
    } = options;
    
    if (prefersReducedMotion() || !element) {
        element.textContent = `${prefix}${to}${suffix}`;
        return Promise.resolve();
    }
    
    const startTime = performance.now();
    
    return new Promise(resolve => {
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Ease out
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(from + (to - from) * eased);
            
            element.textContent = `${prefix}${current}${suffix}`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.textContent = `${prefix}${to}${suffix}`;
                resolve();
            }
        };
        
        requestAnimationFrame(animate);
    });
}

// ========================================
// Stagger Animations
// ========================================

/**
 * Stagger children animation
 */
export function staggerChildren(elements, options = {}) {
    const {
        animation = 'fadeUp',
        delay = 100,
        startDelay = 0
    } = options;
    
    if (prefersReducedMotion()) {
        elements.forEach(el => {
            el.style.opacity = '1';
            el.style.transform = '';
        });
        return Promise.resolve();
    }
    
    const animations = {
        fadeUp: (el, i) => slideIn(el, 'up', { delay: startDelay + i * delay }),
        fadeIn: (el, i) => fadeIn(el, { delay: startDelay + i * delay }),
        scaleIn: (el, i) => scaleIn(el, { delay: startDelay + i * delay }),
        slideInLeft: (el, i) => slideIn(el, 'left', { delay: startDelay + i * delay }),
        slideInRight: (el, i) => slideIn(el, 'right', { delay: startDelay + i * delay })
    };
    
    const animFn = animations[animation] || animations.fadeUp;
    
    return Promise.all(elements.map((el, i) => animFn(el, i)));
}

// ========================================
// Intersection Observer Animations
// ========================================

/**
 * Animate on scroll (Intersection Observer)
 */
export function animateOnScroll(elements, options = {}) {
    const {
        threshold = 0.1,
        rootMargin = '0px 0px -50px 0px',
        once = true,
        animation = 'fadeUp'
    } = options;
    
    if (!elements.length) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                
                const animations = {
                    fadeUp: () => slideIn(el, 'up'),
                    fadeIn: () => fadeIn(el),
                    scaleIn: () => scaleIn(el),
                    slideInLeft: () => slideIn(el, 'left'),
                    slideInRight: () => slideIn(el, 'right')
                };
                
                (animations[animation] || animations.fadeUp)();
                
                if (once) {
                    observer.unobserve(el);
                }
            }
        });
    }, { threshold, rootMargin });
    
    elements.forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
    
    return observer;
}

// ========================================
// 3D Tilt Effect
// ========================================

/**
 * 3D Card Tilt
 */
export function create3DTilt(element, options = {}) {
    const {
        perspective = 1000,
        maxRotation = 5,
        scale = 1.02
    } = options;
    
    if (!element) return;
    
    element.style.transformStyle = 'preserve-3d';
    element.style.perspective = `${perspective}px`;
    
    const handleMouseMove = (e) => {
        const rect = element.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = ((y - centerY) / centerY) * -maxRotation;
        const rotateY = ((x - centerX) / centerX) * maxRotation;
        
        element.style.transform = `perspective(${perspective}px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`;
    };
    
    const handleMouseLeave = () => {
        element.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
    };
    
    element.addEventListener('mousemove', handleMouseMove);
    element.addEventListener('mouseleave', handleMouseLeave);
    
    // Return cleanup function
    return () => {
        element.removeEventListener('mousemove', handleMouseMove);
        element.removeEventListener('mouseleave', handleMouseLeave);
    };
}

// ========================================
// Magnetic Button Effect
// ========================================

/**
 * Magnetic button effect
 */
export function createMagneticButton(element, options = {}) {
    const {
        strength = 0.3,
        ease = 0.1
    } = options;
    
    if (!element) return;
    
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    
    const handleMouseMove = (e) => {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        targetX = (e.clientX - centerX) * strength;
        targetY = (e.clientY - centerY) * strength;
    };
    
    const handleMouseLeave = () => {
        targetX = 0;
        targetY = 0;
    };
    
    const animate = () => {
        currentX += (targetX - currentX) * ease;
        currentY += (targetY - currentY) * ease;
        
        element.style.transform = `translate(${currentX}px, ${currentY}px)`;
        
        requestAnimationFrame(animate);
    };
    
    element.addEventListener('mousemove', handleMouseMove);
    element.addEventListener('mouseleave', handleMouseLeave);
    animate();
    
    return () => {
        element.removeEventListener('mousemove', handleMouseMove);
        element.removeEventListener('mouseleave', handleMouseLeave);
    };
}

// ========================================
// Parallax Effect
// ========================================

/**
 * Create parallax effect
 */
export function createParallax(element, options = {}) {
    const {
        speed = 0.5,
        direction = 'vertical'
    } = options;
    
    if (!element) return;
    
    const handleScroll = () => {
        const scrolled = window.scrollY;
        
        if (direction === 'vertical') {
            element.style.transform = `translateY(${scrolled * speed}px)`;
        } else {
            element.style.transform = `translateX(${scrolled * speed}px)`;
        }
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
        window.removeEventListener('scroll', handleScroll);
    };
}

// ========================================
// Typewriter Effect
// ========================================

/**
 * Typewriter effect
 */
export function typewriter(element, options = {}) {
    const {
        text = '',
        speed = 50,
        cursor = true,
        delay = 0
    } = options;
    
    if (!element) return Promise.resolve();
    
    return new Promise(resolve => {
        setTimeout(() => {
            element.textContent = '';
            let index = 0;
            
            const type = () => {
                if (index < text.length) {
                    element.textContent += text.charAt(index);
                    index++;
                    setTimeout(type, speed);
                } else {
                    resolve();
                }
            };
            
            type();
        }, delay);
    });
}

// ========================================
// Export default
// ========================================

export default {
    fadeIn,
    fadeOut,
    slideIn,
    scaleIn,
    shake,
    pulse,
    counter,
    staggerChildren,
    animateOnScroll,
    create3DTilt,
    createMagneticButton,
    createParallax,
    typewriter
};
