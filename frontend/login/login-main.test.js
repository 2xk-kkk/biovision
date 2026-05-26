/**
 * Tests for input blur event handler in login-main.html (lines 587-589)
 *
 * Code under test:
 *   input.addEventListener('blur', function () {
 *       this.parentElement.style.transform = 'scale(1)';
 *   });
 *
 * This handler resets the parent element's transform to scale(1)
 * when the input field loses focus (blur event).
 */

import { describe, it, expect, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Helper: initialize the DOM and attach the event listeners exactly
// as done in the source code (lines 581-589 of login-main.html)
// ---------------------------------------------------------------------------
function initInputHandlers() {
  const inputs = document.querySelectorAll('.input-field');
  inputs.forEach((input) => {
    input.addEventListener('focus', function () {
      this.parentElement.style.transform = 'scale(1.02)';
    });
    input.addEventListener('blur', function () {
      this.parentElement.style.transform = 'scale(1)';
    });
  });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('blur event handler on .input-field', () => {
  beforeEach(() => {
    // Set up minimal DOM structure matching login-main.html
    document.body.innerHTML = `
      <div class="input-group">
        <label for="username">用户名</label>
        <input type="text" id="username" class="input-field" placeholder="请输入用户名">
      </div>
      <div class="input-group">
        <label for="password">密码</label>
        <input type="password" id="password" class="input-field" placeholder="请输入密码">
      </div>
    `;
    initInputHandlers();
  });

  // ── Normal path ──────────────────────────────────────────────────────
  it('should reset parent transform to scale(1) on blur', () => {
    const input = document.getElementById('username');
    const parent = input.parentElement;

    // Dispatch blur directly (no prior focus needed — it's an independent behavior)
    input.dispatchEvent(new FocusEvent('blur'));

    expect(parent.style.transform).toBe('scale(1)');
  });

  // ── Focus → blur sequence ────────────────────────────────────────────
  it('should set scale(1.02) on focus then reset to scale(1) on blur', () => {
    const input = document.getElementById('username');
    const parent = input.parentElement;

    input.dispatchEvent(new FocusEvent('focus'));
    expect(parent.style.transform).toBe('scale(1.02)');

    input.dispatchEvent(new FocusEvent('blur'));
    expect(parent.style.transform).toBe('scale(1)');
  });

  // ── Multiple inputs: independence ────────────────────────────────────
  it('should handle blur independently for each input', () => {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const usernameParent = usernameInput.parentElement;
    const passwordParent = passwordInput.parentElement;

    // Focus username, blur password — each operates on its own parent
    usernameInput.dispatchEvent(new FocusEvent('focus'));
    expect(usernameParent.style.transform).toBe('scale(1.02)');

    // Blur password — only password's parent should reset
    passwordInput.dispatchEvent(new FocusEvent('blur'));
    expect(passwordParent.style.transform).toBe('scale(1)');
    // Username parent should still have scale(1.02)
    expect(usernameParent.style.transform).toBe('scale(1.02)');

    // Blur username now — both should be reset
    usernameInput.dispatchEvent(new FocusEvent('blur'));
    expect(usernameParent.style.transform).toBe('scale(1)');
  });

  // ── Idempotent blur ──────────────────────────────────────────────────
  it('should be idempotent when blurring multiple times', () => {
    const input = document.getElementById('username');
    const parent = input.parentElement;

    // Blur twice
    input.dispatchEvent(new FocusEvent('blur'));
    input.dispatchEvent(new FocusEvent('blur'));

    expect(parent.style.transform).toBe('scale(1)');
  });

  // ── Blur without focus ───────────────────────────────────────────────
  it('should set scale(1) even if focus was never triggered', () => {
    const input = document.getElementById('username');
    const parent = input.parentElement;

    // No focus dispatched, go straight to blur
    input.dispatchEvent(new FocusEvent('blur'));

    expect(parent.style.transform).toBe('scale(1)');
  });

  // ── Boundary: no .input-field elements exist ─────────────────────────
  it('should not throw when no .input-field elements are present', () => {
    // Replace body with empty DOM (no inputs)
    document.body.innerHTML = '<div></div>';

    expect(() => initInputHandlers()).not.toThrow();
  });

  // ── Boundary: input with no parentElement ────────────────────────────
  it('should throw when input is not inside a parent container', () => {
    // Create an orphan input (not attached to a parent in the body)
    document.body.innerHTML = '';
    const orphanInput = document.createElement('input');
    orphanInput.className = 'input-field';
    // Directly run the handler logic
    orphanInput.addEventListener('blur', function () {
      this.parentElement.style.transform = 'scale(1)';
    });

    // parentElement is null for a detached node
    expect(() => orphanInput.dispatchEvent(new FocusEvent('blur'))).toThrow();
  });

  // ── Focus+blur on password field ─────────────────────────────────────
  it('should work correctly on the password field as well', () => {
    const input = document.getElementById('password');
    const parent = input.parentElement;

    input.dispatchEvent(new FocusEvent('focus'));
    expect(parent.style.transform).toBe('scale(1.02)');

    input.dispatchEvent(new FocusEvent('blur'));
    expect(parent.style.transform).toBe('scale(1)');
  });
});
