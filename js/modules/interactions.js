/**
 * Interactions Module
 * Agent Swarm - Mouse Interactions Controller
 */

import { $, $$, throttle, prefersReducedMotion } from './utils.js';

// ========================================
// Custom Cursor
// ========================================

/**
 * Custom Cursor
 */
export class CustomCursor {
    constructor(options = {}) {
        this.options = {
            size: 20,
            color: '#007AFF',
            blendMode: 'difference',
            hoverSize: 40,
            hoverBlendMode: 'normal',
            hideDefault: true,
            ...options
        };
        
        this.cursor = null;
        this.cursorFollower = null;
        this.hoverElements = [];
        this.isHovering = false;
        
        this.init();
    }
    
    init() {
        if (!this.isSupported()) return;
        
        // Hide default cursor
        if (this.options.hideDefault) {
            document.body.style.cursor = 'none';
        }
        
        // Create cursor element
        this.cursor = createCursorDot(this.options);
        document.body.appendChild(this.cursor);
        
        // Create follower
        this.cursorFollower = createCursorFollower(this.options);
        document.body.appendChild(this.cursorFollower);
        
        // Set up hover elements
        this.setupHoverElements();
        
        // Add event listeners
        document.addEventListener('mousemove', this.onMouseMove.bind(this));
        document.addEventListener('mouseover', this.onMouseOver.bind(this));
        document.addEventListener('mouseout', this.onMouseOut.bind(this));
    }
    
    isSupported() {
        return !prefersReducedMotion() && !('ontouchstart' in window);
    }
    
    setupHoverElements() {
        this.hoverElements = $$('a, button, input, select, textarea, [data-cursor-hover]');
        
        this.hoverElements.forEach(el => {
            el.style.cursor = 'none';
            
            el.addEventListener('mouseenter', () => {
                this.isHovering = true;
                this.cursor.style.transform = `translate(-50%, -50%) scale(${this.options.hoverSize / this.options.size})`;
                this.cursor.style.backgroundColor = this.options.color;
                this.cursorFollower.style.mixBlendMode = this.options.hoverBlendMode;
            });
            
            el.addEventListener('mouseleave', () => {
                this.isHovering = false;
                this.cursor.style.transform = 'translate(-50%, -50%) scale(1)';
                this.cursor.style.backgroundColor = 'transparent';
                this.cursorFollower.style.mixBlendMode = this.options.blendMode;
            });
        });
    }
    
    onMouseMove(e) {
        requestAnimationFrame(() => {
            this.cursor.style.left = e.clientX + 'px';
            this.cursor.style.top = e.clientY + 'px';
            this.cursorFollower.style.left = e.clientX + 'px';
            this.cursorFollower.style.top = e.clientY + 'px';
        });
    }
    
    onMouseOver(e) {
        if (e.target.closest('a, button, input, select, textarea, [data-cursor-hover]')) {
            this.isHovering = true;
        }
    }
    
    onMouseOut(e) {
        if (e.target.closest('a, button, input, select, textarea, [data-cursor-hover]')) {
            this.isHovering = false;
        }
    }
    
    destroy() {
        if (this.cursor) this.cursor.remove();
        if (this.cursorFollower) this.cursorFollower.remove();
        document.body.style.cursor = '';
        
        this.hoverElements.forEach(el => {
            el.style.cursor = '';
        });
    }
}

function createCursorDot(options) {
    const el = document.createElement('div');
    el.className = 'custom-cursor';
    el.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: ${options.size}px;
        height: ${options.size}px;
        border: 2px solid ${options.color};
        border-radius: 50%;
        pointer-events: none;
        z-index: 99999;
        transform: translate(-50%, -50%);
        mix-blend-mode: ${options.blendMode};
        transition: transform 0.15s ease, background-color 0.15s ease;
    `;
    return el;
}

function createCursorFollower(options) {
    const el = document.createElement('div');
    el.className = 'custom-cursor-follower';
    el.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: ${options.size * 2}px;
        height: ${options.size * 2}px;
        background: ${options.color};
        border-radius: 50%;
        pointer-events: none;
        z-index: 99998;
        transform: translate(-50%, -50%);
        mix-blend-mode: ${options.blendMode};
        opacity: 0.3;
        transition: transform 0.3s ease, opacity 0.3s ease;
    `;
    return el;
}

// ========================================
// Hover Effects
// ========================================

/**
 * Magnetic Button Effect
 */
