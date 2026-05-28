# 合并所有上传目录的文件到主目录
$mainUploads = "c:\Users\Vivian\biovision\uploads"
$oldUploads = "c:\Users\Vivian\biovision\backend\uploads"

Write-Host "正在将 $oldUploads 中的文件复制到 $mainUploads..."

$oldFiles = Get-ChildItem -Path $oldUploads -File
$copiedCount = 0

foreach ($file in $oldFiles) {
    $dstPath = Join-Path -Path $mainUploads -ChildPath $file.Name
    if (-not (Test-Path $dstPath)) {
        Copy-Item -Path $file.FullName -Destination $dstPath
        Write-Host "复制: $($file.Name)"
        $copiedCount++
    }
}

Write-Host "复制完成！共复制了 $copiedCount 个文件。"

# 检查主目录总文件数
$totalFiles = (Get-ChildItem -Path $mainUploads -File).Count
Write-Host "主目录现在共有 $totalFiles 个文件。"