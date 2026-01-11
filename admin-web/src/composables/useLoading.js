/**
 * 加载状态管理 Composable (P2-5)
 * 
 * 提供统一的加载状态管理功能
 */

import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useLoading(initialState = false) {
  const loading = ref(initialState)
  const error = ref(null)
  
  /**
   * 执行异步操作并管理加载状态
   * @param {Function} asyncFn - 异步函数
   * @param {Object} options - 配置选项
   * @returns {Promise} 异步函数的结果
   */
  async function execute(asyncFn, options = {}) {
    const {
      errorMessage = '操作失败',
      successMessage = null,
      showError = true,
      showSuccess = false,
      onSuccess = null,
      onError = null
    } = options
    
    loading.value = true
    error.value = null
    
    try {
      const result = await asyncFn()
      
      if (successMessage && showSuccess) {
        ElMessage.success(successMessage)
      }
      
      if (onSuccess) {
        onSuccess(result)
      }
      
      return result
    } catch (err) {
      error.value = err
      
      if (showError) {
        ElMessage.error(errorMessage)
      }
      
      if (onError) {
        onError(err)
      }
      
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 设置加载状态
   * @param {Boolean} state - 加载状态
   */
  function setLoading(state) {
    loading.value = state
  }
  
  /**
   * 重置状态
   */
  function reset() {
    loading.value = false
    error.value = null
  }
  
  return {
    loading,
    error,
    execute,
    setLoading,
    reset
  }
}

/**
 * 多个加载状态管理
 * @param {Object} initialStates - 初始状态对象
 * @returns {Object} 加载状态管理对象
 */
export function useMultipleLoading(initialStates = {}) {
  const loadingStates = {}
  
  for (const key in initialStates) {
    loadingStates[key] = ref(initialStates[key])
  }
  
  function setLoading(key, state) {
    if (loadingStates[key]) {
      loadingStates[key].value = state
    }
  }
  
  function isAnyLoading() {
    return Object.values(loadingStates).some(state => state.value)
  }
  
  function resetAll() {
    for (const key in loadingStates) {
      loadingStates[key].value = false
    }
  }
  
  return {
    ...loadingStates,
    setLoading,
    isAnyLoading,
    resetAll
  }
}