export class MagneticButton {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            strength: 0.3,
            ease: 0.1,
            ...options
        };
        
        this.targetX = 0;
        this.targetY = 0;
        this.currentX = 0;
        this.currentY = 0;
        
        this.init();
    }
    
    init() {
        if (!this.element || prefersReducedMotion()) return;
        
        this.element.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.element.addEventListener('mouseleave', this.onMouseLeave.bind(this));
        
        this.animate();
    }
    
    onMouseMove(e) {
        const rect = this.element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        this.targetX = (e.clientX - centerX) * this.options.strength;
        this.targetY = (e.clientY - centerY) * this.options.strength;
    }
    
    onMouseLeave() {
        this.targetX = 0;
        this.targetY = 0;
    }
    
    animate() {
        this.currentX += (this.targetX - this.currentX) * this.options.ease;
        this.currentY += (this.targetY - this.currentY) * this.options.ease;
        
        this.element.style.transform = `translate(${this.currentX}px, ${this.currentY}px)`;
        
        requestAnimationFrame(this.animate.bind(this));
    }
    
    destroy() {
        this.element.removeEventListener('mousemove', this.onMouseMove);
        this.element.removeEventListener('mouseleave', this.onMouseLeave);
        this.element.style.transform = '';
    }
}

// ========================================
// 3D Tilt Card
// ========================================

/**
 * 3D Tilt Card Effect
 */
export class TiltCard {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            perspective: 1000,
            maxRotationX: 5,
            maxRotationY: 5,
            scale: 1.02,
            transition: 0.1,
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.element || prefersReducedMotion()) return;
        
        this.element.style.transformStyle = 'preserve-3d';
        this.element.style.perspective = `${this.options.perspective}px`;
        
        this.element.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.element.addEventListener('mouseleave', this.onMouseLeave.bind(this));
    }
    
    onMouseMove(e) {
        const rect = this.element.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = ((y - centerY) / centerY) * -this.options.maxRotationX;
        const rotateY = ((x - centerX) / centerX) * this.options.maxRotationY;
        
        this.element.style.transform = `
            perspective(${this.options.perspective}px)
            rotateX(${rotateX}deg)
            rotateY(${rotateY}deg)
            scale(${this.options.scale})
        `;
    }
    
    onMouseLeave() {
        this.element.style.transform = `
            perspective(${this.options.perspective}px)
            rotateX(0)
            rotateY(0)
            scale(1)
        `;
    }
    
    destroy() {
        this.element.removeEventListener('mousemove', this.onMouseMove);
        this.element.removeEventListener('mouseleave', this.onMouseLeave);
    }
}

// ========================================
// Ripple Effect
// ========================================

/**
 * Ripple Effect on Click
 */
