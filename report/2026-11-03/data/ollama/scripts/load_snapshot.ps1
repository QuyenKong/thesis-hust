param([string]$Tag)
$out = "D:/hust-master/Thesis/report/2026-11-03/data/ollama/load_$Tag.txt"
$t = Get-Date -Format o
$l = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average
$cores = (Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
$p = Get-Process | Where-Object { $_.Name -match 'sumo|python|ollama' } |
    Select-Object Name, Id, CPU, @{n = 'WS_MB'; e = { [int]($_.WorkingSet64 / 1MB) } }, StartTime |
    Format-Table -AutoSize | Out-String -Width 200
$g = nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv | Out-String
$text = "time $t`r`ncpu_load_pct $l (logical processors $cores)`r`n$p`r`n$g"
Set-Content -Path $out -Value $text -Encoding utf8
Write-Output $text
