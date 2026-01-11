/**
 * 防抖 Composable (P2-5)
 * 
 * 提供防抖功能，优化频繁操作
 */

import { ref, watch, onUnmounted } from 'vue'

/**
 * 防抖函数
 * @param {Function} fn - 要防抖的函数
 * @param {Number} delay - 延迟时间（毫秒）
 * @returns {Function} 防抖后的函数
 */
export function debounce(fn, delay = 300) {
  let timeoutId = null
  
  return function (...args) {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    
    timeoutId = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * 防抖 Ref
 * @param {Ref} value - 响应式值
 * @param {Number} delay - 延迟时间（毫秒）
 * @returns {Ref} 防抖后的响应式值
 */
export function useDebouncedRef(value, delay = 300) {
  const debouncedValue = ref(value.value)
  let timeoutId = null
  
  watch(value, (newValue) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    
    timeoutId = setTimeout(() => {
      debouncedValue.value = newValue
    }, delay)
  })
  
  onUnmounted(() => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
  })
  
  return debouncedValue
}

/**
 * 节流函数
 * @param {Function} fn - 要节流的函数
 * @param {Number} delay - 延迟时间（毫秒）
 * @returns {Function} 节流后的函数
 */
export function throttle(fn, delay = 300) {
  let lastCall = 0
  
  return function (...args) {
    const now = Date.now()
    
    if (now - lastCall >= delay) {
      lastCall = now
      fn.apply(this, args)
    }
  }
}