export class Ripple {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            color: 'rgba(255, 255, 255, 0.3)',
            duration: 600,
            scale: 2,
            ...options
        };
        
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        this.element.style.position = 'relative';
        this.element.style.overflow = 'hidden';
        
        this.element.addEventListener('click', this.createRipple.bind(this));
    }
    
    createRipple(e) {
        const rect = this.element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * this.options.scale;
        
        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            top: ${e.clientY - rect.top - size / 2}px;
            left: ${e.clientX - rect.left - size / 2}px;
            width: ${size}px;
            height: ${size}px;
            background: ${this.options.color};
            border-radius: 50%;
            transform: scale(0);
            animation: ripple ${this.options.duration}ms ease-out forwards;
            pointer-events: none;
        `;
        
        // Add keyframes if not exists
        if (!document.getElementById('ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        this.element.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), this.options.duration);
    }
    
    destroy() {
        this.element.removeEventListener('click', this.createRipple);
    }
}

// ========================================
// Long Press
// ========================================

/**
 * Long Press Detection
 */
export class LongPress {
    constructor(element, callback, options = {}) {
        this.element = element;
        this.callback = callback;
        this.options = {
            duration: 500,
            ...options
        };
        
        this.timer = null;
        
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        this.element.addEventListener('mousedown', this.start.bind(this));
        this.element.addEventListener('mouseup', this.cancel.bind(this));
        this.element.addEventListener('mouseleave', this.cancel.bind(this));
        
        // Touch support
        this.element.addEventListener('touchstart', this.start.bind(this));
        this.element.addEventListener('touchend', this.cancel.bind(this));
    }
    
    start(e) {
        this.timer = setTimeout(() => {
            this.callback(e);
            this.timer = null;
        }, this.options.duration);
    }
    
    cancel() {
        if (this.timer) {
            clearTimeout(this.timer);
            this.timer = null;
        }
    }
    
    destroy() {
        this.cancel();
        this.element.removeEventListener('mousedown', this.start);
        this.element.removeEventListener('mouseup', this.cancel);
        this.element.removeEventListener('mouseleave', this.cancel);
        this.element.removeEventListener('touchstart', this.start);
        this.element.removeEventListener('touchend', this.cancel);
    }
}

// ========================================
// Drag and Drop
// ========================================

/**
 * Simple Drag Handler
 */
export class DragHandler {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            handle: null,
            bounds: null,
            onDragStart: () => {},
            onDrag: () => {},
            onDragEnd: () => {},
            ...options
        };
        
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.initialX = 0;
        this.initialY = 0;
        
        this.init();
    }
    
    init() {
        const handle = this.options.handle || this.element;
        
        handle.addEventListener('mousedown', this.onMouseDown.bind(this));
        document.addEventListener('mousemove', this.onMouseMove.bind(this));
        document.addEventListener('mouseup', this.onMouseUp.bind(this));
        
        // Touch support
        handle.addEventListener('touchstart', this.onTouchStart.bind(this));
        document.addEventListener('touchmove', this.onTouchMove.bind(this));
        document.addEventListener('touchend', this.onTouchEnd.bind(this));
    }
    
    onMouseDown(e) {
        e.preventDefault();
        this.startDrag(e.clientX, e.clientY);
    }
    
    onTouchStart(e) {
        this.startDrag(e.touches[0].clientX, e.touches[0].clientY);
    }
    
    startDrag(x, y) {
        this.isDragging = true;
        this.startX = x;
        this.startY = y;
        
        const rect = this.element.getBoundingClientRect();
        this.initialX = rect.left;
        this.initialY = rect.top;
        
        this.options.onDragStart({
            x: this.initialX,
            y: this.initialY,
            element: this.element
        });
    }
    
    onMouseMove(e) {
        if (!this.isDragging) return;
        this.drag(e.clientX, e.clientY);
    }
    
    onTouchMove(e) {
        if (!this.isDragging) return;
        this.drag(e.touches[0].clientX, e.touches[0].clientY);
    }
    
    drag(x, y) {
        const deltaX = x - this.startX;
        const deltaY = y - this.startY;
        
        let newX = this.initialX + deltaX;
        let newY = this.initialY + deltaY;
        
        // Apply bounds
        if (this.options.bounds) {
            const bounds = typeof this.options.bounds === 'string'
                ? document.querySelector(this.options.bounds).getBoundingClientRect()
                : this.options.bounds;
            
            newX = Math.max(bounds.left, Math.min(newX, bounds.right - this.element.offsetWidth));
            newY = Math.max(bounds.top, Math.min(newY, bounds.bottom - this.element.offsetHeight));
        }
        
        this.element.style.position = 'fixed';
        this.element.style.left = newX + 'px';
        this.element.style.top = newY + 'px';
        this.element.style.zIndex = '9999';
        
        this.options.onDrag({
            x: newX,
            y: newY,
            deltaX,
            deltaY,
            element: this.element
        });
    }
    
    onMouseUp() {
        if (this.isDragging) {
            this.endDrag();
        }
    }
    
    onTouchEnd() {
        if (this.isDragging) {
            this.endDrag();
        }
    }
    
    endDrag() {
        this.isDragging = false;
        this.options.onDragEnd({ element: this.element });
    }
    
    destroy() {
        document.removeEventListener('mousemove', this.onMouseMove);
        document.removeEventListener('mouseup', this.onMouseUp);
        document.removeEventListener('touchmove', this.onTouchMove);
        document.removeEventListener('touchend', this.onTouchEnd);
    }
}

// ========================================
// Double Tap
// ========================================

/**
 * Double Tap Detection
 */
export class DoubleTap {
    constructor(element, callback, options = {}) {
        this.element = element;
        this.callback = callback;
        this.options = {
            delay: 300,
            ...options
        };
        
        this.lastTap = 0;
        
        this.init();
    }
    
    init() {
        if (!this.element) return;
        
        this.element.addEventListener('click', this.handleClick.bind(this));
    }
    
    handleClick(e) {
        const now = Date.now();
        
        if (now - this.lastTap <= this.options.delay) {
            this.callback(e);
            this.lastTap = 0;
        } else {
            this.lastTap = now;
        }
    }
    
    destroy() {
        this.element.removeEventListener('click', this.handleClick);
    }
}

// Export all
export default {
    CustomCursor,
    MagneticButton,
    TiltCard,
    Ripple,
    LongPress,
    DragHandler,
    DoubleTap
};
