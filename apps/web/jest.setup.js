import '@testing-library/jest-dom'

// Mock global objects that might be used in tests
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  disconnect() {}
  unobserve() {}
}

// Mock matchMedia
global.matchMedia = global.matchMedia || function() {
  return {
    matches: false,
    addListener: function() {},
    removeListener: function() {},
  }
}

// Mock alert to avoid jsdom not-implemented errors
if (typeof globalThis.alert !== 'function') {
  globalThis.alert = () => {}
}
if (typeof globalThis.window !== 'undefined' && typeof globalThis.window.alert !== 'function') {
  globalThis.window.alert = () => {}
}
