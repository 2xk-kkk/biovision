# 搜索所有可能的上传目录
$possiblePaths = @(
    "c:\Users\Vivian\biovision\uploads",
    "c:\Users\Vivian\biovision\backend\uploads",
    "c:\Users\Vivian\uploads",
    "c:\uploads"
)

Write-Host "正在搜索可能的上传目录..."

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        Write-Host "找到目录: $path"
        $files = Get-ChildItem -Path $path -File
        Write-Host "  文件数量: $($files.Count)"
        $files | Select-Object Name | Format-Table -AutoSize
    }
}