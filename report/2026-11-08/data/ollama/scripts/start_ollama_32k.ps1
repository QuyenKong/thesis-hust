$env:OLLAMA_MODELS = 'D:\ollama\models'
$env:OLLAMA_CONTEXT_LENGTH = '32768'
$log = 'D:\hust-master\Thesis\report\2026-11-08\data\ollama'
$p = Start-Process -FilePath 'C:\Users\qdcon\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve' `
  -WindowStyle Hidden -RedirectStandardError "$log\server_ctx32768.log" -RedirectStandardOutput "$log\server_ctx32768.out.log" -PassThru
$p.Id
