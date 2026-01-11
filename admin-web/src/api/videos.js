import request from './request'

export const videosApi = {
  // 获取视频列表
  getList(params) {
    return request.get('/admin/videos', { params })
  },
  
  // 获取视频详情
  getDetail(id) {
    return request.get(`/admin/videos/${id}`)
  },
  
  // 创建视频
  create(data) {
    return request.post('/admin/videos', data)
  },
  
  // 更新视频
  update(id, data) {
    return request.patch(`/admin/videos/${id}`, data)
  },
  
  // 删除视频
  delete(id) {
    return request.delete(`/admin/videos/${id}`)
  },
  
  // 上传视频
  upload(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post('/admin/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(percent)
        }
      }
    })
  },
  
  // 获取视频选项（下拉框用）
  getOptions(params) {
    return request.get('/admin/videos/options', { params })
  }
}

