# Docker 磁盘空间不足 - 快速修复指南

## 🚨 紧急情况：Docker 无法启动

如果 Docker Desktop 因为磁盘空间不足无法启动，请按以下步骤操作：

### 步骤 1: 关闭 Docker Desktop

1. 打开任务管理器（`Ctrl + Shift + Esc`）
2. 结束所有 Docker 相关进程：
   - `Docker Desktop`
   - `com.docker.backend`
   - `com.docker.proxy`

### 步骤 2: 压缩 WSL2 磁盘（Windows）

这是最有效的方法，可以释放大量空间：

```powershell
# 1. 以管理员身份打开 PowerShell

# 2. 关闭所有 WSL 实例
wsl --shutdown

# 3. 等待几秒确保完全关闭

# 4. 运行磁盘压缩脚本（自动查找并压缩 Docker 的 vhdx 文件）
# 或者手动使用 diskpart：
```

**手动压缩方法：**

```powershell
# 在管理员 PowerShell 中：
wsl --shutdown

# 打开 diskpart
diskpart

# 在 diskpart 中执行（替换 <YourUser> 为你的用户名）：
select vdisk file="C:\Users\<YourUser>\AppData\Local\Docker\wsl\data\ext4.vhdx"
compact vdisk
exit
```

**或者使用自动化脚本：**

```powershell
# 查找 Docker vhdx 文件位置
$vhdxPath = "$env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx"

if (Test-Path $vhdxPath) {
    Write-Host "找到 Docker 磁盘文件: $vhdxPath"
    Write-Host "正在压缩..."

    wsl --shutdown
    Start-Sleep -Seconds 5

    # 使用 diskpart 压缩
    $diskpartScript = @"
select vdisk file="$vhdxPath"
compact vdisk
exit
"@

    $diskpartScript | diskpart
    Write-Host "压缩完成！"
} else {
    Write-Host "未找到 Docker 磁盘文件"
}
```

### 步骤 3: 清理 Docker 临时文件

```powershell
# 清理 Docker 临时目录（确保 Docker Desktop 已关闭）
$dockerPaths = @(
    "$env:LOCALAPPDATA\Docker\wsl\data",
    "$env:LOCALAPPDATA\Docker\tmp"
)

foreach ($path in $dockerPaths) {
    if (Test-Path $path) {
        Write-Host "清理: $path"
        Get-ChildItem $path -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    }
}
```

### 步骤 4: 使用 Windows 磁盘清理

1. 按 `Win + R`，输入 `cleanmgr`
2. 选择系统盘（通常是 C:）
3. 勾选所有选项，特别是：
   - 临时文件
   - 系统错误内存转储文件
   - Windows 更新清理

### 步骤 5: 重新启动 Docker Desktop

1. 启动 Docker Desktop
2. 等待完全启动
3. 运行清理脚本：

```powershell
.\scripts\cleanup-docker.ps1 -DiskSpace
```

## ✅ Docker 可以运行时的清理

如果 Docker 可以启动，直接运行：

```powershell
# 推荐：使用清理脚本（保留数据卷）
.\scripts\cleanup-docker.ps1 -DiskSpace

# 如果需要重启服务
.\scripts\cleanup-docker.ps1 -DiskSpace -Restart
```

## 📊 检查磁盘使用情况

```powershell
# 查看 Docker 资源使用
docker system df

# 查看详细使用情况
docker system df -v

# 查看 WSL2 磁盘使用（Windows）
wsl --list --verbose
```

## 🔍 查找占用空间的文件

```powershell
# 查找 Docker 相关的大文件
Get-ChildItem "$env:LOCALAPPDATA\Docker" -Recurse -File |
    Sort-Object Length -Descending |
    Select-Object -First 10 FullName, @{Name="Size(GB)";Expression={[math]::Round($_.Length/1GB,2)}}
```

## ⚠️ 注意事项

1. **数据备份**: 清理前确保重要数据已备份
2. **数据卷**: `-DiskSpace` 选项不会删除数据卷，数据是安全的
3. **构建缓存**: 清理构建缓存后，下次构建可能需要更长时间
4. **WSL2 压缩**: 压缩 vhdx 文件可能需要较长时间，请耐心等待

## 🆘 Docker 运行在 E 盘且空间不足

如果 Docker 安装在 E 盘且 E 盘空间不足：

```powershell
# 检查 E 盘 Docker 使用情况
.\scripts\check-docker-e-drive.ps1

# 预览清理（不实际删除）
.\scripts\cleanup-docker-e-drive.ps1 -DryRun

# 执行清理
.\scripts\cleanup-docker-e-drive.ps1

# 或者使用快速修复
.\scripts\fix-docker-e-drive.ps1
```

**重要提示**：

- E 盘需要至少 10GB 可用空间才能正常启动 Docker
- 如果 E 盘几乎满了（< 1GB），Docker 将无法启动
- 考虑将 Docker 数据迁移到其他有更多空间的驱动器

## 🆘 Docker 卡在启动界面

如果 Docker Desktop 一直卡在启动界面，使用专门的修复脚本：

```powershell
# 先诊断问题
.\scripts\fix-docker-startup.ps1 -Diagnose

# 执行修复
.\scripts\fix-docker-startup.ps1

# 强制修复（不询问确认）
.\scripts\fix-docker-startup.ps1 -Force
```

修复脚本会自动：

1. ✅ 强制关闭所有 Docker 进程
2. ✅ 关闭 WSL2
3. ✅ 清理临时文件
4. ✅ 压缩 WSL2 磁盘（需要管理员权限）
5. ✅ 重置网络配置

## 🆘 如果仍然无法启动

如果清理后 Docker 仍然无法启动：

1. **检查磁盘空间**:

   ```powershell
   Get-PSDrive C | Select-Object Used,Free
   ```

2. **检查 Docker 日志**:

   - Docker Desktop 设置 → Troubleshoot → View logs
   - 或查看: `%LOCALAPPDATA%\Docker\log.txt`

3. **检查 WSL2**:

   ```powershell
   # 查看 WSL2 状态
   wsl --list --verbose

   # 如果 WSL2 有问题，尝试重置
   wsl --shutdown
   wsl --unregister docker-desktop
   wsl --unregister docker-desktop-data
   ```

4. **重置 Docker Desktop**（最后手段，会删除所有数据）:

   - Docker Desktop 设置 → Troubleshoot → Reset to factory defaults
   - 或手动删除: `%LOCALAPPDATA%\Docker`

5. **重新安装 Docker Desktop**:
   - 完全卸载后重新安装

## 📝 预防措施

定期运行清理脚本：

```powershell
# 每周运行一次
.\scripts\cleanup-docker.ps1 -DiskSpace
```

设置 Docker Desktop 自动清理：

1. Docker Desktop 设置 → Resources → Advanced
2. 启用 "Automatically clean up unused data"
