# Git 大文件防护配置指南

本文档说明如何配置 Git 以防止上传不重要的大文件。

## 已完成的配置

### 1. `.gitignore` 文件增强

已在 `.gitignore` 中添加了以下规则：

- **视频和音频文件**: `*.mp4`, `*.avi`, `*.mov`, `*.mp3`, `*.wav` 等
- **大型数据文件**: `*.csv`, `*.pkl`, `*.h5`, `*.parquet` 等
- **测试数据文件**: `tests/**/*_test_data.*`
- **临时输出文件**: `vision_content*.txt`, `new_vision_content*.txt` 等
- **压缩文件**: `*.zip`, `*.tar.gz`, `*.rar` 等
- **大型日志文件**: `*.log.gz`, `*.log.zip` 等

**注意**: 图片文件（`*.png`, `*.jpg`）和文档文件（`*.pdf`, `*.docx`）的规则已添加但被注释，如果需要忽略这些文件，请取消注释。

### 2. Git Pre-Push Hook

已创建 `.git/hooks/pre-push` hook，在推送前自动检查大文件（>10MB）。

**功能**:

- 自动检查即将推送的提交中的大文件
- 如果发现超过 10MB 的文件，会阻止推送并显示警告
- 提供解决建议

**如何禁用**（如果需要）:

```bash
# 临时禁用
git push --no-verify

# 永久禁用（删除或重命名 hook 文件）
mv .git/hooks/pre-push .git/hooks/pre-push.disabled
```

### 3. Git 性能优化配置

已配置以下 Git 设置以提升性能：

- `core.preloadindex = true` - 预加载索引
- `core.fsmonitor = true` - 启用文件系统监控

## 使用方法

### 检查已跟踪的大文件

使用 PowerShell 脚本检查：

```powershell
.\scripts\prevent-large-files.ps1
```

### 从 Git 中移除已跟踪的大文件

如果大文件已经被 Git 跟踪，需要从历史记录中移除：

```bash
# 1. 从暂存区移除（如果已暂存）
git reset HEAD <file>

# 2. 从 .gitignore 中添加该文件
echo "path/to/large/file" >> .gitignore

# 3. 从 Git 索引中移除（但保留本地文件）
git rm --cached <file>

# 4. 提交更改
git commit -m "Remove large file from tracking"
```

### 使用 Git LFS 管理大文件

如果某些大文件需要版本控制（如模型文件），可以使用 Git LFS：

```bash
# 1. 安装 Git LFS（如果未安装）
# Windows: choco install git-lfs
# macOS: brew install git-lfs
# Linux: sudo apt-get install git-lfs

# 2. 初始化 Git LFS
git lfs install

# 3. 跟踪特定文件类型
git lfs track "*.pt"
git lfs track "*.pth"
git lfs track "*.ckpt"

# 4. 提交 .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"

# 5. 添加大文件
git add model.pt
git commit -m "Add model file via LFS"
```

## 配置自定义文件大小限制

### 修改 Pre-Push Hook 的大小限制

编辑 `.git/hooks/pre-push`，修改以下行：

```bash
# 将 10MB 改为其他值（例如 5MB）
MAX_FILE_SIZE=5242880  # 5MB in bytes
```

### 修改 PowerShell 脚本的大小限制

编辑 `scripts/prevent-large-files.ps1`，修改以下行：

```powershell
$MAX_FILE_SIZE = 5MB  # 改为所需大小
```

## 常见问题

### Q: Hook 在 Windows 上不工作？

A: 确保 Git Bash 已安装，或者使用 PowerShell 脚本手动检查：

```powershell
.\scripts\prevent-large-files.ps1
```

### Q: 如何忽略特定的大文件？

A: 在 `.gitignore` 中添加文件路径或模式：

```
# 忽略特定文件
path/to/specific/large/file.bin

# 忽略特定目录
large_data/
```

### Q: 已经推送了大文件怎么办？

A: 需要从 Git 历史中完全移除（**注意：这会重写历史**）：

```bash
# 使用 git filter-repo（推荐）或 BFG Repo-Cleaner
# 安装: pip install git-filter-repo

git filter-repo --path path/to/large/file --invert-paths
git push --force
```

**警告**: 强制推送会重写远程历史，确保团队成员已同步。

## 最佳实践

1. **定期检查**: 在提交前运行 `prevent-large-files.ps1` 检查
2. **使用 Git LFS**: 对于需要版本控制的大文件（模型、数据集）
3. **使用外部存储**: 对于非常大的文件，考虑使用云存储（S3、OSS 等）
4. **文档说明**: 在 README 中说明大文件的存储位置和获取方式

## 相关资源

- [Git LFS 文档](https://git-lfs.github.com/)
- [Git 忽略文件文档](https://git-scm.com/docs/gitignore)
- [Git Hooks 文档](https://git-scm.com/docs/githooks)
