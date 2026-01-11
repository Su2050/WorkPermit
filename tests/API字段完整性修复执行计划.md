# API字段完整性修复执行计划

## 执行状态总览

| 阶段 | 任务 | 状态 | 备注 |
|------|------|------|------|
| **阶段1** | 修复Videos模块 | ✅ 已完成 | 代码已修复，后端测试通过 |
| **阶段2** | 创建测试用例 | ✅ 已完成 | 后端和前端测试用例已创建 |
| **阶段3** | 运行测试验证 | ⏳ 进行中 | 后端测试通过，前端测试待执行 |
| **阶段4** | 更新文档 | ✅ 已完成 | 检查报告和修复计划已创建 |

## 详细执行步骤

### ✅ 阶段1：修复Videos模块（已完成）

#### 1.1 修复前端代码
- [x] 文件：`admin-web/src/views/videos/index.vue`
- [x] 添加 `sitesApi` 和 `useAppStore` 导入
- [x] 在form中添加 `site_id` 字段
- [x] 添加site_id获取逻辑
- [x] 在创建请求中包含 `site_id`
- [x] 添加错误处理

**修改内容：**
```javascript
// 1. 添加导入
import { sitesApi } from '@/api/sites'
import { useAppStore } from '@/stores/app'

// 2. 添加site_id获取逻辑
let siteId = appStore.currentSiteId
if (!siteId) {
  const sitesResponse = await sitesApi.getOptions()
  if (sitesResponse.data?.code === 0 && sitesResponse.data.data?.length > 0) {
    siteId = sitesResponse.data.data[0].site_id || sitesResponse.data.data[0].id
  }
}

// 3. 在创建请求中包含site_id
response = await videosApi.create({
  site_id: siteId,
  // ... 其他字段
})
```

### ✅ 阶段2：创建测试用例（已完成）

#### 2.1 后端API测试
- [x] 创建 `tests/backend/test_videos_create_site_id.py`
- [x] 测试缺少site_id时返回422错误
- [x] 测试提供site_id时成功创建
- [x] 测试无效site_id时返回错误

**测试结果：** ✅ 3个测试全部通过

#### 2.2 前端UI测试
- [x] 创建 `tests/test_videos_create_ui.py`
- [x] 测试打开创建对话框
- [x] 测试表单字段完整性
- [x] 测试成功创建视频（验证site_id传递）
- [x] 测试无工地时的错误处理

### ⏳ 阶段3：运行测试验证（进行中）

#### 3.1 后端API测试 ✅
```bash
# 已执行，全部通过
python -m pytest tests/backend/test_videos_create_site_id.py -v
# 结果：3 passed
```

#### 3.2 前端UI测试 ⏳
```bash
# 需要启动前端和后端服务后执行
python -m pytest tests/test_videos_create_ui.py -v -s
```

**前置条件：**
- 前端服务运行在 `http://localhost:5173`
- 后端服务运行在 `http://localhost:8000`
- 数据库中有至少一个工地

#### 3.3 综合测试 ⏳
```bash
# 运行所有site_id相关测试
python -m pytest tests/backend/test_*_create_site_id.py -v

# 运行所有创建流程UI测试
python -m pytest tests/test_*_create_ui.py -v -s
```

### ✅ 阶段4：更新文档（已完成）

- [x] 创建 `tests/API字段完整性检查与修复计划.md`
- [x] 创建 `tests/API字段完整性检查报告.md`
- [x] 创建 `tests/新增人员bug修复测试报告.md`
- [x] 创建 `tests/API字段完整性修复执行计划.md`（本文件）

## 待执行任务

### 优先级P0（必须执行）

1. **运行前端UI测试验证Videos模块修复**
   ```bash
   python -m pytest tests/test_videos_create_ui.py -v -s
   ```
   - 验证创建视频时site_id正确传递
   - 验证无工地时的错误处理

2. **验证Areas模块（虽然已有site_id，但需要确认）**
   - 检查前端代码是否正确传递site_id
   - 运行现有测试验证

### 优先级P1（建议执行）

3. **运行所有相关测试进行回归测试**
   ```bash
   # 后端API测试
   python -m pytest tests/backend/test_workers_api.py tests/backend/test_videos_api.py -v
   
   # 前端UI测试
   python -m pytest tests/test_workers_create_ui.py tests/test_videos_create_ui.py -v -s
   ```

4. **更新测试用例清单**
   - 更新 `doc/TEST_CASES_CHECKLIST.md`
   - 添加新增的测试用例

## 验证清单

### Videos模块修复验证
- [x] 代码已修复
- [x] 后端测试通过
- [ ] 前端UI测试通过（待执行）
- [ ] 手动测试创建视频功能（待执行）

### Workers模块修复验证
- [x] 代码已修复
- [x] 后端测试通过
- [x] 前端UI测试已创建
- [ ] 手动测试创建人员功能（待执行）

### 整体验证
- [ ] 所有模块创建功能正常
- [ ] 无422错误
- [ ] 错误提示清晰
- [ ] 测试覆盖完整

## 下一步行动

1. **立即执行：**
   - 启动前端和后端服务
   - 运行前端UI测试：`python -m pytest tests/test_videos_create_ui.py -v -s`
   - 手动测试创建视频功能

2. **后续改进：**
   - 添加API契约测试自动化
   - 更新开发文档，明确site_id获取规范
   - 代码审查时检查必填字段

## 风险提示

- ⚠️ **前端UI测试需要服务运行**：确保前端和后端服务都已启动
- ⚠️ **数据库状态**：确保数据库中有至少一个工地，否则测试会失败
- ⚠️ **测试环境**：前端UI测试使用Playwright，需要浏览器环境

## 成功标准

1. ✅ 所有后端API测试通过
2. ⏳ 所有前端UI测试通过
3. ⏳ 手动测试所有创建功能正常
4. ✅ 代码修复完成
5. ✅ 测试用例创建完成
6. ✅ 文档更新完成

## 时间线

- **2026-01-11 18:00** - 开始检查
- **2026-01-11 18:30** - 发现问题（Workers和Videos）
- **2026-01-11 19:00** - 修复Workers模块
- **2026-01-11 19:30** - 修复Videos模块
- **2026-01-11 20:00** - 创建测试用例
- **2026-01-11 20:30** - 运行后端测试验证
- **待执行** - 运行前端UI测试验证

