/**
 * Main Entry Point
 * Agent Swarm - Initialization & Event Handling
 */

// Import modules
import {
    ScrollProgress,
    BackToTop,
    StickyHeader,
    ScrollReveal,
    ScrollSnap
} from './modules/scroll-effects.js';

import {
    fadeIn,
    slideIn,
    staggerChildren,
    animateOnScroll,
    create3DTilt,
    createMagneticButton
} from './modules/animations.js';

import {
    MagneticButton,
    TiltCard,
    Ripple
} from './modules/interactions.js';

import {
    $,
    $$,
    throttle,
    debounce,
    prefersReducedMotion,
    storage
} from './modules/utils.js';

// ========================================
// App Initialization
// ========================================

class App {
    constructor() {
        this.initialized = false;
    }
    
    async init() {
        if (this.initialized) return;
        
        console.log('Agent Swarm Initializing...');
        
        // Initialize components
        this.initScrollEffects();
        this.initInteractions();
        this.initAnimations();
        
        this.initialized = true;
        console.log('Agent Swarm Ready!');
    }
    
    // Scroll Effects
    initScrollEffects() {
        // Progress bar
        const progressBar = $('.scroll-progress');
        if (progressBar) {
            new ScrollProgress(progressBar);
        }
        
        // Back to top
        const backToTop = $('.back-to-top');
        if (backToTop) {
            new BackToTop(backToTop);
        }
        
        // Sticky header
        const header = $('.navbar');
        if (header) {
            new StickyHeader(header, {
                hideOnScrollDown: true,
                hideThreshold: 100
            });
        }
        
        // Scroll reveal
        const revealElements = $$('.reveal');
        if (revealElements.length) {
            new ScrollReveal(revealElements, {
                threshold: 0.1,
                animation: 'fadeUp',
                stagger: 100
            });
        }
    }
    
    // Mouse Interactions
    initInteractions() {
        if (prefersReducedMotion()) return;
        
        // Magnetic buttons
        const magneticButtons = $$('[data-magnetic]');
        magneticButtons.forEach(btn => {
            new MagneticButton(btn, { strength: 0.3 });
        });
        
        // 3D tilt cards
        const tiltCards = $$('[data-tilt]');
        tiltCards.forEach(card => {
            new TiltCard(card, {
                perspective: 1000,
                maxRotationX: 5,
                maxRotationY: 5,
                scale: 1.02
            });
        });
        
        // Ripple effect
        const rippleButtons = $$('[data-ripple]');
        rippleButtons.forEach(btn => {
            new Ripple(btn);
        });
    }
    
    // Entrance Animations
    initAnimations() {
        if (prefersReducedMotion()) return;
        
        // Hero animations
        const heroTitle = $('.hero-title');
        const heroSubtitle = $('.hero-subtitle');
        const heroCta = $('.hero-cta');
        
        if (heroTitle) fadeIn(heroTitle, { duration: 800 });
        if (heroSubtitle) fadeIn(heroSubtitle, { duration: 800, delay: 200 });
        if (heroCta) fadeIn(heroCta, { duration: 800, delay: 400 });
        
        // Stagger feature cards
        const featureCards = $$('.feature-card');
        if (featureCards.length) {
            staggerChildren(featureCards, {
                animation: 'fadeUp',
                delay: 100,
                startDelay: 200
            });
        }
    }
}

// ========================================
// DOM Ready
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});

// ========================================
// Utility Exports
// ========================================

export {
    ScrollProgress,
    BackToTop,
    StickyHeader,
    ScrollReveal,
    fadeIn,
    slideIn,
    staggerChildren,
    animateOnScroll,
    create3DTilt,
    createMagneticButton,
    MagneticButton,
    TiltCard,
    Ripple,
    $,
    $$,
    throttle,
    debounce,
    storage
};

export default app;
