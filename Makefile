# Makefile for WorkPermit Project
# 提供便捷的命令来运行测试和开发任务

.PHONY: help e2e e2e-headless e2e-cleanup

help:
	@echo "可用命令:"
	@echo "  make e2e              - 运行E2E测试（可视化模式，显示浏览器）"
	@echo "  make e2e-headless  - 运行E2E测试（无头模式，不显示浏览器）"
	@echo "  make e2e-cleanup   - 运行E2E测试并清理测试数据"
	@echo ""
	@echo "环境变量:"
	@echo "  SHOW_BROWSER=true/false  - 控制是否显示浏览器（默认: true）"
	@echo "  SLOW_MO=500              - 操作延迟时间，单位毫秒（默认: 500）"

# 运行E2E测试（可视化模式，显示浏览器）
e2e:
	@echo "🚀 运行E2E测试（可视化模式）..."
	@export SHOW_BROWSER=true && \
	export SLOW_MO=500 && \
	pytest tests/test_e2e_business_workflow.py -v -s --tb=short

# 运行E2E测试（无头模式，不显示浏览器）
e2e-headless:
	@echo "🚀 运行E2E测试（无头模式）..."
	@export SHOW_BROWSER=false && \
	export SLOW_MO=100 && \
	pytest tests/test_e2e_business_workflow.py -v -s --tb=short

# 运行E2E测试并清理测试数据
e2e-cleanup:
	@echo "🚀 运行E2E测试并清理数据..."
	@export SHOW_BROWSER=true && \
	export SLOW_MO=500 && \
	pytest tests/test_e2e_business_workflow.py -v -s --tb=short --cleanup

